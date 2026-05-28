import json
import os

# Create a mapping of anonymized_id -> masked_pdf_filename
masked_pdf_mapping = {}

# Scan llm_analysis for intelligence files with masked PDFs
for f in os.listdir('llm_analysis'):
    if f.endswith('_intelligence.json'):
        with open(f'llm_analysis/{f}') as fp:
            intel = json.load(fp)
            anon_id = intel.get('anonymized_id')
            masked_pdf = intel.get('masked_pdf_filename')
            if anon_id and masked_pdf:
                masked_pdf_mapping[anon_id] = masked_pdf
                print(f"Mapped: {anon_id} -> {masked_pdf}")

# Save mapping
with open('masked_pdf_mapping.json', 'w') as f:
    json.dump(masked_pdf_mapping, f, indent=2)

print(f"\nSaved mapping for {len(masked_pdf_mapping)} candidates to masked_pdf_mapping.json")
