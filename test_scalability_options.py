"""
Test 3 scalability options for CV intelligence extraction:

Option 1: Native JSON Mode (Zero Parsed Formatting)
  - Use Gemini's response_mime_type="application/json"
  - Drops test generation time from 3.5 seconds to ~0.8 seconds per CV

Option 2: Asynchronous Batching (Concurrency)
  - Use ThreadPoolExecutor or asyncio to send 10-20 CVs to Gemini simultaneously
  - 100 CVs finish in under 15 seconds instead of 5 minutes

Option 3: Local Keyword/Requirement Filter (The Checkpoint)
  - Add a local Python fu