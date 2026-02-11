# 🚀 Supabase Setup Guide - Step by Step

## Quick Setup (5 minutes)

### Step 1: Create Free Supabase Account

1. Go to **https://supabase.com**
2. Click **"Start your project"** or **"Sign Up"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if needed

### Step 2: Create New Project 

1. After logging in, click **"New Project"**
2. Fill in the details:
   - **Name:** `cv-intelligence` (or any name you like)
   - **Database Password:** Choose a strong password (save it!)
   - **Region:** Choose closest to you
   - **Pricing Plan:** Select **Free** (includes 500MB database, perfect for CVs)
3. Click **"Create new project"**
4. Wait 1-2 minutes for project to be created

### Step 3: Get Your Credentials

Once your project is created:

1. Look at the left sidebar and click **"Settings"** (gear icon at bottom)
2. Click **"API"** under Project Settings
3. You'll see:
   - **Project URL** - looks like: `https://xxxxxxxxxxxxx.supabase.co`
   =>
   - **API Keys** section:
     - **anon public** key - this is what you need (starts with `eyJhb...`) //
     =>eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwbnZ3eHNzbHZhc3l1ZndxendyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MjYzNzAsImV4cCI6MjA4NjQwMjM3MH0.hTBeGnN_5YEi-oynzTAehWeRN8xd579K-nqjiLa19M0

**Copy these two values!** You'll need them in the next step.

### Step 4: Set Environment Variables in PowerShell

In your PowerShell terminal, run these commands (replace with your actual values):

```powershell
# Set Supabase URL (replace with your project URL)
$env:SUPABASE_URL = "https://xxxxxxxxxxxxx.supabase.co"

# Set Supabase Key (replace with your anon public key)
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc..."

# Verify they're set
echo "Supabase URL: $env:SUPABASE_URL"
echo "Supabase Key: [HIDDEN]"
```

### Step 5: Create Database Table

Now run this Python command to get the SQL setup script:

```powershell
python supabase_storage.py --action setup
```

This will output SQL code. Copy the entire SQL output.

### Step 6: Execute SQL in Supabase

1. Go back to your Supabase project dashboard
2. Click **"SQL Editor"** in the left sidebar
3. Click **"New query"**
4. Paste the SQL code you copied
5. Click **"Run"** (or press Ctrl+Enter)
6. You should see: **"Success. No rows returned"**

### Step 7: Verify Everything Works

Run this to test the connection:

```powershell
python supabase_storage.py --action stats
```

If you see statistics (even if all zeros), it's working! ✅

---

## Alternative: Quick Commands

Once you have your credentials, just run these 2 commands:

```powershell
# 1. Set credentials (replace with yours)
$env:SUPABASE_URL = "YOUR_URL_HERE"
$env:SUPABASE_KEY = "YOUR_KEY_HERE"

# 2. Generate and execute SQL
python supabase_storage.py --action setup
# Copy output, paste in Supabase SQL Editor, run it
```

---

## Make Environment Variables Permanent (Optional)

To avoid setting them every time you open PowerShell:

### Option 1: Add to Windows Environment Variables
1. Press **Win + X**, select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **User variables**, click **New**
5. Add:
   - Variable name: `SUPABASE_URL`
   - Variable value: Your URL
6. Repeat for `SUPABASE_KEY`
7. Restart PowerShell

### Option 2: Add to PowerShell Profile (Easier)
```powershell
# Edit your profile
notepad $PROFILE

# Add these lines to the file:
$env:GOOGLE_API_KEY = "AIzaSyBW7pa0akQ24wxPwBy17TkaeJ3nh49gcG0"
$env:SUPABASE_URL = "https://xxxxxxxxxxxxx.supabase.co"
$env:SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Save and close. Next time you open PowerShell, they'll auto-load!
```

---

## Troubleshooting

**"Profile not found" error:**
```powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

**Can't connect to Supabase:**
- Check URL starts with `https://` and ends with `.supabase.co`
- Check key starts with `eyJ`
- Make sure project is fully created (takes 1-2 min)
- Check your internet connection

**SQL errors:**
- Make sure you copied the complete SQL (scroll to see all)
- Run in Supabase SQL Editor, not in PowerShell
- Try running sections one at a time if full script fails

---

## What You Get with Supabase

✅ **Database Storage** - Store all CV intelligence  
✅ **Fast Filtering** - SQL queries by verdict, skills, score  
✅ **Real-time Dashboard** - Live statistics  
✅ **Scalability** - Handle thousands of CVs  
✅ **Vector Search** - Semantic search (future feature)  
✅ **API Access** - REST and GraphQL endpoints  
✅ **Free Tier** - 500MB database, 2GB bandwidth/month  

---

## Ready to Continue?

Once you've completed the setup, you can:

1. **Run the app again:**
   ```powershell
   python app.py
   ```

2. **Access the dashboard:**
   http://localhost:5000/dashboard

3. **Start analyzing CVs!**
   - Upload CVs → Extract Intelligence → Search & Filter

---

**Need help?** Follow the steps above or let me know which step you're stuck on!
