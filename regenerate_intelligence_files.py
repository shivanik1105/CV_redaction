#!/usr/bin/env python
"""
Regenerate Intelligence JSON files from redacted CVs
Fixes the issue where intelligence files have errors and are skipped in search
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from cv_intelligence_extractor import CVIntelligenceExtractor
from universal_pipeline_engine import PipelineOrchestrator


def load_redacted_text(file_path: str) -> str:
    """Load redacted text from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return ""


def extract_anonymized_id_from_filename(filename: str) -> str:
    """Extract anonymized ID from filename like REDACTED_20260528_094651_de805ff7925db095.txt"""
    # Try to extract from corresponding intelligence file naming pattern
    stem = Path(filename).stem
    # Format: REDACTED_timestamp_hash
    parts = stem.split('_')
    if len(parts) >= 3:
        hash_part = parts[-1]  # e.g., "de805ff7925db095"
        # Generate CAND_XXXX from hash
        hash_int = int(hash_part[:8], 16)  # Convert first 8 chars to int
        cand_id = f"CAND_{hash_int:08X}"
        return cand_id
    return f"CAND_{os.urandom(4).hex().upper()}"


def regenerate_intelligence_file(redacted_file: Path, llm_extractor: CVIntelligenceExtractor) -> bool:
    """Regenerate intelligence JSON from redacted CV text"""
    try:
        logger.info(f"Processing: {redacted_file.name}")
        
        # Load redacted text
        redacted_text = load_redacted_text(str(redacted_file))
        if not redacted_text:
            logger.error(f"No text found in {redacted_file.name}")
            return False
        
        # Extract anonymized ID from filename
        anonymized_id = extract_anonymized_id_from_filename(redacted_file.name)
        
        # Generate intelligence using LLM
        logger.info(f"  → Generating intelligence for {anonymized_id}")
        intelligence = llm_extractor.extract_intelligence(
            cv_text=redacted_text,
            original_filename=redacted_file.name,
            trust_source=True  # Trust that text is already redacted
        )
        
        if 'error' in intelligence:
            logger.error(f"  ✗ Error in LLM extraction: {intelligence['error']}")
            return False
        
        # Create output JSON filename to match the pattern
        # Extract the hash from the redacted filename
        parts = redacted_file.stem.split('_')
        if len(parts) >= 3:
            hash_part = '_'.join(parts[1:])  # e.g., "20260528_094651_de805ff7925db095"
            output_filename = f"REDACTED_{hash_part}_intelligence.json"
        else:
            output_filename = f"{redacted_file.stem}_intelligence.json"
        
        output_path = Path('llm_analysis') / output_filename
        
        # Save intelligence JSON
        logger.info(f"  → Saving to {output_filename}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(intelligence, f, indent=2, ensure_ascii=False)
        
        logger.info(f"  ✓ Successfully generated intelligence for {anonymized_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {redacted_file.name}: {e}")
        return False


def main():
    """Main regeneration process"""
    logger.info("=" * 60)
    logger.info("REGENERATING INTELLIGENCE FILES")
    logger.info("=" * 60)
    
    # Create llm_analysis directory if it doesn't exist
    Path('llm_analysis').mkdir(exist_ok=True)
    
    # Initialize LLM extractor
    try:
        logger.info("Initializing LLM extractor...")
        extractor = CVIntelligenceExtractor(
            api_provider=os.getenv('LLM_PROVIDER', 'groq'),
            api_key=os.getenv('GROQ_API_KEY'),
            model=os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile')
        )
        logger.info("✓ LLM extractor initialized")
    except Exception as e:
        logger.error(f"Failed to initialize LLM extractor: {e}")
        return False
    
    # Find all redacted text files
    redacted_dir = Path('redacted_output')
    if not redacted_dir.exists():
        logger.error(f"Redacted output directory not found: {redacted_dir}")
        return False
    
    redacted_files = list(redacted_dir.glob('REDACTED_*.txt'))
    logger.info(f"Found {len(redacted_files)} redacted CV files")
    
    if not redacted_files:
        logger.warning("No redacted CV files found")
        return False
    
    # Process each redacted file
    success_count = 0
    failure_count = 0
    
    for redacted_file in sorted(redacted_files):
        if regenerate_intelligence_file(redacted_file, extractor):
            success_count += 1
        else:
            failure_count += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"REGENERATION COMPLETE")
    logger.info(f"  ✓ Success: {success_count}")
    logger.info(f"  ✗ Failed: {failure_count}")
    logger.info("=" * 60)
    
    if success_count > 0:
        logger.info("✓ Intelligence files regenerated successfully!")
        logger.info("  Search should now display candidates properly")
        return True
    else:
        logger.error("✗ No intelligence files were generated")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
