"""
Test script to verify multi-column CV extraction and redaction
"""
import sys
from pathlib import Path
from universal_pipeline_engine import PipelineOrchestrator

def test_cv_extraction(pdf_path: str):
    """Test CV extraction and redaction"""
    print("=" * 80)
    print(f"Testing CV: {pdf_path}")
    print("=" * 80)
    
    orchestrator = PipelineOrchestrator(debug=True, config_dir='config')
    
    # Process the CV
    redacted_text, profile = orchestrator.process_cv(pdf_path)
    
    print("\n" + "=" * 80)
    print("PROFILE DETECTED:")
    print("=" * 80)
    print(profile)
    
    print("\n" + "=" * 80)
    print("REDACTED TEXT OUTPUT:")
    print("=" * 80)
    print(redacted_text)
    
    # Save to file for inspection
    output_file = Path("test_output_multicolumn.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(redacted_text)
    
    print("\n" + "=" * 80)
    print(f"Output saved to: {output_file}")
    print("=" * 80)
    
    return redacted_text, profile

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_multicolumn_extraction.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    test_cv_extraction(pdf_path)
