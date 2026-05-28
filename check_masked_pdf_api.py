import requests
import json

response = requests.post('http://127.0.0.1:5000/api/quick-search', json={'job_description': 'test', 'limit': 1})
data = response.json()

if data.get('matches'):
    match = data['matches'][0]
    print("API Response Sample:")
    print(f"  ID: {match.get('anonymized_id')}")
    print(f"  Has masked_pdf_filename: {'masked_pdf_filename' in match}")
    print(f"  Has masked_pdf_download_url: {'masked_pdf_download_url' in match}")
    if match.get('masked_pdf_download_url'):
        print(f"  URL: {match.get('masked_pdf_download_url')[:50]}...")
else:
    print("No matches in response")
