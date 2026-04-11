import json
import math
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

URL = "http://127.0.0.1:5000/api/quick-search"
PAYLOAD = {
    "job_description": "Looking for Python backend engineer with FastAPI, Django, PostgreSQL, Docker, API design, debugging, production readiness.",
    "limit": 5,
}


def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)


def worker(_worker_id):
    out = []
    with requests.Session() as session:
        for _ in range(2):
            start = time.perf_counter()
            status = None
            try:
                response = session.post(URL, json=PAYLOAD, timeout=30)
                status = response.status_code
            except Exception:
                status = "EXC"
            latency_ms = (time.perf_counter() - start) * 1000.0
            out.append((status, latency_ms))
    return out


results = []
with ThreadPoolExecutor(max_workers=30) as executor:
    futures = [executor.submit(worker, i) for i in range(30)]
    for future in as_completed(futures):
        results.extend(future.result())

latencies = [lat for _, lat in results]
status_hist = Counter(str(status) for status, _ in results)
success_count = sum(1 for status, _ in results if isinstance(status, int) and 200 <= status < 300)
total = len(results)
failure_count = total - success_count

summary = {
    "total_requests": total,
    "success_count": success_count,
    "failure_count": failure_count,
    "http_status_histogram": dict(sorted(status_hist.items(), key=lambda kv: kv[0])),
    "latency_ms": {
        "p50": round(percentile(latencies, 0.50), 2) if latencies else None,
        "p90": round(percentile(latencies, 0.90), 2) if latencies else None,
        "p95": round(percentile(latencies, 0.95), 2) if latencies else None,
        "max": round(max(latencies), 2) if latencies else None,
    },
}
print(json.dumps(summary, indent=2))
