# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CV Redactor standalone executable
This creates a single-file .exe for ONLY the CV redaction functionality
No LLM, no database, no web interface - just pure PII redaction
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect configuration files
config_datas = [
    ('config', 'config'),  # Include config directory
]

# Collect spaCy model data
try:
    import en_core_web_sm
    spacy_data = [(en_core_web_sm.__path__[0], 'en_core_web_sm')]
except ImportError:
    spacy_data = []
    print("WARNING: en_core_web_sm not found. Install with: python -m spacy download en_core_web_sm")

# Collect Presidio data
presidio_datas = []
try:
    presidio_datas += collect_data_files('presidio_analyzer')
    presidio_datas += collect_data_files('presidio_anonymizer')
except:
    print("WARNING: Presidio data files not found")

# All data files
datas = config_datas + spacy_data + presidio_datas

# Hidden imports for redaction only
hiddenimports = [
    # Core redaction
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'en_core_web_sm',
    
    # PDF/DOCX processing
    'fitz',  # PyMuPDF
    'pdfplumber',
    'docx',
    'PIL',
    
    # Standard library
    'json',
    'pathlib',
    'argparse',
    'logging',
    're',
    'typing',
]

# Exclude heavy dependencies we don't need
excludes = [
    # No LLM
    'groq',
    'openai',
    'anthropic',
    'google.generativeai',
    'ollama',
    
    # No ML/embeddings
    'torch',
    'tensorflow',
    'transformers',
    'sentence_transformers',
    
    # No database
    'supabase',
    'psycopg2',
    'sqlalchemy',
    'redis',
    'celery',
    
    # No web
    'flask',
    'werkzeug',
    'jinja2',
    'requests',
    
    # No data science
    'pandas',
    'numpy',
    'scipy',
    'matplotlib',
    'sklearn',
    
    # No testing
    'pytest',
    'unittest',
    'IPython',
    'jupyter',
]

a = Analysis(
    ['cv_redaction_pipeline.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CVRedactor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for CLI interface
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
