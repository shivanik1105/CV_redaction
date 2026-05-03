import os, json, requests
url='http://127.0.0.1:5000/upload'
file_path=r'samples/Naukri_MayurPatil[3y_2m].pdf'
with open(file_path,'rb') as f:
    files={'cv_file':(os.path.basename(file_path),f,'application/pdf')}
    r=requests.post(url,files=files,timeout=300)
print('status',r.status_code)
try:
    j=r.json()
    print('keys',sorted(j.keys()))
    print(json.dumps({k:j.get(k) for k in ['pipeline_executed','contains_intelligence','has_intelligence_data','has_intelligence','error','mode','success']},indent=2))
except Exception as e:
    print('non-json',r.text[:500])
