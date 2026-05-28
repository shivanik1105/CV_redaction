# Render Deployment Guide - CV Intelligence System

## ✅ Pre-Deployment Checklist

All fixes have been applied and your application is ready for Render deployment:

- ✅ **Encoding fix** - UTF-8 handling in `cv_intelligence_extractor.py`
- ✅ **Visual masking** - Black boxes in masked PDFs
- ✅ **PyMuPDF** - Added to `requirements.txt`
- ✅ **Database cleaned** - Only CVs with files
- ✅ **Upload feature** - Works with user API keys
- ✅ **Render config** - `render.yaml` configured

---

## 🚀 Deployment Steps

### 1. Push Code to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit changes
git commit -m "Ready for Render deployment with all fixes"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/cv-intelligence.git

# Push to GitHub
git push -u origin main
```

### 2. Create Render Web Service

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml`

### 3. Configure Environment Variables

In Render dashboard, add these environment variables:

#### Required:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_api_key
```

#### Optional (if using other LLM providers):
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
```

#### Application Settings:
```
UPLOAD_WORKER_COUNT=0
LLM_MAX_CONCURRENT_REQUESTS=1
PYTHON_VERSION=3.11.0
WEB_CONCURRENCY=1
```

### 4. Deploy

Click **"Create Web Service"** and Render will:
1. Install dependencies from `requirements.txt`
2. Download spaCy model
3. Install PyMuPDF for visual masking
4. Start the application with gunicorn

---

## 📋 Render Configuration Details

### Build Command:
```bash
pip install -r requirements.txt
```

### Start Command:
```bash
gunicorn --preload --workers 1 --threads 1 --timeout 180 --max-requests 100 --max-requests-jitter 10 --bind 0.0.0.0:$PORT app:app
```

### Why These Settings?

- **`--workers 1`**: Single worker to avoid memory issues on free tier
- **`--threads 1`**: Single thread for stability
- **`--timeout 180`**: 3 minutes for LLM processing
- **`--preload`**: Load app before forking workers
- **`--max-requests 100`**: Restart worker after 100 requests (memory management)

---

## 🔧 Important Notes

### 1. File Storage on Render

⚠️ **Render uses ephemeral storage** - uploaded files are lost on restart!

**Solutions**:

**Option A: Use Supabase Storage (Recommended)**
- Store uploaded CVs in Supabase storage bucket
- Modify upload endpoint to save to Supabase
- Files persist across restarts

**Option B: Use External Storage**
- AWS S3
- Google Cloud Storage
- Cloudinary

**Option C: Accept Ephemeral Storage**
- Files lost on restart
- Users must re-upload CVs
- Database entries remain (will show "file not found")

### 2. Database

✅ **Supabase database persists** - CV metadata is safe
❌ **Local files don't persist** - Need external storage

### 3. Memory Limits

Render free tier has memory limits:
- **Free**: 512 MB RAM
- **Starter**: 1 GB RAM

**Optimization**:
- Set `UPLOAD_WORKER_COUNT=0` (no background workers)
- Set `WEB_CONCURRENCY=1` (single worker)
- Process uploads synchronously

---

## 🐛 Troubleshooting

### Build Fails

**Error**: "Could not find a version that satisfies the requirement"

**Fix**: Check `requirements.txt` for version conflicts
```bash
# Test locally first
pip install -r requirements.txt
```

### Timeout Errors

**Error**: "Worker timeout"

**Fix**: Increase timeout in `render.yaml`:
```yaml
startCommand: gunicorn --timeout 300 ...
```

### Memory Errors

**Error**: "Out of memory"

**Fix**: 
1. Upgrade to Starter plan (1 GB RAM)
2. Or reduce concurrent requests:
```
LLM_MAX_CONCURRENT_REQUESTS=1
```

### Files Not Found After Restart

**Expected**: Render uses ephemeral storage

**Fix**: Implement Supabase storage (see below)

---

## 💾 Implementing Supabase Storage (Recommended)

To persist uploaded files across restarts:

### 1. Create Supabase Storage Bucket

1. Go to Supabase dashboard
2. Storage → Create bucket
3. Name: `cv-uploads`
4. Make it private

### 2. Modify Upload Endpoint

Add this to `app.py` after saving file locally:

```python
# After: file.save(upload_path)

# Upload to Supabase storage
try:
    supabase_storage = get_supabase_storage()
    if supabase_storage:
        with open(upload_path, 'rb') as f:
            file_bytes = f.read()
        
        storage_path = f"originals/{anonymized_id}{Path(upload_path).suffix}"
        supabase_storage.client.storage.from_('cv-uploads').upload(
            storage_path,
            file_bytes,
            file_options={"content-type": "application/pdf"}
        )
        logger.info(f"Uploaded to Supabase storage: {storage_path}")
except Exception as e:
    logger.warning(f"Could not upload to Supabase storage: {e}")
```

### 3. Modify Download Endpoint

Add fallback to download from Supabase storage when local file not found.

---

## 📊 Post-Deployment Checklist

After deployment:

- [ ] Check Render logs for errors
- [ ] Test homepage loads
- [ ] Test upload CV feature
- [ ] Test search feature
- [ ] Test download original CV
- [ ] Test download masked PDF
- [ ] Verify visual black boxes in masked PDF
- [ ] Check Supabase connection
- [ ] Monitor memory usage

---

## 🔗 Useful Links

- **Render Dashboard**: https://dashboard.render.com
- **Render Docs**: https://render.com/docs
- **Supabase Dashboard**: https://supabase.com/dashboard
- **Your App URL**: `https://your-app-name.onrender.com`

---

## 📝 Environment Variables Summary

Copy these to Render dashboard:

```
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=gsk_your_groq_key

# Optional LLM Providers
OPENAI_API_KEY=sk-your_openai_key
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
GEMINI_API_KEY=your_gemini_key

# Application Settings
UPLOAD_WORKER_COUNT=0
LLM_MAX_CONCURRENT_REQUESTS=1
PYTHON_VERSION=3.11.0
WEB_CONCURRENCY=1

# Optional
SUPABASE_STORAGE_BUCKET=cv-uploads
```

---

## 🎯 Quick Deploy Commands

```bash
# 1. Commit all changes
git add .
git commit -m "Deploy to Render with all fixes"

# 2. Push to GitHub
git push origin main

# 3. Render will auto-deploy!
```

---

## ✅ What's Included in This Deployment

1. ✅ **Visual PDF masking** - Black boxes over PII
2. ✅ **UTF-8 encoding** - Handles international characters
3. ✅ **User API keys** - Users provide their own LLM keys
4. ✅ **Clean database** - Only CVs with files
5. ✅ **Optimized for Render** - Memory-efficient settings
6. ✅ **All dependencies** - PyMuPDF, spaCy, etc.

---

## 🚨 Important Reminders

1. **Files are ephemeral** - Implement Supabase storage for persistence
2. **Set environment variables** - Required for app to work
3. **Monitor memory** - Free tier has 512 MB limit
4. **Check logs** - Render dashboard → Logs tab
5. **Test thoroughly** - After deployment, test all features

---

**Your application is ready for Render deployment!** 🚀

Just push to GitHub and create the web service on Render!
