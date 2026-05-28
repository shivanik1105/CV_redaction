# Fix CV Visibility Issues

## Problem Summary

You have **315 CVs in the database** but only **39 files on disk**. This causes:
- ❌ Search shows CVs that can't be downloaded
- ❌ Error: "Original CV file not found on server"
- ❌ 292 CVs are not accessible

## Root Cause

The CVs in the database were either:
1. Uploaded on a different machine
2. Imported from an archive
3. Files were deleted from `uploads/` folder

## Solution Options

### Option 1: Clean Database (Recommended)

**Remove database entries for CVs without files**

```bash
python clean_database.py
```

**What it does**:
- Removes 292 CV entries from database
- Keeps only 23 CVs that have files on disk
- Search will only show accessible CVs
- No more "file not found" errors

**Pros**:
- ✅ Clean, consistent state
- ✅ All visible CVs are downloadable
- ✅ No errors

**Cons**:
- ❌ Loses database entries (but files are already gone)

### Option 2: Re-upload Missing CVs

**Upload the original CV files again**

1. Find the original CV files (if you have them)
2. Upload them through the web interface
3. They will get new anonymized IDs
4. Old database entries will remain but be inaccessible

**Pros**:
- ✅ Keeps all CVs
- ✅ No data loss

**Cons**:
- ❌ Need original files
- ❌ Duplicate database entries
- ❌ Time-consuming (292 files)

### Option 3: Keep As-Is

**Do nothing, accept the errors**

**Pros**:
- ✅ No changes needed

**Cons**:
- ❌ Search shows inaccessible CVs
- ❌ Errors when trying to download
- ❌ Confusing for users

## Recommended Steps

### Step 1: Clean the Database

```bash
python clean_database.py
```

This will:
1. Check which CVs have files on disk
2. Ask for confirmation
3. Delete entries without files
4. Keep only accessible CVs

### Step 2: Fix Supabase Connection

The search 503 error is because Supabase connection failed during startup.

**Option A: Restart the app** (Simplest)
```bash
# Stop the app (Ctrl+C)
python app.py
```

**Option B: Reset connection** (If app is running)
```bash
python fix_search_503.py
```

### Step 3: Verify Everything Works

1. **Start the app**:
   ```bash
   python app.py
   ```

2. **Open browser**:
   ```
   http://127.0.0.1:5000
   ```

3. **Test search**:
   - Enter a job description
   - Click search
   - Should see only CVs with files
   - All CVs should be downloadable

## Current State

```
Database Status:
├── Total CVs in database: 315
├── CVs with files on disk: 23
├── CVs missing files: 292
└── Files in uploads/: 39

Processing Status:
├── Redacted files: 5
├── Intelligence files: 6
└── Filename mappings: 311
```

## After Cleanup

```
Database Status:
├── Total CVs in database: 23
├── CVs with files on disk: 23
├── CVs missing files: 0
└── Files in uploads/: 39

All CVs in database will be:
✅ Searchable
✅ Downloadable
✅ Accessible
```

## Troubleshooting

### If clean_database.py fails

**Error**: "Cannot connect to Supabase"
**Fix**: Check `.env` file has correct credentials

**Error**: "Permission denied"
**Fix**: Check Supabase key has delete permissions

### If search still returns 503

**Fix 1**: Restart the Flask app
```bash
python app.py
```

**Fix 2**: Reset Supabase connection
```bash
python fix_search_503.py
```

**Fix 3**: Check health endpoint
```
http://127.0.0.1:5000/health
```

Look for:
- `supabase_reachable_flag`: should be `true`
- `supabase`: should be "connected"

### If CVs still show errors

**Check**: Are the files actually in `uploads/` folder?
```bash
# Windows PowerShell
Get-ChildItem uploads | Measure-Object
```

**Check**: Do the filenames match?
- Database stores original filename
- Files might have timestamp prefix
- Example: `20260406_211457_Resume.pdf`

## Summary

**Problem**: 292 CVs in database but files missing
**Solution**: Clean database to remove entries without files
**Result**: All visible CVs will be accessible

**Commands**:
```bash
# 1. Analyze the situation
python sync_cvs_with_database.py

# 2. Clean the database
python clean_database.py

# 3. Restart the app
python app.py

# 4. Test search
# Go to http://127.0.0.1:5000 and search
```

**Expected Result**:
- ✅ Search works (no 503 error)
- ✅ All CVs are downloadable
- ✅ No "file not found" errors
- ✅ Clean, consistent state
