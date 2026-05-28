import json

# Read the app.py and check for the issue
with open('app.py', 'r') as f:
    content = f.read()
    
# Find the quick_search_api function and the part where masked_pdf_download_url is added
start_idx = content.find("masked_pdf_download_url = None")
if start_idx != -1:
    # Print 500 chars around it
    print("Found 'masked_pdf_download_url = None' at position:", start_idx)
    print("\nContext:")
    print(content[max(0, start_idx-200):min(len(content), start_idx+1000)])
else:
    print("Could not find 'masked_pdf_download_url = None' in app.py")
