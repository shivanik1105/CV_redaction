# Simple Deployment Guide - CV Intelligence System

## 🚀 Deploy to Render in 10 Minutes (No Authentication)

This is a simplified deployment without user authentication. Anyone with the URL can access the system.

---

## 📋 Prerequisites

1. **GitHub account** - https://github.com
2. **Render account** - https://render.com (free to start)
3. **Groq API key** - https://console.groq.com (free)
4. **Supabase account** - https://supabase.com (free)

---

## 🔑 Step 1: Get API Keys (5 minutes)

### 1.1 Groq API Key (Free)
1. Go to https://console.groq.com
2. Sign up / Log in
3. Go to "API Keys"
4. Click "Create API Key"
5. Copy the key (starts with `gsk_...`)
6. Save it securely

**Free Tier**: 6,000 requests/day

### 1.2 Supabase Setup
1. Go to https://supabase.com
2. Create new project
3. Wait for database to initialize (~2 minutes)
4. Go to Project Settings → API
5. Copy:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJ...`

### 1.3 Run SQL Setup
1. In Supabase Dashboard, go to SQL Editor
2. Click "New Query"
3. Copy content from `supabase_pgvector_setup.sql` in your project
4. Paste and click "Run"
5. Should see "Success"

---

## 📤 Step 2: Push to GitHub (2 minutes)

### Option A: Using the Script (Easiest)
```powershell
# Run the push script
.\push_to_github.ps1

# Follow the instructions to:
# 1. Create GitHub repo at: https://github.com/new
# 2. Name it: cv-intelligence-system
# 3. Run the command shown to add remote and push
```

### Option B: Manual Steps
```powershell
# Initialize Git
git init
git add .
git commit -m "Initial commit - CV Intelligence System"

# Create repo on GitHub: https://github.com/new
# Name: cv-intelligence-system

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/cv-intelligence-system.git
git branch -M main
git push -u origin main
```

---

## 🌐 Step 3: Deploy to Render (3 minutes)

### 3.1 Create Web Service
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository: `cv-intelligence-system`

### 3.2 Configure Service
Fill in these settings:

- **Name**: `cv-intelligence-system` (or your choice)
- **Region**: Oregon (or closest to you)
- **Branch**: `main`
- **Root Directory**: (leave empty)
- **Runtime**: Python 3
- **Build Command**:
  ```bash
  pip install -r requirements.txt && python -m spacy download en_core_web_sm
  ```
- **Start Command**:
  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
  ```
- **Plan**: 
  - Free (sleeps after 15 min) or
  - Starter ($7/month - always on, recommended)

### 3.3 Add Environment Variables
Click "Advanced" → "Add Environment Variable"

Add these:
```
GROQ_API_KEY=gsk_your_actual_groq_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
```

### 3.4 Deploy
1. Click "Create Web Service"
2. Wait 5-10 minutes for deployment
3. Watch the logs for any errors
4. Once deployed, you'll get a URL like: `https://cv-intelligence-system.onrender.com`

---

## ✅ Step 4: Test Your Deployment

### 4.1 Access the Application
1. Go to your Render URL: `https://your-app.onrender.com`
2. You should see the main page (no login required)

### 4.2 Test Features
- [ ] Go to `/redactor` - Upload and redact a CV
- [ ] Go to `/upload` - Upload CV with intelligence extraction
- [ ] Go to `/search` - Search candidates
- [ ] Go to `/dashboard` - View statistics

### 4.3 Health Check
Visit: `https://your-app.onrender.com/health`

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": {
    "supabase": true,
    "llm": true
  }
}
```

---

## 🔗 Share with Your Team

Send your team this URL:
```
CV Intelligence System

URL: https://your-app.onrender.com

Pages:
- CV Redactor: /redactor
- Upload & Process: /upload
- Search Candidates: /search
- Dashboard: /dashboard

No login required - just access the URL!
```

---

## 💰 Cost Breakdown

### Free Tier:
```
Render Free: $0
  - Sleeps after 15 min inactivity
  - Cold start: 30-60 seconds

Supabase Free: $0
  - 500MB database
  - 1GB file storage

Groq Free: $0
  - 6,000 requests/day

Total: $0/month
```

### Production (Recommended):
```
Render Starter: $7/month
  - Always on (no sleep)
  - Fast response

Supabase Free: $0
Groq Free: $0

Total: $7/month
```

---

## 🔧 Troubleshooting

### Issue: Build Failed
**Check**: Render logs for specific error
**Solution**: Verify requirements.txt is correct

### Issue: App Crashes
**Check**: Environment variables are set correctly
**Solution**: 
- Verify GROQ_API_KEY is valid
- Verify SUPABASE_URL and SUPABASE_KEY are correct

### Issue: "Supabase not connected"
**Check**: Supabase credentials
**Solution**:
- Verify SUPABASE_URL and SUPABASE_KEY
- Check Supabase project is active
- Re-run SQL setup if needed

### Issue: Slow Performance
**Cause**: Free tier sleeps after 15 min
**Solution**: Upgrade to Starter plan ($7/month)

### Issue: LLM Extraction Fails
**Check**: GROQ_API_KEY is valid
**Solution**: 
- Verify API key in Groq dashboard
- Check API usage/limits

---

## 🔄 Updates

### Deploy Updates:
```powershell
# Make changes to your code
git add .
git commit -m "Update: description"
git push origin main

# Render will auto-deploy
```

---

## ⚠️ Security Note

**This deployment has NO authentication!**

Anyone with the URL can:
- Upload CVs
- View all candidates
- Search and download data

**Recommendations**:
1. Don't share the URL publicly
2. Only share with trusted team members
3. Consider adding authentication later if needed
4. Monitor usage in Render dashboard

---

## 📊 Features Available

✅ CV Redaction (PII removal)
✅ Intelligence Extraction (LLM)
✅ Job Description Matching
✅ Candidate Search & Ranking
✅ Supabase Cloud Storage
✅ Multi-column CV Support
✅ Dashboard & Statistics

---

## 🎉 You're Done!

Your CV Intelligence System is now live and accessible!

**URL**: `https://your-app.onrender.com`

**Cost**: $0-7/month

**Time to deploy**: ~10 minutes

Enjoy! 🚀
