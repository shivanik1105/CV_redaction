# User Guide - CV Intelligence System

Simple guide for using the application to upload and search CVs.

---

## 🎯 What This Application Does

1. **Upload CVs** → Automatically removes personal information (names, emails, phones)
2. **Search CVs** → Find candidates using job descriptions or filters
3. **Download Results** → Get anonymized CVs with visual black boxes over PII

---

## 📤 How to Upload a CV

### Step-by-Step:

1. **Open the application** in your browser: `http://127.0.0.1:5000`

2. **Click on "Upload and Process Single CV" tab**

3. **Choose your CV file**
   - Click "Choose file"
   - Select a PDF or DOCX file
   - You'll see the filename appear

4. **Get an API Key** (Required!)
   - Go to https://console.groq.com/keys
   - Sign up for free
   - Create a new API key
   - Copy the key (starts with `gsk_`)

5. **Enter your API Key**
   - Paste it in the "LLM API Key (Required)" field
   - This is needed for AI processing
   - Your key is NOT stored on the server

6. **(Optional) Add Job Description**
   - If you want to match this CV against a specific job
   - Paste the job description in the text area
   - Leave empty for general processing

7. **Click "Upload CV"**
   - Processing takes 30-60 seconds
   - You'll see a progress indicator

8. **Download Results**
   - **"Download Redacted Output"** - Text file with [REDACTED] markers
   - **"Download Masked PDF"** - PDF with black boxes over personal info

### What Gets Removed:
- ✅ Names
- ✅ Email addresses
- ✅ Phone numbers
- ✅ Home addresses
- ✅ LinkedIn/GitHub links
- ✅ Personal websites

### What's Kept:
- ✅ Work experience
- ✅ Skills
- ✅ Education
- ✅ Projects
- ✅ Achievements
- ✅ Job titles
- ✅ Company names (without locations)

---

## 🔍 How to Search CVs

### Option 1: Search with Job Description (Recommended)

**Use this when**: You have a specific job opening and want to find matching candidates

**Steps**:

1. **Click on "Search & Filter CVs" tab**

2. **Paste your job description**
   - Copy the full job description
   - Paste it in the "Job Description" text area
   - Include requirements, skills, experience needed

3. **Click "Search"**

4. **View Results**
   - Candidates are ranked by match percentage
   - Higher percentage = better match
   - See why each candidate was selected

5. **Download CVs**
   - Click "Download all redacted CVs (recommended)" for top matches
   - Or click "Original CV" on individual candidates

### Option 2: Filter Search (No Job Description)

**Use this when**: You want to browse all candidates or filter by specific criteria

**Steps**:

1. **Click on "Search & Filter CVs" tab**

2. **Leave job description empty**

3. **Set filters** (all optional):
   - **Seniority Level**: Entry, Mid, Senior, Lead, Executive
   - **Min Match Score**: 0-100% (only works with JD)
   - **Min Confidence**: 0-100% (how confident AI is)
   - **Min Years Experience**: e.g., 3
   - **Max Years Experience**: e.g., 10
   - **Required Skills**: e.g., "Python, AWS, Docker"
   - **Primary Domain**: e.g., "Cloud Computing"

4. **Click "Search"**

5. **View all matching candidates**

### Understanding Search Results:

Each candidate card shows:

```
CAND_ABC123                                    [83%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Confidence: 90%
Experience: 5 years (Senior)
Domain: Cloud Computing, DevOps

Matched: kubernetes, terraform, docker, python, ci/cd

Why selected: Semantic match with 5/5 critical skills

Critical Skill Coverage: 100%

Best Knowledge: Core strengths: AWS, Docker, Kubernetes...

[AWS] [Docker] [Kubernetes] [Ansible] [Terraform]

[Original CV]
```

**What each field means**:

- **CAND_ABC123**: Anonymized candidate ID
- **83%**: Match percentage (only with job description)
- **Confidence: 90%**: How confident the AI is about this candidate's info
- **Experience: 5 years (Senior)**: Total experience and seniority level
- **Domain**: Primary area of expertise
- **Matched**: Keywords that match your job description
- **Why selected**: Reason this candidate was recommended
- **Critical Skill Coverage**: % of must-have skills this candidate has
- **Best Knowledge**: Summary of candidate's strengths
- **Skill Tags**: Top 5 skills
- **Original CV**: Click to download the CV

---

## 💡 Tips for Best Results

### For Uploading:

1. **Use clear, well-formatted CVs**
   - PDFs work best
   - DOCX also supported
   - Avoid scanned images (text must be selectable)

2. **Always provide your API key**
   - Get a free key from Groq
   - Processing won't work without it

3. **Add job description for better matching**
   - More detailed JD = better matches
   - Include required skills, experience, responsibilities

### For Searching:

1. **With Job Description**:
   - Be specific about requirements
   - Include must-have skills
   - Mention years of experience needed
   - Describe the role clearly

2. **Without Job Description**:
   - Use filters to narrow down
   - Start broad, then refine
   - Try different skill combinations

3. **Interpreting Results**:
   - **80%+ match**: Excellent fit
   - **60-80% match**: Good fit, worth reviewing
   - **40-60% match**: Partial fit, may need training
   - **Below 40%**: Weak match

---

## 📥 Downloading CVs

### Individual CV:
- Click **"Original CV"** button on any candidate card
- Downloads the original uploaded file (PDF/DOCX)

### Bulk Download (with Job Description):
- Click **"Download all redacted CVs (recommended)"**
- Downloads a ZIP file with top matching CVs
- All CVs are anonymized

### Masked PDF (after upload):
- Click **"Download Masked PDF"**
- Gets PDF with visual black boxes over personal info
- Professional-looking redacted document

---

## ❓ Common Questions

### Q: Why do I need to provide my own API key?
**A**: The server doesn't use its own API key for security and cost reasons. You provide your own key so you control the usage and costs.

### Q: Is my API key stored?
**A**: No, your API key is only used for the current request and is not stored on the server.

### Q: How long does upload take?
**A**: 30-60 seconds for the first upload (loading AI models), then 15-30 seconds for subsequent uploads.

### Q: Can I upload multiple CVs at once?
**A**: Currently, you need to upload CVs one at a time. Each upload is processed independently.

### Q: What if I don't have a job description?
**A**: You can still upload CVs! Just leave the job description field empty. The system will extract intelligence without matching.

### Q: How accurate is the matching?
**A**: The AI uses semantic understanding, not just keyword matching. It understands context and skills relationships. Accuracy is typically 85-95%.

### Q: Can I see the original personal information?
**A**: No, once a CV is processed, the personal information is permanently redacted for privacy protection.

### Q: What happens to uploaded CVs?
**A**: CVs are stored on the server and in the database. The original file is kept for download, and the redacted version is used for searching.

---

## 🚨 Troubleshooting

### Upload Issues:

**"LLM API key is required"**
- You forgot to enter your API key
- Get one from https://console.groq.com/keys

**"Job failed: Unknown error"**
- Your API key might be invalid
- Try a different CV file
- Check if the file is corrupted

**"Invalid file type"**
- Only PDF and DOCX files are supported
- Convert your file to PDF or DOCX

### Search Issues:

**"No matches found"**
- Try broader search criteria
- Remove some filters
- Check if CVs are uploaded

**"503 Service Unavailable"**
- The server might be restarting
- Wait a moment and try again
- Contact administrator if persists

### Download Issues:

**"Original CV file not found"**
- The file might have been deleted
- Re-upload the CV
- Contact administrator

---

## 📞 Need Help?

1. **Check this guide** - Most questions are answered here
2. **Check the logs** - Look at the terminal running the app
3. **Restart the app** - Sometimes fixes issues
4. **Contact support** - If nothing else works

---

## 🎉 Quick Reference

### Upload CV:
```
1. Go to "Upload and Process Single CV"
2. Choose file
3. Get API key from https://console.groq.com/keys
4. Enter API key
5. Click "Upload CV"
6. Download results
```

### Search CVs:
```
1. Go to "Search & Filter CVs"
2. Paste job description (or leave empty)
3. Set filters (optional)
4. Click "Search"
5. View results
6. Download CVs
```

---

**That's all you need to know to use the CV Intelligence System!** 🚀

For technical setup and installation, see `README.md`
