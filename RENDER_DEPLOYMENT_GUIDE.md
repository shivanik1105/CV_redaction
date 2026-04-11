# Complete Render Deployment Guide - CV Intelligence System

## 🚀 Deploy Full System to Render (All Features)

This guide will help you deploy the complete CV Intelligence System with:
- ✅ Authentication & User Management
- ✅ CV Redaction
- ✅ Intelligence Extraction (LLM)
- ✅ Job Description Matching
- ✅ Candidate Search & Ranking
- ✅ Supabase Integration
- ✅ Rate Limiting & Security

---

## 📋 Prerequisites

### 1. Accounts Needed:
- [ ] GitHub account (to host code)
- [ ] Render account (https://render.com - free to start)
- [ ] Groq API key (https://console.groq.com - free tier)
- [ ] Supabase account (https://supabase.com - free tier)

### 2. Local Setup:
- [ ] Git installed
- [ ] Code ready in local directory

---

## 🔧 Step 1: Prepare Your Code

### 1.1 Initialize Git Repository (if not already done)
```powershell
# In your project directory
git init
git add .
git commit -m "Initial commit - CV Intelligence System"
```

### 1.2 Create .gitignore
```powershell
# Create .gitignore file
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Environment variables
.env
.env.local

# User data
users.json
uploads/
redacted_output/
llm_analysis/
intelligence_output/
test_results/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/

# Logs
*.log
"@ | Out-File -FilePath .gitignore -Encoding utf8
```

### 1.3 Create GitHub Repository
```powershell
# Go to GitHub.com
# Click "New Repository"
# Name: cv-intelligence-system
# Public or Private (your choice)
# Don't initialize with README (you already have code)

# Then push your code:
git remote add origin https://github.com/YOUR_USERNAME/cv-intelligence-system.git
git branch -M main
git push -u origin main
```

---

## 🔑 Step 2: Get API Keys

### 2.1 Groq API Key (Free - Recommended)
1. Go to https://console.groq.com
2. Sign up / Log in
3. Go to "API Keys"
4. Click "Create API Key"
5. Copy the key (starts with `gsk_...`)
6. Save it securely

**Free Tier**: 6,000 requests/day, 30 requests/minute

### 2.2 Supabase Setup
1. Go to https://supabase.com
2. Create new project
3. Wait for database to initialize (~2 minutes)
4. Go to Project Settings → API
5. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public key** (starts with `eyJ...`)

### 2.3 Run Supabase SQL Setup
1. In Supabase Dashboard, go to SQL Editor
2. Click "New Query"
3. Copy content from `supabase_pgvector_setup.sql`
4. Paste and click "Run"
5. Should see "Success" message

---

## 🌐 Step 3: Deploy to Render

### 3.1 Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (recommended)
3. Authorize Render to access your repositories

### 3.2 Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select `cv-intelligence-system` repository
4. Configure:
   - **Name**: `cv-intelligence-system` (or your choice)
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command**:
     ```bash
     gunicorn app_secure:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
     ```
   - **Plan**: Starter ($7/month) or Free (with limitations)

### 3.3 Add Environment Variables
In Render Dashboard, go to "Environment" tab and add:

#### Required Variables:
```
FLASK_ENV=production
ADMIN_PASSWORD=YourSecurePassword123!
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_your_actual_groq_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Optional Variables (for advanced features):
```
OPENAI_API_KEY=sk-your-openai-key (if using OpenAI)
ANTHROPIC_API_KEY=sk-ant-your-key (if using Claude)
EMBEDDING_PROVIDER=local
UPLOAD_WORKER_COUNT=2
LLM_MAX_CONCURRENT_REQUESTS=2
```

### 3.4 Deploy
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Watch the logs for any errors
4. Once deployed, you'll get a URL like: `https://cv-intelligence-system.onrender.com`

---

## ✅ Step 4: Test Your Deployment

### 4.1 Access the Application
1. Go to your Render URL: `https://your-app.onrender.com`
2. You should see the login page
3. Login with:
   - **Username**: `admin`
   - **Password**: (the ADMIN_PASSWORD you set)

### 4.2 Change Admin Password
1. After login, go to "Change Password"
2. Enter old password
3. Set new secure password
4. Save

### 4.3 Test Features
- [ ] Upload a CV
- [ ] Redact PII
- [ ] Extract intelligence (if LLM configured)
- [ ] Search candidates
- [ ] View dashboard

---

## 👥 Step 5: Add Users

### 5.1 Create User Accounts
1. Login as admin
2. Go to `/admin/users`
3. Click "Create User"
4. Fill in:
   - Username
   - Email
   - Password (min 8 characters)
   - Role (user or admin)
5. Click "Create"

### 5.2 Share Access
Send your team:
```
CV Intelligence System Access

URL: https://your-app.onrender.com
Username: [their username]
Password: [their password]

Please change your password after first login.
```

---

## 🔒 Security Checklist

- [ ] Changed default admin password
- [ ] Using HTTPS (Render provides this automatically)
- [ ] Environment variables are secrets (not in code)
- [ ] Rate limiting enabled (automatic)
- [ ] Authentication required for all pages
- [ ] Supabase RLS policies enabled (if using Supabase)
- [ ] Regular backups configured

---

## 💰 Cost Breakdown

### Free Tier (Limited):
```
Render Free: $0 (sleeps after 15 min inactivity)
Supabase Free: $0 (500MB database, 1GB file storage)
Groq Free: $0 (6000 requests/day)
---
Total: $0/month
```

### Recommended Production:
```
Render Starter: $7/month (always on, 512MB RAM)
Supabase Free: $0 (sufficient for small teams)
Groq Free: $0 (sufficient for most use cases)
---
Total: $7/month
```

### High Volume:
```
Render Standard: $25/month (1GB RAM, better performance)
Supabase Pro: $25/month (8GB database, 100GB storage)
Groq Free: $0 (or upgrade if needed)
---
Total: $50/month
```

---

## 🔧 Troubleshooting

### Issue: Build Failed
**Check**:
- requirements.txt is correct
- All dependencies are compatible
- Python version is 3.11+

**Solution**:
```bash
# In Render logs, look for specific error
# Common fix: Update requirements.txt versions
```

### Issue: App Crashes on Start
**Check**:
- Environment variables are set correctly
- GROQ_API_KEY is valid
- SUPABASE_URL and SUPABASE_KEY are correct

**Solution**:
```bash
# Check Render logs for error messages
# Verify all environment variables in Render Dashboard
```

### Issue: "Supabase not connected"
**Check**:
- SUPABASE_URL is correct
- SUPABASE_KEY is correct
- Supabase project is active
- SQL setup was run successfully

**Solution**:
```bash
# Test Supabase connection in Render logs
# Re-run SQL setup if needed
# Check Supabase project status
```

### Issue: Slow Performance
**Causes**:
- Free tier sleeps after 15 min inactivity
- Cold start takes 30-60 seconds
- Limited resources on free/starter plan

**Solutions**:
- Upgrade to Starter plan ($7/month) - always on
- Upgrade to Standard plan ($25/month) - better performance
- Use cron job to keep app awake (free tier only)

### Issue: LLM Extraction Fails
**Check**:
- GROQ_API_KEY is valid
- API rate limits not exceeded
- LLM_PROVIDER is set correctly

**Solution**:
```bash
# Check Render logs for API errors
# Verify API key in Groq dashboard
# Check API usage/limits
```

---

## 📊 Monitoring

### Check Application Health:
```
https://your-app.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": {
    "authentication": true,
    "rate_limiting": true,
    "supabase": true,
    "llm": true
  }
}
```

### Monitor in Render Dashboard:
- CPU usage
- Memory usage
- Request count
- Error rate
- Response time

---

## 🔄 Updates & Maintenance

### Deploy Updates:
```powershell
# Make changes to your code
git add .
git commit -m "Update: description of changes"
git push origin main

# Render will auto-deploy (if auto-deploy is enabled)
```

### Manual Deploy:
1. Go to Render Dashboard
2. Click "Manual Deploy"
3. Select branch
4. Click "Deploy"

### Rollback:
1. Go to Render Dashboard
2. Click "Rollback"
3. Select previous deployment
4. Confirm

---

## 📞 Support & Resources

### Render Documentation:
- https://render.com/docs

### Supabase Documentation:
- https://supabase.com/docs

### Groq Documentation:
- https://console.groq.com/docs

### Your Application:
- Health Check: `https://your-app.onrender.com/health`
- Login: `https://your-app.onrender.com/login`
- Dashboard: `https://your-app.onrender.com/dashboard`

---

## ✅ Deployment Checklist

### Pre-Deployment:
- [ ] Code pushed to GitHub
- [ ] .gitignore configured
- [ ] requirements.txt updated
- [ ] Groq API key obtained
- [ ] Supabase project created
- [ ] Supabase SQL setup completed

### Deployment:
- [ ] Render account created
- [ ] Web service created
- [ ] Environment variables configured
- [ ] Build successful
- [ ] Application running

### Post-Deployment:
- [ ] Login page accessible
- [ ] Admin password changed
- [ ] Test CV upload
- [ ] Test redaction
- [ ] Test intelligence extraction
- [ ] Test search
- [ ] Users created
- [ ] Team notified

---

## 🎉 Success!

Your CV Intelligence System is now deployed and accessible to your team!

**Share this URL with your team**:
```
https://your-app.onrender.com
```

**Features Available**:
✅ Secure authentication
✅ CV redaction (PII removal)
✅ Intelligence extraction (skills, experience)
✅ Job description matching
✅ Candidate search & ranking
✅ Multi-user support
✅ Admin panel
✅ Rate limiting
✅ Cloud storage (Supabase)

**Next Steps**:
1. Create user accounts for your team
2. Upload and process CVs
3. Search and rank candidates
4. Monitor usage in dashboard

Enjoy your deployment! 🚀
