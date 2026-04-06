# -*- mode: python ; coding: utf-8 -*-
"""
Ultra-minimal PyInstaller spec file for CV Intelligence System
Excludes all heavy ML/data science packages
"""

import os

block_cipher = None

# Collect only essential data files
datas = [
    ('templates', 'templates'),
    ('config', 'config'),
    ('.env.example', '.'),
]

# Minimal hidden imports - only what's absolutely necessary
hiddenimports = [
    'flask',
    'werkzeug',
    'jinja2',
    'fitz',  # PyMuPDF
    'pdfplumber',
    'docx',
    'groq',
    'supabase',
]

# Exclude ALL heavy packages
excludes = [
    'torch',
    'tensorflow',
    'matplotlib',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'sklearn',
    'scikit-learn',
    'numpy',
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'transformers',
    'sentence_transformers',
    'h5py',
    'pyarrow',
    'plotly',
    'altair',
    'boto3',
    'botocore',
    'django',
    'datasets',
    'cv2',
    'opencv',
    'PIL',
    'Pillow',
    'skimage',
    'librosa',
    'soundfile',
    'sounddevice',
]

a = Analysis(
    ['app_launcher.py'],
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
    name='CVIntelligence',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
