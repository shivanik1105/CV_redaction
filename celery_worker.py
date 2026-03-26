"""
Celery Worker for CV Processing Pipeline
Handles async CV processing with rate limiting and retry logic
"""
import os
import sys
import logging
import time
from pathlib import Path
from celery import Celery
from redis import Redis

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from queue_manager import QueueManager
from rate_limiter import RateLimiter
from enhanced_triage import get_triage_engine
from universal_pipeline_engine import PipelineOrchestrator
from cv_intelligence_extractor import CVIntelligenceExtractor, is_cv_anonymized
from llm_batch_processor import QuotaExhaustedException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Celery configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
BACKEND_URL = BROKER_URL

# Create Celery app
app = Celery(
    'cv_processing',
    broker=BROKER_URL,
    backend=BACKEND_URL
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

# Initialize Redis client
redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# Initialize queue manager and rate limiter
queue_manager = QueueManager(
    redis_host=REDIS_HOST,
    redis_port=REDIS_PORT,
    redis_db=REDIS_DB,
    redis_password=REDIS_PASSWORD
)

rate_limiter = RateLimiter(redis_client)

# Initialize processing components (lazy load)
_orchestrator = None
_intelligence_extractor = None

def get_orchestrator():
    """Get or create pipeline orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator(config_dir='config')
    return _orchestrator

def get_intelligence_extractor():
    """Get or create intelligence extractor"""
    global _intelligence_extractor
    if _intelligence_extractor is None:
        api_provider = os.getenv('LLM_PROVIDER', 'gemini')
        _intelligence_extractor = CVIntelligenceExtractor(api_provider=api_provider)
    return _intelligence_extractor


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_cv_task(self, job_id: str):
    """
    Celery task to process a CV
    
    Args:
        job_id: Job identifier from queue
    
    Returns:
        Result dictionary with intelligence data
    """
    logger.info(f"Starting task for job {job_id}")
    
    try:
        # Get job data
        job_data = queue_manager.get_job_status(job_id)
        if not job_data:
            logger.error(f"Job {job_id} not found")
            return {"error": "Job not found"}
        
        cv_path = job_data["cv_path"]
        job_description = job_data["job_description"]
        
        # Check if CV file exists
        if not os.path.exists(cv_path):
            error_msg = f"CV file not found: {cv_path}"
            logger.error(error_msg)
            queue_manager.update_job_status(job_id, QueueManager.STATUS_FAILED, error=error_msg)
            return {"error": error_msg}
        
        # Determine if CV needs redaction
        needs_redaction = not cv_path.startswith("REDACTED_")
        
        if needs_redaction:
            # Step 1: Redact PII
            logger.info(f"Redacting CV: {cv_path}")
            orchestrator = get_orchestrator()
            
            try:
                redacted_text, profile = orchestrator.process_cv(cv_path)
            except Exception as e:
                error_msg = f"Redaction failed: {str(e)}"
                logger.error(error_msg)
                queue_manager.update_job_status(job_id, QueueManager.STATUS_FAILED, error=error_msg)
                return {"error": error_msg}
            
            # Save redacted output
            output_dir = Path('redacted_output')
            output_dir.mkdir(exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            redacted_filename = f"REDACTED_{timestamp}_{Path(cv_path).name}.txt"
            redacted_path = output_dir / redacted_filename
            
            with open(redacted_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
            
            cv_text = redacted_text
            cv_filename = redacted_filename
        else:
            # CV already redacted, read it
            with open(cv_path, 'r', encoding='utf-8') as f:
                cv_text = f.read()
            cv_filename = Path(cv_path).name
        
        # Verify anonymization
        if not is_cv_anonymized(cv_text):
            error_msg = "CV is not properly anonymized"
            logger.error(error_msg)
            queue_manager.update_job_status(job_id, QueueManager.STATUS_FAILED, error=error_msg)
            return {"error": error_msg}
        
        # Step 2: Enhanced Triage - Check relevance before LLM call
        logger.info(f"Running triage check for job {job_id}")
        triage_engine = get_triage_engine()
        should_process, triage_reason, relevance_score = triage_engine.should_process(
            cv_text, job_description
        )
        
        if not should_process:
            # CV rejected by triage - save rejection reason without LLM call
            logger.info(f"CV rejected by triage: {triage_reason}")
            
            intelligence = {
                "anonymized_id": f"CAND_{hash(cv_filename) % 1000:03d}",
                "analysis_date": time.strftime('%Y-%m-%dT%H:%M:%S'),
                "verdict": "REJECT",
                "confidence_score": 100,
                "match_score": int(relevance_score * 100),
                "verdict_reason": f"TRIAGE FILTER: {triage_reason}",
                "years_experience": 0,
                "seniority_level": "N/A",
                "core_technical_skills": [],
                "secondary_technical_skills": [],
                "primary_domain": "",
                "secondary_domains": [],
                "leadership_indicators": [],
                "cleaned_narrative": f"CV auto-rejected by triage filter. Relevance score: {relevance_score:.1%}",
                "matched_requirements": [],
                "missing_requirements": [],
                "key_strengths": [],
                "potential_concerns": [triage_reason],
                "fitment_analysis": [],
                "requires_human_review": False,
                "triage_filtered": True,
                "relevance_score": relevance_score,
                "original_filename": cv_filename
            }
            
            # Save intelligence JSON
            intelligence_dir = Path('llm_analysis')
            intelligence_dir.mkdir(exist_ok=True)
            
            intelligence_filename = f"{Path(cv_filename).stem}_intelligence.json"
            intelligence_path = intelligence_dir / intelligence_filename
            
            import json
            with open(intelligence_path, 'w', encoding='utf-8') as f:
                json.dump(intelligence, f, indent=2, ensure_ascii=False)
            
            # Store in Supabase if available
            stored_in_supabase = False
            try:
                from supabase_storage import SupabaseStorage
                storage = SupabaseStorage()
                storage.store_intelligence(intelligence)
                stored_in_supabase = True
            except Exception as e:
                logger.warning(f"Could not store in Supabase: {e}")
            
            # Update job status to completed (rejected by triage)
            result = {
                "intelligence": intelligence,
                "intelligence_file": intelligence_filename,
                "stored_in_supabase": stored_in_supabase,
                "triage_filtered": True,
                "relevance_score": relevance_score
            }
            
            queue_manager.update_job_status(job_id, QueueManager.STATUS_COMPLETED, result=result)
            
            logger.info(f"Completed job {job_id} (triage rejected, no LLM call)")
            return result
        
        # CV passed triage, proceed with LLM extraction
        logger.info(f"CV passed triage ({relevance_score:.1%} relevance), proceeding with LLM extraction")
        
        # Step 3: Check rate limit before LLM call
        extractor = get_intelligence_extractor()
        api_provider = extractor.api_provider
        
        max_wait_attempts = 5
        wait_attempt = 0
        
        while not rate_limiter.check_quota(api_provider):
            wait_time = rate_limiter.get_wait_time(api_provider)
            
            if wait_attempt >= max_wait_attempts:
                # Requeue job for later
                logger.warning(f"Rate limit exceeded, requeueing job {job_id}")
                queue_manager.requeue_job(job_id, delay_seconds=wait_time)
                return {"status": "requeued", "reason": "rate_limit", "wait_time": wait_time}
            
            logger.info(f"Rate limit hit, waiting {wait_time}s (attempt {wait_attempt + 1}/{max_wait_attempts})")
            time.sleep(min(wait_time, 60))  # Wait max 60s per attempt
            wait_attempt += 1
        
        # Step 4: Extract intelligence with LLM
        logger.info(f"Extracting intelligence for job {job_id}")
        
        try:
            intelligence = extractor.extract_intelligence(
                cv_text,
                job_description,
                cv_filename
            )
            
            # Record API call for rate limiting
            rate_limiter.record_api_call(api_provider)
            
        except QuotaExhaustedException as e:
            # Quota exhausted, requeue job
            logger.warning(f"Quota exhausted: {e}")
            wait_time = rate_limiter.get_wait_time(api_provider)
            queue_manager.requeue_job(job_id, delay_seconds=wait_time)
            return {"status": "requeued", "reason": "quota_exhausted", "wait_time": wait_time}
        
        except Exception as e:
            error_msg = f"Intelligence extraction failed: {str(e)}"
            logger.error(error_msg)
            
            # Check if it's a retryable error
            if "429" in str(e) or "rate" in str(e).lower():
                # Rate limit error, requeue
                wait_time = rate_limiter.get_wait_time(api_provider)
                queue_manager.requeue_job(job_id, delay_seconds=wait_time)
                return {"status": "requeued", "reason": "rate_limit_error", "wait_time": wait_time}
            
            # Non-retryable error
            queue_manager.update_job_status(job_id, QueueManager.STATUS_FAILED, error=error_msg)
            return {"error": error_msg}
        
        # Check for extraction errors
        if intelligence.get("error") == "CV_NOT_ANONYMIZED":
            error_msg = intelligence.get("error_message", "CV not anonymized")
            queue_manager.update_job_status(job_id, QueueManager.STATUS_FAILED, error=error_msg)
            return {"error": error_msg}
        
        # Step 5: Save intelligence JSON
        intelligence_dir = Path('llm_analysis')
        intelligence_dir.mkdir(exist_ok=True)
        
        intelligence_filename = f"{Path(cv_filename).stem}_intelligence.json"
        intelligence_path = intelligence_dir / intelligence_filename
        
        import json
        with open(intelligence_path, 'w', encoding='utf-8') as f:
            json.dump(intelligence, f, indent=2, ensure_ascii=False)
        
        # Step 6: Store in Supabase if available
        stored_in_supabase = False
        try:
            from supabase_storage import SupabaseStorage
            storage = SupabaseStorage()
            storage.store_intelligence(intelligence)
            
            # Store filename mapping
            anon_id = intelligence.get('anonymized_id')
            if anon_id:
                storage.store_filename_mapping(
                    anonymized_id=anon_id,
                    original_filename=cv_filename,
                    anonymized_filename=cv_filename
                )
            
            # Step 7: Generate and store embedding
            try:
                from vector_search import generate_embedding_for_intelligence
                
                logger.info(f"Generating embedding for {anon_id}")
                embedding = generate_embedding_for_intelligence(intelligence)
                
                if embedding:
                    storage.store_embedding(anon_id, embedding)
                    logger.info(f"Stored embedding for {anon_id}")
            except Exception as e:
                logger.warning(f"Could not generate/store embedding: {e}")
            
            stored_in_supabase = True
            logger.info(f"Stored intelligence in Supabase for job {job_id}")
        except Exception as e:
            logger.warning(f"Could not store in Supabase: {e}")
        
        # Update job status to completed
        result = {
            "intelligence": intelligence,
            "intelligence_file": intelligence_filename,
            "stored_in_supabase": stored_in_supabase,
            "similarity_score": intelligence.get('similarity_score')
        }
        
        queue_manager.update_job_status(job_id, QueueManager.STATUS_COMPLETED, result=result)
        
        logger.info(f"Completed job {job_id} successfully")
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Try to update job status
        try:
            queue_manager.update_job_status(job_id, QueueManager.STATUS_FAILED, error=error_msg)
        except:
            pass
        
        # Retry task if retries remaining
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))  # Exponential backoff
        
        return {"error": error_msg}


@app.task
def cleanup_old_jobs():
    """
    Periodic task to clean up old completed/failed jobs
    Run this daily via Celery beat
    """
    logger.info("Running job cleanup task")
    cleared = queue_manager.clear_completed_jobs(older_than_hours=24)
    logger.info(f"Cleaned up {cleared} old jobs")
    return {"cleared": cleared}


if __name__ == '__main__':
    # Start Celery worker
    logger.info("Starting Celery worker...")
    app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',  # 4 concurrent workers
        '--max-tasks-per-child=50'
    ])
