"""
Flask Web UI for CV Redaction Pipeline with Intelligence Extraction
Allows users to upload CVs, redact PII, extract intelligence, and search candidates
"""
import os
import sys
import json
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

def get_intelligence_extractor():
    """Get or create intelligence extractor"""
    global _intelligence_extractor
    if _intelligence_extractor is None:
        api_provider = os.getenv('LLM_PROVIDER', 'gemini')
        _intelligence_extractor = CVIntelligenceExtractor(api_provider=api_provider)
    return _intelligence_extractor

def get_supabase_storage():
    """Get or create Supabase storage"""
    global _supabase_storage
    if _supabase_storage is None and SUPABASE_AVAILABLE:
        try:
            _supabase_storage = SupabaseStorage()
        except Exception as e:
            logger.warning(f"Could not initialize Supabase: {e}")
    return _supabase_storage

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
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'CV Redaction Pipeline'})

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
    """Search candidates using filters"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available'}), 503
        
        data = request.get_json() or {}
        
        results = storage.search_by_filters(
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
        )
        
        return jsonify({
            'success': True,
            'count': len(results),
            'candidates': results
        })
        
    except Exception as e:
        logger.error(f"Error searching candidates: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/candidate/<anonymized_id>')
def get_candidate(anonymized_id):
    """Get specific candidate details by anonymized ID"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available'}), 503
        
        candidate = storage.get_candidate(anonymized_id)
        
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        return jsonify({
            'success': True,
            'candidate': candidate
        })
        
    except Exception as e:
        logger.error(f"Error getting candidate: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """Get database statistics"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available'}), 503
        
        stats = storage.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-candidates')
def get_all_candidates():
    """Get all candidates with pagination"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available'}), 503
        
        limit = request.args.get('limit', 100, type=int)
        candidates = storage.get_all_candidates(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(candidates),
            'candidates': candidates
        })
        
    except Exception as e:
        logger.error(f"Error getting all candidates: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/review-queue')
def get_review_queue():
    """Get candidates requiring human review (confidence < 70%)"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available'}), 503
        
        limit = request.args.get('limit', 50, type=int)
        candidates = storage.get_candidates_requiring_review(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(candidates),
            'candidates': candidates,
            'message': f'{len(candidates)} candidates need human review (confidence <70% or unclear AI verdict)'
        })
        
    except Exception as e:
        logger.error(f"Error getting review queue: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/recruiter-override/<anonymized_id>', methods=['POST'])
def add_recruiter_override(anonymized_id):
    """Add recruiter's final decision to candidate"""
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        storage = get_supabase_storage()
        if not storage:
            return jsonify({'error': 'Supabase not available'}), 503
        
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
        
        result = storage.add_recruiter_override(
            anonymized_id,
            recruiter_decision,
            recruiter_notes,
            recruiter_id
        )
        
        return jsonify({
            'success': True,
            'message': f'Recruiter override added: {recruiter_decision}',
            'candidate': result
        })
        
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
