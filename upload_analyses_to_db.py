"""
Upload existing JSON intelligence files to Supabase database
"""
from supabase_storage import SupabaseStorage
import json
import os
from pathlib import Path

def upload_existing_analyses():
    print("\n" + "="*60)
    print(" Uploading Existing Intelligence Files to Database")
    print("="*60 + "\n")
    
    llm_analysis_dir = Path("llm_analysis")
    storage = SupabaseStorage()
    
    # Find all intelligence JSON files
    json_files = list(llm_analysis_dir.glob("*_intelligence.json"))
    
    print(f"Found {len(json_files)} intelligence files\n")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for json_file in json_files:
        print(f"Processing: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                intelligence = json.load(f)
            
            # Check if already in database (by anonymized_id)
            anon_id = intelligence.get('anonymized_id')
            if anon_id:
                existing = storage.client.table("cv_intelligence").select("anonymized_id").eq("anonymized_id", anon_id).execute()
                if existing.data:
                    print(f"  ⚠️  Skipped - already in database")
                    skip_count += 1
                    continue
            
            # Upload to database
            storage.store_intelligence(intelligence)
            print(f"  ✓ Uploaded successfully")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            error_count += 1
    
    print("\n" + "="*60)
    print(" Upload Complete!")
    print("="*60)
    print(f"\n✓ Successfully uploaded: {success_count}")
    print(f"⚠️  Skipped (already exist): {skip_count}")
    print(f"✗ Errors: {error_count}")
    
    # Show final database stats
    print("\n" + "-"*60)
    print(" Database Statistics:")
    print("-"*60 + "\n")
    
    stats = storage.get_statistics()
    print(f"Total candidates: {stats['total_candidates']}")
    print(f"Shortlisted: {stats['shortlisted']}")
    print(f"Backup: {stats['backup']}")
    print(f"Review needed: {stats['review_needed']}")
    print(f"Average confidence: {stats.get('average_confidence_score', 0):.1f}%")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    upload_existing_analyses()
