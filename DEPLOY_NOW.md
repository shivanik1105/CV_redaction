# Deploy to Render - Quick Guide

## ✅ Your App is Ready!

All fixes applied:
- ✅ Encoding fix
- ✅ Visual masking (black boxes)
- ✅ PyMuPDF installed
- ✅ Database cleaned
- ✅ Upload feature working

---

## 🚀 Deploy in 3 Steps

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Service

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml`

### Step 3: Add Environment Variables

In Render dashboard, add:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
```

Click **"Create Web Service"** → Done! ✅

---

## ⚠️ Important: File Storage

**Render uses ephemeral storage** - uploaded files are lost on restart!

**Quick Fix**: After deployment, implement Supabase storage:
- Create bucket: `cv-uploads` in Supabase
- Files will persist across restarts

See `RENDER_DEPLOYMENT_GUIDE.md` for details.

---

## 🎯 After Deployment

Your app will be at: `https://your-app-name.onrender.com`

Test:
1. ✅ Upload CV (with your API key)
2. ✅ Search CVs
3. ✅ Download masked PDF (black boxes!)
4. ✅ Download original CV

---

## 📋 Quick Commands

```bash
# Deploy
git add .
git commit -m "Deploy"
git push origin main

# Check logs (after deployment)
# Go to Render dashboard → Logs
```

---

**Ready to deploy!** 🚀
