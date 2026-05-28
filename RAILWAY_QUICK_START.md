# Railway Deployment - Quick Checklist

## 🚀 Deploy in 7 Steps (15 Minutes)

### ✅ Step 1: Push to GitHub (2 min)

```powershell
cd C:\Users\shiva\Downloads\samplecvs
git add .
git commit -m "Deploy to Railway"
git push origin main
```

If you don't have a GitHub repo yet:
1. Go to https://github.com/new
2. Create repo named "cv-redactor"
3. Run:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/cv-redactor.git
git push -u origin main
```

---

### ✅ Step 2: Create Railway Account (1 min)

1. Go to https://railway.app
2. Click "Login with GitHub"
3. Authorize Railway

---

### ✅ Step 3: Deploy from GitHub (1 min)

1. Click **"New Project"**
2. Click **"Deploy from GitHub repo"**
3. Select **"cv-redactor"**
4. Wait for build to start

---

### ✅ Step 4: Add Environment Variables (3 min)

Click "Variables" tab, add these:

| Variable | Value |
|----------|-------|
| `SUPABASE_URL` | Your Supabase URL |
| `SUPABASE_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service key |
| `FLASK_SECRET_KEY` | Any random string |
| `PORT` | `5000` |
| `PYTHON_VERSION` | `3.11.0` |

---

### ✅ Step 5: Generate Domain (1 min)

1. Click **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. Copy the URL

---

### ✅ Step 6: Wait for Build (10-15 min)

1. Click **"Deployments"** tab
2. Watch build progress
3. Wait for ✅ "Success"

---

### ✅ Step 7: Test Your App (2 min)

1. Open the URL from Step 5
2. Test upload feature
3. Test search feature
4. Done! 🎉

---

## 🎯 Your App is Live!

**URL**: `https://your-app.up.railway.app`

**Cost**: $0 for first 5-10 days (using $5 credit)

**After credit**: ~$10-15/month (or migrate to Oracle Cloud for free)

---

## 📊 Monitor Usage

**Check credit**: Profile → Usage

**View logs**: Deployments → View Logs

**Redeploy**: Settings → Redeploy

---

## 🔄 Update Your App

```powershell
# Make changes to code
git add .
git commit -m "Update"
git push

# Railway auto-deploys!
```

---

## 🆘 Troubleshooting

| Issue | Fix |
|-------|-----|
| Build failed | Check logs for error message |
| App crashes | Check environment variables |
| Can't access | Wait 1-2 minutes, check deployment status |
| 502 error | App is starting, wait 30 seconds |

**Full guide**: See `RAILWAY_DEPLOY_STEPS.md`

---

## ✅ Checklist

- [ ] Code pushed to GitHub
- [ ] Railway account created
- [ ] Project deployed
- [ ] Environment variables added
- [ ] Domain generated
- [ ] Build successful
- [ ] App tested

---

**Need detailed help?** See `RAILWAY_DEPLOY_STEPS.md`

**Want free forever?** See `ORACLE_CLOUD_FREE_DEPLOYMENT.md`
