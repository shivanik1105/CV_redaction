"""Check intelligence JSON files for errors"""
import json, os, glob

files = sorted(glob.glob('llm_analysis/*_intelligence.json'))
errors = 0
ok = 0
error_types = {}

for f in files:
    d = json.load(open(f, encoding='utf-8'))
    if 'error' in d and d.get('verdict') is None:
        errors += 1
        err = str(d.get('error', ''))[:100]
        error_types[err] = error_types.get(err, 0) + 1
    else:
        ok += 1

print(f"Total: {len(files)} | Valid (has verdict): {ok} | With errors: {errors}")
print("\nError types:")
for e, c in sorted(error_types.items(), key=lambda x: -x[1]):
    print(f"  [{c}x] {e}")

# Show first valid one
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    if d.get('verdict'):
        print(f"\nSample valid record: {os.path.basename(f)}")
        print(f"  anonymized_id: {d.get('anonymized_id')}")
        print(f"  verdict: {d.get('verdict')}")
        print(f"  match_score: {d.get('match_score')}")
        print(f"  confidence_score: {d.get('confidence_score')}")
        print(f"  seniority: {d.get('seniority_level')}")
        break

# Show first error
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    if 'error' in d and d.get('verdict') is None:
        print(f"\nSample error record: {os.path.basename(f)}")
        print(f"  error: {str(d.get('error', ''))[:200]}")
        break
