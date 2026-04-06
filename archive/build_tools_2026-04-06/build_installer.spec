# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CV Intelligence System
This creates a single-file executable with all dependencies
"""

block_cipher = None

# Collect all data files
datas = [
    ('templates', 'templates'),
    ('config', 'config'),
    ('.env.example', '.'),
]

# Hidden imports
hiddenimports = [
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'en_core_web_sm',
    'sentence_transformers',
    'sklearn',
    'supabase',
    'groq',
    'flask',
    'werkzeug',
    'jinja2',
    'fitz',  # PyMuPDF
    'pdfplumber',
    'docx',
    'PIL',
    'numpy',
    'torch',
    'transformers',
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
    excludes=['matplotlib', 'pandas'],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
