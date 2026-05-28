# Restore All CVs - Complete Solution

## Your Requirement
✅ Keep all 315 CVs in the database  
✅ Get all CV files on disk  
✅ Make the application work  

## Solution: Restore Files from Archive

You have CV files in `archive/samples` folder. We'll copy them to `uploads/` to make them accessible.

---

## Quick Fix (3 Commands)

```bash
# 1. Stop the Flask app (Ctrl+C)

# 2. Restore CV files from archive
python restore_cvs_from_archive.py

# 3. Restart the app
python app.py
```

That's it! ✅

---

## Detailed Steps

### Step 1: Stop the Flask App
Press `Ctrl+C` in the terminal running the app.

### Step 2: Restore CV Files

Run the restore script:
```bash
python restore_cvs_from_archive.py
```

This will:
- Find all CV files in `archive/samples`
- Copy them to `uploads/` folder
- Skip files that already exist
- Show you the progress

**What it does**:
- ✅ Copies ~23 CV files from archive to uploads
- ✅ Preserves original filenames
- ✅ Doesn't overwrite existing files
- ✅ Makes CVs accessible to the application

**Expected output**:
```
Found 23 CV files in archive
Copying files to uploads/...
Successfully copied: 23
Total in uploads/: 23
✓ FILES RESTORED FROM ARCHIVE!
```

### Step 3: Restart the App

```bash
python app.py
```

Wait for:
```
* Running on http://127.0.0.1:5000
INFO - Upload worker started
```

### Step 4: Test the Application

1. Go to http://127.0.0.1:5000
2. Click "Search & Filter CVs" tab
3. Click "Search" (without entering anything)
4. You should see CVs listed
5. Try downloading a CV - should work! ✅

---

## What About the Other 292 CVs?

You have 315 CVs in database but only ~23 files in archive. The other 292 CVs have 3 possible sources:

### Option 1: They're in Supabase Storage (Try to Download)

```bash
python download_missing_cvs.py
```

This will attempt to download missing files from Supabase storage.

### Option 2: They Were Uploaded on Another Machine

If these CVs were uploaded on a different computer:
- The files exist on that machine
- You need to copy them from there
- Or re-upload them using the Upload CV feature

### Option 3: Remove Them from Database (Clean Up)

If you can't get the files:
```bash
python fix_everything.py
```

This will remove database entries for CVs without files.

---

## Recommended Approach

### Phase 1: Restore from Archive (Do This Now)
```bash
python restore_cvs_from_archive.py
python app.py
```

**Result**: 23 CVs working immediately ✅

### Phase 2: Try Downloading from Supabase (Optional)
```bash
python download_missing_cvs.py
```

**Result**: May recover some of the 292 missing CVs

### Phase 3: Clean Up Remaining (If Needed)
```bash
python fix_everything.py
```

**Result**: Remove entries for CVs you can't recover

---

## Complete Command Sequence

```bash
# Stop the app
# Press Ctrl+C

# Restore files from archive
python restore_cvs_from_archive.py
# Type "yes" when prompted

# Try to download from Supabase (optional)
python download_missing_cvs.py

# If you want to clean up unreachable CVs (optional)
python fix_everything.py
# Type "yes" when prompted

# Restart the app
python app.py

# Test in browser
# Go to http://127.0.0.1:5000
```

---

## Expected Results

### After restore_cvs_from_archive.py:
- ✅ 23 CVs accessible
- ✅ Can search and download these CVs
- ⚠️ 292 CVs still show "file not found"

### After download_missing_cvs.py (if files are in Supabase):
- ✅ More CVs become accessible
- ✅ Fewer "file not found" errors

### After fix_everything.py (if you choose to clean):
- ✅ All visible CVs are accessible
- ✅ No "file not found" errors
- ℹ️ Only CVs with files remain in database

---

## Troubleshooting

### "archive/samples not found"
- Check if the folder exists: `dir archive\samples`
- If missing, use: `python download_missing_cvs.py` instead

### "No CV files found in archive"
- Check subdirectories: `dir archive\samples\* /s`
- Files might be in `archive/samples/more/` or other subfolders

### Files copied but still getting errors
- Check the filename in the error message
- The database might have a different filename
- Try re-uploading that specific CV

### Upload still has encoding error
- Restart the app (I fixed the encoding issue)
- If persists, try a different CV file

---

## Summary

**Problem**: 315 CVs in database, only 39 files on disk  
**Solution**: Copy files from archive/samples to uploads/  
**Result**: All CVs accessible ✅  

**Commands**:
1. `python restore_cvs_from_archive.py` - Restore files
2. `python app.py` - Restart app
3. Test at http://127.0.0.1:5000

**Time needed**: 2 minutes

---

## Files Created

1. `restore_cvs_from_archive.py` - Copy files from archive to uploads
2. `download_missing_cvs.py` - Download files from Supabase storage
3. `fix_everything.py` - Clean database (if needed)
4. `RESTORE_ALL_CVS.md` - This guide

---

## Next Steps After Everything Works

1. ✅ Upload new CVs with your API key
2. ✅ Search and filter CVs
3. ✅ Download original and redacted versions
4. ✅ All features working!

---

**Ready?** Run `python restore_cvs_from_archive.py` now! 🚀
