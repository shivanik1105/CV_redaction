# Deploy to Railway (Easiest Option)

## Why Railway?

✅ **$5 free credit/month** - Usually enough for small apps  
✅ **8GB RAM** - Can handle ALL dependencies  
✅ **10-minute setup** - Easiest deployment  
✅ **Keep ALL requirements** - sentence-transformers, spaCy, everything  
✅ **Auto-scaling** - Handles traffic spikes  
✅ **GitHub integration** - Auto-deploy on push  

---

## Cost Breakdown

- **First month**: $0 (using $5 free credit)
- **After free credit**: ~$10-15/month depending on usage
- **Pay only for what you use** - Scales down when idle

---

## Step-by-Step Deployment

### Step 1: Create Railway Account

1. **Go to**: https://railway.app
2. **Click**: "Start a New Project"
3. **Sign up with GitHub** (recommended)
4. **Verify email**

---

### Step 2: Prepare Your Repository

**Option A: If you have a GitHub repo**
- Skip to Step 3

**Option B: If you don't have a GitHub repo**

```bash
# On your Windows machine
cd C:\Users\shiva\Downloads\samplecvs

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for Railway deployment"

# Create GitHub repo (go to github.com/new)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

### Step 3: Deploy to Railway

1. **In Railway Dashboard**:
   - Click "New Project"
   - Click "Deploy from GitHub repo"
   - Select your repository
   - Click "Deploy Now"

2. **Railway will automatically**:
   - Detect it's a Python app
   - Install requirements.txt
   - Start the app

---

### Step 4: Add Environment Variables

1. **In Railway Dashboard**:
   - Click your deployed service
   - Go to "Variables" tab
   - Click "New Variable"

2. **Add these variables**:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
FLASK_SECRET_KEY=your_secret_key
PORT=5000
PYTHON_VERSION=3.11.0
```

3. **Click "Add" for each variable**

---

### Step 5: Configure Start Command

1. **In Railway Dashboard**:
   - Click "Settings" tab
   - Scroll to "Deploy"
   - Find "Start Command"

2. **Set start command**:
```bash
gunicorn --workers 2 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT app:app
```

3. **Click "Save"**

---

### Step 6: Generate Public URL

1. **In Railway Dashboard**:
   - Click "Settings" tab
   - Scroll to "Networking"
   - Click "Generate Domain"

2. **Copy the URL** (e.g., `your-app.railway.app`)

3. **Test in browser**:
   - Go to `https://your-app.railway.app`
   - Should see your CV Redactor app

---

## Optional: Create railway.json

For better control, create `railway.json` in your project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "gunicorn --workers 2 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## Optional: Create Procfile

Create `Procfile` in your project root:

```
web: gunicorn --workers 2 --threads 2 --timeout 120 --bind 0.0.0.0:$PORT app:app
```

---

## Monitoring Usage

1. **In Railway Dashboard**:
   - Click "Usage" tab
   - See how much of your $5 credit is used

2. **Typical usage**:
   - Idle app: ~$0.50/day
   - Active app: ~$1-2/day
   - $5 credit = ~5-10 days of usage

---

## Auto-Deploy on Git Push

Railway automatically deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push

# Railway will automatically:
# 1. Detect the push
# 2. Build the app
# 3. Deploy the new version
```

---

## View Logs

1. **In Railway Dashboard**:
   - Click your service
   - Click "Deployments" tab
   - Click latest deployment
   - Click "View Logs"

2. **See real-time logs**:
   - Build logs
   - Application logs
   - Error logs

---

## Troubleshooting

### Issue: Build Failed

**Check logs**:
1. Go to "Deployments" tab
2. Click failed deployment
3. Check build logs

**Common fixes**:
- Ensure `requirements.txt` is in root directory
- Ensure Python version is compatible
- Check for syntax errors in code

### Issue: App Crashes on Start

**Check logs**:
1. Go to "Deployments" tab
2. Click "View Logs"
3. Look for error messages

**Common fixes**:
- Ensure all environment variables are set
- Check `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Ensure `PORT` variable is set

### Issue: Can't Access App

**Check**:
1. Ensure domain is generated (Settings → Networking)
2. Ensure app is running (should show "Active")
3. Check logs for errors

### Issue: Out of Credit

**Options**:
1. **Add payment method** - Railway will charge ~$10-15/month
2. **Switch to Oracle Cloud** - Free forever
3. **Optimize usage** - Reduce workers, add sleep mode

---

## Cost Optimization

### Reduce Costs:

1. **Reduce workers**:
```bash
# In start command
gunicorn --workers 1 --threads 1 --bind 0.0.0.0:$PORT app:app
```

2. **Add sleep mode** (Railway Pro feature):
   - App sleeps after 15 minutes of inactivity
   - Wakes up on first request

3. **Monitor usage**:
   - Check "Usage" tab daily
   - Set up billing alerts

---

## Comparison: Railway vs Others

| Feature | Railway | Oracle Cloud | Render Starter |
|---------|---------|--------------|----------------|
| Setup Time | 10 min | 40 min | 5 min |
| Free Credit | $5/month | Forever | None |
| RAM | 8GB | 1-24GB | 1GB |
| Cost After Free | $10-15/mo | $0 | $7/mo |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Auto-Deploy | ✅ Yes | ❌ No | ✅ Yes |

---

## When to Use Railway

✅ **Use Railway if**:
- You want fastest deployment (10 minutes)
- You're okay with ~$10/month after free credit
- You want auto-deploy on git push
- You want easy monitoring and logs

❌ **Don't use Railway if**:
- You want $0 cost forever → Use Oracle Cloud
- You're on tight budget → Use Oracle Cloud
- You want maximum control → Use Oracle Cloud

---

## Next Steps

1. **Create Railway account** (2 minutes)
2. **Connect GitHub repo** (3 minutes)
3. **Add environment variables** (3 minutes)
4. **Deploy and test** (2 minutes)

**Total time**: ~10 minutes

---

## Need Help?

If you get stuck:
1. Share the error message from Railway logs
2. Share which step you're on
3. I'll help you troubleshoot

---

**Ready to deploy?** Go to https://railway.app and start!

---

## After Deployment

Once deployed, you can:

1. **Share the URL** with users
2. **Monitor usage** in Railway dashboard
3. **View logs** for debugging
4. **Auto-deploy** by pushing to GitHub

**Your app will be live at**: `https://your-app.railway.app`

---

## Upgrading from Free Credit

When your $5 credit runs out:

1. **Railway will email you**
2. **Add payment method** in dashboard
3. **Continue using** - Will charge ~$10-15/month
4. **Or migrate to Oracle Cloud** for free forever

---

**Recommendation**: Start with Railway for quick deployment, then migrate to Oracle Cloud if you want $0 cost forever.
