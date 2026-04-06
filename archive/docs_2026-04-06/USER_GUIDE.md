# CV Intelligence System - User Guide

## For End Users (No Technical Knowledge Required)

---

## 📥 Download and Install

### Step 1: Download
1. Download `CVIntelligence.exe` from the provided link
2. Save it to your computer (e.g., Desktop or Downloads folder)
3. File size: ~500-800 MB (one-time download)

### Step 2: First Time Setup
1. Get a FREE Groq API key:
   - Go to https://console.groq.com
   - Click "Sign Up" (free account)
   - Go to "API Keys"
   - Click "Create API Key"
   - Copy the key (starts with `gsk_...`)

2. Configure the application:
   - Find `.env.example` file (same folder as exe)
   - Copy it and rename to `.env`
   - Open `.env` with Notepad
   - Replace `your_groq_api_key_here` with your actual key
   - Save and close

### Step 3: Run
1. Double-click `CVIntelligence.exe`
2. A console window will open (don't close it!)
3. Your browser will open automatically
4. You'll see the CV Intelligence interface

---

## 🚀 How to Use

### Processing CVs

**Step 1: Go to "Process CVs" Tab**
- Click the "Process CVs" tab at the top

**Step 2: Add Your CVs**
- Place your CV files (PDF or DOCX) in the `uploads` folder
- The folder is created automatically when you run the app

**Step 3: Process**
- Click "Process All Sample CVs"
- Wait for processing to complete (6-8 seconds per CV)
- You'll see a success message

### Searching Candidates

**Step 1: Go to "Search" Tab**
- Click the "Search" tab at the top (default view)

**Step 2: Enter Job Description (Optional)**
- Paste your job description in the text area
- Or leave empty to search all candidates

**Step 3: Set Filters (Optional)**
- Seniority Level: Entry, Mid, Senior, Lead, Executive
- Min Match Score: 0-100%
- Min Confidence: 0-100%
- Years Experience: Min and Max
- Required Skills: e.g., "Python, AWS, Docker"
- Primary Domain: e.g., "Web Development"

**Step 4: Search**
- Click "Search Candidates"
- Results appear instantly
- See candidate cards with scores and skills

---

## 📊 Understanding the Results

### Candidate Card Example:
```
CAND_902                    67%
Confidence: 70%
Experience: 17 years (SENIOR)
Domain: Automotive, Android TV
Skills: C++, C, Java, JavaScript, Python
```

### What the Numbers Mean:

**67% (Match Score)**:
- How well the candidate matches your job description
- 90-100%: Excellent match
- 70-89%: Good match
- 50-69%: Moderate match (this candidate)
- 0-49%: Poor match

**70% (Confidence Score)**:
- How confident the AI is in its analysis
- 80-100%: High confidence
- 60-79%: Medium confidence (this candidate)
- 40-59%: Low confidence
- 0-39%: Very low confidence

---

## 🔧 Common Tasks

### Task 1: Process New CVs
```
1. Put CV files in uploads/ folder
2. Go to "Process CVs" tab
3. Click "Process All Sample CVs"
4. Wait for completion
```

### Task 2: Find Top Candidates
```
1. Go to "Search" tab
2. Paste job description
3. Set "Min Match Score" to 70%
4. Click "Search Candidates"
5. Top matches appear first
```

### Task 3: Filter by Skills
```
1. Go to "Search" tab
2. Enter skills in "Required Skills" field
   Example: "Python, AWS, Docker"
3. Click "Search Candidates"
4. Only candidates with those skills appear
```

### Task 4: Filter by Experience
```
1. Go to "Search" tab
2. Set "Min Years Experience" (e.g., 5)
3. Set "Max Years Experience" (e.g., 10)
4. Click "Search Candidates"
5. Only candidates in that range appear
```

---

## ❓ Troubleshooting

### Problem: Browser doesn't open automatically
**Solution**: 
- Open your browser manually
- Go to: http://localhost:5000

### Problem: "Port 5000 is already in use"
**Solution**:
- Close other applications using port 5000
- Or restart your computer

### Problem: "API key error"
**Solution**:
- Check your `.env` file
- Make sure GROQ_API_KEY is correct
- No spaces around the = sign
- Key should start with `gsk_`

### Problem: CVs not processing
**Solution**:
- Check CVs are in `uploads/` folder
- Make sure files are PDF or DOCX
- Check file size < 16MB
- Check internet connection (API needs internet)

### Problem: Slow processing
**Solution**:
- Normal: 6-8 seconds per CV
- Check internet speed
- Close other applications
- Restart the application

### Problem: Antivirus blocks the exe
**Solution**:
- Add exception in antivirus
- Or download from official source only

---

## 📁 Folder Structure

```
CVIntelligence/
├── CVIntelligence.exe      # Main application
├── .env                    # Your configuration (create from .env.example)
├── .env.example            # Configuration template
├── config/                 # System configuration
├── uploads/                # Put your CVs here (created automatically)
├── redacted_output/        # Anonymized CVs (created automatically)
└── llm_analysis/           # Extracted intelligence (created automatically)
```

---

## 💡 Tips and Best Practices

### For Best Results:
1. **Use clear CVs**: Well-formatted PDFs work best
2. **Provide JD**: Better matching with job description
3. **Set realistic filters**: Don't over-filter
4. **Check confidence**: Low confidence = verify manually
5. **Review top matches**: Don't rely 100% on scores

### For Faster Processing:
1. **Batch process**: Process all CVs at once
2. **Good internet**: Faster API calls
3. **Close other apps**: More RAM available
4. **Don't reprocess**: System caches results

### For Better Searches:
1. **Use JD**: Paste full job description
2. **Combine filters**: Use multiple filters together
3. **Start broad**: Then narrow down
4. **Check skills**: Verify key skills manually

---

## 🔒 Privacy and Security

### Your Data is Safe:
- ✅ All CVs anonymized before AI processing
- ✅ No names, emails, or phone numbers sent to API
- ✅ Data stored locally on your computer
- ✅ Optional cloud storage (Supabase)

### What Gets Anonymized:
- Names → [REDACTED_NAME]
- Emails → [REDACTED_EMAIL]
- Phones → [REDACTED_PHONE]
- Addresses → [REDACTED_ADDRESS]

### What's Preserved:
- Skills and experience
- Job titles and roles
- Technical knowledge
- Professional achievements

---

## 📞 Support

### Need Help?
- Read this guide first
- Check troubleshooting section
- Contact support with:
  - Error message (if any)
  - What you were trying to do
  - Screenshot (if possible)

### Want to Learn More?
- See `COMPLETE_SYSTEM_ARCHITECTURE.md` for technical details
- See `COST_ANALYSIS_AND_SCALING.md` for pricing
- See `EXE_BUILD_GUIDE.md` for building from source

---

## 🎯 Quick Reference

### Keyboard Shortcuts:
- `Ctrl + R`: Refresh page
- `Ctrl + F`: Find on page
- `F5`: Reload page

### URLs:
- Main Interface: http://localhost:5000
- Semantic Search: http://localhost:5000/semantic-search

### File Formats Supported:
- ✅ PDF (.pdf)
- ✅ Word (.docx, .doc)
- ❌ Images (not supported)
- ❌ Text files (not supported)

### Limits:
- Max file size: 16MB per CV
- Max CVs: Unlimited (local storage)
- API calls: 6,000/day (free tier)

---

## 📝 Example Workflow

### Scenario: Hiring Python Developer

**Step 1: Prepare**
```
- Collect 50 CVs
- Put in uploads/ folder
- Write job description
```

**Step 2: Process**
```
- Run CVIntelligence.exe
- Go to "Process CVs" tab
- Click "Process All Sample CVs"
- Wait ~5 minutes (50 CVs × 6 sec)
```

**Step 3: Search**
```
- Go to "Search" tab
- Paste job description:
  "Senior Python developer with 5+ years experience.
   Must have: Python, Django, PostgreSQL, AWS.
   Nice to have: Docker, Kubernetes, React."
- Set filters:
  - Seniority: Senior
  - Min Match Score: 70%
  - Min Years: 5
  - Required Skills: Python, Django
- Click "Search Candidates"
```

**Step 4: Review**
```
- Top 10 candidates appear
- Review match scores
- Check confidence levels
- Verify key skills
- Shortlist for interview
```

**Result**: Found 8 strong candidates in 5 minutes instead of 8 hours manual screening!

---

**Version**: 1.0  
**Last Updated**: March 27, 2026  
**For**: Windows 10/11 (64-bit)
