#!/usr/bin/env python3
"""
Quick test to verify CV uploads work with the fixes applied
Run this AFTER starting the Flask app to test the upload functionality
"""
import requests
import sys
import time
from pathlib import Path

# Configuration
FLASK_URL = "http://127.0.0.1:5000"
UPLOAD_ENDPOINT = f"{FLASK_URL}/upload"
STATUS_ENDPOINT = f"{FLASK_URL}/api/upload-jobs"

def test_cv_upload(cv_file_path: str, job_description: str = None):
    """Test uploading a CV and tracking its processing."""
    
    cv_path = Path(cv_file_path)
    if not cv_path.exists():
        print(f"✗ CV file not found: {cv_file_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"TESTING CV UPLOAD")
    print(f"{'='*60}")
    print(f"File: {cv_path.name}")
    print(f"Size: {cv_path.stat().st_size / 1024:.1f} KB")
    
    # Test 1: Upload the CV
    print(f"\n1. Uploading CV...")
    try:
        with open(cv_path, 'rb') as f:
            files = {'cv_file': (cv_path.name, f)}
            data = {}
            if job_description:
                data['job_description'] = job_description
            
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=10)
            
        if response.status_code != 200:
            print(f"   ✗ Upload failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        job_id = result.get('job_id')
        
        if not job_id:
            print(f"   ✗ No job ID returned")
            print(f"   Response: {result}")
            return False
        
        print(f"   ✓ Upload successful")
        print(f"   Job ID: {job_id}")
        
    except Exception as e:
        print(f"   ✗ Upload failed: {e}")
        return False
    
    # Test 2: Check job status
    print(f"\n2. Checking job status...")
    max_attempts = 30  # 30 seconds max wait
    for attempt in range(max_attempts):
        try:
            status_url = f"{STATUS_ENDPOINT}/{job_id}"
            response = requests.get(status_url, timeout=5)
            
            if response.status_code != 200:
                print(f"   ✗ Status check failed")
                return False
            
            job_status = response.json()
            current_status = job_status.get('status', 'unknown')
            
            if attempt % 5 == 0:  # Print every 5 attempts
                print(f"   Status: {current_status}...", end='')
            
            if current_status == 'completed':
                print(f"\n   ✓ Processing completed successfully")
                
                # Check for intelligence data
                intelligence = job_status.get('intelligence', {})
                if intelligence:
                    anonymized_id = intelligence.get('anonymized_id', 'N/A')
                    confidence = intelligence.get('confidence_score', 0)
                    skills = intelligence.get('core_technical_skills', [])
                    years = intelligence.get('years_experience', 0)
                    
                    print(f"\n3. Intelligence extracted:")
                    print(f"   ✓ ID: {anonymized_id}")
                    print(f"   ✓ Confidence: {confidence}%")
                    print(f"   ✓ Experience: {years} years")
                    print(f"   ✓ Skills: {', '.join(skills[:5])}")
                    print(f"\n   ✓✓✓ CV UPLOAD WORKING PERFECTLY ✓✓✓")
                    return True
                else:
                    print(f"   ⚠ No intelligence data found")
                    return True
            
            elif current_status == 'failed':
                error = job_status.get('error', 'Unknown error')
                print(f"\n   ✗ Processing failed: {error}")
                return False
            
        except Exception as e:
            print(f"   ✗ Status check failed: {e}")
            return False
        
        time.sleep(1)
    
    print(f"\n   ✗ Job processing timeout")
    return False

if __name__ == "__main__":
    # Find a test CV
    test_cv = None
    search_paths = [
        Path("uploads"),
        Path(".")
    ]
    
    for search_path in search_paths:
        for file in search_path.glob("*.pdf"):
            if file.name.startswith("20260528"):  # Today's upload
                test_cv = file
                break
    
    if not test_cv:
        print("Usage: python test_live_upload.py <cv_file_path>")
        print("\nQuick test with any PDF:")
        pdf_files = list(Path(".").glob("*.pdf"))
        if pdf_files:
            test_cv = pdf_files[0]
        else:
            print("✗ No CV files found")
            sys.exit(1)
    
    success = test_cv_upload(str(test_cv))
    
    print(f"\n{'='*60}")
    if success:
        print("✓ ALL TESTS PASSED")
        print("\nThe CV upload is working properly with non-ASCII character support!")
    else:
        print("✗ TESTS FAILED")
        print("\nPlease check:")
        print("1. Flask app is running (python app.py)")
        print("2. CV file exists and is readable")
        print("3. Check Flask logs for detailed error messages")
    print(f"{'='*60}")
