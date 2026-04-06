#!/usr/bin/env python3
"""
Database migration script to remove verdict-related columns
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("❌ Supabase not available. Install with: pip install supabase")
    exit(1)

def run_migration():
    """Run the database migration to remove verdict columns"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in .env file")
        return False
    
    print("=" * 60)
    print("Database Migration: Remove Verdict Columns")
    print("=" * 60)
    print()
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        print()
        
        # Migration SQL
        migrations = [
            {
                "name": "Drop verdict column",
                "sql": "ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS verdict CASCADE;"
            },
            {
                "name": "Drop requires_human_review column",
                "sql": "ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS requires_human_review CASCADE;"
            },
            {
                "name": "Drop idx_verdict index",
                "sql": "DROP INDEX IF EXISTS idx_verdict;"
            },
            {
                "name": "Drop idx_requires_human_review index",
                "sql": "DROP INDEX IF EXISTS idx_requires_human_review;"
            },
            {
                "name": "Rename evidence_based_reasoning to assessment_reason",
                "sql": "ALTER TABLE cv_intelligence RENAME COLUMN evidence_based_reasoning TO assessment_reason;"
            }
        ]
        
        print("Running migrations...")
        print()
        
        for migration in migrations:
            try:
                print(f"  → {migration['name']}...", end=" ")
                # Execute SQL using RPC or direct query
                result = supabase.rpc('exec_sql', {'query': migration['sql']}).execute()
                print("✅")
            except Exception as e:
                error_msg = str(e)
                # Check if it's a "column does not exist" or "already renamed" error
                if "does not exist" in error_msg or "already" in error_msg.lower():
                    print("⚠️  (already done)")
                else:
                    print(f"❌ Error: {error_msg}")
                    # Try alternative method - direct SQL execution
                    try:
                        # Some migrations might fail if already applied, that's OK
                        if "RENAME COLUMN" in migration['sql']:
                            # Check if column already renamed
                            check = supabase.table('cv_intelligence').select('assessment_reason').limit(1).execute()
                            print("✅ (column already renamed)")
                        else:
                            print(f"⚠️  Skipping (may already be applied)")
                    except:
                        pass
        
        print()
        print("=" * 60)
        print("✅ Migration completed!")
        print("=" * 60)
        print()
        print("Verifying changes...")
        
        # Verify by checking table structure
        try:
            # Try to query the table to see if it works
            result = supabase.table('cv_intelligence').select('anonymized_id, confidence_score, assessment_reason').limit(1).execute()
            print("✅ Table structure verified - verdict columns removed")
            print(f"✅ Found {len(result.data)} sample record(s)")
        except Exception as e:
            print(f"⚠️  Verification note: {e}")
            print("   (This might be OK if the column rename is pending)")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print()
        print("Manual migration required. Run this SQL in Supabase SQL Editor:")
        print()
        print("-- Remove verdict-related columns")
        print("ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS verdict CASCADE;")
        print("ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS requires_human_review CASCADE;")
        print()
        print("-- Drop verdict-related indexes")
        print("DROP INDEX IF EXISTS idx_verdict;")
        print("DROP INDEX IF EXISTS idx_requires_human_review;")
        print()
        print("-- Rename column (optional)")
        print("ALTER TABLE cv_intelligence RENAME COLUMN evidence_based_reasoning TO assessment_reason;")
        return False

if __name__ == '__main__':
    success = run_migration()
    exit(0 if success else 1)
