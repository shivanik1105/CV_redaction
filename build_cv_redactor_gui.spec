# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for CV Redactor Web GUI with improved multi-column extraction.
This builds the complete web-based CV redaction system.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect config files
config_datas = [
    ('config', 'config'),
    ('templates', 'templates'),
    ('static', 'static'),
]

# Collect spaCy model if available
try:
    import en_core_web_sm
    spacy_data = [(en_core_web_sm.__path__[0], 'en_core_web_sm')]
except ImportError:
    spacy_data = []
    print("WARNING: en_core_web_sm not found. Install with: python -m spacy download en_core_web_sm")

# Collect Presidio data files
presidio_datas = []
try:
    presidio_datas += collect_data_files('presidio_analyzer')
    presidio_datas += collect_data_files('presidio_anonymizer')
except Exception as e:
    print(f"WARNING: Presidio data files not found: {e}")

# Collect Flask/Jinja2 templates
flask_datas = []
try:
    flask_datas += collect_data_files('flask')
    flask_datas += collect_data_files('jinja2')
except Exception as e:
    print(f"WARNING: Flask data files not found: {e}")

# Combine all data files
datas = config_datas + spacy_data + presidio_datas + flask_datas

# Hidden imports - all required modules
hiddenimports = [
    # Core dependencies
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'en_core_web_sm',
    
    # PDF processing
    'fitz',  # PyMuPDF
    'pdfplumber',
    'pdfminer',
    'pdfminer.pdfpage',
    'pdfminer.pdfinterp',
    'pdfminer.converter',
    'pdfminer.layout',
    
    # Document processing
    'docx',
    'PIL',
    'PIL.Image',
    
    # Web framework
    'flask',
    'flask.json',
    'flask.templating',
    'werkzeug',
    'werkzeug.security',
    'werkzeug.serving',
    'werkzeug.datastructures',
    'jinja2',
    'jinja2.ext',
    
    # Standard library
    'json',
    'pathlib',
    'argparse',
    'logging',
    're',
    'typing',
    'datetime',
    'time',
    'threading',
    'webbrowser',
    'hashlib',
    'uuid',
    'collections',
    'itertools',
    'functools',
    
    # Data handling
    'csv',
    'io',
    'base64',
    'urllib',
    'urllib.parse',
]

# Modules to exclude (not needed for CV redaction)
excludes = [
    # LLM providers (not needed for redaction-only)
    'groq',
    'openai',
    'anthropic',
    'google.generativeai',
    'ollama',
    
    # Heavy ML libraries (not needed)
    'torch',
    'tensorflow',
    'transformers',
    'sentence_transformers',
    
    # Database (optional)
    'supabase',
    'psycopg2',
    'sqlalchemy',
    'redis',
    'celery',
    
    # Data science (not needed)
    'pandas',
    'numpy',
    'scipy',
    'matplotlib',
    'sklearn',
    'seaborn',
    
    # Testing
    'pytest',
    'unittest',
    'IPython',
    'jupyter',
    'notebook',
    
    # Development
    'black',
    'pylint',
    'mypy',
]

a = Analysis(
    ['app_launcher.py'],  # Main entry point
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
    name='CVRedactorGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
