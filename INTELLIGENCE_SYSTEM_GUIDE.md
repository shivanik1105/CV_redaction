# 🎯 CV Intelligence & Recruitment System - Complete Guide

## Overview

This enhanced CV Redaction Pipeline now includes **intelligent extraction** and **recruitment management** capabilities powered by AI and Supabase.

## 🚀 Three-Step Workflow

### 1. **Anonymize** (Existing Feature)
Strips all personal information from CVs:
- Names, emails, phones
- Addresses and locations
- Company names
- Personal identifiers

**Output:** Clean anonymized `.txt` files ready for analysis

---

### 2. **Extract Intelligence** (NEW)
Feeds anonymized CVs + Job Description into an LLM to extract:

**Structured Data:**
- **Skills:** Technical, soft skills, tools, certifications
- **Experience:** Years, seniority level, domains, roles
- **Education:** Degree, field, education level

**Intelligence:**
- **JD Fitment Verdict:** SHORTLIST / BACKUP / REJECT
- **Match Score:** 0-100 based on job requirements
- **Reasoning:** Why this verdict was given
- **Matched/Missing Requirements:** Detailed breakdown
- **Strengths & Concerns:** Key points for recruiters

**Search-Ready:**
- **Narrative Summary:** Clean 2-3 sentence professional summary
- **Keywords:** Optimized for search and filtering

**Output:** Structured JSON files + Supabase storage

---

### 3. **Store & Search** (NEW)
All intelligence is stored in **Supabase** with powerful querying:

**SQL Filtering:**
- Filter by verdict (SHORTLIST/BACKUP/REJECT)
- Filter by seniority level
- Filter by minimum match score
- Filter by required skills
- Filter by domains/industries

**Vector Search (Coming Soon):**
- Semantic search using embeddings
- Natural language queries
- Find similar candidates

**Recruiter Dashboard:**
- Real-time statistics
- Visual candidate cards
- One-click filtering
- Detailed candidate profiles

---

## 🛠️ Setup Guide

### Prerequisites

```powershell
# 1. Python 3.11+ installed
python --version

# 2. Set up Google Gemini API (or other LLM provider)
$env:GOOGLE_API_KEY = "your-api-key-here"

# Alternative providers:
$env:OPENAI_API_KEY = "your-openai-key"
$env:ANTHROPIC_API_KEY = "your-anthropic-key"
# Or use Ollama (FREE, local, no API key needed)
```

### Installation

```powershell
# Install dependencies
pip install -r requirements.txt

# Download spaCy model (required for PII detection)
python -m spacy download en_core_web_sm

# Install Supabase (for database features)
pip install supabase
```

### Supabase Setup

1. **Create a Supabase Project:**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your Project URL and API Key

2. **Set Environment Variables:**
```powershell
$env:SUPABASE_URL = "https://your-project.supabase.co"
$env:SUPABASE_KEY = "your-anon-key"
```

3. **Create Database Table:**
   - Run the setup command to get SQL:
   ```powershell
   python supabase_storage.py --action setup
   ```
   - Copy the SQL output
   - Paste into Supabase SQL Editor
   - Execute to create table with indexes

---

## 💻 Usage

### Option 1: Web Interface (Recommended)

```powershell
# Start the Flask app
python app.py

# Access at http://localhost:5000
```

**Workflow:**
1. **Upload CVs** at `/` (home page)
   - Upload PDF/DOCX files
   - Download anonymized versions

2. **Extract Intelligence** at `/dashboard`
   - Paste job description
   - Click "Extract Intelligence from All CVs"
   - Wait for LLM processing

3. **Search & Filter** at `/dashboard`
   - Filter by verdict, seniority, score, skills
   - View detailed candidate cards
   - Export or share results

---

### Option 2: Command Line Interface

#### Step 1: Redact CVs
```powershell
# Single CV
python universal_pipeline_engine.py path/to/cv.pdf

# Batch process
python universal_pipeline_engine.py path/to/cv/folder/*.pdf
```

#### Step 2: Extract Intelligence
```powershell
# Single CV
python cv_intelligence_extractor.py redacted_output/REDACTED_cv.txt --job-description "Senior Python Developer..."

# Batch extraction
python cv_intelligence_extractor.py redacted_output/REDACTED_*.txt --job-description job_description.txt --provider gemini

# With different LLM providers
python cv_intelligence_extractor.py redacted_output/*.txt --jd jobs/senior_dev.txt --provider openai
python cv_intelligence_extractor.py redacted_output/*.txt --jd jobs/senior_dev.txt --provider anthropic
python cv_intelligence_extractor.py redacted_output/*.txt --jd jobs/senior_dev.txt --provider ollama  # FREE!
```

**Output:**
- Individual JSON files in `llm_analysis/` folder
- Batch summary file with all results
- Automatic Supabase storage (if configured)

#### Step 3: Search & Filter
```powershell
# Get statistics
python supabase_storage.py --action stats

# Search candidates
python supabase_storage.py --action search --verdict SHORTLIST
python supabase_storage.py --action search --verdict SHORTLIST --min-score 80

# Store individual JSON (if not auto-stored)
python supabase_storage.py --action store --input llm_analysis/candidate_intelligence.json
```

---

## 📊 API Endpoints

### Intelligence Extraction

**POST `/api/extract-intelligence`**
```json
{
  "redacted_cv_file": "REDACTED_john_doe.txt",
  "job_description": "Senior Python Developer with 5+ years..."
}
```

**POST `/api/batch-extract`**
```json
{
  "job_description": "Senior Python Developer with 5+ years..."
}
```

### Search & Filter

**POST `/api/search-candidates`**
```json
{
  "verdict": "SHORTLIST",
  "seniority_level": "SENIOR",
  "min_match_score": 75,
  "required_skills": ["Python", "AWS", "Docker"],
  "domains": ["FinTech", "E-commerce"],
  "limit": 50
}
```

**GET `/api/all-candidates?limit=100`**
- Returns all candidates with pagination

**GET `/api/candidate/<candidate_id>`**
- Get specific candidate details

**GET `/api/statistics`**
- Get database statistics (total, shortlisted, backup, rejected, avg score)

---

## 🎯 JSON Output Structure

```json
{
  "candidate_id": "A7F3K9B2",
  "analysis_date": "2026-02-11T10:30:00",
  "skills": {
    "technical_skills": ["Python", "AWS", "Docker", "PostgreSQL"],
    "soft_skills": ["Leadership", "Communication"],
    "tools_technologies": ["Git", "Jenkins", "Terraform"],
    "certifications": ["AWS Certified Solutions Architect"]
  },
  "experience": {
    "total_years": "7-8",
    "seniority_level": "SENIOR",
    "domains": ["FinTech", "E-commerce"],
    "roles": ["Backend Developer", "Tech Lead"]
  },
  "education": {
    "highest_degree": "Master of Science",
    "field_of_study": "Computer Science",
    "education_level": "MASTERS"
  },
  "jd_fitment": {
    "verdict": "SHORTLIST",
    "match_score": 88,
    "reasoning": "Strong match with required Python and AWS skills, proven leadership experience",
    "matched_requirements": [
      "5+ years Python experience",
      "AWS cloud expertise",
      "Team leadership"
    ],
    "missing_requirements": ["Kubernetes experience"],
    "strengths": ["Deep Python expertise", "Cloud architecture"],
    "concerns": ["Limited Kubernetes exposure"]
  },
  "narrative_summary": "Senior technologist with 7+ years specializing in Python backend development and AWS cloud solutions. Proven track record in leading technical teams.",
  "keywords": ["Python", "AWS", "Backend", "Leadership", "FinTech"],
  "source_file": "REDACTED_cv.txt",
  "llm_provider": "gemini"
}
```

---

## 🔍 Filtering & Search Examples

### Web Dashboard
1. **Find all shortlisted senior developers:**
   - Verdict: SHORTLIST
   - Seniority: SENIOR
   - Click Search

2. **Find Python+AWS experts with 80+ match:**
   - Min Score: 80
   - Required Skills: Python, AWS
   - Click Search

3. **Find backup candidates in FinTech:**
   - Verdict: BACKUP
   - (Would need to add domain filter in UI)

### SQL (Direct Supabase Queries)
```sql
-- All shortlisted candidates with 85+ score
SELECT * FROM cv_intelligence 
WHERE verdict = 'SHORTLIST' AND match_score >= 85 
ORDER BY match_score DESC;

-- Find candidates with specific skill
SELECT candidate_id, narrative_summary, match_score 
FROM cv_intelligence 
WHERE technical_skills @> '["Python"]'::jsonb 
ORDER BY match_score DESC;

-- Count by verdict
SELECT verdict, COUNT(*) 
FROM cv_intelligence 
GROUP BY verdict;
```

---

## 🚀 Advanced Features

### Custom LLM Providers

```python
# In cv_intelligence_extractor.py
extractor = CVIntelligenceExtractor(
    api_provider="ollama",  # Use local Ollama
    model="llama3.2"        # Specify model
)
```

### Custom Prompts
Edit the `_create_extraction_prompt()` method in [cv_intelligence_extractor.py](cv_intelligence_extractor.py) to customize extraction logic.

### Vector Search (TODO)
Enable semantic search by:
1. Generate embeddings for `narrative_summary`
2. Store in `embedding` column (VECTOR type)
3. Use pgvector similarity search

```python
# Coming soon in supabase_storage.py
storage.semantic_search("experienced Python developer in healthcare")
```

---

## 📁 Project Structure

```
samplecvs/
├── app.py                          # Flask web app (enhanced with API)
├── universal_pipeline_engine.py    # CV redaction pipeline
├── cv_intelligence_extractor.py    # NEW: LLM-based extraction
├── supabase_storage.py            # NEW: Database operations
├── llm_batch_processor.py         # LLM API wrapper
├── templates/
│   ├── index.html                 # CV upload page
│   └── dashboard.html             # NEW: Recruiter dashboard
├── config/                        # PII patterns, sections, etc.
├── uploads/                       # Uploaded CVs
├── redacted_output/               # Anonymized CVs
├── llm_analysis/                  # NEW: Intelligence JSON files
└── requirements.txt               # Updated with supabase
```

---

## 🎓 Best Practices

### 1. Job Description Quality
- Be specific about required skills
- Include years of experience needed
- Mention key responsibilities
- Add "must-have" vs "nice-to-have" sections

**Good JD Example:**
```
Senior Python Developer (5+ years)

Required:
- 5+ years Python development
- AWS cloud expertise (EC2, S3, Lambda)
- RESTful API design
- Team leadership experience

Nice to have:
- Kubernetes/Docker
- FinTech domain experience
```

### 2. Batch Processing
- Process 10-20 CVs at a time to monitor quality
- Review first few extractions manually
- Adjust prompts if needed
- Use consistent job descriptions

### 3. Cost Management
- **Gemini:** ~$0.50 per 1M tokens (cheapest)
- **OpenAI:** ~$5-15 per 1M tokens
- **Anthropic:** ~$3-15 per 1M tokens
- **Ollama:** FREE (local, but slower)

**Average:** ~2000 tokens per CV = $0.001-0.03 per CV

### 4. Quality Checks
- Review verdicts for first 10 CVs
- Check if match scores seem reasonable
- Verify extracted skills are accurate
- Adjust prompts if hallucinations occur

---

## 🐛 Troubleshooting

### Supabase Connection Issues
```powershell
# Check environment variables
echo $env:SUPABASE_URL
echo $env:SUPABASE_KEY

# Test connection
python supabase_storage.py --action stats
```

### LLM API Errors
```powershell
# Check API key
echo $env:GOOGLE_API_KEY

# Try different provider
$env:LLM_PROVIDER = "ollama"  # FREE alternative
```

### JSON Parse Errors
- LLM occasionally returns malformed JSON
- Check `llm_analysis/` folder for raw responses
- Adjust prompt in `cv_intelligence_extractor.py`
- Use more reliable models (gpt-4o, claude-3.5-sonnet)

### No Candidates Showing in Dashboard
1. Run batch extraction first
2. Check if Supabase is configured
3. Verify table was created
4. Check browser console for errors

---

## 🔐 Security Notes

- **Never commit API keys** to Git
- Use environment variables for all secrets
- Supabase RLS (Row Level Security) is enabled
- Redacted CVs still contain skills/experience (by design)
- Store original CVs securely, separate from redacted ones

---

## 📈 Roadmap

- [x] CV Anonymization
- [x] LLM Intelligence Extraction
- [x] Supabase Storage
- [x] Recruiter Dashboard
- [x] SQL Filtering
- [ ] Vector Search / Semantic Search
- [ ] OpenAI Embeddings Integration
- [ ] Candidate Comparison View
- [ ] Export to CSV/Excel
- [ ] Email Notifications
- [ ] Batch Processing Queue
- [ ] Analytics Dashboard
- [ ] Multi-user Authentication

---

## 💡 Need Help?

**Common Issues:**
1. **"Supabase not configured"** → Set SUPABASE_URL and SUPABASE_KEY env vars
2. **"No candidates found"** → Run batch extraction first
3. **"API key error"** → Set GOOGLE_API_KEY (or other provider key)
4. **"JSON parse error"** → Check LLM response quality, try different model

**Documentation:**
- Main README: [README.md](README.md)
- LLM Setup: [LLM_QUICKSTART.md](LLM_QUICKSTART.md)
- Redaction Guide: [QUICKSTART.md](QUICKSTART.md)

---

## 🎉 Success Checklist

- [x] CVs redacted successfully
- [x] Google API key configured
- [x] Supabase project created
- [x] Database table created
- [x] Job description prepared
- [x] Flask app running
- [x] First batch extracted
- [x] Candidates visible in dashboard
- [x] Filters working
- [x] Ready to hire! 🚀

---

**Built with ❤️ using Python, Flask, Presidio, Google Gemini, and Supabase**
