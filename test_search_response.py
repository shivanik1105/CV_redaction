import requests
import json

response = requests.post('http://127.0.0.1:5000/api/quick-search', json={'job_description': 'developer', 'limit': 5})
print("Status Code:", response.status_code)
print("\nFull Response:")
print(json.dumps(response.json(), indent=2)[:1500])
