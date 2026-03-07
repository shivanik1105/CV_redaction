"""
CV Redaction Pipeline — Standalone Web App
==========================================
Redaction-only deployment: no LLM, no Supabase, no API keys needed.
Strips PII from uploaded CVs using local regex + config files.

Start with:  python redact_server.py
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename

# Ensure the project root is on sys.path so universal_pipeline_engine is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from universal_pipeline_engine import PipelineOrchestrator

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024   # 16 MB
app.config['UPLOAD_FOLDER']  = 'uploads'
app.config['OUTPUT_FOLDER']  = 'redacted_output'
app.secret_key = 'cv-redaction-secret-key-2024'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html', hide_dashboard=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'cv_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['cv_file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF or DOCX files'}), 400

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)

        logger.info(f"Uploaded: {upload_path}")

        try:
            orchestrator = PipelineOrchestrator(config_dir='config')
            redacted_text, _profile = orchestrator.process_cv(upload_path)

            output_filename = f"REDACTED_{unique_filename}.txt"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)

            logger.info(f"Redacted: {output_path}")

            return jsonify({
                'success': True,
                'message': 'CV processed successfully',
                'output_filename': output_filename,
                'preview': redacted_text,
                'download_url': url_for('download_file', filename=output_filename),
            })

        except Exception as e:
            logger.error(f"Redaction error: {e}", exc_info=True)
            return jsonify({'error': f'Error processing CV: {e}'}), 500

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        return jsonify({'error': f'Error uploading file: {e}'}), 500


@app.route('/download/<filename>')
def download_file(filename: str):
    # Prevent path traversal: only allow simple filenames, no directory components
    safe_name = os.path.basename(filename)
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], safe_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=safe_name, mimetype='text/plain')
    return jsonify({'error': 'File not found'}), 404


@app.route('/health')
def health():
    redacted_count = len(list(Path(app.config['OUTPUT_FOLDER']).glob('REDACTED_*.txt')))
    return jsonify({
        'status': 'healthy',
        'service': 'CV Redaction Pipeline (redact-only)',
        'redacted_cvs': redacted_count,
    })
