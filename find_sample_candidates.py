import json
import os

# Check which sample candidates are in llm_analysis
sample_ids = []
for f in os.listdir('llm_analysis'):
    if f.endswith('_intelligence.json'):
        with open(f'llm_analysis/{f}') as fp:
            intel = json.load(fp)
            if intel.get('extraction_mode') == 'sample_archive':
                sample_ids.append(intel.get('anonymized_id'))
                print(f"Sample candidate: {intel.get('anonymized_id')}")
                print(f"  Source: {intel.get('archive_source_path')}")
                print(f"  Masked PDF: {intel.get('masked_pdf_filename')}")
                print()

if not sample_ids:
    print("No sample candidates found in llm_analysis")
