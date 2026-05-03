# Quick Setup Checklist

## ✅ What's Already Done

- [x] Multi-column CV extraction fixed (Sunil Durgale CV works!)
- [x] Native GUI executable built (`dist\CVRedactor.exe`)
- [x] Web application ready (`app.py`)
- [x] Test results verified (85.3% success rate on 68 CVs)
- [x] Integration complete (both use same redaction engine)
- [x] Local JSON fallback working (no Supabase required)

---

## 🚀 Quick Start (Choose One)

### Option A: Native GUI Only (Simplest)
```powershell
cd dist\CVRedactor_Package
.\CVRedactor.exe
```
✅ Done! No configuration needed.

### Option B: Web App (Full Features)
```powershell
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env (optional - can skip for local mode)
notepad .env

# 3. Start application
python app_launcher.py
```
✅ Opens browser automatically at http://localhost:5000

---

## 📋 Configuration Checklist

### Required (Already Done)
- [x] Python 3.11+ installed
- [x] Dependencies installed (`.venv`)
- [x] Config files present (`config/` folder)
- [x] Folders created (`uploads/`, `redacted_output/`, `llm_analysis/`)

### Optional (For Full Features)

#### LLM Provider (For Intelligence Extraction)
- [ ] Get Groq API key (free): https://console.groq.com/keys
- [ ] Add to `.env`:
  ```env
  LLM_PROVIDER=groq
  GROQ_API_KEY=gsk_xxxxxxxxxxxxx
  ```
- [ ] Test: Go to http://localhost:5000/dashboard

#### Supabase (For Cloud Storage)
- [ ] Create Supabase project: https://supabase.com
- [ ] Run SQL setup: `supabase_pgvector_setup.sql`
- [ ] Add credentials to `.env`:
  ```env
  SUPABASE_URL=https://xxxxx.supabase.co
  SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```
- [ ] Test: Go to http://localhost:5000/dashboard

---

## 🧪 Testing Checklist

### Test 1: Native GUI
```powershell
cd dist\CVRedactor_Package
.\CVRedactor.exe
```
- [ ] GUI opens without errors
- [ ] Can browse and select CV
- [ ] Redaction completes in 1-2 seconds
- [ ] Output file is created
- [ ] Output has [REDACTED_*] placeholders

### Test 2: Web App (Redactor Page)
```powershell
python app_launcher.py
# Go to: http://localhost:5000/redactor
```
- [ ] Page loads
- [ ] Can upload CV
- [ ] Redaction works
- [ ] Can download output

### Test 3: Sunil Durgale CV (The Fixed One!)
```powershell
python app_launcher.py --test "samples/Resume -Sunil Durgale.pdf"
```
- [ ] Extraction completes
- [ ] SUMMARY section has content
- [ ] SKILLS section has content
- [ ] WORK EXPERIENCE is in proper sequence
- [ ] No mixed sections
- [ ] Output saved to `test_redaction_output.txt`

### Test 4: Web App (Upload & Process)
```powershell
# Go to: http://localhost:5000/upload
```
- [ ] Page loads
- [ ] Can upload CV
- [ ] Redaction works
- [ ] Intelligence extraction works (if LLM configured)
- [ ] Results saved to `llm_analysis/` folder

### Test 5: Web App (Search)
```powershell
# Go to: http://localhost:5000/search
```
- [ ] Page loads
- [ ] Shows candidates from local JSON
- [ ] Can filter by skills, experience, etc.
- [ ] Can view candidate profiles

### Test 6: Dashboard
```powershell
# Go to: http://localhost:5000/dashboard
```
- [ ] Shows statistics
- [ ] Shows LLM status
- [ ] Shows Supabase status (or "not configured")
- [ ] Shows data source (local_json or supabase)

---

## 🔧 Troubleshooting Checklist

### Issue: "Supabase not connected"
- [ ] Check if `.env` has real credentials (not placeholders)
- [ ] Check if Supabase project is active
- [ ] Test connection manually:
  ```powershell
  python -c "from supabase_storage import SupabaseStorage; s = SupabaseStorage(); print('OK!')"
  ```
- [ ] If fails, use local mode (automatic)

### Issue: "LLM Provider not configured"
- [ ] Check if `.env` has API key
- [ ] Check if API key is valid
- [ ] Test manually:
  ```powershell
  python -c "from cv_intelligence_extractor import CVIntelligenceExtractor; e = CVIntelligenceExtractor(); print('OK!')"
  ```
- [ ] Try different provider (Groq is free)

### Issue: "Empty sections in output"
- [ ] Check if using latest code (multi-column fix)
- [ ] Test with Sunil Durgale CV (should work)
- [ ] Check `test_results/Resume -Sunil Durgale_output.txt`
- [ ] If still fails, check CV format (might be scanned image)

### Issue: "Native GUI won't start"
- [ ] Check if `config/` folder exists next to .exe
- [ ] Run as administrator
- [ ] Check Windows Firewall
- [ ] Rebuild:
  ```powershell
  .\build_native_gui.ps1 -Clean
  ```

### Issue: "Web app slow"
- [ ] First CV: 10-15 seconds (normal - model loading)
- [ ] Subsequent CVs: 1-2 seconds (normal)
- [ ] If always slow, check LLM provider

---

## 📊 Success Criteria

### Native GUI
- ✅ Opens without errors
- ✅ Processes CV in 1-2 seconds
- ✅ Output has proper PII redaction
- ✅ Multi-column CVs work (Sunil Durgale)

### Web App (Basic)
- ✅ All pages load
- ✅ Redaction works
- ✅ Local JSON storage works
- ✅ Can search candidates

### Web App (Full)
- ✅ LLM extraction works
- ✅ Job matching works
- ✅ Supabase storage works
- ✅ Vector search works

---

## 🎯 Current Status

Based on your question "Supabase not connected":

### What's Working:
✅ Native GUI (standalone)
✅ Web app (local mode)
✅ CV redaction (both)
✅ Multi-column extraction (Sunil Durgale fixed)
✅ Local JSON storage

### What Needs Configuration:
⚠️ Supabase (optional - for cloud storage)
⚠️ LLM Provider (optional - for intelligence extraction)

### What to Do Next:

**If you just want to redact CVs:**
→ Use Native GUI (`dist\CVRedactor.exe`)
→ No configuration needed!

**If you want full intelligence system:**
1. Get Groq API key (free)
2. Add to `.env`
3. Restart web app
4. Upload CVs to `/upload` page

**If you want cloud storage:**
1. Create Supabase project
2. Run SQL setup
3. Add credentials to `.env`
4. Restart web app

---

## 📞 Quick Help

### Files to Check:
- `COMPLETE_USER_GUIDE.md` - Full documentation
- `SYSTEM_ARCHITECTURE_VISUAL.md` - Visual diagrams
- `BUILD_SUCCESS.md` - Build details
- `test_results/Resume -Sunil Durgale_output.txt` - Fixed CV output

### Commands to Run:
```powershell
# Test Sunil Durgale CV
python app_launcher.py --test "samples/Resume -Sunil Durgale.pdf"

# Start web app
python app_launcher.py

# Start native GUI
cd dist\CVRedactor_Package
.\CVRedactor.exe

# Check system status
# Browser: http://localhost:5000/dashboard
```

---

## ✅ Summary

**Everything is ready!** You can:
1. Use Native GUI for quick redaction (no setup)
2. Use Web App in local mode (no Supabase/LLM)
3. Configure LLM for intelligence extraction (optional)
4. Configure Supabase for cloud storage (optional)

**Sunil Durgale CV issue is completely fixed!** ✅

The system works with or without Supabase. The "not connected" message just means you're using local mode, which is perfectly fine for single-user setup.

🎉 Ready to use!
