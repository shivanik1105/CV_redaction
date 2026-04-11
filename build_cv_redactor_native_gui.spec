# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for CV Redactor Native GUI (tkinter-based).
This builds a standalone Windows application with native GUI.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect config files
config_datas = [
    ('config', 'config'),
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

# Combine all data files
datas = config_datas + spacy_data + presidio_datas

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
    
    # GUI (tkinter is built-in but include for safety)
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',
    
    # Standard library
    'json',
    'pathlib',
    'logging',
    're',
    'typing',
    'datetime',
    'time',
    'threading',
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

# Modules to exclude (not needed for redaction)
excludes = [
    # Web frameworks (not needed for native GUI)
    'flask',
    'werkzeug',
    'jinja2',
    
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
    ['cv_redactor_gui.py'],  # Main GUI entry point
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
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
