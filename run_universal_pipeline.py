#!/usr/bin/env python3
"""
Quick Start Runner for Universal CV Pipeline Engine
Simple wrapper to get started quickly
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import fitz
    except ImportError:
        missing.append("PyMuPDF")
    
    try:
        import pdfplumber
    except ImportError:
        missing.append("pdfplumber")
    
    if missing:
        print("ERROR: Missing required dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    # Check optional dependencies
    optional_missing = []
    
    try:
        import spacy
        try:
            import en_core_web_sm
        except ImportError:
            optional_missing.append("spacy model (run: python -m spacy download en_core_web_sm)")
    except ImportError:
        optional_missing.append("spacy")
    
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        optional_missing.append("paddleocr")
    
    if optional_missing:
        print("WARNING: Optional dependencies missing (reduced functionality):")
        for dep in optional_missing:
            print(f"   - {dep}")
        print("\nInstall for full functionality:")
        if "spacy" in str(optional_missing):
            print("   pip install spacy")
            print("   python -m spacy download en_core_web_sm")
        if "paddleocr" in str(optional_missing):
            print("   pip install paddleocr paddlepaddle")
        print()
    
    return True

def show_welcome():
    """Show welcome message"""
    print("=" * 80)
    print("UNIVERSAL CV PIPELINE ENGINE")
    print("=" * 80)
    print("Comprehensive CV redaction system with 6 specialized pipelines")
    print("Automatically detects and processes all CV types\n")

def show_usage():
    """Show usage information"""
    print("Usage:")
    print("  python run_universal_pipeline.py [input_dir] [output_dir] [--debug]")
    print()
    print("Examples:")
    print("  python run_universal_pipeline.py")
    print("  python run_universal_pipeline.py resume/")
    print("  python run_universal_pipeline.py resume/ output/")
    print("  python run_universal_pipeline.py resume/ output/ --debug")
    print()
    print("Default:")
    print("  input_dir  = 'samples'")
    print("  output_dir = 'final_output'")
    print()

def main():
    """Main entry point"""
    show_welcome()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Parse arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    flags = [arg for arg in sys.argv[1:] if arg.startswith('--')]
    
    # Show help
    if '--help' in flags or '-h' in flags:
        show_usage()
        return 0
    
    # Set defaults
    input_dir = args[0] if len(args) > 0 else "samples"
    output_dir = args[1] if len(args) > 1 else "final_output"
    debug = '--debug' in flags
    
    # Validate input directory
    if not Path(input_dir).exists():
        print(f"ERROR: Input directory '{input_dir}' not found")
        print()
        
        # Suggest available directories
        current_dir = Path('.')
        pdf_dirs = []
        for item in current_dir.iterdir():
            if item.is_dir() and list(item.glob('*.pdf')):
                pdf_dirs.append(item.name)
        
        if pdf_dirs:
            print("Available directories with PDFs:")
            for dir_name in pdf_dirs:
                pdf_count = len(list(Path(dir_name).glob('*.pdf')))
                print(f"   - {dir_name}/ ({pdf_count} PDFs)")
        
        print()
        show_usage()
        return 1
    
    # Count PDFs
    pdf_count = len(list(Path(input_dir).glob('**/*.pdf')))
    if pdf_count == 0:
        print(f"WARNING: No PDF files found in '{input_dir}'")
        return 1
    
    # Show configuration
    print("Configuration:")
    print(f"   Input directory:  {input_dir}")
    print(f"   Output directory: {output_dir}")
    print(f"   PDF files found:  {pdf_count}")
    print(f"   Debug mode:       {'Enabled' if debug else 'Disabled'}")
    print()
    
    # Import and run
    try:
        from universal_pipeline_engine import PipelineOrchestrator
        
        print("Starting processing...\n")
        
        # Create orchestrator and process
        orchestrator = PipelineOrchestrator(debug=debug)
        orchestrator.process_directory(input_dir, output_dir)
        
        print()
        print("=" * 80)
        print("PROCESSING COMPLETE!")
        print("=" * 80)
        print(f"Output saved to: {output_dir}/")
        if debug:
            print(f"Debug files saved to: debug_output/")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR OCCURRED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        
        if debug:
            import traceback
            print("Traceback:")
            traceback.print_exc()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
