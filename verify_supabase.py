import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase client not installed.")
    sys.exit(1)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    logger.error("SUPABASE_URL or SUPABASE_KEY is missing.")
    sys.exit(1)

try:
    logger.info(f"Connecting to Supabase at {url}...")
    supabase: Client = create_client(url, key)
    
    # Try to select from the table to check if it exists
    logger.info("Checking 'cv_intelligence' table...")
    try:
        response = supabase.table("cv_intelligence").select("count", count="exact").limit(1).execute()
        count = response.count
        logger.info(f"✅ Table 'cv_intelligence' exists! Row count: {count}")
    except Exception as e:
        logger.warning(f"❌ Table 'cv_intelligence' likely does not exist or structure is wrong.")
        logger.warning(f"Error details: {e}")
        logger.info("\nIMPORTANT: You need to run the SQL setup script in your Supabase Dashboard SQL Editor.")
        
except Exception as e:
    logger.error(f"Failed to connect to Supabase: {e}")
    sys.exit(1)
