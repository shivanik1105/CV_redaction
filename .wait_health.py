import time, requests, sys
url = 'http://127.0.0.1:5000/health'
last = None
for i in range(60):
    try:
        r = requests.get(url, timeout=2)
        last = f'status={r.status_code} body={r.text[:200]}'
        if r.ok:
            print('HealthReady:', r.status_code)
            sys.exit(0)
    except Exception as e:
        last = str(e)
    time.sleep(1)
print('HealthFailed:', last)
sys.exit(1)
