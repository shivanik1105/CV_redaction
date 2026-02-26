import requests
import json
import traceback

print("Sending request to batch-extract...")
try:
    response = requests.post(
        "http://localhost:5000/api/batch-extract",
        json={"job_description": "We need a Python expert."},
        timeout=120
    )
    print(f"Status: {response.status_code}")
    print("Response text:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
    traceback.print_exc()
