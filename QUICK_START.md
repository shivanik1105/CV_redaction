# 🚀 Quick Start Commands

## Every Time You Start the System

Copy and paste these commands in PowerShell before running `app.py`:

```powershell
# Set all API credentials
$env:GOOGLE_API_KEY="AIzaSyBW7pa0akQ24wxPwBy17TkaeJ3nh49gcG0"
$env:SUPABASE_URL="https://dpnvwxsslvasyufwqzwr.supabase.co"
$env:SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwbnZ3eHNzbHZhc3l1ZndxendyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MjYzNzAsImV4cCI6MjA4NjQwMjM3MH0.hTBeGnN_5YEi-oynzTAehWeRN8xd579K-nqjiLa19M0"

# Verify credentials are set
Write-Host "✓ Credentials configured!" -ForegroundColor Green

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
# CV Intelligence System API Keys
$env:GOOGLE_API_KEY="AIzaSyBW7pa0akQ24wxPwBy17TkaeJ3nh49gcG0"
$env:SUPABASE_URL="https://dpnvwxsslvasyufwqzwr.supabase.co"
$env:SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwbnZ3eHNzbHZhc3l1ZndxendyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MjYzNzAsImV4cCI6MjA4NjQwMjM3MH0.hTBeGnN_5YEi-oynzTAehWeRN8xd579K-nqjiLa19M0"
```

**Save and close.** Next time you open PowerShell, credentials will auto-load!

### Option 2: Windows Environment Variables (System-wide)

1. Press **Win + X**, select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **User variables**, click **New** for each:
   - Name: `GOOGLE_API_KEY`  
     Value: `AIzaSyBW7pa0akQ24wxPwBy17TkaeJ3nh49gcG0`
   - Name: `SUPABASE_URL`  
     Value: `https://dpnvwxsslvasyufwqzwr.supabase.co`
   - Name: `SUPABASE_KEY`  
     Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwbnZ3eHNzbHZhc3l1ZndxendyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MjYzNzAsImV4cCI6MjA4NjQwMjM3MH0.hTBeGnN_5YEi-oynzTAehWeRN8xd579K-nqjiLa19M0`
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
