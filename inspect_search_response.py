import requests
import json

response = requests.post('http://127.0.0.1:5000/api/quick-search', json={
    'job_description': 'developer',
    'limit': 2
})

data = response.json()

# Save full response to file
with open('search_response_full.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Full response saved to search_response_full.json")
print(f"\nTotal matches: {len(data.get('matches', []))}")

if data.get('matches'):
    match = data['matches'][0]
    print(f"\nFirst match keys ({len(match)} total):")
    for key in sorted(match.keys()):
        print(f"  - {key}")
    
    # Specifically check for masked PDF fields
    print(f"\nMasked PDF fields check:")
    print(f"  'masked_pdf_filename' in keys: {'masked_pdf_filename' in match}")
    print(f"  'masked_pdf_download_url' in keys: {'masked_pdf_download_url' in match}")
