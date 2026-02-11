# 🎯 CV Intelligence System - Quick Reference

## 🚀 Start the System

```powershell
# Set your API key (pick one)
$env:GOOGLE_API_KEY = "your-gemini-api-key"      # Recommended
# OR
$env:OPENAI_API_KEY = "your-openai-api-key"
# OR use Ollama (free, no key needed)

# Set Supabase credentials (optional, for database features)
$env:SUPABASE_URL = "https://your-project.supabase.co"
$env:SUPABASE_KEY = "your-anon-key"

# Start the web app
python app.py

# Access at: http://localhost:5000
```

## 📋 Typical Workflow

### 1. Upload & Anonymize CVs
1. Go to http://localhost:5000
2. Upload PDF/DOCX files
3. Download anonymized versions
4. Files saved to `redacted_output/`

### 2. Extract Intelligence
1. Go to http://localhost:5000/dashboard
2. Paste your job description in the text area
3. Click "Extract Intelligence from All CVs"
4. Wait for LLM processing (30-60 seconds per CV)
5. Intelligence saved to `llm_analysis/` + Supabase

### 3. Search & Filter
1. Use filters on dashboard:
   - Verdict: SHORTLIST / BACKUP / REJECT
   - Seniority: ENTRY / MID / SENIOR / LEAD / EXECUTIVE
   - Min Score: 0-100
   - Required Skills: Python, AWS, Docker, etc.
2. Click "Search"
3. Review candidate cards
4. Click candidate for full details

## 🎯 What You Get

Each candidate analyzed produces:

- **Candidate ID:** Unique identifier
- **Skills:** Technical, soft, tools, certifications
- **Experience:** Years, level, domains, roles
- **Education:** Degree, field, level
- **Verdict:** SHORTLIST / BACKUP / REJECT
- **Match Score:** 0-100
- **Detailed Reasoning:** Why this verdict
- **Matched/Missing Requirements:** Breakdown
- **Strengths & Concerns:** Key points
- **Professional Summary:** Clean narrative
- **Keywords:** For search optimization

## 📊 API Quick Reference

```powershell
# Extract intelligence from one CV
curl -X POST http://localhost:5000/api/extract-intelligence \
  -H "Content-Type: application/json" \
  -d '{"redacted_cv_file": "REDACTED_john.txt", "job_description": "Senior Python Dev..."}'

# Batch extract all CVs
curl -X POST http://localhost:5000/api/batch-extract \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Senior Python Dev..."}'

# Search candidates
curl -X POST http://localhost:5000/api/search-candidates \
  -H "Content-Type: application/json" \
  -d '{"verdict": "SHORTLIST", "min_match_score": 80}'

# Get all candidates
curl http://localhost:5000/api/all-candidates

# Get statistics
curl http://localhost:5000/api/statistics
```

## 💻 Command Line Usage

```powershell
# Extract intelligence from CVs
python cv_intelligence_extractor.py redacted_output/REDACTED_*.txt \
  --job-description "Senior Python Developer with 5+ years..." \
  --provider gemini

# Or use a JD file
python cv_intelligence_extractor.py redacted_output/*.txt \
  --jd job_descriptions/senior_dev.txt \
  --provider gemini

# Supabase operations
python supabase_storage.py --action stats
python supabase_storage.py --action search --verdict SHORTLIST --min-score 80
```

## 🔧 Environment Variables

```powershell
# LLM Provider (choose one)
$env:GOOGLE_API_KEY = "AIza..."        # Google Gemini (recommended)
$env:OPENAI_API_KEY = "sk-..."         # OpenAI
$env:ANTHROPIC_API_KEY = "sk-ant-..."  # Anthropic Claude
$env:LLM_PROVIDER = "ollama"           # Use Ollama (free, local)

# Supabase (optional, for database)
$env:SUPABASE_URL = "https://xxx.supabase.co"
$env:SUPABASE_KEY = "eyJhb..."

# Flask (optional)
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
```

## 📁 File Locations

```
uploads/              → Original uploaded CVs
redacted_output/      → Anonymized CVs (REDACTED_*.txt)
llm_analysis/         → Intelligence JSON files
config/               → PII patterns, sections
templates/            → HTML templates
static/               → CSS, JavaScript
```

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "No candidates found" | Run batch extraction first |
| "Supabase not configured" | Set SUPABASE_URL and SUPABASE_KEY |
| "API key error" | Set GOOGLE_API_KEY or other provider key |
| "JSON parse error" | LLM returned invalid JSON, check logs |
| Port 5000 in use | Change port: `app.run(port=5001)` |

## 💡 Tips

- **Job Description Quality:** Be specific! List required skills clearly
- **Batch Size:** Process 10-20 CVs at a time for better monitoring
- **Cost:** Gemini is cheapest (~$0.001 per CV), Ollama is FREE
- **Accuracy:** GPT-4o and Claude have best accuracy for structured extraction
- **Speed:** Gemini is fastest, GPT-3.5 is good balance

## 📚 Full Documentation

- **Complete Guide:** [INTELLIGENCE_SYSTEM_GUIDE.md](INTELLIGENCE_SYSTEM_GUIDE.md)
- **LLM Setup:** [LLM_QUICKSTART.md](LLM_QUICKSTART.md)
- **Basic Redaction:** [QUICKSTART.md](QUICKSTART.md)
- **Main README:** [README.md](README.md)

## ⚡ One-Line Starters

```powershell
# Setup everything
.\setup_intelligence_system.ps1

# Start web app
python app.py

# Process CVs + extract intelligence in one go
python cv_intelligence_extractor.py redacted_output/REDACTED_*.txt --jd job.txt --provider gemini
```

---

**Need Help?** Check [INTELLIGENCE_SYSTEM_GUIDE.md](INTELLIGENCE_SYSTEM_GUIDE.md) for detailed instructions!
