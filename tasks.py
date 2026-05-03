"""
Celery tasks for async CV processing.
All long-running operations moved here from Flask routes.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from celery import Task
from celery_app import celery

# Import pipeline components
from cv_redaction_pipeline import redact_cv_text
from cv_intelligence_extractor import CVIntelligenceExtractor
from vector_search import get_vector_search_engine
from supabase_storage import SupabaseStorage

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks for status updates."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure."""
        logger.error(f"Task {task_id} failed: {exc}", exc_info=True)
        # Update processing_jobs table
        try:
            update_processing_status(task_id, 'failed', error=str(exc))
        except Exception as e:
            logger.error(f"Failed to update processing status: {e}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Log task success."""
        logger.info(f"Task {task_id} completed successfully")


def update_processing_status(job_id: str, status: str, stage: str = None, error: str = None):
    """Update processing_jobs table in Supabase."""
    try:
        storage = SupabaseStorage()
        update_data = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        if stage:
            update_data['stage_completed'] = stage
        if error:
            update_data['error_message'] = error
        
        storage.client.table('processing_jobs').update(update_data).eq(
            'job_id', job_id
        ).execute()
    except Exception as e:
        logger.warning(f"Could not update processing status: {e}")


@celery.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60,
    name='tasks.process_cv_task'
)
def process_cv_task(
    self,
    job_id: str,
    upload_path: str,
    original_filename: str,
    job_description: Optional[str] = None,
    force_reprocess: bool = False,
    llm_runtime_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Process uploaded CV through full pipeline.
    
    Args:
        job_id: Unique job identifier
        upload_path: Path to uploaded CV file
        original_filename: Original filename
        job_description: Optional JD for matching
        force_reprocess: Force reprocessing even if exists
        llm_runtime_config: Optional LLM configuration
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info(f"Starting CV processing: {job_id} - {original_filename}")
        
        # Create processing job record
        try:
            storage = SupabaseStorage()
            storage.client.table('processing_jobs').insert({
                'job_id': job_id,
                'status': 'queued',
                'stage_completed': None,
                'candidate_id': None,
                'error_message': None
            }).execute()
        except Exception as e:
            logger.warning(f"Could not create processing job record: {e}")
        
        # Stage 1: Extract text from PDF/DOCX
        update_processing_status(job_id, 'processing', stage='extracting')
        
        from universal_pipeline_engine import PipelineOrchestrator
        orchestrator = PipelineOrchestrator()
        
        cv_path = Path(upload_path)
        if not cv_path.exists():
            raise FileNotFoundError(f"CV file not found: {upload_path}")
        
        # Extract text
        cv_text = orchestrator.extract_text_from_cv(cv_path)
        if not cv_text or len(cv_text.strip()) < 100:
            raise ValueError("CV text extraction failed or too short")
        
        # Stage 2: PII Redaction
        update_processing_status(job_id, 'processing', stage='redacting')
        logger.info(f"Redacting PII for job {job_id}")
        
        redacted_text, redaction_stats = redact_cv_text(cv_text)
        
        # Save redacted CV with anonymous filename (no original filename for privacy)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use only job_id and timestamp - NO original filename
        redacted_filename = f"REDACTED_{timestamp}_{job_id[:8]}.txt"
        output_folder = Path(os.getenv('OUTPUT_FOLDER', 'redacted_output'))
        output_folder.mkdir(exist_ok=True)
        redacted_path = output_folder / redacted_filename
        
        with open(redacted_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
        
        # Stage 3: Intelligence Extraction
        update_processing_status(job_id, 'processing', stage='extracting_intelligence')
        logger.info(f"Extracting intelligence for job {job_id}")
        
        extractor = CVIntelligenceExtractor(
            llm_provider=llm_runtime_config.get('llm_provider') if llm_runtime_config else None,
            api_key=llm_runtime_config.get('llm_api_key') if llm_runtime_config else None,
            model_name=llm_runtime_config.get('llm_model') if llm_runtime_config else None
        )
        
        intelligence = extractor.extract_intelligence(
            redacted_text=redacted_text,
            job_description=job_description,
            original_filename=original_filename
        )
        
        if not intelligence.get('success'):
            raise ValueError(f"Intelligence extraction failed: {intelligence.get('error')}")
        
        # Stage 4: Generate Embedding
        update_processing_status(job_id, 'processing', stage='generating_embedding')
        logger.info(f"Generating embedding for job {job_id}")
        
        engine = get_vector_search_engine()
        embedding = engine.generate_embedding(redacted_text)
        
        if not engine.validate_embedding(embedding):
            logger.warning(f"Invalid embedding generated for job {job_id}")
            embedding = None
        
        # Stage 5: Store in Supabase
        update_processing_status(job_id, 'processing', stage='storing')
        logger.info(f"Storing data in Supabase for job {job_id}")
        
        storage = SupabaseStorage()
        stored_data = storage.store_intelligence(intelligence)
        
        # Store embedding if generated
        if embedding and stored_data.get('anonymized_id'):
            storage.store_embedding(
                anonymized_id=stored_data['anonymized_id'],
                embedding=embedding
            )
        
        # Mark as complete
        update_processing_status(job_id, 'done', stage='completed')
        
        result = {
            'success': True,
            'job_id': job_id,
            'redacted_filename': redacted_filename,
            'intelligence': intelligence,
            'anonymized_id': stored_data.get('anonymized_id'),
            'redaction_stats': redaction_stats,
            'embedding_generated': embedding is not None
        }
        
        logger.info(f"CV processing completed: {job_id}")
        return result
        
    except Exception as e:
        logger.error(f"CV processing failed for job {job_id}: {e}", exc_info=True)
        update_processing_status(job_id, 'failed', error=str(e))
        
        # Retry on transient errors
        if 'rate limit' in str(e).lower() or 'timeout' in str(e).lower():
            raise self.retry(exc=e)
        
        return {
            'success': False,
            'job_id': job_id,
            'error': str(e)
        }


@celery.task(
    bind=True,
    base=CallbackTask,
    max_retries=2,
    default_retry_delay=30,
    name='tasks.generate_embedding_task'
)
def generate_embedding_task(self, text: str, cache_key: str = None) -> list:
    """
    Generate embedding for text (used for JD embeddings).
    
    Args:
        text: Text to embed
        cache_key: Optional Redis cache key
        
    Returns:
        Embedding vector as list
    """
    try:
        engine = get_vector_search_engine()
        embedding = engine.generate_embedding(text)
        
        if not engine.validate_embedding(embedding):
            raise ValueError("Invalid embedding generated")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery.task(
    bind=True,
    base=CallbackTask,
    name='tasks.search_candidates_task'
)
def search_candidates_task(
    self,
    job_description: str,
    limit: int = 10,
    filters: Dict = None
) -> Dict[str, Any]:
    """
    Search candidates by job description (high priority task).
    
    Args:
        job_description: Job description text
        limit: Maximum results
        filters: Optional filters (verdict, skills, etc.)
        
    Returns:
        Search results dictionary
    """
    try:
        storage = SupabaseStorage()
        
        # Generate JD embedding
        engine = get_vector_search_engine()
        jd_embedding = engine.generate_embedding(job_description)
        
        # Perform semantic search
        results = storage.semantic_search(
            query_text=job_description,
            limit=limit,
            similarity_threshold=0.5,
            filters=filters
        )
        
        return {
            'success': True,
            'candidates': results,
            'count': len(results)
        }
        
    except Exception as e:
        logger.error(f"Candidate search failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'candidates': []
        }


@celery.task(name='tasks.cleanup_old_files')
def cleanup_old_files_task():
    """
    Periodic task to cleanup old uploaded and redacted files.
    Run daily via Celery beat.
    """
    try:
        from datetime import timedelta
        import time
        
        now = time.time()
        max_age_days = 30
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        # Cleanup uploads
        upload_folder = Path(os.getenv('UPLOAD_FOLDER', 'uploads'))
        deleted_uploads = 0
        for file_path in upload_folder.glob('*'):
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    deleted_uploads += 1
        
        # Cleanup redacted files
        output_folder = Path(os.getenv('OUTPUT_FOLDER', 'redacted_output'))
        deleted_redacted = 0
        for file_path in output_folder.glob('REDACTED_*'):
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    deleted_redacted += 1
        
        logger.info(f"Cleanup: deleted {deleted_uploads} uploads, {deleted_redacted} redacted files")
        
        return {
            'deleted_uploads': deleted_uploads,
            'deleted_redacted': deleted_redacted
        }
        
    except Exception as e:
        logger.error(f"File cleanup failed: {e}", exc_info=True)
        return {'error': str(e)}
