#!/usr/bin/env python3
"""
Test Supabase connection and check for candidates
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("Testing Supabase Connection...")
print("=" * 60)

# Get credentials
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"SUPABASE_URL: {url[:30]}..." if url else "SUPABASE_URL: NOT SET")
print(f"SUPABASE_KEY: {key[:30]}..." if key else "SUPABASE_KEY: NOT SET")
print()

if not url or not key:
    print("ERROR: Supabase credentials not set in .env file")
    exit(1)

# Try to connect
print("Attempting to connect to Supabase...")
try:
    from supabase import create_client
    print("OK: supabase library imported")
except ImportError as e:
    print(f"ERROR: Cannot import supabase library: {e}")
    print("Fix: pip install supabase")
    exit(1)

try:
    client = create_client(url, key)
    print("OK: Supabase client created")
except Exception as e:
    print(f"ERROR: Failed to create client: {e}")
    exit(1)

# Try to query the database
print("\nQuerying cv_intelligence table...")
try:
    result = client.table('cv_intelligence').select('anonymized_id').limit(5).execute()
    count = len(result.data) if result.data else 0
    print(f"OK: Query successful")
    print(f"Found {count} candidates in database")
    
    if count > 0:
        print("\nFirst few candidates:")
        for row in result.data[:5]:
            print(f"  - {row.get('anonymized_id')}")
    else:
        print("\nWARNING: Database is empty - no candidates found")
        print("This is why search returns 503")
        
except Exception as e:
    print(f"ERROR: Query failed: {e}")
    print("\nPossible causes:")
    print("1. Table 'cv_intelligence' doesn't exist")
    print("2. Credentials don't have read permission")
    print("3. Network/firewall issue")
    exit(1)

print("\n" + "=" * 60)
print("Supabase connection test complete!")
print("=" * 60)
