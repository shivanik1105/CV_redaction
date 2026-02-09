"""
Flask Web UI for CV Redaction Pipeline
Allows users to upload CVs and download redacted versions
"""
import os
import sys
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our pipeline
from universal_pipeline_engine import PipelineOrchestrator

# Configure Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'redacted_output'
app.secret_key = 'cv-redaction-secret-key-2024'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

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
