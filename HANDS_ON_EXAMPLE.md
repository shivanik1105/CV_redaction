# 🎯 Hands-On Example - Test the CV Intelligence System

## Step-by-Step Tutorial (5 Minutes)

Let's analyze a real CV and see the AI in action!

---

## Step 1: Start the Server 🚀

First, make sure your credentials are set and start the Flask server:

```powershell
# Set API credentials (copy-paste all 3 lines)
$env:GOOGLE_API_KEY="AIzaSyBW7pa0akQ24wxPwBy17TkaeJ3nh49gcG0"
$env:SUPABASE_URL="https://dpnvwxsslvasyufwqzwr.supabase.co"
$env:SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwbnZ3eHNzbHZhc3l1ZndxendyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA4MjYzNzAsImV4cCI6MjA4NjQwMjM3MH0.hTBeGnN_5YEi-oynzTAehWeRN8xd579K-nqjiLa19M0"

# Start the server
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Restarting with stat
 * Debugger is active!
```

**Keep this terminal open!** The server needs to stay running.

---

## Step 2: Open the Application 🌐

Open your web browser and go to:
```
http://localhost:5000
```

You should see the **"CV Redaction Pipeline"** homepage with:
- Upload CV section
- Job Description text area
- "Extract Intelligence" button

---

## Step 3: Prepare a Job Description 📝

Copy this sample job description (or write your own):

```
Senior Python Developer - 5+ Years Experience

We're looking for an experienced Python developer to join our team.

Requirements:
- 5+ years of professional Python development
- Strong experience with Django or Flask frameworks
- Database experience (PostgreSQL, MySQL)
- REST API design and development
- Cloud platforms (AWS, Azure, or GCP)
- Git version control
- Strong problem-solving skills
- Good communication and teamwork

Nice to have:
- DevOps experience (Docker, Kubernetes)
- CI/CD pipeline knowledge
- Machine Learning or Data Science experience
- Frontend skills (React, Vue.js)

Responsibilities:
- Design and develop backend services
- Write clean, maintainable code
- Collaborate with frontend team
- Review code and mentor junior developers
- Participate in technical planning
```

**Paste this into the "Job Description" text area on the webpage.**

---

## Step 4: Choose a Sample CV 📄

Use one of these sample CVs from your `samples/` folder:

### Option A: Senior Developer (Recommended for testing)
**File:** `samples/Naukri_jyotiSaxena[9y_1m].pdf`
- 9 years experience
- Python, DevOps background
- Should get **SHORTLIST** verdict

### Option B: Mid-Level Developer
**File:** `samples/Naukri_ChirayuYelane[5y_2m].pdf`
- 5 years experience
- Should get **BACKUP** or **SHORTLIST** verdict

### Option C: Entry Level
**File:** `samples/Naukri_MayurPatil[3y_2m].pdf`
- 3 years experience
- Should get **REVIEW** verdict (less than required 5+ years)

---

## Step 5: Upload and Analyze 🤖

1. **Click "Choose File"** in the CV upload section
2. **Select one of the sample CVs** (e.g., `Naukri_jyotiSaxena[9y_1m].pdf`)
3. **Make sure the job description is pasted** in the text area
4. **Click "Extract Intelligence"** button
5. **Wait 10-20 seconds** (AI is analyzing!)

---

## Step 6: See the Results! 🎉

After processing, you'll see a **detailed analysis**:

### A. Anonymized Candidate ID
```
Candidate ID: CAND_1234
```
💡 **Notice:** No real name shows up - privacy protected!

### B. AI Verdict
One of three options:
- ✅ **SHORTLIST** - Strong match (>70% confidence)
- ⚙️ **BACKUP** - Good match (60-70% confidence)
- 👤 **REVIEW** - Human review needed (<60% confidence)

💡 **Notice:** Never says "REJECT" - that's the no-auto-reject policy!

### C. Confidence Score
```
Confidence: 85%
```

### D. Evidence-Based Reasoning
```
Verdict Reason:
- 9+ years of Python experience (exceeds 5+ requirement)
- Strong Django and Flask expertise
- PostgreSQL database skills confirmed
- AWS cloud experience present
- DevOps skills including Docker (nice-to-have met)
...
```

💡 **Notice:** AI must explain its decision with evidence!

### E. Skills Breakdown
```
Core Technical Skills:
- Python (9 years)
- Django, Flask
- PostgreSQL, MySQL
- REST APIs
- AWS, Docker

Soft Skills:
- Team Leadership
- Problem Solving
- Communication
...
```

### F. Career Intelligence
```
Years of Experience: 9.0
Seniority Level: SENIOR
Primary Domain: Web Development
Role Types: Full Stack Developer, Backend Engineer
```

---

## Step 7: Check the Dashboard 📊

Open a new browser tab and go to:
```
http://localhost:5000/dashboard
```

You'll see:

### Statistics Panel
```
┌─────────────────────────────────────┐
│  Total CVs: 1                       │
│  Shortlisted: 1 (100%)              │
│  Backup: 0 (0%)                     │
│  Review Queue: 0 (0%)               │
│  Avg Confidence: 85%                │
└─────────────────────────────────────┘
```

### Candidate Cards
Each candidate shows:
- Anonymized ID (CAND_XXX)
- Skills tags
- Experience level
- AI verdict and confidence
- Evidence reasoning

### Human Review Queue
If a candidate has **REVIEW** verdict or low confidence (<70%), they appear here:
```
┌─────────────────────────────────────┐
│  👤 Human Review Required           │
│                                     │
│  These candidates need your review: │
│  - Low AI confidence (<70%)         │
│  - Unclear CV content               │
│  - Borderline qualifications        │
└─────────────────────────────────────┘
```

### Recruiter Override
For any candidate, you can:
- ✅ **Accept** (confirm AI decision)
- ⚙️ **Reconsider** (move to backup)
- ✗ **Reject** (only humans can reject!)
- Add notes explaining your decision

---

## Step 8: Check the Files 📁

### A. Uploads Folder
```powershell
ls uploads/
```
You'll see the original uploaded CV (temporary storage)

### B. Redacted Output Folder
```powershell
ls redacted_output/
```
You'll see the **anonymized CV** with all PII removed:
```
REDACTED_20260212_XXXXXX_jyotiSaxena.txt
```
**Open this file** - notice all names, emails, phones are removed!

### C. LLM Analysis Folder
```powershell
ls llm_analysis/
```
You'll see the **complete AI analysis** in JSON format:
```
CAND_1234_analysis.json
```

**Open this file** to see:
```json
{
  "anonymized_id": "CAND_1234",
  "years_experience": 9.0,
  "verdict": "SHORTLIST",
  "confidence_score": 85,
  "core_technical_skills": ["Python", "Django", "Flask", ...],
  "verdict_reason": "Candidate exceeds all requirements...",
  ...
}
```

---

## Step 9: Check the Database 🗄️

### Option A: Via Supabase Dashboard
1. Go to **https://app.supabase.com**
2. Open your project: **cv-intelligence**
3. Click **"Table Editor"** → **"cv_intelligence"**
4. You'll see the candidate record with:
   - Anonymized ID
   - Original CV hash (SHA256)
   - LLM prompt used
   - LLM raw response
   - Verdict, confidence, reasoning
   - All audit trail fields

### Option B: Via Python Script
```powershell
# Query all candidates
python -c "from supabase_storage import SupabaseStorage; storage = SupabaseStorage(); print(storage.get_all_candidates())"
```

---

## 🎯 Try Different Scenarios

### Scenario 1: High Confidence Match
**CV:** `Naukri_jyotiSaxena[9y_1m].pdf` (9 years Python)  
**JD:** Senior Python Developer (5+ years)  
**Expected:** SHORTLIST, >70% confidence

### Scenario 2: Borderline Match
**CV:** `Naukri_ChirayuYelane[5y_2m].pdf` (5 years)  
**JD:** Senior Python Developer (5+ years)  
**Expected:** SHORTLIST or BACKUP, 60-75% confidence

### Scenario 3: Under-Qualified (Tests No-Auto-Reject)
**CV:** `Naukri_MayurPatil[3y_2m].pdf` (3 years)  
**JD:** Senior Python Developer (5+ years)  
**Expected:** **REVIEW** (NOT reject!), <60% confidence

💡 **Key Point:** Even when candidate doesn't meet requirements, AI says **REVIEW** (needs human decision), never **REJECT**!

### Scenario 4: Different Tech Stack
**CV:** Any Java developer CV  
**JD:** Python Developer  
**Expected:** REVIEW verdict, AI explains skill gap

---

## 🔍 What to Look For

### ✅ Ethical AI Features Working:

1. **No Auto-Reject Policy**
   - Low-confidence candidates → REVIEW (not REJECT)
   - Under-qualified candidates → REVIEW (not REJECT)
   - AI never makes final rejection decision

2. **Full Explainability**
   - Every verdict includes detailed reasoning
   - Evidence from CV cited
   - Match against job requirements explained

3. **Privacy Protection**
   - Original CV names → CAND_XXX
   - Emails, phones, addresses removed
   - Backend knows real identity, frontend doesn't

4. **Audit Trail**
   - Original CV hash stored
   - Exact LLM prompt saved
   - Complete LLM response stored
   - Timestamp of all actions
   - Ready for compliance audits

5. **Human Oversight**
   - Low confidence → Review queue
   - Recruiters can override any decision
   - Override reason required
   - Top 50 always reviewed

---

## 📊 Expected Timeline

| Step | Action | Expected Time |
|------|--------|---------------|
| 1 | Start server | 5 seconds |
| 2 | Upload CV | 2 seconds |
| 3 | AI analysis | 10-20 seconds |
| 4 | Results display | 1 second |
| 5 | Dashboard view | 1 second |

**Total: Under 1 minute!**

---

## 🐛 Troubleshooting

### "API key error"
```powershell
# Re-set credentials in the SAME terminal where app.py is running
$env:GOOGLE_API_KEY="AIzaSyBW7pa0akQ24wxPwBy17TkaeJ3nh49gcG0"
```

### "Cannot reach server"
- Make sure `python app.py` is still running
- Check for errors in the server terminal
- Try accessing http://127.0.0.1:5000 instead

### "Upload failed"
- Check file size (must be <16MB)
- Supported formats: PDF, DOCX
- Make sure `uploads/` folder exists

### "No results showing"
- Wait 20 seconds (AI analysis takes time)
- Check server terminal for errors
- Verify Google API key has quota remaining

### "Database error"
- Verify Supabase credentials are set correctly
- Check Supabase project is active (not paused)
- Ensure SQL schema was run in Supabase

---

## 🎓 Learning Outcomes

After completing this example, you've seen:

✅ **End-to-end CV processing** - Upload to analysis  
✅ **AI intelligence extraction** - Deep candidate insights  
✅ **No auto-reject policy** - Ethical AI in action  
✅ **Privacy protection** - PII anonymization  
✅ **Full audit trail** - Compliance-ready  
✅ **Recruiter dashboard** - Human oversight interface  
✅ **Override workflow** - Human final decision  

---

## 🚀 Next Steps

1. **Try multiple CVs** - Upload 5-10 CVs with the same job description
2. **Check statistics** - See dashboard analytics update
3. **Test review queue** - Upload under-qualified CV, verify it goes to review
4. **Test override** - Change an AI verdict, add notes
5. **Export results** - Download analysis JSON files
6. **Query database** - Practice Supabase queries

---

## 📞 Ready to Deploy?

Once you've tested and are satisfied:

1. **Review** PRODUCTION_DEPLOYMENT_GUIDE.md
2. **Package** all files for company delivery
3. **Train** recruiters using RECRUITER_QUICK_REFERENCE.md
4. **Deploy** to production server
5. **Monitor** using health endpoint and test suite

---

**🎉 Enjoy testing your production-ready CV Intelligence System!**
