"""
Test script to verify the upload endpoint correctly receives and processes the API key.
This will help diagnose if the issue is in the frontend or backend.
"""

import requests
import os
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload"

def test_upload_with_api_key():
    """Test uploading a CV with an API key provided."""
    
    # Find a test CV file
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        print("❌ uploads/ directory not found")
        return
    
    cv_files = list(uploads_dir.glob("*.pdf")) + list(uploads_dir.glob("*.docx"))
    if not cv_files:
        print("❌ No CV files found in uploads/ directory")
        return
    
    test_file = cv_files[0]
    print(f"📄 Using test file: {test_file.name}")
    
    # Prepare the form data
    with open(test_file, 'rb') as f:
        files = {'cv_file': (test_file.name, f, 'application/pdf')}
        
        data = {
            'job_description': 'Test job description for Python developer',
            'async': 'false',  # Use sync mode for immediate response
            'force_reprocess': 'true',  # Force reprocess to avoid duplicate check
            'llm_provider': 'groq',  # Use groq as it's likely configured
            'llm_model': '',
            'llm_api_key': 'test_api_key_12345'  # Test API key
        }
        
        print("\n🔄 Sending upload request...")
        print(f"   - File: {test_file.name}")
        print(f"   - API Key: {data['llm_api_key'][:10]}...")
        print(f"   - Provider: {data['llm_provider']}")
        print(f"   - Async: {data['async']}")
        
        try:
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=30)
            
            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"\n📋 Response JSON:")
                import json
                print(json.dumps(response_json, indent=2))
                
                if response.status_code == 400:
                    if 'LLM_API_KEY_REQUIRED' in str(response_json):
                        print("\n❌ ISSUE CONFIRMED: Backend is not receiving the API key!")
                        print("   This means the form data is not being sent correctly.")
                    else:
                        print(f"\n⚠️  Got 400 error: {response_json.get('error')}")
                elif response.status_code == 200:
                    print("\n✅ Upload successful! API key was received correctly.")
                else:
                    print(f"\n⚠️  Unexpected status code: {response.status_code}")
                    
            except Exception as e:
                print(f"\n❌ Could not parse JSON response: {e}")
                print(f"Raw response: {response.text[:500]}")
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request failed: {e}")

def test_upload_without_api_key():
    """Test uploading a CV WITHOUT an API key to verify the error message."""
    
    uploads_dir = Path("uploads")
    cv_files = list(uploads_dir.glob("*.pdf")) + list(uploads_dir.glob("*.docx"))
    if not cv_files:
        print("❌ No CV files found")
        return
    
    test_file = cv_files[0]
    print(f"\n\n{'='*60}")
    print("TEST 2: Upload WITHOUT API key (should fail with clear error)")
    print('='*60)
    print(f"📄 Using test file: {test_file.name}")
    
    with open(test_file, 'rb') as f:
        files = {'cv_file': (test_file.name, f, 'application/pdf')}
        
        data = {
            'job_description': 'Test job description',
            'async': 'false',
            'force_reprocess': 'true',
            'llm_provider': 'groq',
            'llm_model': '',
            'llm_api_key': ''  # Empty API key
        }
        
        print("\n🔄 Sending upload request WITHOUT API key...")
        
        try:
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=30)
            
            print(f"\n📊 Response Status: {response.status_code}")
            
            try:
                response_json = response.json()
                print(f"\n📋 Response JSON:")
                import json
                print(json.dumps(response_json, indent=2))
                
                if response.status_code == 400 and 'LLM_API_KEY_REQUIRED' in str(response_json):
                    print("\n✅ CORRECT: Backend properly rejects upload without API key")
                else:
                    print(f"\n⚠️  Unexpected response")
                    
            except Exception as e:
                print(f"\n❌ Could not parse JSON response: {e}")
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    print("="*60)
    print("TEST 1: Upload WITH API key (should work)")
    print("="*60)
    test_upload_with_api_key()
    
    test_upload_without_api_key()
    
    print("\n\n" + "="*60)
    print("DIAGNOSIS COMPLETE")
    print("="*60)
    print("\nIf TEST 1 succeeds, the backend is working correctly.")
    print("If TEST 1 fails with LLM_API_KEY_REQUIRED, there's a backend issue.")
    print("\nThe user should:")
    print("1. Open browser DevTools (F12)")
    print("2. Go to Network tab")
    print("3. Try uploading a CV")
    print("4. Click on the /upload request")
    print("5. Check the 'Payload' tab to see if llm_api_key is being sent")
