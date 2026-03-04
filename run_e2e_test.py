"""End-to-end pipeline test: process all sample CVs with dynamic JD"""
import requests, json, time

jd = """We are looking for a Senior Java Developer with 5+ years experience in Java, 
Spring Boot, Microservices, and REST APIs. Experience with cloud platforms (AWS/Azure) 
and CI/CD pipelines is preferred. Strong problem-solving skills required."""

print("=== E2E Test: Processing all sample CVs ===")
print("Sending to /api/process-samples with dynamic JD...")
start = time.time()

r = requests.post('http://localhost:5000/api/process-samples', json={
    'job_description': jd,
    'force_reprocess': False
}, timeout=1800)

elapsed = time.time() - start
data = r.json()
print(f"Status: {r.status_code} | Time: {elapsed:.0f}s")
print(f"Total originals: {data.get('total_originals')}")
print(f"Redacted: {data.get('redacted')}")
print(f"Intelligence extracted: {data.get('intelligence_extracted')}")
print(f"Successful: {data.get('successful')}")
print(f"Failed: {data.get('failed')}")
print(f"Skipped (quota): {data.get('skipped', 0)}")
if data.get('quota_exhausted'):
    print('WARNING: Daily API quota exhausted. Re-run later to process remaining CVs.')

# Show first 5 results
print("\n--- Sample Results ---")
for res in data.get('results', [])[:5]:
    i = res.get('intelligence', {})
    print(f"  {res['file']}: {i.get('verdict')} | Match: {i.get('match_score')}% | Confidence: {i.get('confidence_score')}%")

# Show failures
failures = [res for res in data.get('results', []) if res.get('status') == 'error']
if failures:
    print(f"\n--- Failed ({len(failures)}) ---")
    for f in failures[:10]:
        print(f"  {f['file']}: {f.get('error', '')[:100]}")

# Verify Supabase
print("\n--- Supabase Verification ---")
stats = requests.get('http://localhost:5000/api/statistics').json()
s = stats.get('statistics', {})
print(f"Total candidates in DB: {s.get('total_candidates')}")
print(f"Avg match score: {s.get('average_match_score')}")
print(f"Avg confidence: {s.get('average_confidence_score')}")
print(f"Review needed: {s.get('review_needed')}")
print(f"Shortlisted: {s.get('shortlisted')}")

print("\n=== E2E Test Complete ===")
