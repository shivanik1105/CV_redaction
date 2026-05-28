# Deploy Your CV Redactor App

## ❌ Can I Deploy on Vercel or Supabase?

**NO** - Neither platform supports Flask apps with ML dependencies like sentence-transformers.

See `DEPLOYMENT_OPTIONS_COMPARISON.md` for detailed explanation.

---

## ✅ Choose Your Deployment Platform

### Option 1: Oracle Cloud Free Tier ⭐ **BEST VALUE**
- **Cost**: $0 forever
- **RAM**: 1-24GB
- **Setup**: 40 minutes
- **Guide**: `ORACLE_CLOUD_FREE_DEPLOYMENT.md`

### Option 2: Railway 🚀 **EASIEST**
- **Cost**: $0 first month, then ~$10-15/month
- **RAM**: 8GB
- **Setup**: 10 minutes
- **Guide**: `RAILWAY_DEPLOYMENT.md`

### Option 3: Render Starter 💰 **FAMILIAR**
- **Cost**: $7/month
- **RAM**: 1GB
- **Setup**: 5 minutes
- **Guide**: See below

---

## 🚀 Quick Deploy to Railway (10 Minutes)

### Step 1: Create Account
1. Go to https://railway.app
2. Sign up with GitHub

### Step 2: Deploy
1. Click "New Project" → "Deploy from GitHub"
2. Select your repository
3. Railway auto-detects Python app

### Step 3: Add Environment Variables
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
FLASK_SECRET_KEY=your_secret_key
```

### Step 4: Generate Domain
1. Go to Settings → Networking
2. Click "Generate Domain"
3. Done! ✅

**Your app**: `https://your-app.railway.app`

---

## 💰 Quick Deploy to Render Starter (5 Minutes)

### Step 1: Update render.yaml

Change plan to `starter`:

```yaml
services:
  - type: web
    name: cv-redactor
    env: python
    plan: starter  # Changed from 'free'
```

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Deploy to Render Starter"
git push origin main
```

### Step 3: Create Render Service

1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Select **"Starter"** plan ($7/month)
5. Add environment variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
FLASK_SECRET_KEY=your_secret_key
```

6. Click "Create Web Service"

**Your app**: `https://your-app.onrender.com`

---

## 🎯 Deploy to Oracle Cloud Free (40 Minutes)

**Best for**: $0 cost forever, keep ALL features

**Full guide**: See `ORACLE_CLOUD_FREE_DEPLOYMENT.md`

**Quick steps**:
1. Create Oracle Cloud account
2. Create VM instance (Ubuntu 22.04)
3. SSH into VM
4. Upload code
5. Install dependencies
6. Run app

---

## 📊 Platform Comparison

| Platform | Cost | RAM | Setup Time |
|----------|------|-----|------------|
| **Oracle Cloud** | $0 forever | 1-24GB | 40 min |
| **Railway** | $0 → $10-15/mo | 8GB | 10 min |
| **Render Starter** | $7/mo | 1GB | 5 min |

---

## ⚠️ Why NOT Render Free Tier?

Render Free tier has only **512MB RAM** - NOT enough for:
- sentence-transformers (~400MB)
- spaCy models (~100MB)
- Flask + other dependencies (~100MB)

**Total needed**: ~600MB  
**Render Free**: 512MB ❌

**Solution**: Use Starter plan ($7/month) or Oracle Cloud (free forever)

---

## 🎯 My Recommendation

### For You: **Oracle Cloud Free Tier**

**Why:**
- ✅ $0 cost forever
- ✅ Keep ALL requirements (sentence-transformers)
- ✅ Up to 24GB RAM on ARM instances
- ✅ 200GB storage
- ⚠️ 40 minutes setup (worth it!)

**Follow**: `ORACLE_CLOUD_FREE_DEPLOYMENT.md`

---

## 📋 After Deployment Checklist

1. ✅ Test upload feature (with user's API key)
2. ✅ Test search feature
3. ✅ Test download masked PDF (black boxes)
4. ✅ Test download original CV
5. ✅ Check logs for errors
6. ✅ Monitor resource usage

---

## 🆘 Need Help?

1. **Choose a platform** from above
2. **Follow the guide**:
   - Oracle Cloud: `ORACLE_CLOUD_FREE_DEPLOYMENT.md`
   - Railway: `RAILWAY_DEPLOYMENT.md`
   - Render: This file
3. **Get stuck?** Share error message

---

## 📚 More Resources

- **Platform Comparison**: `DEPLOYMENT_OPTIONS_COMPARISON.md`
- **Oracle Cloud Guide**: `ORACLE_CLOUD_FREE_DEPLOYMENT.md`
- **Railway Guide**: `RAILWAY_DEPLOYMENT.md`
- **Render Troubleshooting**: `RENDER_TROUBLESHOOTING.md`

---

**Ready to deploy?** Start with **Railway** (easiest) or **Oracle Cloud** (free forever)! 🚀
