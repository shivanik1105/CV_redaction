"""
Build script to create Windows .exe for CV Intelligence System
Run: python build_exe.py
"""
import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build_exe():
    """Build the Windows executable"""
    
    print("=" * 60)
    print("Building CV Intelligence System .exe")
    print("=" * 60)
    
    # Clean previous builds
    if Path('dist').exists():
        shutil.rmtree('dist')
    if Path('build').exists():
        shutil.rmtree('build')
    
    # PyInstaller arguments
    args = [
        'app.py',                           # Main script
        '--name=CVIntelligence',            # Exe name
        '--onefile',                        # Single exe file
        '--windowed',                       # No console window (GUI mode)
        '--icon=icon.ico',                  # App icon (if you have one)
        
        # Add data files
        '--add-data=templates;templates',
        '--add-data=config;config',
        '--add-data=.env.example;.',
        
        # Add hidden imports
        '--hidden-import=presidio_analyzer',
        '--hidden-import=presidio_anonymizer',
        '--hidden-import=spacy',
        '--hidden-import=en_core_web_sm',
        '--hidden-import=sentence_transformers',
        '--hidden-import=sklearn',
        '--hidden-import=supabase',
        '--hidden-import=groq',
        '--hidden-import=flask',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--hidden-import=PyMuPDF',
        '--hidden-import=pdfplumber',
        '--hidden-import=docx',
        
        # Collect all submodules
        '--collect-all=presidio_analyzer',
        '--collect-all=presidio_anonymizer',
        '--collect-all=spacy',
        '--collect-all=sentence_transformers',
        '--collect-all=transformers',
        
        # Exclude unnecessary packages
        '--exclude-module=matplotlib',
        '--exclude-module=pandas',
        '--exclude-module=numpy.distutils',
        
        # Clean build
        '--clean',
        
        # No UPX compression (faster build)
        '--noupx',
    ]
    
    print("\nRunning PyInstaller...")
    PyInstaller.__main__.run(args)
    
    print("\n" + "=" * 60)
    print("✅ Build complete!")
    print("=" * 60)
    print(f"\nExecutable location: dist/CVIntelligence.exe")
    print(f"Size: ~{os.path.getsize('dist/CVIntelligence.exe') / (1024*1024):.1f} MB")
    print("\nNext steps:")
    print("1. Test the exe: dist/CVIntelligence.exe")
    print("2. Create installer (optional)")
    print("3. Distribute to users")

if __name__ == '__main__':
    build_exe()
