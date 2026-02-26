# 🚀 Quick Supabase Setup (5 Minutes)

## Step 1: Create Supabase Account

1. Go to: **https://app.supabase.com/sign-in**
2. Click "Sign up" (or sign in with GitHub for faster setup)
3. Verify your email

## Step 2: Create New Project

1. Click **"New Project"** button
2. Fill in:
   - **Name:** CV Intelligence System
   - **Database Password:** Generate a strong password (save it!)
   - **Region:** Choose closest to your location (e.g., US East, Europe West)
3. Click **"Create new project"**
4. Wait 2-3 minutes for project initialization

## Step 3: Get Your Credentials

1. Once project is ready, go to **"Project Settings"** (gear icon on left sidebar)
2. Click **"API"** in the settings menu
3. You'll see two important values:

   **Project URL:**
   ```
   https://xxxxxxxxxxxxx.supabase.co
   ```
   Copy this entire URL

   **anon/public key:**
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZi...
   ```
   Copy this entire key (it's very long, ~250 characters)

## Step 4: Run SQL Schema

1. In Supabase dashboard, click **"SQL Editor"** (on left sidebar)
2. Click **"New query"**
3. Copy and paste this SQL:

```sql
-- Create cv_intelligence table (Main audit trail)
CREATE TABLE IF NOT EXISTS cv_intelligence (
    anonymized_id TEXT PRIMARY KEY,
    original_cv_hash TEXT NOT NULL,
    llm_prompt_used TEXT NOT NULL,
    llm_raw_response TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('SHORTLIST', 'BACKUP', 'REVIEW')),
    confidence_score FLOAT NOT NULL,
    evidence_based_reasoning TEXT NOT NULL,
    overall_summary TEXT,
    key_skills TEXT[],
    years_of_experience FLOAT,
    career_level TEXT,
    domain_expertise TEXT[],
    recruiter_override TEXT,
    reviewer_id TEXT,
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create cv_filename_mapping table (Privacy-preserving mapping)
CREATE TABLE IF NOT EXISTS cv_filename_mapping (
    anonymized_id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    anonymized_filename TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anonymized_id) REFERENCES cv_intelligence(anonymized_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_verdict ON cv_intelligence(verdict);
CREATE INDEX IF NOT EXISTS idx_confidence ON cv_intelligence(confidence_score);
CREATE INDEX IF NOT EXISTS idx_created_at ON cv_intelligence(created_at);
CREATE INDEX IF NOT EXISTS idx_reviewer_override ON cv_intelligence(recruiter_override);
CREATE INDEX IF NOT EXISTS idx_filename ON cv_filename_mapping(original_filename);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE cv_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_filename_mapping ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (you can restrict this later)
CREATE POLICY "Enable all access for authenticated users" ON cv_intelligence
    FOR ALL USING (true);

CREATE POLICY "Enable all access for authenticated users" ON cv_filename_mapping
    FOR ALL USING (true);
```

4. Click **"Run"** (or press Ctrl+Enter)
5. You should see: **"Success. No rows returned"**

## Step 5: Verify Tables Created

1. Click **"Table Editor"** (on left sidebar)
2. You should see two tables:
   - ✓ `cv_intelligence` (with 17 columns)
   - ✓ `cv_filename_mapping` (with 4 columns)

## Step 6: Configure Environment Variables

Now that you have both credentials, configure them in PowerShell:

```powershell
# Set Supabase URL (replace with your project URL)
$env:SUPABASE_URL="https://xxxxxxxxxxxxx.supabase.co"

# Set Supabase Key (replace with your anon/public key)
$env:SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey..."

# Verify they're set
Write-Host "✓ SUPABASE_URL: $($env:SUPABASE_URL)" -ForegroundColor Green
Write-Host "✓ SUPABASE_KEY: $($env:SUPABASE_KEY.Substring(0,20))..." -ForegroundColor Green
```

## Step 7: Test the Connection

Run the test suite again:

```powershell
python test_production_system.py
```

You should now see **7/7 TESTS PASSED** ✅

---

## 🎯 Quick Reference

### Your Credentials Template:
```powershell
# Replace these with your actual values
$env:GOOGLE_API_KEY="your-google-api-key-here"  # Get from Google AI Studio
$env:SUPABASE_URL="https://YOUR-PROJECT.supabase.co"           # Get from Step 3
$env:SUPABASE_KEY="eyJhbGciOiJIUz..."                           # Get from Step 3
```

### Restart Flask Server:
After setting environment variables, restart the server:
```powershell
# Stop current server (Ctrl+C if running in foreground)
# Or kill the background process

# Start server with new credentials
python app.py
```

---

## 🆓 Supabase Free Tier Includes:
- ✅ 500 MB database storage
- ✅ Unlimited API requests
- ✅ Up to 50,000 monthly active users
- ✅ Social OAuth providers
- ✅ Database backups (7 days)
- ✅ Community support

**Perfect for testing and small deployments!**

---

## ❓ Troubleshooting

### "Project URL not working"
- Make sure you copied the entire URL including `https://`
- Verify the project is fully initialized (green checkmark in dashboard)

### "Authentication error with Supabase key"
- Make sure you copied the **anon/public** key (not the service_role key)
- The key should start with `eyJhbGciOiJIUzI1NiI...`
- It's very long (~250 characters)

### "Table already exists" error
- This is OK! It means the tables were created successfully
- You can proceed to Step 5 to verify

### "SQL error" when creating tables
- Make sure you copied the entire SQL block
- Try running each CREATE TABLE statement separately
- Check the error message in the SQL Editor

---

## ✅ Success Checklist

After completing all steps, you should have:

- [x] Supabase account created
- [x] New project initialized
- [x] Project URL copied
- [x] Anon/public key copied
- [x] SQL schema executed successfully
- [x] Two tables visible in Table Editor
- [x] Environment variables set in PowerShell
- [x] Test suite showing 7/7 passing

**You're ready to use the full system with AI intelligence extraction and persistent storage!** 🎉
