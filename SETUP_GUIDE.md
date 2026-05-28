# Setup Guide - For Developers

Quick setup guide for running the CV Intelligence System locally.

---

## ⚡ Quick Setup (5 minutes)

### 1. Prerequisites

Install these first:
- **Python 3.10+**: https://www.python.org/downloads/
- **Git**: https://git-scm.com/downloads/
- **pip**: Comes with Python

### 2. Clone & Setup

```bash
# Clone the repository
git clone <repository-url>
cd samplecvs

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file in project root:

```env
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# LLM Provider (Required - choose at least one)
GROQ_API_KEY=gsk_your_groq_api_key
OPENAI_API_KEY=sk-your_openai_key
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
GEMINI_API_KEY=your_gemini_key

# Optional
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Get API Keys**:
- **Supabase**: https://supabase.com → Create project → Settings → API
- **Groq** (Free): https://console.groq.com/keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **Gemini**: https://aistudio.google.com/app/apikey

### 4. Setup Supabase Database

Run this SQL in Supabase SQL Editor:

```sql
-- Create cv_intelligence table
CREATE TABLE cv_intelligence (
    anonymized_id TEXT PRIMARY KEY,
    years_of_experience NUMERIC,
    seniority_level TEXT,
    primary_domain TEXT,
    core_technical_skills TEXT[],
    secondary_technical_skills TEXT[],
    confidence_score INTEGER,
    cleaned_text TEXT,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create cv_filename_mapping table
CREATE TABLE cv_filename_mapping (
    anonymized_id TEXT PRIMARY KEY REFERENCES cv_intelligence(anonymized_id) ON DELETE CASCADE,
    original_filename TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_cv_intelligence_domain ON cv_intelligence(primary_domain);
CREATE INDEX idx_cv_intelligence_seniority ON cv_intelligence(seniority_level);
CREATE INDEX idx_cv_intelligence_created ON cv_intelligence(created_at DESC);
```

### 5. Run the Application

```bash
python app.py
```

Open browser: http://127.0.0.1:5000

---

## 📁 Project Structure

```
samplecvs/
├── app.py                          # Main Flask app
├── requirements.txt                # Dependencies
├── .env                           # Environment variables (create this)
├── .gitignore                     # Git ignore file
├── README.md                      # Project documentation
├── USER_GUIDE.md                  # User guide
├── SETUP_GUIDE.md                 # This file
│
├── config/                        # Configuration files
│   ├── pii_patterns.json         # PII detection patterns
│   ├── sections.json             # CV section patterns
│   ├── protected_terms.json      # Terms to protect
│   ├── text_healing.json         # Text cleanup rules
│   └── locations.json            # Location patterns
│
├── templates/                     # HTML templates
│   └── index_new.html            # Main UI
│
├── uploads/                       # Uploaded CV files (created automatically)
├── final_output/                  # Processed files (created automatically)
├── debug_output/                  # Debug files (created automatically)
│
└── archive/                       # Optional: Sample CVs
    └── samples/                   # Put sample CVs here
```

---

## 🔧 Configuration Details

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_KEY` | Yes | - | Supabase anon key |
| `GROQ_API_KEY` | Yes* | - | Groq API key |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `GEMINI_API_KEY` | No | - | Google Gemini key |
| `REDIS_HOST` | No | localhost | Redis host |
| `REDIS_PORT` | No | 6379 | Redis port |
| `UPLOAD_WORKER_COUNT` | No | 2 | Background workers |
| `LLM_MAX_CONCURRENT_REQUESTS` | No | 3 | Max concurrent LLM calls |

*At least one LLM provider key required

### Config Files

**`config/pii_patterns.json`**
- Defines patterns for detecting PII (emails, phones, etc.)
- Customize to add more patterns

**`config/sections.json`**
- Defines CV section headers
- Used for intelligent text extraction

**`config/protected_terms.json`**
- Terms that should NOT be redacted
- e.g., company names, technologies

**`config/text_healing.json`**
- Rules for cleaning up extracted text
- Fixes common OCR/extraction issues

---

## 🧪 Testing

### Test Upload:
1. Go to http://127.0.0.1:5000
2. Upload a sample CV
3. Check `uploads/` folder for original
4. Check `final_output/` for redacted version
5. Check Supabase database for entry

### Test Search:
1. Upload a few CVs first
2. Go to "Search & Filter CVs"
3. Try searching with a job description
4. Try filtering without JD

### Test Download:
1. Search for CVs
2. Click "Original CV" on a result
3. Should download the file
4. Check for visual black boxes in masked PDF

---

## 🐛 Common Issues

### Issue: `ModuleNotFoundError: No module named 'fitz'`
```bash
# Solution: Install PyMuPDF
pip install PyMuPDF
```

### Issue: `Supabase connection failed`
```bash
# Solution: Check .env file
# Make sure SUPABASE_URL and SUPABASE_KEY are correct
# Test connection:
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('Connected!')"
```

### Issue: `spaCy model not found`
```bash
# Solution: Download spaCy model
python -m spacy download en_core_web_sm
```

### Issue: Port 5000 already in use
```bash
# Solution: Kill the process or use different port
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:5000 | xargs kill -9

# Or change port in app.py:
# app.run(port=5001)
```

### Issue: Upload fails with "Unknown error"
```bash
# Solution: Check logs in terminal
# Common causes:
# 1. Invalid API key
# 2. Corrupted CV file
# 3. Missing dependencies
# 4. Supabase connection issue
```

---

## 📦 Dependencies

### Core:
- **Flask**: Web framework
- **Supabase**: Database and storage
- **PyMuPDF**: PDF manipulation
- **spaCy**: NLP for PII detection

### LLM Providers:
- **Groq**: Fast inference
- **OpenAI**: GPT models
- **Anthropic**: Claude models
- **Google**: Gemini models

### Processing:
- **pdfplumber**: PDF text extraction
- **python-docx**: DOCX processing
- **Pillow**: Image processing
- **reportlab**: PDF generation

### AI/ML:
- **sentence-transformers**: Embeddings
- **presidio**: PII detection
- **numpy**: Numerical operations

---

## 🚀 Development

### Running in Development Mode:
```bash
# Enable debug mode
export FLASK_ENV=development  # Mac/Linux
set FLASK_ENV=development     # Windows

python app.py
```

### Running Tests:
```bash
# Test Supabase connection
python test_supabase_connection.py

# Test upload backend
python test_upload_api_key.py

# Check database schema
python check_database_schema.py
```

### Useful Scripts:
- `restore_cvs_from_archive.py` - Copy CVs from archive to uploads
- `fix_everything.py` - Clean database (remove CVs without files)
- `download_missing_cvs.py` - Download CVs from Supabase storage
- `sync_cvs_with_database.py` - Check database vs files sync

---

## 📊 Performance

### Local Development:
- **First upload**: 30-60 seconds (loading models)
- **Subsequent uploads**: 15-30 seconds
- **Search**: 1-3 seconds
- **Download**: Instant

### Memory Usage:
- **Idle**: ~500 MB
- **Processing**: ~1-2 GB
- **With models loaded**: ~2-3 GB

### Optimization Tips:
1. Use Redis for caching
2. Reduce `UPLOAD_WORKER_COUNT` if low memory
3. Use Groq for faster LLM inference
4. Enable `--preload` in gunicorn for production

---

## 🔒 Security

### Best Practices:
1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Contains sensitive keys

2. **Use environment variables**
   - Don't hardcode API keys
   - Use `.env` for local, Render/Heroku env vars for production

3. **Validate uploads**
   - Only allow PDF/DOCX
   - Check file size limits
   - Scan for malware in production

4. **Secure Supabase**
   - Use Row Level Security (RLS)
   - Limit API key permissions
   - Enable 2FA on Supabase account

---

## 📝 Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
git add .
git commit -m "Add my feature"

# Push to remote
git push origin feature/my-feature

# Create pull request on GitHub
```

### Important Files to NOT Commit:
- `.env` (secrets)
- `uploads/` (user data)
- `final_output/` (processed files)
- `.venv/` (virtual environment)
- `__pycache__/` (Python cache)

---

## 🎯 Quick Commands Reference

```bash
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run
python app.py

# Test
python test_supabase_connection.py

# Clean database
python fix_everything.py

# Restore CVs
python restore_cvs_from_archive.py

# Deploy to Render
git push origin main
```

---

**You're all set! Start developing!** 🚀

For user instructions, see `USER_GUIDE.md`
For deployment, see `RENDER_DEPLOYMENT_GUIDE.md`
