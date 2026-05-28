# Test CV Upload - Quick Guide

## Fixes Applied ✅

1. ✅ Better Supabase error handling
2. ✅ LLM extraction error handling  
3. ✅ Favicon 404 fixed
4. ✅ Better error logging

## How to Test

### Step 1: Restart the Application

**Stop the current server** (if running):
- Press `Ctrl+C` in the terminal

**Start the server**:
```bash
python app.py
```

**Wait for**:
```
* Running on http://127.0.0.1:5000
INFO - Upload worker started
INFO - Embedding model loaded
```

### Step 2: Open the Application

Go to: **http://127.0.0.1:5000**

### Step 3: Upload a CV

1. Click "Choose file" or drag & drop a PDF/DOCX
2. (Optional) Paste a job description
3. Click "Upload CV"
4. **Watch the server terminal** for logs

### Step 4: Check the Logs

#### ✅ Success Logs (Good):
```
INFO - Processing CV: filename.pdf
INFO - Text extraction successful
INFO - Text redaction successful
INFO - LLM extraction successful (or WARNING if failed)
INFO - Supabase connection established (or WARNING if failed)
INFO - CV processed successfully
```

#### ⚠️ Warning Logs (OK - Handled):
```
WARNING - Supabase connection test failed: ...
WARNING - Could not store intelligence in Supabase: ...
ERROR - LLM extraction failed: ...
```

#### ❌ Error Logs (Problem):
```
ERROR - CV processing failed: ...
ERROR - Unhandled exception: ...
```

### Step 5: Verify Results

#### If Upload Succeeds:
- ✅ You'll see a success message in the UI
- ✅ Preview of redacted text appears
- ✅ Download buttons appear
- ✅ File created in `redacted_output/` directory

#### If Upload Fails:
- ❌ Error message appears in UI
- ❌ Check server logs for details
- ❌ Share the error message for help

## Common Issues & Solutions

### Issue 1: "Job failed: CV processing failed"

**Check**: Server logs for the actual error

**Possible causes**:
1. LLM API timeout → Now handled gracefully
2. Supabase connection → Now handled gracefully
3. File format issue → Check if PDF/DOCX is valid

**Solution**: The fixes should prevent this. If it still happens, check logs.

### Issue 2: Upload takes too long (>60 seconds)

**Normal**: First upload can take 30-60 seconds because:
- Embedding model loads (20-30 seconds)
- LLM extraction (10-20 seconds)
- Text processing (5-10 seconds)

**Solution**: Wait patiently. Subsequent uploads will be faster.

### Issue 3: 503 Error on Search

**Normal**: This happens when:
- No CVs uploaded yet
- Supabase not connected

**Solution**: Upload a CV first, then search will work.

### Issue 4: Supabase Connection Failed

**Error**: `Client.__init__() got an unexpected keyword argument 'proxy'`

**Solution**:
```bash
pip install --upgrade supabase
```

Then restart the app.

## What to Look For

### ✅ Good Signs:
- Server starts without errors
- Upload completes (even with warnings)
- Redacted file created
- Preview shows redacted text
- Download buttons work

### ⚠️ Warnings (OK):
- Supabase connection failed (app continues)
- LLM extraction failed (app continues)
- Redis connection failed (app continues)

### ❌ Bad Signs:
- Server crashes
- Upload fails with no error message
- No files created in `redacted_output/`
- Unhandled exceptions in logs

## Testing Checklist

- [ ] Server starts successfully
- [ ] Can access http://127.0.0.1:5000
- [ ] Can select a file
- [ ] Upload button works
- [ ] Server logs show processing
- [ ] Upload completes (success or handled error)
- [ ] Redacted file created
- [ ] Can download redacted text
- [ ] (Optional) Can download masked PDF
- [ ] (Optional) CV appears in search

## Next Steps After Successful Upload

### If Everything Works:
1. Upload more CVs
2. Test the search functionality
3. Test job matching
4. Review the redacted output

### If Supabase Works:
1. Check the database for stored CVs
2. Test semantic search
3. Test bulk download
4. Test candidate management

### If Only Local Storage Works:
1. You can still use the redaction
2. You can still download files
3. Search won't work (no database)
4. Fix Supabase connection for full features

## Getting Help

If upload still fails after these fixes:

1. **Copy the error from server logs**
2. **Note what step failed**:
   - Text extraction?
   - Redaction?
   - LLM extraction?
   - Supabase storage?
3. **Check the error type**:
   - Timeout?
   - API error?
   - File format?
   - Permission issue?

## Summary

**Before fixes**:
- ❌ Upload failed with no useful error
- ❌ Supabase issues crashed upload
- ❌ LLM issues crashed upload
- ❌ Favicon 404 error

**After fixes**:
- ✅ Upload continues even if Supabase fails
- ✅ Upload continues even if LLM fails
- ✅ Detailed error logging
- ✅ Favicon 404 fixed
- ✅ Better error messages

**Result**: Upload should work now, even if some services fail!

---

**Ready to test?** Restart the app and try uploading a CV! 🚀
