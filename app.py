"""
Flask Web UI for CV Redaction Pipeline with Intelligence Extraction
Allows users to upload CVs, redact PII, extract intelligence, and search candidates
Supports both Supabase and local JSON-based storage with automatic fallback
"""
import os
import sys
import json
import glob
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
from datetime import datetime

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

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process CV"""
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
        
        # Process the CV
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
    if _supabase_reachable is True:
        supabase_status = 'connected'
    elif _supabase_reachable is False:
        supabase_status = 'configured but unreachable (using local fallback)'
    
    llm_provider = os.getenv('LLM_PROVIDER', 'gemini')
    
    # Count local data
    redacted_count = len(list(Path(app.config['OUTPUT_FOLDER']).glob('REDACTED_*.txt')))
    intelligence_count = len(list(Path(app.config['INTELLIGENCE_FOLDER']).glob('*_intelligence.json')))
    
    return jsonify({
        'status': 'healthy',
        'service': 'CV Redaction Pipeline',
        'supabase': supabase_status,
        'llm_provider': llm_provider,
        'redacted_cvs': redacted_count,
        'intelligence_files': intelligence_count,
        'api_key_configured': bool(os.getenv('GOOGLE_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    })

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
    """Extract intelligence from redacted CV with job description"""
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
        
        # Extract intelligence
        extractor = get_intelligence_extractor()
        intelligence = extractor.extract_intelligence(
            cv_text,
            job_description,
            redacted_cv_file
        )
        
        # Save intelligence JSON
        intelligence_file = f"{Path(redacted_cv_file).stem}_intelligence.json"
        intelligence_path = os.path.join(app.config['INTELLIGENCE_FOLDER'], intelligence_file)
        with open(intelligence_path, 'w', encoding='utf-8') as f:
            json.dump(intelligence, f, indent=2, ensure_ascii=False)
        
        # Store in Supabase if available
        stored = False
        if SUPABASE_AVAILABLE and "error" not in intelligence:
            storage = get_supabase_storage()
            if storage:
                try:
                    storage.store_intelligence(intelligence)
                    stored = True
                except Exception as e:
                    logger.warning(f"Could not store in Supabase: {e}")
        
        return jsonify({
            'success': True,
            'intelligence': intelligence,
            'intelligence_file': intelligence_file,
            'stored_in_supabase': stored
        })
        
    except Exception as e:
        logger.error(f"Error extracting intelligence: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch-extract', methods=['POST'])
def batch_extract_intelligence():
    """Batch extract intelligence from all redacted CVs"""
    try:
        data = request.get_json()
        job_description = data.get('job_description')
        
        if not job_description:
            return jsonify({'error': 'job_description required'}), 400
        
        # Get all redacted CV files
        output_dir = Path(app.config['OUTPUT_FOLDER'])
        cv_files = list(output_dir.glob('REDACTED_*.txt'))
        
        if not cv_files:
            return jsonify({'error': 'No redacted CVs found'}), 404
        
        # Process in batch
        extractor = get_intelligence_extractor()
        results = []
        
        for cv_file in cv_files:
            try:
                # Check if intelligence already exists
                intelligence_file = f"{cv_file.stem}_intelligence.json"
                intelligence_path = os.path.join(app.config['INTELLIGENCE_FOLDER'], intelligence_file)
                
                if os.path.exists(intelligence_path):
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
                        except Exception as e:
                            logger.warning(f"Could not store {cv_file.name} in Supabase: {e}")
                
            except Exception as e:
                logger.error(f"Error processing {cv_file}: {e}")
                results.append({
                    'file': cv_file.name,
                    'status': 'error',
                    'error': str(e)
                })
        
        successful = len([r for r in results if r['status'] == 'success'])
        
        return jsonify({
            'success': True,
            'total': len(cv_files),
            'successful': successful,
            'failed': len(cv_files) - successful,
            'results': results
        })
        
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
            results = try_supabase_operation(
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
                timeout_seconds=5
            )
            if results is not None:
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
            candidate = try_supabase_operation(
                lambda: storage.get_candidate(anonymized_id),
                fallback_result=None,
                timeout_seconds=5
            )
            if candidate:
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
                timeout_seconds=5
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
            candidates = try_supabase_operation(
                lambda: storage.get_all_candidates(limit=limit),
                fallback_result=None,
                timeout_seconds=5
            )
            if candidates is not None:
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

if __name__ == '__main__':
    print("\n" + "="*60)
    print("CV Redaction Pipeline - Web Interface")
    print("="*60)
    print(f"\nServer starting...")
    print(f"Upload folder: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print(f"Output folder: {os.path.abspath(app.config['OUTPUT_FOLDER'])}")
    print(f"\nAccess the application at: http://localhost:5000")
    print(f"Press CTRL+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
