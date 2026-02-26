# Error Resolution Log

This document tracks the technical issues encountered during the development and deployment of the CV Intelligence & Recruitment System, along with their resolutions.

## 1. Google Gemini API Quota Exhaustion (429 RESOURCE_EXHAUSTED)

**Issue:**
- Attempting to use the Google Gemini API (`gemini-2.0-flash`, `gemini-1.5-flash`) resulted in immediate `429 RESOURCE_EXHAUSTED` errors.
- The error message indicated `limit: 0` for the free tier, even when using brand new API keys from new Google Cloud projects.
- This suggested a broader IP-based or device-based block on the free tier usage from the deployment environment.

**Resolution:**
- **Switched to Ollama (Local AI):** Configured the system to use a local LLM via Ollama (`qwen2.5:7b`). service.
- **Implementation:**
  - Installed `ollama` Python package.
  - Modified `llm_batch_processor.py` to support `LLM_PROVIDER="ollama"`.
  - Updated `cv_intelligence_extractor.py` to route requests correctly.
  - Added fallback environment variables to force the use of local models.

## 2. Missing `ollama` Python Package

**Issue:**
- After switching the configuration to use Ollama, the application crashed with `ModuleNotFoundError: No module named 'ollama'`.

**Resolution:**
- **Installed Dependency:** Ran `pip install ollama` to add the required client library for local AI communication.

## 3. Server Crash & Port Conflicts (500 Internal Server Error)

**Issue:**
- The Flask server became unresponsive or returned `500 Internal Server Error` during batch operations.
- Debugging scripts (`debug_500.py`) showed `ConnectionRefusedError: [WinError 10061]` and `ReadTimeout`, indicating the server process was either dead or hanging.
- Attempts to restart often failed because the previous process was still holding port 5000.

**Resolution:**
- **Process Cleanup:** Used `taskkill /F /IM python.exe` to forcefully terminate all stale Python processes before restarting.
- **Restart Procedure:** Standardized the restart command to ensure environment variables are set correctly before launching `app.py`.

## 4. Prompt Engineering & Output Parsing

**Issue:**
- Early AI responses were inconsistent, sometimes returning Markdown or conversational text instead of strict JSON.
- This caused `json.JSONDecodeError` in the backend, leading to empty dashboards.

**Resolution:**
- **Human-Readable Prompting:** Updated `cv_intelligence_extractor.py` to use a detailed "Prose" prompt format (SECTION 1, SECTION 2, RECOMMENDATION) which is easier for smaller models to generate reliably.
- **Regex Parsing:** Implemented a robust `_parse_prose_response` method using regular expressions to extract structured data (verdict, score, summary) from the text output, even if the JSON format was malformed.

## 5. Indentation Error in `llm_batch_processor.py`

**Issue:**
- During a hot-fix to add file caching logic, an `IndentationError` was introduced in `llm_batch_processor.py` after a `try:` block.
- This prevented the application from starting.

**Resolution:**
- **Code Fix:** Corrected the indentation to ensure the code block following `try:` was properly aligned.

## 6. Dashboard Data Population

**Issue:**
- The "Intelligence" dashboard was empty because the `batch_extract` API was failing silently or due to API blocks.

**Resolution:**
- **Batch Processing Fix:** Once the LLM provider was stabilized (via Ollama or a valid Gemini key), the batch processor successfully generated `_intelligence.json` files for each CV.
- **Caching:** Added logic to check for existing `_intelligence.json` files to skip re-processing already analyzed CVs, saving time and potential API tokens.
