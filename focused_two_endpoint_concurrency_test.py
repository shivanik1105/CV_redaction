import json
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = "http://127.0.0.1:5000"
TOTAL_REQUESTS = 60
MAX_WORKERS = 30

quick_payload = {
    "job_description": "python developer",
    "query": "python developer",
    "limit": 10,
}

search_payload = {
    "query": "python backend django api",
    "required_skills": ["python", "django", "api"],
    "limit": 50,
}


def make_tasks():
    tasks = []
    for _ in range(TOTAL_REQUESTS // 2):
        tasks.append(("/api/quick-search", quick_payload, 60))
    for _ in range(TOTAL_REQUESTS // 2):
        tasks.append(("/api/search-candidates", search_payload, 60))
    random.shuffle(tasks)
    return tasks


def run_task(task):
    endpoint, payload, timeout = task
    t0 = time.perf_counter()
    try:
        r = requests.post(BASE_URL + endpoint, json=payload, timeout=timeout)
        dt = (time.perf_counter() - t0) * 1000
        return {
            "endpoint": endpoint,
            "status": r.status_code,
            "latency_ms": dt,
        }
    except Exception as e:
        dt = (time.perf_counter() - t0) * 1000
        return {
            "endpoint": endpoint,
            "status": "EXC",
            "latency_ms": dt,
            "error": f"{type(e).__name__}: {str(e)}"[:200],
        }


def main():
    tasks = make_tasks()
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(run_task, t) for t in tasks]
        for f in as_completed(futures):
            results.append(f.result())

    overall = Counter(str(r["status"]) for r in results)
    per_endpoint = defaultdict(Counter)
    for r in results:
        per_endpoint[r["endpoint"]][str(r["status"])] += 1

    success = sum(1 for r in results if r["status"] == 200)
    failure = len(results) - success

    summary = {
        "config": {
            "total_requests": TOTAL_REQUESTS,
            "parallel_workers": MAX_WORKERS,
            "distribution": {
                "/api/quick-search": TOTAL_REQUESTS // 2,
                "/api/search-candidates": TOTAL_REQUESTS // 2,
            },
        },
        "success_count": success,
        "failure_count": failure,
        "overall_status_codes": dict(overall),
        "per_endpoint_status_codes": {k: dict(v) for k, v in per_endpoint.items()},
        "representative_errors": [r for r in results if str(r["status"]) != "200"][:6],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
