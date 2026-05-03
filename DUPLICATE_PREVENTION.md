# Duplicate Prevention System

## 🎯 Overview

The CV Intelligence System now includes **automatic duplicate detection** to prevent the same CV from being uploaded multiple times. This saves storage space, processing costs, and keeps your database clean.

## ✅ Features

### 1. **Automatic Detection**
- Every uploaded CV is checked against existing candidates
- Uses SHA256 hash for accurate duplicate detection
- Works for both PDF and DOCX files
- Detection happens **before** processing (saves LLM costs)

### 2. **User-Friendly Warnings**
When a duplicate is detected, the user sees:
- ⚠️ Clear warning message
- Details of the existing candidate:
  - Anonymized ID
  - Upload date
  - Years of experience
  - Primary domain
  - Core skills
- Option to force reprocess if needed

### 3. **Force Reprocess Option**
Users can override duplicate detection by:
- Checking the "Force Reprocess" checkbox
- Useful for:
  - Updated CVs (same person, new version)
  - Testing purposes
  - Re-running with different JD

## 🔧 How It Works

### Upload Flow

```
1. User uploads CV file
   ↓
2. Compute SHA256 hash of file content
   ↓
3. Check if hash exists in database
   ↓
4a. DUPLICATE FOUND          4b. NOT A DUPLICATE
    ↓                             ↓
    Show warning with details     Continue processing
    ↓                             ↓
    User can force reprocess      Save to database with hash
```

### Technical Details

**Hash Computation:**
```python
import hashlib
file_hash = hashlib.sha256(file_content).hexdigest()
```

**Database Check:**
```sql
SELECT * FROM cv_intelligence 
WHERE original_cv_hash = '<computed_hash>' 
LIMIT 1
```

**Response (409 Conflict):**
```json
{
  "success": false,
  "error": "Duplicate CV detected",
  "is_duplicate": true,
  "existing_candidate": {
    "anonymized_id": "CAND_123",
    "uploaded_at": "2026-05-03 10:30:00",
    "years_experience": 5,
    "primary_domain": "Software Development",
    "core_skills": ["Python", "Django", "Flask"]
  },
  "message": "This CV was already uploaded as CAND_123. Use 'force_reprocess' to upload anyway."
}
```

## 📊 Statistics

After cleanup, your system has:
- **139 unique candidates** (down from 263)
- **100% hash coverage** (all candidates have hashes)
- **0 duplicates** in database
- **10 files** in storage (down from 268)

## 🎨 User Interface

### Upload Form

```
┌─────────────────────────────────────────┐
│ CV File (PDF/DOCX)                      │
│ [Choose File] No file selected          │
├─────────────────────────────────────────┤
│ Job Description (Optional)              │
│ [Text area for JD]                      │
├─────────────────────────────────────────┤
│ ☑ Process asynchronously                │
│ ☐ Force Reprocess (upload even if       │
│   duplicate detected)                   │
├─────────────────────────────────────────┤
│ [Upload CV] [Reset]                     │
└─────────────────────────────────────────┘
```

### Duplicate Warning

```
⚠️ Duplicate CV Detected!

This CV was already uploaded:
• ID: CAND_225
• Uploaded: 2026-03-04 12:26:36
• Experience: 5.5 years
• Domain: Software Development
• Skills: Python, Django, Flask

To upload anyway, enable "Force Reprocess" option.
```

## 🔒 Security & Privacy

- **Hash-based detection**: Only file content hash is stored, not the file itself
- **No PII in hash**: Hash is computed from binary content, not extracted text
- **Fast lookup**: Database index on `original_cv_hash` column
- **Graceful degradation**: If Supabase is down, upload is allowed (better than blocking)

## 📈 Benefits

### Before Duplicate Prevention
- ❌ Same CV uploaded 20+ times
- ❌ Wasted storage space (268 files)
- ❌ Wasted LLM processing costs
- ❌ Polluted search results
- ❌ Confused recruiters

### After Duplicate Prevention
- ✅ Each CV uploaded once
- ✅ Minimal storage (10 files)
- ✅ No wasted LLM calls
- ✅ Clean search results
- ✅ Clear candidate tracking

## 🧪 Testing

### Test Duplicate Detection

```bash
python test_duplicate_detection.py
```

**Expected Output:**
```
✓ Duplicate detection is working correctly!
✓ New uploads will be checked for duplicates
✓ Users can override with 'Force Reprocess' checkbox
```

### Manual Test

1. Upload a CV through the web interface
2. Try uploading the **same file** again
3. You should see the duplicate warning
4. Enable "Force Reprocess" checkbox
5. Upload succeeds with new anonymized ID

## 🔧 Configuration

### Enable/Disable Duplicate Detection

In `app.py`, the duplicate check can be bypassed with:

```python
force_reprocess = True  # Skip duplicate check
```

### Adjust Hash Algorithm

Currently using SHA256. To change:

```python
# In _check_duplicate_upload function
file_hash = hashlib.sha256(file_content).hexdigest()  # Current
file_hash = hashlib.md5(file_content).hexdigest()     # Faster, less secure
file_hash = hashlib.sha512(file_content).hexdigest()  # More secure, slower
```

## 📝 API Reference

### Upload Endpoint

**POST** `/upload`

**Parameters:**
- `cv_file` (file, required): PDF or DOCX file
- `job_description` (string, optional): JD for matching
- `async` (boolean, optional): Process asynchronously
- `force_reprocess` (boolean, optional): Skip duplicate check

**Response (Success):**
```json
{
  "success": true,
  "mode": "asynchronous",
  "job_id": "abc123",
  "status_url": "/api/upload-jobs/abc123"
}
```

**Response (Duplicate - 409 Conflict):**
```json
{
  "success": false,
  "error": "Duplicate CV detected",
  "is_duplicate": true,
  "existing_candidate": {
    "anonymized_id": "CAND_123",
    "uploaded_at": "2026-05-03 10:30:00",
    "years_experience": 5,
    "primary_domain": "Software Development",
    "core_skills": ["Python", "Django", "Flask"]
  }
}
```

## 🐛 Troubleshooting

### Issue: Duplicate not detected

**Possible causes:**
1. Old candidates don't have hashes (uploaded before this feature)
2. File was modified slightly (different hash)
3. `force_reprocess` was enabled

**Solution:**
- Check if candidate has `original_cv_hash` in database
- Run cleanup script to backfill hashes for old candidates

### Issue: False positive (not a duplicate)

**Possible causes:**
1. Exact same file uploaded twice (legitimate duplicate)
2. Hash collision (extremely rare with SHA256)

**Solution:**
- Use "Force Reprocess" to upload anyway
- Check if files are truly identical

### Issue: Duplicate check is slow

**Possible causes:**
1. No index on `original_cv_hash` column
2. Large database

**Solution:**
```sql
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_hash 
ON cv_intelligence(original_cv_hash);
```

## 📚 Related Documentation

- [Cleanup Scripts](cleanup_duplicates_simple.py) - Remove existing duplicates
- [Orphaned Files](cleanup_orphaned_files.py) - Clean up files without DB records
- [Database Schema](supabase_production_tables.sql) - Table structure

## 🎉 Summary

The duplicate prevention system:
- ✅ Automatically detects duplicate uploads
- ✅ Shows clear warnings to users
- ✅ Allows override with "Force Reprocess"
- ✅ Saves storage space and processing costs
- ✅ Keeps database clean and organized
- ✅ Works seamlessly with existing features

**Result:** Your CV Intelligence System is now production-ready with robust duplicate prevention! 🚀
