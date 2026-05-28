#!/usr/bin/env python3
"""
Check the actual schema of the cv_intelligence table.
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("Checking database schema...")

try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    client = create_client(url, key)
    
    # Get one record to see all columns
    result = client.table('cv_intelligence').select('*').limit(1).execute()
    
    if result.data:
        print("\nColumns in cv_intelligence table:")
        for column in sorted(result.data[0].keys()):
            print(f"  - {column}")
    else:
        print("No data in table")
        
except Exception as e:
    print(f"Error: {e}")
