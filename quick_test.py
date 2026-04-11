"""
Quick test script for CV redaction
Usage: python quick_test.py <path_to_pdf>
"""
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <path_to_pdf>")
        print("\nExample:")
        print('  python quick_test.py "Resume-Sunil-Durgale.pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("CV REDACTION TEST")
    print("=" * 80)
    print(f"Input: {pdf_path}")
    print()
    
    try:
        from universal_pipeline_engine import PipelineOrchestrator
        
        print("Loading pipeline...")
        orchestrator = PipelineOrchestrator(debug=False, config_dir='config')
        
        print("Processing CV...")
        redacted_text, profile = orchestrator.process_cv(pdf_path)
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"CV Type: {profile.cv_type}")
        print(f"Confidence: {profile.confidence:.1%}")
        print(f"Text Length: {len(redacted_text)} characters")
        print(f"Number of Lines: {len(redacted_text.split(chr(10)))}")
        print()
        
        # Save output
        output_file = Path("test_redaction_output.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
        
        print(f"✓ Output saved to: {output_file}")
        print()
        
        # Show full preview (not just 50 lines)
        print("=" * 80)
        print("FULL OUTPUT")
        print("=" * 80)
        lines = redacted_text.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}: {line}")
        
        print()
        print("=" * 80)
        print("✓ Test completed successfully!")
        print(f"✓ Full output available in: {output_file}")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("✗ ERROR")
        print("=" * 80)
        print(f"{e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
