import os
from pathlib import Path

aid = Path('.last_anonymized_id').read_text(encoding='utf-8').strip() if Path('.last_anonymized_id').exists() else ''
if not aid:
    print('supabase_check=skipped (no anonymized_id)')
    raise SystemExit(0)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from supabase import create_client
except Exception as e:
    print(f'supabase_check=failed (import error: {e})')
    raise SystemExit(0)

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not url or not key:
    print('supabase_check=failed (missing SUPABASE_URL or key)')
    raise SystemExit(0)

try:
    client = create_client(url, key)
    res = client.table('cv_intelligence').select('*').eq('anonymized_id', aid).limit(1).execute()
    row = res.data[0] if isinstance(res.data, list) and res.data else {}
    print(f'supabase_row_found={bool(row)}')
    checks = {
        'overall_summary': bool(row.get('overall_summary')),
        'key_skills': bool(row.get('key_skills')),
        'domain_expertise': bool(row.get('domain_expertise')),
        'years': row.get('years') is not None,
        'confidence': row.get('confidence') is not None,
        'verdict': bool(row.get('verdict')),
    }
    for k, v in checks.items():
        print(f'{k}_present={v}')
except Exception as e:
    print(f'supabase_check=failed ({e})')
