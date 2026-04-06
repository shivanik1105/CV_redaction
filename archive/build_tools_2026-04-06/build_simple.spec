# -*- mode: python ; coding: utf-8 -*-
"""
Simplified PyInstaller spec file for CV Intelligence System
This version excludes heavy dependencies like torch
"""

import os

block_cipher = None

# Collect only essential data files
datas = [
    ('templates', 'templates'),
    ('config', 'config'),
    ('.env.example', '.'),
]

# Minimal hidden imports (exclude torch-heavy packages)
hiddenimports = [
    'flask',
    'werkzeug',
    'jinja2',
    'fitz',  # PyMuPDF
    'pdfplumber',
    'docx',
    'presidio_analyzer',
    'presidio_anonymizer',
    'spacy',
    'groq',
    'supabase',
    'sklearn.metrics.pairwise',
    'numpy',
]

# Exclude heavy packages
excludes = [
    'torch',
    'tensorflow',
    'matplotlib',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
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
    upx=False,  # Disable UPX for faster build
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
