import os
import requests

url = "http://127.0.0.1:5000/upload"
file_path = r"samples/Naukri_RajeshwariSakharkar[5y_4m].pdf"
with open(file_path, "rb") as f:
    files = {"cv_file": (os.path.basename(file_path), f, "application/pdf")}
    data = {"async": "false", "job_description": "", "force_reprocess": "true"}
    resp = requests.post(url, files=files, data=data, timeout=600)

print(f"status={resp.status_code}")
try:
    payload = resp.json()
except Exception:
    payload = {}
    print("response_text=" + resp.text[:500])

if not isinstance(payload, dict):
    payload = {}

pipeline_executed = payload.get("pipeline_executed")
stored_in_supabase = payload.get("stored_in_supabase")
intelligence = payload.get("intelligence") if isinstance(payload.get("intelligence"), dict) else {}
has_intelligence = bool(intelligence)
anonymized_id = payload.get("anonymized_id") or intelligence.get("anonymized_id")

print(f"pipeline_executed={pipeline_executed}")
print(f"stored_in_supabase={stored_in_supabase}")
print(f"has_intelligence={has_intelligence}")
print(f"anonymized_id={anonymized_id}")

with open('.last_anonymized_id', 'w', encoding='utf-8') as out:
    out.write('' if anonymized_id is None else str(anonymized_id))
