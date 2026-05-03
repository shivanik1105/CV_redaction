import os
import json
import math
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE_URL = "http://127.0.0.1:5000"
PDF_PATH = r"samples\more\Dnyanesh_Palkhiwale_HIL_Validation.pdf"
TOTAL_REQUESTS = 60
MAX_WORKERS = 30


def percentile(values, p):
    if not values:
        return None
    vals = sorted(values)
    if len(vals) == 1:
        return vals[0]
    k = (len(vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return vals[int(k)]
    return vals[f] + (vals[c] - vals[f]) * (k - f)


def extract_error_message(resp):
    try:
        payload = resp.json()
        if isinstance(payload, dict):
            for key in ("error", "message", "detail"):
                if payload.get(key):
                    return str(payload.get(key))[:240]
            return json.dumps(payload)[:240]
        return str(payload)[:240]
    except Exception:
        return (resp.text or "")[:240]


def make_tasks():
    tasks = []
    for _ in range(20):
        tasks.append({
            "name": "/api/quick-search",
            "path": "/api/quick-search",
            "kind": "json",
            "json": {
                "job_description": "python developer",
                "query": "python developer",
                "limit": 10,
            },
            "timeout": 45,
        })
    for _ in range(20):
        tasks.append({
            "name": "/api/search-candidates",
            "path": "/api/search-candidates",
            "kind": "json",
            "json": {
                "query": "python backend django api",
                "required_skills": ["python", "django", "api"],
                "limit": 50,
            },
            "timeout": 45,
        })
    for i in range(20):
        with_jd = (i % 2 == 0)
        form = {"job_description": "python backend django api"} if with_jd else {}
        tasks.append({
            "name": "/upload",
            "variant": "with_jd" if with_jd else "without_jd",
            "path": "/upload",
            "kind": "multipart",
            "form": form,
            "timeout": 90,
        })
    random.shuffle(tasks)
    return tasks


def execute_task(task):
    url = BASE_URL + task["path"]
    start = time.perf_counter()
    try:
        if task["kind"] == "json":
            resp = requests.post(url, json=task["json"], timeout=task["timeout"])
        else:
            with open(PDF_PATH, "rb") as f:
                files = {"cv_file": (os.path.basename(PDF_PATH), f, "application/pdf")}
                resp = requests.post(url, data=task.get("form", {}), files=files, timeout=task["timeout"])
        latency_ms = (time.perf_counter() - start) * 1000.0
        err = None if resp.status_code == 200 else extract_error_message(resp)
        return {
            "endpoint": task["name"],
            "variant": task.get("variant"),
            "status": resp.status_code,
            "latency_ms": latency_ms,
            "error": err,
        }
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000.0
        return {
            "endpoint": task["name"],
            "variant": task.get("variant"),
            "status": "EXC",
            "latency_ms": latency_ms,
            "error": f"{type(e).__name__}: {str(e)}"[:240],
        }


def main():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"Sample PDF not found: {PDF_PATH}")

    warm_start = time.perf_counter()
    warmup_resp = requests.post(
        BASE_URL + "/api/quick-search",
        json={"job_description": "python developer", "query": "python developer", "limit": 10},
        timeout=45,
    )
    warmup_ms = (time.perf_counter() - warm_start) * 1000.0

    tasks = make_tasks()
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(execute_task, t) for t in tasks]
        for fut in as_completed(futures):
            results.append(fut.result())

    endpoint_stats = defaultdict(lambda: {"success": 0, "failure": 0, "status_codes": Counter()})
    overall_status = Counter()
    latencies = []
    errors = []

    for r in results:
        endpoint = r["endpoint"]
        status = str(r["status"])
        endpoint_stats[endpoint]["status_codes"][status] += 1
        overall_status[status] += 1
        latencies.append(r["latency_ms"])
        if r["status"] == 200:
            endpoint_stats[endpoint]["success"] += 1
        else:
            endpoint_stats[endpoint]["failure"] += 1
            if r.get("error"):
                errors.append({
                    "endpoint": endpoint,
                    "variant": r.get("variant"),
                    "status": status,
                    "message": r["error"],
                })

    unique_errors = []
    seen = set()
    for e in errors:
        key = (e["endpoint"], e.get("variant"), e["status"], e["message"])
        if key in seen:
            continue
        seen.add(key)
        unique_errors.append(e)
        if len(unique_errors) >= 8:
            break

    summary = {
        "warmup": {
            "endpoint": "/api/quick-search",
            "status": warmup_resp.status_code,
            "latency_ms": round(warmup_ms, 2),
        },
        "config": {
            "total_requests": TOTAL_REQUESTS,
            "parallel_workers": MAX_WORKERS,
            "distribution": {
                "/api/quick-search": 20,
                "/api/search-candidates": 20,
                "/upload": 20,
                "/upload_with_jd": 10,
                "/upload_without_jd": 10,
            },
        },
        "per_endpoint": {
            ep: {
                "success": st["success"],
                "failure": st["failure"],
                "status_codes": dict(st["status_codes"]),
            }
            for ep, st in endpoint_stats.items()
        },
        "overall_status_codes": dict(overall_status),
        "overall_latency_ms": {
            "p50": round(percentile(latencies, 50), 2) if latencies else None,
            "p95": round(percentile(latencies, 95), 2) if latencies else None,
            "min": round(min(latencies), 2) if latencies else None,
            "max": round(max(latencies), 2) if latencies else None,
        },
        "non_200_count": len(errors),
        "representative_non_200": unique_errors,
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
