# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for CV Redactor standalone executable.
This builds only CV redaction functionality.
"""

import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

config_datas = [
    ('config', 'config'),
]

try:
    import en_core_web_sm
    spacy_data = [(en_core_web_sm.__path__[0], 'en_core_web_sm')]
except ImportError:
    spacy_data = []
    print("WARNING: en_core_web_sm not found. Install with: python -m spacy download en_core_web_sm")

presidio_datas = []
try:
    presidio_datas += collect_data_files('presidio_analyzer')
    presidio_datas += collect_data_files('presidio_anonymizer')
except Exception:
    print("WARNING: Presidio data files not found")

datas = config_datas + spacy_data + presidio_datas

hiddenimports = [
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'en_core_web_sm',
    'fitz',
    'pdfplumber',
    'docx',
    'PIL',
    'json',
    'pathlib',
    'argparse',
    'logging',
    're',
    'typing',
]

excludes = [
    'groq',
    'openai',
    'anthropic',
    'google.generativeai',
    'ollama',
    'torch',
    'tensorflow',
    'transformers',
    'sentence_transformers',
    'supabase',
    'psycopg2',
    'sqlalchemy',
    'redis',
    'celery',
    'flask',
    'werkzeug',
    'jinja2',
    'requests',
    'pandas',
    'numpy',
    'scipy',
    'matplotlib',
    'sklearn',
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
