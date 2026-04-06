# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CV Intelligence System - ONEDIR mode
Creates a folder with exe and supporting files (faster, more reliable)
"""

import os

block_cipher = None

# Collect only essential data files
datas = [
    ('templates', 'templates'),
    ('config', 'config'),
    ('.env.example', '.'),
]

# Core imports needed
hiddenimports = [
    'flask',
    'werkzeug',
    'jinja2',
    'fitz',
    'pdfplumber',
    'docx',
    'groq',
    'supabase',
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
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ONEDIR mode - creates folder instead of single exe
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # This makes it ONEDIR
    name='CVIntelligence',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CVIntelligence',
)
