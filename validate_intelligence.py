#!/usr/bin/env python
"""Quick validation of all intelligence files"""
import json
from pathlib import Path

intel_dir = Path('llm_analysis')
valid_count = 0
error_count = 0

print('Validating all intelligence files...')
print('=' * 60)

for f in sorted(intel_dir.glob('*_intelligence.json')):
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        has_error = 'error' in data
        has_anon_id = bool(data.get('anonymized_id'))
        has_confidence = data.get('confidence_score', 0) > 0
        
        if has_error:
            print(f'✗ ERROR: {f.name}')
            error_count += 1
        elif not has_anon_id or not has_confidence:
            print(f'✗ MISSING: {f.name}')
            error_count += 1
        else:
            anon_id = data.get('anonymized_id')
            confidence = data.get('confidence_score', 0)
            skills = len(data.get('core_technical_skills', []))
            seniority = data.get('seniority_level', 'N/A')
            print(f'✓ {anon_id}: confidence={confidence}% seniority={seniority} skills={skills}')
            valid_count += 1
    except Exception as e:
        print(f'✗ JSON ERROR {f.name}: {str(e)[:50]}')
        error_count += 1

print('=' * 60)
print(f'Summary: {valid_count} VALID, {error_count} INVALID')
if error_count == 0:
    print('✓ All intelligence files are ready for search!')
