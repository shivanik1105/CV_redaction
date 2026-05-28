import requests
import json

# Test search that might match CAND_D108B415 (Sunil Durgale resume)
response = requests.post('http://127.0.0.1:5000/api/quick-search', json={
    'job_description': 'Sunil',  # Try searching for the name to see if it matches
    'limit': 10
})

data = response.json()
print(f"Total matches: {len(data.get('matches', []))}")
print("\nMatches:")
for i, match in enumerate(data.get('matches', [])[:5]):
    print(f"\n{i+1}. {match['anonymized_id']}")
    print(f"   Match %: {match.get('match_percentage')}%")
    print(f"   Has masked_pdf_filename: {'masked_pdf_filename' in match}")
    print(f"   Has masked_pdf_download_url: {'masked_pdf_download_url' in match}")
