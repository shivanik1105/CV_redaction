from supabase_storage import SupabaseStorage
import json

storage = SupabaseStorage()

# Get one row to see the schema
response = storage.client.table('cv_intelligence').select('*').limit(1).execute()
if response.data:
    row = response.data[0]
    print("cv_intelligence table columns:")
    for key in sorted(row.keys()):
        print(f"  - {key}: {type(row[key]).__name__}")
else:
    print("No data in cv_intelligence table")
