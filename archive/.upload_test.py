import os, sys, requests
url = 'http://127.0.0.1:5000/upload'
file_path = r'samples/Resume -Sunil Durgale.pdf'
data = {
    'llm_provider': 'openai',
    'llm_model': 'gpt-4o-mini',
    'llm_api_key': 'runtime_test_key',
}
with open(file_path, 'rb') as f:
    files = {'cv_file': (os.path.basename(file_path), f, 'application/pdf')}
    r = requests.post(url, data=data, files=files, timeout=180)
print('UploadStatus:', r.status_code)
try:
    j = r.json()
except Exception:
    print('UploadBody:', r.text[:500])
    sys.exit(1)
for key in ['success', 'mode', 'pipeline_executed', 'has_intelligence', 'output_filename']:
    print(f'{key}: {j.get(key)}')
