# 🚀 Quick Start Commands

## Every Time You Start the System

Copy and paste these commands in PowerShell before running `app.py`:

```powershell
# Set all API credentials
# Credentials are loaded automatically from .env file
# See .env.example for the template

# Start the application
python app.py
```

## Or Set Them Permanently

### Option 1: PowerShell Profile (Recommended)

```powershell
# Open your PowerShell profile
notepad $PROFILE

# If file doesn't exist, create it first:
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

**Add these lines to the profile file:**
```powershell
# CV Intelligence System - load from .env file
# Or set manually:
$env:GOOGLE_API_KEY="your-google-api-key-here"
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_KEY="your-supabase-anon-key-here"
```

**Save and close.** Next time you open PowerShell, credentials will auto-load!

### Option 2: Windows Environment Variables (System-wide)

1. Press **Win + X**, select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **User variables**, click **New** for each:
   - Name: `GOOGLE_API_KEY`  
     Value: (your Google API key)
   - Name: `SUPABASE_URL`  
     Value: (your Supabase project URL)
   - Name: `SUPABASE_KEY`  
     Value: (your Supabase anon key)
5. Click **OK** on all dialogs
6. **Restart PowerShell**

---

## Testing

Run the test suite to verify everything works:
```powershell
python test_production_system.py
```

Expected result: **✓ ALL TESTS PASSED (7/7)**

---

## Running the Application

```powershell
# Start the Flask server
python app.py
```

Then open: **http://localhost:5000**

---

## For Company Deployment

See complete deployment guide in:
- **PRODUCTION_DEPLOYMENT_GUIDE.md** - Full deployment instructions
- **PRODUCTION_READINESS_REPORT.md** - System validation report
- **SUPABASE_SETUP_STEPS.md** - Detailed Supabase setup
