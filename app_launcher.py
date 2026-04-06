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

def open_browser():
    """Open browser after a short delay."""
    time.sleep(2)  # Wait for Flask to start
    webbrowser.open('http://localhost:5000/dashboard')
    opened = webbrowser.open('http://localhost:5000/dashboard')
    if not opened:
        webbrowser.open('http://localhost:5000/semantic-search')

def main():
    """Main launcher function"""
    print("=" * 60)
    print("CV Intelligence System")
    print("=" * 60)
    print("\nStarting server...")
    print("Opening recruiter dashboard in your browser...")
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
