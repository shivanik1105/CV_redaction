import os
from pathlib import Path
import requests

base_url = os.getenv('APP_BASE_URL', 'http://127.0.0.1:5000').rstrip('/')
upload_url = f"{base_url}/upload"
pdf_path = Path('samples/Naukri_RajeshwariSakharkar[5y_4m].pdf')

if not pdf_path.exists():
    print(f"status: FILE_NOT_FOUND ({pdf_path})")
    raise SystemExit(1)

with pdf_path.open('rb') as f:
    files = {'cv_file': (pdf_path.name, f, 'application/pdf')}
    data = {'async': 'false', 'job_description': '', 'force_reprocess': 'true'}
    resp = requests.post(upload_url, files=files, data=data, timeout=300)

print(f"status: {resp.status_code}")
try:
    payload = resp.json()
except Exception:
    payload = {'raw': resp.text[:1000]}

intelligence = payload.get('intelligence') if isinstance(payload, dict) else None
if not isinstance(intelligence, dict):
    intelligence = {}

pipeline_executed = payload.get('pipeline_executed') if isinstance(payload, dict) else None
stored_in_supabase = payload.get('stored_in_supabase') if isinstance(payload, dict) else None
has_intelligence = bool(intelligence)
anonymized_id = intelligence.get('anonymized_id') or (payload.get('anonymized_id') if isinstance(payload, dict) else None)

print(f"pipeline_executed: {pipeline_executed}")
print(f"stored_in_supabase: {stored_in_supabase}")
print(f"has_intelligence: {has_intelligence}")
print(f"anonymized_id: {anonymized_id}")

fields = [
    'anonymized_id',
    'overall_summary',
    'key_skills',
    'domain_expertise',
    'years_of_experience',
    'confidence_score',
    'verdict',
    'updated_at',
]

if anonymized_id:
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    supabase_key = os.getenv('SUPABASE_KEY', '')
    if not supabase_url or not supabase_key:
        print('supabase_row_found: UNKNOWN (missing SUPABASE_URL/SUPABASE_KEY)')
    else:
        query_url = f"{supabase_url}/rest/v1/cv_intelligence"
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Accept': 'application/json',
        }
        params = {
            'select': ','.join(fields),
            'anonymized_id': f'eq.{anonymized_id}',
            'limit': '1',
        }
        qresp = requests.get(query_url, headers=headers, params=params, timeout=60)
        print(f"supabase_query_status: {qresp.status_code}")
        if qresp.ok:
            try:
                rows = qresp.json()
            except Exception:
                rows = []
            row = rows[0] if isinstance(rows, list) and rows else None
            print(f"supabase_row_found: {bool(row)}")
            if row:
                for field in fields:
                    value = row.get(field)
                    if value is None:
                        ok = False
                    elif isinstance(value, str):
                        ok = bool(value.strip())
                    elif isinstance(value, (list, dict, tuple, set)):
                        ok = len(value) > 0
                    else:
                        ok = True
                    print(f"{field}_present_nonempty: {ok}")
        else:
            print('supabase_row_found: False')
            print('supabase_query_error:', qresp.text[:500])
else:
    print('supabase_row_found: SKIPPED (no anonymized_id)')
