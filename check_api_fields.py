import requests
import json

response = requests.post('http://127.0.0.1:5000/api/quick-search', json={'job_description': 'developer', 'limit': 1})
data = response.json()

if data.get('matches'):
    match = data['matches'][0]
    print("First match keys:")
    for key in sorted(match.keys()):
        print(f"  - {key}")
    print(f"\nMasked PDF fields present:")
    print(f"  masked_pdf_filename: {'masked_pdf_filename' in match}")
    print(f"  masked_pdf_download_url: {'masked_pdf_download_url' in match}")
else:
    print("No matches in response")
