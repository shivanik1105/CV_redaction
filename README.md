# CV Intelligence System

AI-powered CV anonymization and intelligent matching system. Upload CVs, automatically redact PII, and search candidates using AI-powered semantic matching.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd samplecvs
```

2. **Create virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:

```env
# Required: Supabase Database
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Required: LLM API Key (choose one or more)
GROQ_API_KEY=your_groq_api_key
# OR
OPENAI_API_KEY=your_openai_api_key
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key
# OR
GEMINI_API_KEY=your_gemini_api_key

# Optional: Redis (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
```

**How to get API keys:**
- **Supabase**: https://supabase.com → Create project → Settings → API
- **Groq** (Free): https://console.groq.com/keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **Gemini**: https://aistudio.google.com/app/apikey

5. **Run the application**
```bash
python app.py
```

6. **Open in browser**
```
http://127.0.0.1:5000
```

---

## 📖 User Guide

### How to Use the Application

#### 1. Upload CV

**Purpose**: Upload a CV, automatically redact PII, and extract intelligence

**Steps**:
1. Go to **"Upload and Process Single CV"** tab
2. Click **"Choose file"** and select a PDF or DOCX CV
3. **(Optional)** Paste a job description for JD-specific matching
4. **Important**: Enter your LLM API key in the **"LLM API Key"** field
   - Get a free key from https://console.groq.com/keys
5. **(Optional)** Select LLM provider (Groq, OpenAI, etc.)
6. Click **"Upload CV"**
7. Wait for processing (30-60 seconds)
8. Download results:
   - **"Download Redacted Output"** - Text file with `[REDACTED]` markers
   - **"Download Masked PDF"** - PDF with visual black boxes over PII

**What happens**:
- ✅ Extracts text from CV
- ✅ Detects and redacts PII (names, emails, phones, addresses)
- ✅ Creates masked PDF with black boxes
- ✅ Extracts intelligence (skills, experience, domain)
- ✅ Stores in database for searching

**Important Notes**:
- You **must** provide your own LLM API key
- The server does **not** use its own API key
- Your API key is only used for this request and not stored
- Processing takes 30-60 seconds for first upload (loading models)

---

#### 2. Search & Filter CVs

**Purpose**: Search for candidates using job descriptions or filters

**Steps**:

**Option A: Semantic Search (with Job Description)**
1. Go to **"Search & Filter CVs"** tab
2. Paste a job description in the **"Job Description"** field
3. Click **"Search"**
4. Results show candidates ranked by match percentage
5. Click **"Download all redacted CVs"** to get top matches

**Option B: Filter Search (without Job Description)**
1. Go to **"Search & Filter CVs"** tab
2. Leave job description empty
3. Use filters:
   - **Seniority Level**: Entry, Mid, Senior, Lead, Executive
   - **Min Match Score**: 0-100%
   - **Min Confidence**: 0-100%
   - **Years Experience**: Min and Max
   - **Required Skills**: Comma-separated (e.g., "Python, AWS, Docker")
   - **Domain**: e.g., "Cloud Computing", "Web Development"
4. Click **"Search"**
5. Results show all matching candidates

**Understanding Results**:
- **Match %**: How well candidate matches the JD (only with JD search)
- **Confidence**: How confident the AI is about the extraction
- **Experience**: Years of experience and seniority level
- **Domain**: Primary domain/industry
- **Skills**: Top technical skills
- **Why selected**: Reason for recommendation (with JD search)

**Actions**:
- **Original CV**: Download the original CV file
- **Download all redacted CVs**: Bulk download top matches (with JD search)

---

### 3. View Candidate Details

**In search results**:
- Each candidate card shows:
  - Anonymized ID (e.g., CAND_ABC123)
  - Match percentage (if JD provided)
  - Confidence score
  - Years of experience
  - Seniority level
  - Primary domain
  - Top 5 skills
  - Matched keywords (if JD provided)
  - Why selected (if JD provided)

**Download Options**:
- **Original CV**: Download the original uploaded file
- **Redacted CVs (bulk)**: Download multiple CVs as ZIP

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SUPABASE_URL` | Yes | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Yes | Supabase anon key | `eyJhbGc...` |
| `GROQ_API_KEY` | Yes* | Groq API key | `gsk_...` |
| `OPENAI_API_KEY` | No | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | No | Anthropic API key | `sk-ant-...` |
| `GEMINI_API_KEY` | No | Google Gemini key | `AIza...` |
| `REDIS_HOST` | No | Redis host | `localhost` |
| `REDIS_PORT` | No | Redis port | `6379` |

*At least one LLM provider key is required

---

## 📁 Project Structure

```
samplecvs/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
├── config/                        # Configuration files
│   ├── pii_patterns.json         # PII detection patterns
│   ├── sections.json             # CV section patterns
│   └── text_healing.json         # Text cleanup rules
├── templates/                     # HTML templates
│   └── index_new.html            # Main UI
├── uploads/                       # Uploaded CV files
├── final_output/                  # Processed output files
└── archive/                       # Archive folder (optional)
    └── samples/                   # Sample CVs
```

---

## 🎯 Features

### 1. Automatic PII Redaction
- ✅ Names
- ✅ Email addresses
- ✅ Phone numbers
- ✅ Physical addresses
- ✅ Social media links (LinkedIn, GitHub, etc.)
- ✅ URLs

### 2. Visual PDF Masking
- ✅ Black boxes over PII in PDFs
- ✅ Preserves original formatting
- ✅ Professional appearance

### 3. AI-Powered Intelligence Extraction
- ✅ Years of experience
- ✅ Seniority level
- ✅ Technical skills
- ✅ Primary domain
- ✅ Certifications
- ✅ Education
- ✅ Key strengths

### 4. Semantic Search
- ✅ Match candidates to job descriptions
- ✅ Keyword-based matching
- ✅ Skill coverage analysis
- ✅ Ranked results

### 5. Advanced Filtering
- ✅ Filter by seniority
- ✅ Filter by experience years
- ✅ Filter by skills
- ✅ Filter by domain
- ✅ Filter by confidence score

---

## 🐛 Troubleshooting

### Application won't start

**Error**: `ModuleNotFoundError`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error**: `Supabase connection failed`
```bash
# Solution: Check .env file
# Make sure SUPABASE_URL and SUPABASE_KEY are set correctly
```

### Upload fails

**Error**: "LLM API key is required"
```
Solution: Enter your API key in the "LLM API Key" field before uploading
Get a free key from: https://console.groq.com/keys
```

**Error**: "Job failed: Unknown error"
```
Solution: 
1. Check server logs for details
2. Make sure you entered a valid API key
3. Try restarting the application
```

### Search returns no results

**Issue**: No CVs found
```
Solution:
1. Upload some CVs first
2. Wait for processing to complete
3. Try searching again
```

**Issue**: "503 Service Unavailable"
```
Solution:
1. Check Supabase connection
2. Restart the application
3. Check .env file has correct credentials
```

### Download fails

**Error**: "Original CV file not found"
```
Solution:
This CV's file is missing from the server.
Options:
1. Re-upload the CV
2. The CV will still show in search with metadata
```

---

## 📊 System Requirements

### Minimum:
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Storage**: 5 GB
- **Python**: 3.10+

### Recommended:
- **CPU**: 4 cores
- **RAM**: 4 GB
- **Storage**: 10 GB
- **Python**: 3.11+

---

## 🔒 Privacy & Security

### Data Privacy:
- ✅ All PII is automatically redacted
- ✅ CVs are anonymized with random IDs
- ✅ Original files stored securely
- ✅ User API keys not stored on server

### Security Best Practices:
- ✅ Use environment variables for secrets
- ✅ Never commit `.env` file to git
- ✅ Use HTTPS in production
- ✅ Regularly update dependencies

---

## 📝 License

[Add your license here]

---

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the user guide
3. Check application logs
4. Contact support

---

## 🎉 Quick Start Summary

```bash
# 1. Install
git clone <repo>
cd samplecvs
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure
# Create .env file with Supabase and LLM API keys

# 3. Run
python app.py

# 4. Use
# Open http://127.0.0.1:5000
# Upload CVs with your API key
# Search and filter candidates
```

**That's it! You're ready to use the CV Intelligence System!** 🚀
