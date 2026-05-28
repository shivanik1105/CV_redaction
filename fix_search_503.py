#!/usr/bin/env python3
"""
Fix the 503 error on search by resetting Supabase connection
"""

import requests
import json

print("Fixing Search 503 Error...")
print("=" * 60)

# Step 1: Check current health
print("\n1. Checking current health status...")
try:
    response = requests.get('http://127.0.0.1:5000/health')
    health = response.json()
    print(f"   Supabase status: {health.get('supabase')}")
    print(f"   Supabase reachable flag: {health.get('supabase_reachable_flag')}")
except Exception as e:
    print(f"   ERROR: Cannot connect to app: {e}")
    print("   Make sure the app is running: python app.py")
    exit(1)

# Step 2: Reset Supabase connection
print("\n2. Resetting Supabase connection...")
try:
    response = requests.post('http://127.0.0.1:5000/api/reset-supabase')
    result = response.json()
    if result.get('success'):
        print(f"   ✓ {result.get('message')}")
    else:
        print(f"   ✗ {result.get('message')}")
        print("\n   This means Supabase is still not reachable.")
        print("   Possible causes:")
        print("   - Network/firewall issue")
        print("   - Supabase project paused/deleted")
        print("   - Invalid credentials in .env")
        exit(1)
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# Step 3: Test search
print("\n3. Testing search functionality...")
try:
    response = requests.post(
        'http://127.0.0.1:5000/api/quick-search',
        json={'job_description': 'Python developer with 5 years experience'}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Search working! Found {result.get('total_matches', 0)} matches")
    elif response.status_code == 503:
        print(f"   ✗ Still getting 503 error")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)
print("\nIf search is still not working:")
print("1. Restart the Flask app: python app.py")
print("2. Try searching again in the browser")
print("3. Check server logs for errors")
