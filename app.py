"""
Flask Web UI for CV Redaction Pipeline with Intelligence Extraction
Allows users to upload CVs, redact PII, extract intelligence, and search candidates
Supports both Supabase and local JSON-based storage with automatic fallback
"""
import dns_fix  # Fix JioFiber DNS hijacking - must be before any network imports
import os
import sys
import json
import glob
from typing import Optional
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Override system env vars with .env values
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our pipeline
from universal_pipeline_engine import PipelineOrchestrator
from cv_intelligence_extractor import CVIntelligenceExtractor

# Import Supabase storage (optional)
try:
    from supabase_storage import SupabaseStorage
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase not available. Install with: pip install supabase")

# Import Queue System (optional)
try:
    from queue_manager import QueueManager
    from rate_limiter import RateLimiter
    from celery_worker import process_cv_task
    from redis import Redis
    QUEUE_AVAILABLE = True
    print(f"DEBUG: QUEUE_AVAILABLE set to True")
except (ImportError, Exception) as e:
    QUEUE_AVAILABLE = False
    print(f"DEBUG: QUEUE_AVAILABLE set to False due to: {e}")
    logging.warning(f"Queue system not available: {e}")


# Configure Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'redacted_output'
app.config['INTELLIGENCE_FOLDER'] = 'llm_analysis'
app.secret_key = 'cv-redaction-secret-key-2024'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)
Path(app.config['INTELLIGENCE_FOLDER']).mkdir(exist_ok=True)

# Initialize intelligence extractor (lazy load)
_intelligence_extractor = None
_supabase_storage = None
_supabase_reachable = None  # Track if Supabase is actually reachable
_queue_manager = None
_rate_limiter = None

def get_intelligence_extractor():
    """Get or create intelligence extractor"""
    global _intelligence_extractor
    if _intelligence_extractor is None:
        api_provider = os.getenv('LLM_PROVIDER', 'gemini')
        _intelligence_extractor = CVIntelligenceExtractor(api_provider=api_provider)
    return _intelligence_extractor

def get_supabase_storage():
    """Get or create Supabase storage with timeout handling"""
    global _supabase_storage, _supabase_reachable
    if _supabase_reachable is False:
        return None
    if _supabase_storage is None and SUPABASE_AVAILABLE:
        try:
            _supabase_storage = SupabaseStorage()
            # Don't mark as reachable until first successful query
        except Exception as e:
            logger.warning(f"Supabase not reachable: {e}")
            _supabase_storage = None
            _supabase_reachable = False
    return _supabase_storage

def get_queue_manager():
    """Get or create queue manager"""
    global _queue_manager
    if _queue_manager is None and QUEUE_AVAILABLE:
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            _queue_manager = QueueManager(
                redis_host=redis_host,
                redis_port=redis_port,
                redis_db=redis_db,
                redis_password=redis_password
            )
            logger.info("Queue manager initialized")
        except Exception as e:
            logger.warning(f"Queue manager not available: {e}")
            _queue_manager = None
    return _queue_manager

def get_rate_limiter():
    """Get or create rate limiter"""
    global _rate_limiter
    if _rate_limiter is None and QUEUE_AVAILABLE:
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            redis_password = os.getenv('REDIS_PASSWORD', None)
            redis_client = Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True
            )
            _rate_limiter = RateLimiter(redis_client)
            logger.info("Rate limiter initialized")
        except Exception as e:
            logger.warning(f"Rate limiter not available: {e}")
            _rate_limiter = None
    return _rate_limiter

def try_supabase_operation(operation, fallback_result=None, timeout_seconds=5):
    """
    Try a Supabase operation with a timeout. Falls back gracefully on failure.
    
    Args:
        operation: callable to execute
        fallback_result: value to return on failure
        timeout_seconds: max seconds to wait
    
    Returns:
        Result of operation, or fallback_result on failure
    """
    import threading
    result_holder = [fallback_result]
    error_holder = [None]
    
    def run_operation():
        try:
            result_holder[0] = operation()
        except Exception as e:
            error_holder[0] = e
    
    thread = threading.Thread(target=run_operation, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        global _supabase_reachable
        _supabase_reachable = False
        logger.warning(f"Supabase operation timed out after {timeout_seconds}s, switching to local mode")
        return fallback_result
    
    if error_holder[0]:
        _supabase_reachable = False
        logger.warning(f"Supabase operation failed: {error_holder[0]}, switching to local mode")
        return fallback_result
    
    # Mark as reachable on success
    _supabase_reachable = True
    return result_holder[0]

def is_supabase_configured():
    """Check if Supabase credentials are configured (without connecting)"""
    return SUPABASE_AVAILABLE and bool(os.getenv('SUPABASE_URL')) and bool(os.getenv('SUPABASE_KEY'))


# ============================================================================
# LOCAL JSON STORAGE FALLBACK
# ============================================================================

def load_local_intelligence_files():
    """Load all intelligence JSON files from local disk as fallback data source"""
    intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
    candidates = []
    
    for json_file in intelligence_dir.glob('*_intelligence.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Skip files with errors
            if 'error' in data and not data.get('verdict'):
                continue
            
            # Ensure minimum required fields
            if not data.get('anonymized_id'):
                continue
            
            # Normalize fields for display
            candidate = {
                'anonymized_id': data.get('anonymized_id', 'UNKNOWN'),
                'verdict': data.get('verdict', 'REVIEW'),
                'confidence_score': data.get('confidence_score', 0),
                'match_score': data.get('match_score', 0),
                'years_experience': data.get('years_experience', 0),
                'seniority_level': data.get('seniority_level', 'N/A'),
                'core_technical_skills': data.get('core_technical_skills', []),
                'secondary_technical_skills': data.get('secondary_technical_skills', []),
                'frameworks_tools': data.get('frameworks_tools', []),
                'primary_domain': data.get('primary_domain', ''),
                'secondary_domains': data.get('secondary_domains', []),
                'leadership_indicators': data.get('leadership_indicators', []),
                'cleaned_narrative': data.get('cleaned_narrative', ''),
                'verdict_reason': data.get('verdict_reason', ''),
                'requires_human_review': data.get('requires_human_review', False),
                'recruiter_override': data.get('recruiter_override'),
                'original_filename': data.get('original_filename', ''),
                'analysis_date': data.get('analysis_date', ''),
                'matched_requirements': data.get('matched_requirements', []),
                'missing_requirements': data.get('missing_requirements', []),
                'key_strengths': data.get('key_strengths', []),
                'potential_concerns': data.get('potential_concerns', []),
                '_source': 'local_json',
                '_filename': str(json_file.name)
            }
            candidates.append(candidate)
        except Exception as e:
            logger.debug(f"Skipping {json_file.name}: {e}")
    
    return candidates

def get_local_statistics():
    """Calculate statistics from local JSON intelligence files"""
    candidates = load_local_intelligence_files()
    total = len(candidates)
    
    if total == 0:
        return {
            'total_candidates': 0,
            'shortlisted': 0,
            'backup': 0,
            'review_needed': 0,
            'requires_human_review': 0,
            'recruiter_reviewed': 0,
            'average_match_score': 0,
            'average_confidence_score': 0,
            'data_source': 'local_json'
        }
    
    shortlisted = len([c for c in candidates if c.get('verdict') == 'SHORTLIST'])
    backup = len([c for c in candidates if c.get('verdict') == 'BACKUP'])
    review = len([c for c in candidates if c.get('verdict') == 'REVIEW'])
    human_review = len([c for c in candidates if c.get('requires_human_review')])
    reviewed = len([c for c in candidates if c.get('recruiter_override')])
    avg_match = sum(c.get('match_score', 0) for c in candidates) / total
    avg_conf = sum(c.get('confidence_score', 0) for c in candidates) / total
    
    return {
        'total_candidates': total,
        'shortlisted': shortlisted,
        'backup': backup,
        'review_needed': review,
        'requires_human_review': human_review,
        'recruiter_reviewed': reviewed,
        'average_match_score': round(avg_match, 2),
        'average_confidence_score': round(avg_conf, 2),
        'data_source': 'local_json'
    }

def search_local_candidates(filters):
    """Search local JSON candidates with filters"""
    candidates = load_local_intelligence_files()
    
    verdict = filters.get('verdict')
    seniority = filters.get('seniority_level')
    min_score = filters.get('min_match_score')
    min_conf = filters.get('min_confidence_score')
    primary_domain = filters.get('primary_domain')
    min_years = filters.get('min_years_experience')
    max_years = filters.get('max_years_experience')
    required_skills = filters.get('required_skills')
    
    results = []
    for c in candidates:
        if verdict and c.get('verdict') != verdict:
            continue
        if seniority and c.get('seniority_level') != seniority:
            continue
        if min_score is not None and (c.get('match_score') or 0) < min_score:
            continue
        if min_conf is not None and (c.get('confidence_score') or 0) < min_conf:
            continue
        if primary_domain and primary_domain.lower() not in (c.get('primary_domain') or '').lower():
            continue
        if min_years is not None and (c.get('years_experience') or 0) < min_years:
            continue
        if max_years is not None and (c.get('years_experience') or 0) > max_years:
            continue
        if required_skills:
            candidate_skills = [s.lower() for s in (c.get('core_technical_skills') or [])]
            if not all(skill.lower() in candidate_skills for skill in required_skills):
                continue
        results.append(c)
    
    # Sort by match_score desc
    results.sort(key=lambda x: (x.get('match_score') or 0), reverse=True)
    return results


# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the upload page"""
    return render_template('index.html')

@app.route('/queue-monitor')
def queue_monitor():
    """Render the queue monitoring page"""
    return render_template('queue_monitor.html')

@app.route('/semantic-search')
def semantic_search_page():
    """Render the semantic search page"""
    return render_template('semantic_search.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process CV (with optional queue mode)"""
    try:
        # Check if file is present
        if 'cv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['cv_file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX files'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        
        logger.info(f"File uploaded: {upload_path}")
        
        # Check if queue mode is enabled and requested
        use_queue = request.form.get('use_queue', 'false').lower() == 'true'
        job_description = request.form.get('job_description', '')
        
        if use_queue and QUEUE_AVAILABLE and job_description:
            # Queue mode: enqueue job and return job_id
            queue_manager = get_queue_manager()
            if queue_manager:
                try:
                    job_id = queue_manager.enqueue_cv_processing(
                        cv_path=upload_path,
                        job_description=job_description,
                        priority=QueueManager.PRIORITY_NORMAL,
                        metadata={'original_filename': filename}
                    )
                    
                    # Trigger Celery task
                    process_cv_task.delay(job_id)
                    
                    return jsonify({
                        'success': True,
                        'mode': 'queued',
                        'job_id': job_id,
                        'message': 'CV queued for processing',
                        'status_url': url_for('get_job_status', job_id=job_id, _external=True)
                    })
                except Exception as e:
                    logger.warning(f"Queue failed, falling back to sync: {e}")
                    # Fall through to synchronous processing
        
        # Synchronous mode: process immediately
        try:
            # Create fresh orchestrator instance with latest code
            orchestrator = PipelineOrchestrator(config_dir='config')
            
            logger.info(f"Processing CV with pipeline...")
            redacted_text, profile = orchestrator.process_cv(upload_path)
            
            # Save the output
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"REDACTED_{unique_filename}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
            
            logger.info(f"CV processed successfully: {output_path}")
            
            # Return success response with download link
            return jsonify({
                'success': True,
                'mode': 'synchronous',
                'message': 'CV processed successfully',
                'output_filename': f"REDACTED_{unique_filename}.txt",
                'preview': redacted_text,  # Full text instead of truncated
                'download_url': url_for('download_file', filename=f"REDACTED_{unique_filename}.txt")
            })
            
        except Exception as e:
            logger.error(f"Error processing CV: {str(e)}", exc_info=True)
            return jsonify({'error': f'Error processing CV: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download the redacted CV"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='text/plain'
            )
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/health')
def health():
    """Health check endpoint with connection status"""
    supabase_configured = is_supabase_configured()
    supabase_status = 'configured' if supabase_configured else 'not configured'

    # Proactively probe Supabase if not yet checked
    if _supabase_reachable is None and supabase_configured:
        try:
            storage = get_supabase_storage()
            if storage:
                def _ping():
                    return storage.client.table('cv_intelligence').select('anonymized_id').limit(1).execute()
                try_supabase_operation(_ping, fallback_result=None, timeout_seconds=5)
        except Exception:
            pass

    if _supabase_reachable is True:
        supabase_status = 'connected'
    elif _supabase_reachable is False:
        supabase_status = 'configured but unreachable (using local fallback)'
    
    # Check queue system
    queue_status = 'not configured'
    if QUEUE_AVAILABLE:
        queue_manager = get_queue_manager()
        if queue_manager:
            try:
                queue_manager.redis.ping()
                queue_status = 'connected'
            except:
                queue_status = 'configured but unreachable'
    
    llm_provider = os.getenv('LLM_PROVIDER', 'gemini')
    
    # Count local data
    redacted_count = len(list(Path(app.config['OUTPUT_FOLDER']).glob('REDACTED_*.txt')))
    intelligence_count = len(list(Path(app.config['INTELLIGENCE_FOLDER']).glob('*_intelligence.json')))
    
    return jsonify({
        'status': 'healthy',
        'service': 'CV Redaction Pipeline',
        'supabase': supabase_status,
        'queue_system': queue_status,
        'llm_provider': llm_provider,
        'redacted_cvs': redacted_count,
        'intelligence_files': intelligence_count,
        'api_key_configured': bool(os.getenv('GOOGLE_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    })


@app.route('/api/queue/stats')
def get_queue_stats():
    """Get queue statistics"""
    if not QUEUE_AVAILABLE:
        return jsonify({'error': 'Queue system not available. Install redis and celery.'}), 503
    
    queue_manager = get_queue_manager()
    if not queue_manager:
        return jsonify({'error': 'Queue manager not initialized'}), 503
    
    try:
        stats = queue_manager.get_queue_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/queue/jobs', methods=['GET'])
def get_queued_jobs():
    """Get list of queued jobs"""
    if not QUEUE_AVAILABLE:
        return jsonify({'error': 'Queue system not available'}), 503
    
    queue_manager = get_queue_manager()
    if not queue_manager:
        return jsonify({'error': 'Queue manager not initialized'}), 503
    
    try:
        limit = request.args.get('limit', 100, type=int)
        jobs = queue_manager.get_queued_jobs(limit=limit)
        return jsonify({
            'success': True,
            'count': len(jobs),
            'jobs': jobs
        })
    except Exception as e:
        logger.error(f"Error getting queued jobs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """Get job status by ID"""
    if not QUEUE_AVAILABLE:
        return jsonify({'error': 'Queue system not available'}), 503
    
    queue_manager = get_queue_manager()
    if not queue_manager:
        return jsonify({'error': 'Queue manager not initialized'}), 503
    
    try:
        job_data = queue_manager.get_job_status(job_id)
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': job_data
        })
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id: str):
    """Cancel a queued job"""
    if not QUEUE_AVAILABLE:
        return jsonify({'error': 'Queue system not available'}), 503
    
    queue_manager = get_queue_manager()
    if not queue_manager:
        return jsonify({'error': 'Queue manager not initialized'}), 503
    
    try:
        success = queue_manager.cancel_job(job_id)
        if success:
            return jsonify({
                'success': True,
                'message': f'Job {job_id} cancelled'
            })
        else:
            return jsonify({'error': 'Failed to cancel job'}), 400
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rate-limit/stats', methods=['GET'])
def get_rate_limit_stats():
    """Get rate limit statistics for all LLM providers"""
    if not QUEUE_AVAILABLE:
        return jsonify({'error': 'Queue system not available'}), 503
    
    rate_limiter = get_rate_limiter()
    if not rate_limiter:
        return jsonify({'error': 'Rate limiter not initialized'}), 503
    
    try:
        stats = rate_limiter.get_all_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/triage/test', methods=['POST'])
def test_triage():
    """Test triage engine with CV and JD"""
    try:
        from enhanced_triage import get_triage_engine
        
        data = request.get_json()
        cv_text = data.get('cv_text')
        job_description = data.get('job_description')
        
        if not cv_text or not job_description:
            return jsonify({'error': 'Both cv_text and job_description required'}), 400
        
        triage_engine = get_triage_engine()
        should_process, reason, relevance_score = triage_engine.should_process(
            cv_text, job_description
        )
        
        # Extract keywords for debugging
        cv_keywords = triage_engine.extract_keywords(cv_text)
        jd_keywords = triage_engine.extract_keywords(job_description)
        intersection = cv_keywords.intersection(jd_keywords)
        
        priority = triage_engine.get_priority_from_score(relevance_score)
        
        return jsonify({
            'success': True,
            'should_process': should_process,
            'reason': reason,
            'relevance_score': relevance_score,
            'relevance_percent': f"{relevance_score * 100:.1f}%",
            'priority': priority,
            'priority_label': {0: 'HIGH', 5: 'NORMAL', 10: 'LOW'}.get(priority, 'UNKNOWN'),
            'cv_keywords_count': len(cv_keywords),
            'jd_keywords_count': len(jd_keywords),
            'matched_keywords_count': len(intersection),
            'matched_keywords': sorted(list(intersection))[:20],  # Show first 20
            'thresholds': {
                'extreme_mismatch': triage_engine.extreme_threshold,
                'poor_match': triage_engine.poor_threshold,
                'moderate_match': triage_engine.moderate_threshold
            }
        })
    except Exception as e:
        logger.error(f"Error testing triage: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/semantic', methods=['POST'])
def semantic_search():
    """Perform semantic search using vector embeddings"""
    try:
        data = request.get_json()
        query_text = data.get('query_text')
        
        if not query_text:
            return jsonify({'error': 'query_text required'}), 400
        
        limit = data.get('limit', 10)
        threshold = data.get('similarity_threshold', 0.7)
        filters = data.get('filters', {})
        
        # Try Supabase first
        storage = get_supabase_storage()
        if storage:
            results = try_supabase_operation(
                lambda: storage.semantic_search(
                    query_text=query_text,
                    limit=limit,
                    similarity_threshold=threshold,
                    filters=filters
                ),
                fallback_result=[],
                timeout_seconds=30
            )
            
            if results:
                return jsonify({
                    'success': True,
                    'query': query_text,
                    'count': len(results),
                    'results': results,
                    'data_source': 'supabase_vector'
                })
        
        # Local fallback - load embeddings from JSON files
        try:
            from vector_search import get_vector_search_engine
            
            engine = get_vector_search_engine()
            query_embedding = engine.generate_embedding(query_text)
            
            # Load local intelligence files with embeddings
            intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
            candidate_embeddings = []
            
            for json_file in intelligence_dir.glob('*_intelligence.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    embedding = data.get('embedding')
                    if embedding:
                        candidate_embeddings.append((
                            data.get('anonymized_id'),
                            embedding
                        ))
                except Exception:
                    continue
            
            # Search locally
            results = engine.search_local(
                query_embedding,
                candidate_embeddings,
                limit=limit,
                threshold=threshold
            )
            
            # Load full candidate data
            full_results = []
            for result in results:
                candidates = load_local_intelligence_files()
                candidate = next((c for c in candidates if c.get('anonymized_id') == result['candidate_id']), None)
                if candidate:
                    candidate['similarity_score'] = result['similarity_score']
                    full_results.append(candidate)
            
            return jsonify({
                'success': True,
                'query': query_text,
                'count': len(full_results),
                'results': full_results,
                'data_source': 'local_vector'
            })
            
        except Exception as e:
            logger.error(f"Local semantic search failed: {e}")
            return jsonify({'error': f'Semantic search not available: {str(e)}'}), 503
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/hybrid', methods=['POST'])
def hybrid_search():
    """Perform hybrid search (semantic + SQL filters)"""
    try:
        data = request.get_json()
        query_text = data.get('query_text')
        
        if not query_text:
            return jsonify({'error': 'query_text required'}), 400
        
        limit = data.get('limit', 10)
        filters = data.get('filters', {})
        semantic_weight = data.get('semantic_weight', 0.7)
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available for hybrid search'}), 503
        
        results = try_supabase_operation(
            lambda: storage.hybrid_search(
                query_text=query_text,
                filters=filters,
                limit=limit,
                semantic_weight=semantic_weight
            ),
            fallback_result=[],
            timeout_seconds=30
        )
        
        return jsonify({
            'success': True,
            'query': query_text,
            'count': len(results),
            'results': results,
            'semantic_weight': semantic_weight,
            'data_source': 'supabase_hybrid'
        })
        
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/redacted-files')
def list_redacted_files():
    """List all available redacted CV files"""
    try:
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        files = []
        for f in sorted(output_dir.glob('REDACTED_*.txt'), key=lambda x: x.stat().st_mtime, reverse=True):
            files.append({
                'filename': f.name,
                'size_bytes': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                'download_url': url_for('download_file', filename=f.name)
            })
        
        return jsonify({
            'success': True,
            'count': len(files),
            'files': files
        })
    except Exception as e:
        logger.error(f"Error listing redacted files: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Render the recruiter dashboard"""
    return render_template('dashboard.html')

@app.route('/api/extract-intelligence', methods=['POST'])
def extract_intelligence():
    """Extract intelligence from redacted CV with job description.
    Only processes anonymized CVs - returns error if CV is not anonymized.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        redacted_cv_file = data.get('redacted_cv_file')
        job_description = data.get('job_description')
        
        if not redacted_cv_file or not job_description:
            return jsonify({'error': 'Both redacted_cv_file and job_description required'}), 400
        
        # Read redacted CV
        cv_path = os.path.join(app.config['OUTPUT_FOLDER'], redacted_cv_file)
        if not os.path.exists(cv_path):
            return jsonify({'error': 'Redacted CV file not found'}), 404
        
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
        
        # Verify CV is anonymized before processing
        from cv_intelligence_extractor import is_cv_anonymized
        if not is_cv_anonymized(cv_text):
            return jsonify({
                'error': 'CV is not anonymized. Please redact PII first using the upload/redact feature before extracting intelligence.',
                'action_required': 'anonymize_first'
            }), 400
        
        # Extract intelligence
        extractor = get_intelligence_extractor()
        intelligence = extractor.extract_intelligence(
            cv_text,
            job_description,
            redacted_cv_file
        )
        
        # Check if extraction returned an error (e.g., CV not anonymized)
        if intelligence.get("error") == "CV_NOT_ANONYMIZED":
            return jsonify({
                'error': intelligence.get('error_message', 'CV is not anonymized'),
                'action_required': 'anonymize_first'
            }), 400
        
        # Save intelligence JSON locally (includes raw filename for local tracking)
        intelligence_file = f"{Path(redacted_cv_file).stem}_intelligence.json"
        intelligence_path = os.path.join(app.config['INTELLIGENCE_FOLDER'], intelligence_file)
        with open(intelligence_path, 'w', encoding='utf-8') as f:
            json.dump(intelligence, f, indent=2, ensure_ascii=False)
        
        # Store in Supabase if available (only anonymized data goes to DB)
        stored = False
        if SUPABASE_AVAILABLE and "error" not in intelligence:
            storage = get_supabase_storage()
            if storage:
                try:
                    storage.store_intelligence(intelligence)
                    # Also store filename mapping for tracking
                    anon_id = intelligence.get('anonymized_id')
                    if anon_id:
                        try:
                            storage.store_filename_mapping(
                                anonymized_id=anon_id,
                                original_filename=redacted_cv_file,
                                anonymized_filename=redacted_cv_file
                            )
                        except Exception as me:
                            logger.warning(f"Could not store filename mapping: {me}")
                    stored = True
                except Exception as e:
                    logger.warning(f"Could not store in Supabase: {e}")
        
        return jsonify({
            'success': True,
            'intelligence': intelligence,
            'intelligence_file': intelligence_file,
            'stored_in_supabase': stored,
            'similarity_score': intelligence.get('similarity_score')
        })
        
    except Exception as e:
        logger.error(f"Error extracting intelligence: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-samples', methods=['POST'])
def process_samples():
    """
    Full pipeline: Read original CVs from samples/ → Redact PII → Extract Intelligence → Store in DB.
    JD is provided dynamically from the request body (NOT hardcoded).
    
    Request body: {
        "job_description": "Senior Java Developer...",
        "force_reprocess": false  // optional: re-process even if cached results exist
    }
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description')
        force_reprocess = data.get('force_reprocess', False)
        
        if not job_description:
            return jsonify({'error': 'job_description is required. Paste the JD in the text area.'}), 400
        
        # Collect all original CVs from samples/ and samples/more/
        sample_dirs = [Path('samples'), Path('samples/more')]
        allowed_ext = {'.pdf', '.docx', '.doc'}
        original_cvs = []
        for sample_dir in sample_dirs:
            if sample_dir.exists():
                for f in sorted(sample_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in allowed_ext:
                        original_cvs.append(f)
        
        if not original_cvs:
            return jsonify({'error': 'No original CVs found in samples/ directory'}), 404
        
        logger.info(f"Processing {len(original_cvs)} original CVs with dynamic JD")
        
        # Initialize pipeline components
        orchestrator = PipelineOrchestrator(config_dir='config')
        extractor = get_intelligence_extractor()
        from cv_intelligence_extractor import is_cv_anonymized
        
        results = []
        redacted_count = 0
        intelligence_count = 0
        quota_exhausted = False  # Track if daily quota is hit
        consecutive_429 = 0  # Track consecutive rate-limit failures
        
        for idx, cv_path in enumerate(original_cvs):
            cv_name = cv_path.name
            
            # If quota is exhausted, skip LLM calls for remaining CVs
            if quota_exhausted:
                results.append({
                    'file': cv_name, 'status': 'skipped',
                    'error': 'Skipped — daily API quota exhausted. Already-processed CVs are saved. Re-run later without force_reprocess to continue.'
                })
                continue
            
            try:
                # Rate limit: pause between LLM calls to avoid 429
                if idx > 0:
                    import time
                    time.sleep(6)  # 6s gap = 10 RPM safe for free tier
                # STEP 1: Redact PII
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = secure_filename(cv_name)
                redacted_filename = f"REDACTED_{timestamp}_{safe_name}.txt"
                redacted_path = Path(app.config['OUTPUT_FOLDER']) / redacted_filename
                
                # Check if already redacted (skip if not force_reprocess)
                existing_redacted = list(Path(app.config['OUTPUT_FOLDER']).glob(f'REDACTED_*_{safe_name}*'))
                if existing_redacted and not force_reprocess:
                    redacted_path = existing_redacted[0]
                    redacted_filename = existing_redacted[0].name
                    logger.info(f"  Using cached redacted: {redacted_filename}")
                else:
                    logger.info(f"  Redacting: {cv_name}")
                    redacted_text, profile = orchestrator.process_cv(str(cv_path))
                    with open(redacted_path, 'w', encoding='utf-8') as f:
                        f.write(redacted_text)
                    redacted_count += 1
                
                # Read redacted text
                with open(redacted_path, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
                
                # Verify anonymization
                if not is_cv_anonymized(cv_text):
                    results.append({
                        'file': cv_name, 'status': 'error',
                        'error': 'Redaction did not produce anonymized output (possibly scanned/image CV)'
                    })
                    continue
                
                # STEP 2: Check cached intelligence (skip if not force_reprocess)
                if not force_reprocess:
                    existing_intel = list(Path(app.config['INTELLIGENCE_FOLDER']).glob(
                        f'{Path(redacted_filename).stem}_intelligence.json'
                    ))
                    if existing_intel:
                        try:
                            with open(existing_intel[0], 'r', encoding='utf-8') as f:
                                intelligence = json.load(f)
                            if 'error' not in intelligence:
                                results.append({
                                    'file': cv_name, 'status': 'success',
                                    'intelligence': intelligence, 'cached': True
                                })
                                continue
                        except Exception:
                            pass
                
                # STEP 3: Extract intelligence with the dynamic JD
                logger.info(f"  Analyzing with LLM: {cv_name}")
                intelligence = extractor.extract_intelligence(
                    cv_text, job_description, redacted_filename
                )
                
                if intelligence.get("error") == "CV_NOT_ANONYMIZED":
                    results.append({
                        'file': cv_name, 'status': 'error',
                        'error': 'CV not properly anonymized'
                    })
                    continue
                
                # Save intelligence JSON
                intel_filename = f"{Path(redacted_filename).stem}_intelligence.json"
                intel_path = Path(app.config['INTELLIGENCE_FOLDER']) / intel_filename
                with open(intel_path, 'w', encoding='utf-8') as f:
                    json.dump(intelligence, f, indent=2, ensure_ascii=False)
                intelligence_count += 1
                
                # Store in Supabase
                if SUPABASE_AVAILABLE and 'error' not in intelligence:
                    storage = get_supabase_storage()
                    if storage:
                        try:
                            storage.store_intelligence(intelligence)
                            anon_id = intelligence.get('anonymized_id')
                            if anon_id:
                                storage.store_filename_mapping(
                                    anonymized_id=anon_id,
                                    original_filename=redacted_filename,
                                    anonymized_filename=redacted_filename
                                )
                        except Exception as se:
                            logger.warning(f"Supabase store failed for {cv_name}: {se}")
                
                results.append({
                    'file': cv_name, 'status': 'success',
                    'intelligence': {
                        'anonymized_id': intelligence.get('anonymized_id'),
                        'verdict': intelligence.get('verdict'),
                        'confidence_score': intelligence.get('confidence_score'),
                        'match_score': intelligence.get('match_score'),
                        'years_experience': intelligence.get('years_experience'),
                        'seniority_level': intelligence.get('seniority_level'),
                        'core_technical_skills': intelligence.get('core_technical_skills', []),
                        'primary_domain': intelligence.get('primary_domain', ''),
                        'verdict_reason': intelligence.get('verdict_reason', '')
                    }
                })
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing {cv_name}: {error_msg}")
                
                # Detect quota exhaustion and abort remaining CVs
                if 'quota' in error_msg.lower() or 'rate limit exceeded' in error_msg.lower() or '429' in error_msg:
                    consecutive_429 += 1
                    if consecutive_429 >= 2:
                        quota_exhausted = True
                        logger.error(f"Quota exhausted after {consecutive_429} consecutive failures. Stopping LLM calls.")
                        results.append({'file': cv_name, 'status': 'error', 'error': 'API quota exhausted — stopping. Re-run later to continue.'})
                        continue
                else:
                    consecutive_429 = 0  # Reset on non-quota error
                
                results.append({'file': cv_name, 'status': 'error', 'error': error_msg})
        
        successful = len([r for r in results if r.get('status') == 'success'])
        skipped = len([r for r in results if r.get('status') == 'skipped'])
        
        return jsonify({
            'success': True,
            'total_originals': len(original_cvs),
            'redacted': redacted_count,
            'intelligence_extracted': intelligence_count,
            'successful': successful,
            'failed': len(original_cvs) - successful - skipped,
            'skipped': skipped,
            'quota_exhausted': quota_exhausted,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error processing samples: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch-extract', methods=['POST'])
def batch_extract_intelligence():
    """Batch extract intelligence from all redacted CVs.
    Only processes anonymized CVs — skips any that aren't properly redacted.
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description')
        force_reprocess = data.get('force_reprocess', False)
        
        if not job_description:
            return jsonify({'error': 'job_description required'}), 400
        
        # Get all redacted CV files
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        cv_files = list(output_dir.glob('REDACTED_*.txt'))
        
        if not cv_files:
            return jsonify({'error': 'No redacted CVs found. Process sample CVs first.'}), 404
        
        from cv_intelligence_extractor import is_cv_anonymized
        from llm_batch_processor import QuotaExhaustedException
        
        # Process in batch
        extractor = get_intelligence_extractor()
        results = []
        skipped_not_anonymized = 0
        quota_exhausted = False
        
        for cv_file in cv_files:
            # If quota exhausted, skip remaining immediately
            if quota_exhausted:
                results.append({
                    'file': cv_file.name,
                    'status': 'skipped',
                    'error': 'Skipped — API quota exhausted'
                })
                continue
            try:
                # Check if intelligence already exists (skip unless force_reprocess)
                intelligence_file = f"{cv_file.stem}_intelligence.json"
                intelligence_path = os.path.join(app.config['INTELLIGENCE_FOLDER'], intelligence_file)
                
                if os.path.exists(intelligence_path) and not force_reprocess:
                    try:
                        with open(intelligence_path, 'r', encoding='utf-8') as f:
                            intelligence = json.load(f)
                        results.append({
                            'file': cv_file.name,
                            'status': 'success' if 'error' not in intelligence else 'error',
                            'intelligence': intelligence,
                            'cached': True
                        })
                        continue
                    except:
                        pass # If invalid JSON, re-process

                with open(cv_file, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
                
                # Verify anonymization before processing
                if not is_cv_anonymized(cv_text):
                    skipped_not_anonymized += 1
                    results.append({
                        'file': cv_file.name,
                        'status': 'error',
                        'error': 'CV is not anonymized — please redact PII first'
                    })
                    continue
                
                intelligence = extractor.extract_intelligence(
                    cv_text,
                    job_description,
                    cv_file.name
                )
                
                # Save JSON
                intelligence_file = f"{cv_file.stem}_intelligence.json"
                intelligence_path = os.path.join(app.config['INTELLIGENCE_FOLDER'], intelligence_file)
                with open(intelligence_path, 'w', encoding='utf-8') as f:
                    json.dump(intelligence, f, indent=2, ensure_ascii=False)
                
                results.append({
                    'file': cv_file.name,
                    'status': 'success' if 'error' not in intelligence else 'error',
                    'intelligence': intelligence
                })
                
                # Store in Supabase if available
                if SUPABASE_AVAILABLE and "error" not in intelligence:
                    storage = get_supabase_storage()
                    if storage:
                        try:
                            storage.store_intelligence(intelligence)
                            # Also store filename mapping
                            anon_id = intelligence.get('anonymized_id')
                            if anon_id:
                                try:
                                    storage.store_filename_mapping(
                                        anonymized_id=anon_id,
                                        original_filename=cv_file.name,
                                        anonymized_filename=cv_file.name
                                    )
                                except Exception as me:
                                    logger.warning(f"Could not store filename mapping: {me}")
                        except Exception as e:
                            logger.warning(f"Could not store {cv_file.name} in Supabase: {e}")
                
            except QuotaExhaustedException as qe:
                logger.error(f"Quota exhausted during batch extract: {qe}")
                quota_exhausted = True
                results.append({
                    'file': cv_file.name,
                    'status': 'error',
                    'error': str(qe)
                })
                continue
            except Exception as e:
                logger.error(f"Error processing {cv_file}: {e}")
                results.append({
                    'file': cv_file.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        successful = len([r for r in results if r.get('status') == 'success'])
        skipped = len([r for r in results if r.get('status') == 'skipped'])
        
        response_data = {
            'success': True,
            'total': len(cv_files),
            'successful': successful,
            'failed': len(cv_files) - successful - skipped,
            'skipped': skipped,
            'quota_exhausted': quota_exhausted,
            'results': results
        }
        if skipped_not_anonymized > 0:
            response_data['skipped_not_anonymized'] = skipped_not_anonymized
            response_data['message'] = f'{skipped_not_anonymized} CVs were skipped because they are not anonymized. Please redact PII first.'
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        with open("last_error.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {str(e)}\n\nTraceback:\n")
            traceback.print_exc(file=f)
        logger.error(f"Error in batch extraction: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-candidates', methods=['POST'])
def search_candidates():
    """Search candidates using filters - with Supabase or local fallback"""
    try:
        data = request.get_json() or {}
        
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            raw_results = try_supabase_operation(
                lambda: storage.search_by_filters(
                    verdict=data.get('verdict'),
                    seniority_level=data.get('seniority_level'),
                    min_match_score=data.get('min_match_score'),
                    min_confidence_score=data.get('min_confidence_score'),
                    required_skills=data.get('required_skills'),
                    domains=data.get('domains'),
                    primary_domain=data.get('primary_domain'),
                    min_years_experience=data.get('min_years_experience'),
                    max_years_experience=data.get('max_years_experience'),
                    limit=data.get('limit', 50)
                ),
                fallback_result=None,
                timeout_seconds=10
            )
            if raw_results is not None:
                # Convert DB records to app format
                results = [storage._db_record_to_app_format(r) for r in raw_results]
                return jsonify({
                    'success': True,
                    'count': len(results),
                    'candidates': results,
                    'data_source': 'supabase'
                })
        
        # Local fallback
        results = search_local_candidates(data)
        return jsonify({
            'success': True,
            'count': len(results),
            'candidates': results,
            'data_source': 'local_json'
        })
        
    except Exception as e:
        logger.error(f"Error searching candidates: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidate/<anonymized_id>')
def get_candidate(anonymized_id):
    """Get specific candidate details by anonymized ID - with local fallback"""
    try:
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            raw_candidate = try_supabase_operation(
                lambda: storage.get_candidate(anonymized_id),
                fallback_result=None,
                timeout_seconds=10
            )
            if raw_candidate:
                candidate = storage._db_record_to_app_format(raw_candidate)
                return jsonify({
                    'success': True,
                    'candidate': candidate,
                    'data_source': 'supabase'
                })
        
        # Local fallback - search JSON files
        candidates = load_local_intelligence_files()
        candidate = next((c for c in candidates if c.get('anonymized_id') == anonymized_id), None)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        return jsonify({
            'success': True,
            'candidate': candidate,
            'data_source': 'local_json'
        })
        
    except Exception as e:
        logger.error(f"Error getting candidate: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get database statistics - with local fallback"""
    try:
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            result = try_supabase_operation(
                lambda: storage.get_statistics(),
                fallback_result=None,
                timeout_seconds=10
            )
            if result:
                result['data_source'] = 'supabase'
                return jsonify({'success': True, 'statistics': result})
        
        # Local fallback
        stats = get_local_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-candidates')
def get_all_candidates():
    """Get all candidates with pagination - with local fallback"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            raw_candidates = try_supabase_operation(
                lambda: storage.get_all_candidates(limit=limit),
                fallback_result=None,
                timeout_seconds=10
            )
            if raw_candidates is not None:
                # Convert DB records to app format
                candidates = [storage._db_record_to_app_format(r) for r in raw_candidates]
                return jsonify({
                    'success': True,
                    'count': len(candidates),
                    'candidates': candidates,
                    'data_source': 'supabase'
                })
        
        # Local fallback
        candidates = load_local_intelligence_files()[:limit]
        return jsonify({
            'success': True,
            'count': len(candidates),
            'candidates': candidates,
            'data_source': 'local_json'
        })
        
    except Exception as e:
        logger.error(f"Error getting all candidates: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/review-queue')
def get_review_queue():
    """Get candidates requiring human review (confidence < 70%) - with local fallback"""
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            candidates = try_supabase_operation(
                lambda: storage.get_candidates_requiring_review(limit=limit),
                fallback_result=None,
                timeout_seconds=5
            )
            if candidates is not None:
                return jsonify({
                    'success': True,
                    'count': len(candidates),
                    'candidates': candidates,
                    'message': f'{len(candidates)} candidates need human review (confidence <70% or unclear AI verdict)',
                    'data_source': 'supabase'
                })
        
        # Local fallback
        all_candidates = load_local_intelligence_files()
        candidates = [
            c for c in all_candidates
            if c.get('requires_human_review') and not c.get('recruiter_override')
        ]
        candidates.sort(key=lambda x: x.get('confidence_score', 0))
        candidates = candidates[:limit]
        
        return jsonify({
            'success': True,
            'count': len(candidates),
            'candidates': candidates,
            'message': f'{len(candidates)} candidates need human review (confidence <70% or unclear AI verdict)',
            'data_source': 'local_json'
        })
        
    except Exception as e:
        logger.error(f"Error getting review queue: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/recruiter-override/<anonymized_id>', methods=['POST'])
def add_recruiter_override(anonymized_id):
    """Add recruiter's final decision to candidate - with local fallback"""
    try:
        data = request.get_json()
        
        if not data or 'decision' not in data:
            return jsonify({'error': 'decision field required (SHORTLIST/REJECT/HIRED)'}), 400
        
        recruiter_decision = data.get('decision')
        recruiter_notes = data.get('notes', '')
        recruiter_id = data.get('recruiter_id', 'recruiter')
        
        # Validate decision
        valid_decisions = ['SHORTLIST', 'REJECT', 'HIRED', 'ON_HOLD']
        if recruiter_decision not in valid_decisions:
            return jsonify({'error': f'Invalid decision. Must be one of: {valid_decisions}'}), 400
        
        # Try Supabase first with timeout
        storage = get_supabase_storage()
        if storage:
            result = try_supabase_operation(
                lambda: storage.add_recruiter_override(
                    anonymized_id,
                    recruiter_decision,
                    recruiter_notes,
                    recruiter_id
                ),
                fallback_result=None,
                timeout_seconds=5
            )
            if result:
                return jsonify({
                    'success': True,
                    'message': f'Recruiter override added: {recruiter_decision}',
                    'candidate': result,
                    'data_source': 'supabase'
                })
        
        # Local fallback - update the JSON file
        intelligence_dir = Path(app.config['INTELLIGENCE_FOLDER'])
        updated = False
        for json_file in intelligence_dir.glob('*_intelligence.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                if file_data.get('anonymized_id') == anonymized_id:
                    file_data['recruiter_override'] = recruiter_decision
                    file_data['recruiter_notes'] = recruiter_notes
                    file_data['recruiter_id'] = recruiter_id
                    file_data['reviewed_at'] = datetime.now().isoformat()
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(file_data, f, indent=2, ensure_ascii=False)
                    updated = True
                    break
            except Exception:
                continue
        
        if updated:
            return jsonify({
                'success': True,
                'message': f'Recruiter override saved locally: {recruiter_decision}',
                'data_source': 'local_json'
            })
        else:
            return jsonify({'error': 'Candidate not found'}), 404
        
    except Exception as e:
        logger.error(f"Error adding recruiter override: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync-to-supabase', methods=['POST'])
def sync_to_supabase():
    """Sync all local intelligence JSON files to Supabase database"""
    try:
        if not is_supabase_configured():
            return jsonify({'error': 'Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env'}), 503
        
        # Reset the reachability flag to retry
        global _supabase_reachable, _supabase_storage
        _supabase_reachable = None
        _supabase_storage = None
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Cannot connect to Supabase. Is the project active?'}), 503
        
        candidates = load_local_intelligence_files()
        
        if not candidates:
            return jsonify({'error': 'No local intelligence files to sync'}), 404
        
        synced = 0
        errors = 0
        
        for candidate in candidates:
            try:
                # Load the full JSON file for this candidate
                filename = candidate.get('_filename', '')
                filepath = Path(app.config['INTELLIGENCE_FOLDER']) / filename
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        full_data = json.load(f)
                    
                    result = try_supabase_operation(
                        lambda d=full_data: storage.store_intelligence(d),
                        fallback_result=None,
                        timeout_seconds=10
                    )
                    if result is not None:
                        synced += 1
                    else:
                        errors += 1
            except Exception as e:
                logger.warning(f"Sync error for {candidate.get('anonymized_id')}: {e}")
                errors += 1
        
        return jsonify({
            'success': True,
            'total': len(candidates),
            'synced': synced,
            'errors': errors,
            'message': f'Synced {synced}/{len(candidates)} records to Supabase'
        })
        
    except Exception as e:
        logger.error(f"Error syncing to Supabase: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-status')
def connection_status():
    """Check real-time connection status of all services"""
    status = {
        'supabase': {
            'configured': is_supabase_configured(),
            'reachable': _supabase_reachable if _supabase_reachable is not None else 'unknown',
            'url': os.getenv('SUPABASE_URL', 'NOT SET')
        },
        'llm': {
            'provider': os.getenv('LLM_PROVIDER', 'not set'),
            'model': os.getenv('LLM_MODEL', 'default'),
            'api_key_set': bool(os.getenv('GOOGLE_API_KEY') or os.getenv('OPENAI_API_KEY'))
        },
        'local_data': {
            'redacted_cvs': len(list(Path(app.config['OUTPUT_FOLDER']).glob('REDACTED_*.txt'))),
            'intelligence_files': len(list(Path(app.config['INTELLIGENCE_FOLDER']).glob('*_intelligence.json')))
        },
        'env_loaded_from': '.env file' if os.path.exists('.env') else 'system environment'
    }
    return jsonify(status)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("CV Redaction Pipeline - Web Interface")
    print("="*60)
    print(f"\nServer starting...")
    print(f"Upload folder: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print(f"Output folder: {os.path.abspath(app.config['OUTPUT_FOLDER'])}")
    print(f"\nAccess the application at: http://localhost:5000")
    print(f"Press CTRL+C to stop the server\n")
    
    # Temporarily disable debug mode to avoid reloader issues
    app.run(debug=False, host='0.0.0.0', port=5000)
