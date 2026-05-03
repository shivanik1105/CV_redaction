"""
Launcher script for CV Intelligence System
This opens the browser automatically when the app starts
"""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

def test_extraction():
    """Test CV extraction with a sample file if provided"""
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        if len(sys.argv) < 3:
            print("Usage: python app_launcher.py --test <path_to_pdf>")
            return False
        
        pdf_path = sys.argv[2]
        if not Path(pdf_path).exists():
            print(f"Error: File not found: {pdf_path}")
            return False
        
        print("=" * 80)
        print("TESTING CV EXTRACTION AND REDACTION")
        print("=" * 80)
        print(f"Input file: {pdf_path}")
        print()
        
        try:
            from universal_pipeline_engine import PipelineOrchestrator
            
            orchestrator = PipelineOrchestrator(debug=False, config_dir='config')
            redacted_text, profile = orchestrator.process_cv(pdf_path)
            
            print("Profile detected:")
            print(f"  Type: {profile.cv_type}")
            print(f"  Confidence: {profile.confidence:.2%}")
            print()
            
            # Save test output
            output_file = Path("test_redaction_output.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
            
            print(f"✓ Redaction complete!")
            print(f"✓ Output saved to: {output_file}")
            print()
            print("Preview (first 1000 characters):")
            print("-" * 80)
            print(redacted_text[:1000])
            print("-" * 80)
            print()
            print("✓ Test completed successfully!")
            print("  Review the full output in test_redaction_output.txt")
            print()
            
            return True
            
        except Exception as e:
            print(f"✗ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return None  # No test requested

def open_browser():
    """Open browser after a short delay."""
    time.sleep(2)  # Wait for Flask to start
    opened = webbrowser.open('http://localhost:5000/')
    if not opened:
        webbrowser.open('http://127.0.0.1:5000/')

def main():
    """Main launcher function"""
    # Check if test mode
    test_result = test_extraction()
    if test_result is not None:
        # Test mode was requested
        if test_result:
            print("Press Enter to exit...")
            input()
            sys.exit(0)
        else:
            print("Press Enter to exit...")
            input()
            sys.exit(1)
    
    # Normal mode - start the web app
    print("=" * 60)
    print("CV Intelligence System")
    print("=" * 60)
    print("\nStarting server...")
    print("Opening CV Intelligence page in your browser...")
    print("\nTo stop the server, close this window or press Ctrl+C")
    print("=" * 60)
    
    # Open browser in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Import and run Flask app
    try:
        from app import app
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

if __name__ == '__main__':
    main()
