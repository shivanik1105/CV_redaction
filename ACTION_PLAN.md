# Complete Action Plan - Fix All Issues

## Current Status

### ✅ Working:
- Upload feature (file upload, redaction, masked PDF creation)
- Supabase connection
- File processing pipeline

### ⚠️ Issues to Fix:
1. **Encoding error** during LLM intelligence extraction
2. **Missing CV files** - 292 CVs in database without files on disk

---

## STEP 1: Fix Encoding Error (Already Done)

**What was fixed**: Added UTF-8 encoding handling in `cv_intelligence_extractor.py`

**File modified**: `cv_intelligence_extractor.py` (line ~31-48)

**What to do**: 
```bash
# Stop the Flask app (Ctrl+C in the terminal)
# Then restart it:
python app.py
```

**Expected result**: Upload will complete successfully with intelligence extraction

---

## STEP 2: Clean Up Missing CVs

### Problem:
You have 292 CVs in the database that don't have files on disk. These show error:
```
"error": "Original CV file not found on server for CAND_B418BE2B"
```

### Solution:
Run the cleanup script to remove these database entries.

### How to do it:

**Option A: Automatic Cleanup (Recommended)**
```bash
python fix_everything.py
```

This will:
1. Analyze CVs in database vs files on disk
2. Show you what will be deleted
3. Ask for confirmation
4. Remove database entries for CVs without files
5. Keep only accessible CVs

**Option B: Manual Cleanup**
```bash
python clean_database.py
```

### What will happen:
- **Before**: 315 CVs in database, only 23 accessible
- **After**: 23 CVs in database, all 23 accessible
- **Deleted**: 292 database entries (no files lost, they were already missing)

---

## STEP 3: Restart App and Test

After cleanup:

```bash
# Stop the app (Ctrl+C)
python app.py
```

Then test:
1. Go to http://127.0.0.1:5000
2. Search for CVs
3. All results should be downloadable (no more "file not found" errors)
4. Try uploading a new CV with your API key

---

## Complete Command Sequence

Run these commands in order:

```bash
# 1. Stop the Flask app
# Press Ctrl+C in the terminal running the app

# 2. Clean up database
python fix_everything.py
# Type "yes" when prompted

# 3. Restart the app
python app.py

# 4. Test in browser
# Go to http://127.0.0.1:5000
# Try search and upload
```

---

## Expected Results After All Fixes

### Upload Feature:
- ✅ File upload works
- ✅ Text extraction works
- ✅ PII redaction works
- ✅ Masked PDF creation works
- ✅ LLM intelligence extraction works (no encoding errors)
- ✅ Supabase storage works
- ✅ Success message with download links

### Search Feature:
- ✅ All search results are downloadable
- ✅ No "file not found" errors
- ✅ Only accessible CVs shown
- ✅ 23 CVs available (all with files on disk)

### Database:
- ✅ Clean and in sync with files on disk
- ✅ No orphaned entries
- ✅ All entries have corresponding files

---

## Troubleshooting

### If encoding error persists after restart:
1. Check that you restarted the app (Ctrl+C then `python app.py`)
2. Check the logs for the specific error
3. The CV might have very unusual characters - try a different CV

### If cleanup script fails:
1. Check Supabase credentials in `.env`
2. Make sure you have internet connection
3. Try running `python clean_database.py` instead

### If upload still fails:
1. Make sure you entered your API key in the form
2. Check browser DevTools (F12) → Network tab → /upload request → Payload
3. Verify `llm_api_key` is being sent

---

## Summary

**Total time needed**: ~5 minutes

**Steps**:
1. ✅ Encoding fix applied (restart app)
2. ⏳ Run database cleanup (`python fix_everything.py`)
3. ⏳ Restart app (`python app.py`)
4. ⏳ Test upload and search

**Result**: Fully working CV upload and search system with clean database

---

## Quick Reference

### Start the app:
```bash
python app.py
```

### Stop the app:
```
Press Ctrl+C
```

### Clean database:
```bash
python fix_everything.py
```

### Test upload:
```bash
python test_upload_api_key.py
```

### Check what's in database:
```bash
python sync_cvs_with_database.py
```

---

## Next Steps After Everything Works

1. **Upload more CVs**: Use your API key to upload CVs
2. **Test search**: Search with job descriptions
3. **Download CVs**: Download original and redacted versions
4. **Monitor logs**: Watch for any errors in the terminal

---

## Files Modified

1. `cv_intelligence_extractor.py` - Added UTF-8 encoding handling
2. Database will be cleaned by `fix_everything.py`

## Files Created

1. `ACTION_PLAN.md` (this file)
2. `UPLOAD_FIX_SUMMARY.md` - Detailed upload fix documentation
3. `test_upload_api_key.py` - Backend testing script
4. `test_upload_form.html` - Frontend testing form

---

**Ready to proceed?** Run the commands in Step 3 above!
