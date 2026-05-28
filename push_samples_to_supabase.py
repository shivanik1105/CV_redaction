import json
import os
from datetime import datetime
import hashlib
from supabase_storage import SupabaseStorage

# Load sample candidates from local intelligence files
sample_candidates = []
for f in os.listdir('llm_analysis'):
    if f.endswith('_intelligence.json'):
        with open(f'llm_analysis/{f}') as fp:
            intel = json.load(fp)
            if intel.get('extraction_mode') == 'sample_archive':
                # Add to Supabase
                sample_candidates.append(intel)
                print(f"Will push: {intel.get('anonymized_id')} ({intel.get('masked_pdf_filename')})")

# Connect to Supabase
storage = SupabaseStorage()

# Insert each sample candidate
for intel in sample_candidates:
    try:
        # Check if already exists
        existing = storage.client.table('cv_intelligence').select('*').eq('anonymized_id', intel['anonymized_id']).execute()
        
        if existing.data:
            print(f"  {intel['anonymized_id']} already in Supabase, skipping")
        else:
            # Generate a hash for original_cv_hash (required field)
            anon_id = intel['anonymized_id']
            original_cv_hash = hashlib.md5(anon_id.encode()).hexdigest()
            
            # Insert with all required fields
            storage.client.table('cv_intelligence').insert({
                'anonymized_id': intel['anonymized_id'],
                'original_cv_hash': original_cv_hash,
                'llm_prompt_used': 'sample_archive_import',
                'llm_provider': 'local_sample',
                'llm_model': 'sample',
                'llm_raw_response': '{}',
                'evidence_based_reasoning': intel.get('evidence_based_reasoning', ''),
                'cleaned_text': intel.get('overall_summary', ''),
                'core_technical_skills': intel.get('core_technical_skills', []),
                'overall_summary': intel.get('overall_summary', ''),
                'confidence_score': intel.get('confidence_score', 0),
                'years_of_experience': intel.get('years_experience', 0),
                'seniority_level': intel.get('seniority_level', 'N/A'),
                'primary_domain': intel.get('primary_domain', '')
            }).execute()
            print(f"  [OK] Inserted {intel['anonymized_id']} with masked PDF")
    except Exception as e:
        print(f"  [ERROR] Error for {intel.get('anonymized_id')}: {e}")

print("\nDone pushing sample candidates to Supabase")
