# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the overall recruitment company system executable.
Chatbot is intentionally excluded from this build flow.
"""

import os

block_cipher = None

datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('config', 'config'),
    ('.env.example', '.'),
]

hiddenimports = [
    'flask',
    'werkzeug',
    'jinja2',
    'fitz',
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

excludes = [
    'chatbot',
    'openai',
    'google.generativeai',
    'gradio',
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
    name='RecruitmentSystem',
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
