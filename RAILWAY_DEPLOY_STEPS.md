# Railway Deployment - Step by Step

## ✅ What You'll Get

- **$5 free credit** (lasts 5-10 days)
- **8GB RAM** (enough for all dependencies)
- **Auto-deploy** on git push
- **Easy monitoring** and logs

After free credit: ~$10-15/month

---

## 📋 Prerequisites

Before starting, make sure you have:

1. ✅ GitHub account
2. ✅ Your code pushed to GitHub (or ready to push)
3. ✅ Supabase credentials ready:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`

---

## 🚀 Step-by-Step Deployment

### Step 1: Push Code to GitHub (If Not Already)

Open PowerShell in your project folder:

```powershell
cd C:\Users\shiva\Downloads\samplecvs

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Railway deployment"

# Create a new repo on GitHub:
# Go to https://github.com/new
# Name it: cv-redactor (or any name)
# Don't initialize with README

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/cv-redactor.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your GitHub username.

---

### Step 2: Create Railway Account

1. **Go to**: https://railway.app

2. **Click**: "Login" (top right)

3. **Sign up with GitHub**:
   - Click "Login with GitHub"
   - Authorize Railway to access your GitHub

4. **Verify email** (if asked)

5. **You'll see**: Railway dashboard

---

### Step 3: Create New Project

1. **In Railway Dashboard**:
   - Click **"New Project"** (big button in center)

2. **Select**:
   - Click **"Deploy from GitHub repo"**

3. **Choose repository**:
   - Find and click **"cv-redactor"** (or your repo name)
   - If you don't see it, click "Configure GitHub App" and grant access

4. **Railway will**:
   - Automatically detect it's a Python app
   - Start building (this will take 10-15 minutes)

---

### Step 4: Add Environment Variables

While the build is running:

1. **Click on your service** (in Railway dashboard)

2. **Go to "Variables" tab** (top menu)

3. **Click "New Variable"**

4. **Add these variables one by one**:

```env
SUPABASE_URL
```
Value: `your_supabase_url` (from your .env file)

Click "Add"

```env
SUPABASE_KEY
```
Value: `your_supabase_anon_key`

Click "Add"

```env
SUPABASE_SERVICE_KEY
```
Value: `your_supabase_service_key`

Click "Add"

```env
FLASK_SECRET_KEY
```
Value: `your_random_secret_key` (any random string)

Click "Add"

```env
PORT
```
Value: `5000`

Click "Add"

```env
PYTHON_VERSION
```
Value: `3.11.0`

Click "Add"

5. **Railway will automatically redeploy** with new variables

---

### Step 5: Generate Public URL

1. **Click "Settings" tab** (top menu)

2. **Scroll to "Networking" section**

3. **Click "Generate Domain"**

4. **Copy the URL**:
   - Will look like: `https://cv-redactor-production-xxxx.up.railway.app`

5. **Save this URL** - this is your app's public address

---

### Step 6: Wait for Deployment

1. **Go to "Deployments" tab**

2. **Watch the build progress**:
   - Installing dependencies (10-15 minutes)
   - Building app
   - Starting server

3. **When you see**:
   - ✅ "Success" with green checkmark
   - Status: "Active"

4. **Your app is live!**

---

### Step 7: Test Your App

1. **Open the URL** from Step 5 in your browser

2. **Test features**:
   - ✅ Upload CV (with your API key)
   - ✅ Search CVs
   - ✅ Download masked PDF
   - ✅ Download original CV

3. **If something doesn't work**:
   - Go to "Deployments" tab
   - Click "View Logs"
   - Look for error messages

---

## 🎯 Your App is Now Live!

**URL**: `https://your-app.up.railway.app`

**Share this URL** with anyone who needs to use the app.

---

## 📊 Monitor Usage

### Check Your Free Credit

1. **In Railway Dashboard**:
   - Click your profile (top right)
   - Click "Usage"

2. **You'll see**:
   - How much of $5 credit is used
   - Estimated days remaining

3. **Typical usage**:
   - Idle app: ~$0.50/day
   - Active app: ~$1-2/day
   - $5 credit = 5-10 days

---

## 🔄 Auto-Deploy on Git Push

Railway automatically deploys when you push to GitHub:

```powershell
# Make changes to your code
# Example: edit app.py

# Commit and push
git add .
git commit -m "Update feature"
git push

# Railway will automatically:
# 1. Detect the push
# 2. Build the app
# 3. Deploy the new version
```

**No need to do anything in Railway dashboard!**

---

## 📝 View Logs

### Real-time Logs

1. **In Railway Dashboard**:
   - Click your service
   - Click "Deployments" tab
   - Click latest deployment
   - Click "View Logs"

2. **You'll see**:
   - Build logs
   - Application logs
   - Error messages

### Filter Logs

- **Build logs**: Shows dependency installation
- **Deploy logs**: Shows app startup
- **Runtime logs**: Shows app activity

---

## 🛠️ Troubleshooting

### Issue 1: Build Failed

**Symptoms**: Red "Failed" status

**Fix**:
1. Click "View Logs"
2. Look for error message
3. Common issues:
   - Missing dependency: Add to `requirements.txt`
   - Python version: Check `PYTHON_VERSION` variable
   - Syntax error: Fix in code and push again

### Issue 2: App Crashes on Start

**Symptoms**: Builds successfully but crashes immediately

**Fix**:
1. Check "View Logs" for error
2. Common issues:
   - Missing environment variable: Add in "Variables" tab
   - Wrong Supabase credentials: Update variables
   - Port issue: Ensure `PORT` variable is set

### Issue 3: Can't Access App

**Symptoms**: URL doesn't load

**Fix**:
1. Check deployment status (should be "Active")
2. Ensure domain is generated (Settings → Networking)
3. Wait 1-2 minutes after deployment
4. Try incognito/private browsing

### Issue 4: 502 Bad Gateway

**Symptoms**: "502 Bad Gateway" error

**Fix**:
1. App is starting up (wait 30 seconds)
2. Or app crashed (check logs)
3. Redeploy: Settings → "Redeploy"

---

## 💰 What Happens After Free Credit?

### When $5 Runs Out

1. **Railway will email you**
2. **App will stop** (unless you add payment)
3. **Your data is safe** (not deleted)

### Options

**Option A: Add Payment Method**
- Go to Account → Billing
- Add credit card
- Railway will charge ~$10-15/month
- App resumes automatically

**Option B: Migrate to Oracle Cloud**
- Free forever
- Follow `ORACLE_CLOUD_FREE_DEPLOYMENT.md`
- Export your data first

**Option C: Pause App**
- Settings → "Pause Service"
- No charges while paused
- Resume anytime

---

## 🎛️ Advanced Settings

### Increase Workers (If Needed)

1. **Edit `Procfile`**:
```
web: gunicorn --workers 4 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT app:app
```

2. **Push to GitHub**:
```powershell
git add Procfile
git commit -m "Increase workers"
git push
```

### Add Custom Domain

1. **Settings** → **Networking**
2. **Custom Domain** → Add your domain
3. **Update DNS** (Railway will show instructions)

### Enable Sleep Mode (Railway Pro)

- App sleeps after 15 minutes of inactivity
- Wakes up on first request
- Saves money

---

## 📋 Quick Commands Reference

```powershell
# Deploy changes
git add .
git commit -m "Your message"
git push

# View local logs
# (Use Railway dashboard for deployed logs)

# Check git status
git status

# View commit history
git log --oneline
```

---

## ✅ Deployment Checklist

- [x] Code pushed to GitHub
- [x] Railway account created
- [x] Project created from GitHub repo
- [x] Environment variables added
- [x] Public domain generated
- [x] Deployment successful
- [x] App tested and working
- [x] Logs checked for errors

---

## 🆘 Need Help?

### Common Questions

**Q: How long does deployment take?**
A: 10-15 minutes for first deployment, 5-10 minutes for updates

**Q: Can I use a custom domain?**
A: Yes, in Settings → Networking → Custom Domain

**Q: How do I see errors?**
A: Deployments tab → View Logs

**Q: Can I rollback to previous version?**
A: Yes, Deployments tab → Click old deployment → "Redeploy"

**Q: How do I delete the app?**
A: Settings → Danger Zone → Delete Service

---

## 🎉 Success!

Your CV Redactor app is now live on Railway!

**Next steps**:
1. ✅ Share the URL with users
2. ✅ Monitor usage in Railway dashboard
3. ✅ Check logs regularly
4. ✅ Plan for after free credit runs out

---

## 📚 More Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Alternative (Free Forever)**: `ORACLE_CLOUD_FREE_DEPLOYMENT.md`

---

**Your app URL**: `https://your-app.up.railway.app`

**Enjoy your deployment!** 🚀
