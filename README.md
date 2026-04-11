# CV Intelligence System

Complete recruitment intelligence platform with CV redaction, intelligence extraction, and candidate search.

## 🎯 Features

- **CV Redaction**: Automatic PII removal (names, emails, phones, addresses)
- **Intelligence Extraction**: Extract skills, experience, domain expertise using LLM
- **Job Matching**: Match CVs against job descriptions with scoring
- **Candidate Search**: Advanced search and filtering capabilities
- **Multi-column Support**: Handles complex 2-column CV layouts
- **Cloud Storage**: Supabase integration with vector search
- **Local Fallback**: Works without cloud (JSON-based storage)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/cv-intelligence-system.git
   cd cv-intelligence-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   python app_launcher.py
   ```

6. **Access the application**
   - Open browser: http://localhost:5000

## 🔧 Configuration

### Required Environment Variables

```env
# LLM Provider (for intelligence extraction)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your-groq-api-key-here

# Supabase (optional - for cloud storage)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
```

### Get API Keys

- **Groq API** (Free): https://console.groq.com/keys
  - 6,000 requests/day
  - 30 requests/minute
  
- **Supabase** (Free): https://supabase.com
  - 500MB database
  - 1GB file storage

## 📦 Deployment

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/cv-intelligence-system.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to https://render.com
   - New + → Web Service
   - Connect your GitHub repository
   - Configure:
     - Build Command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
     - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - Add environment variables (GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY)
   - Deploy!

3. **Access your app**
   - URL: `https://your-app.onrender.com`

## 📊 System Architecture

```
CV Upload → Extraction → Redaction → Intelligence → Storage → Search
```

### Components

- **universal_pipeline_engine.py**: CV extraction and redaction
- **cv_intelligence_extractor.py**: LLM-based intelligence extraction
- **supabase_storage.py**: Cloud storage with vector search
- **app.py**: Flask web application
- **vector_search.py**: Semantic search capabilities

## 🧪 Testing

### Test CV Redaction
```bash
python app_launcher.py --test "path/to/cv.pdf"
```

### Test Results
- Tested on 68 CVs
- 85.3% success rate
- Multi-column support verified

## 📁 Project Structure

```
cv-intelligence-system/
├── app.py                          # Main Flask application
├── app_launcher.py                 # Application launcher
├── universal_pipeline_engine.py    # CV processing engine
├── cv_intelligence_extractor.py    # LLM intelligence extraction
├── supabase_storage.py            # Cloud storage
├── vector_search.py               # Semantic search
├── config/                        # Configuration files
│   ├── pii_patterns.json
│   ├── protected_terms.json
│   ├── locations.json
│   └── sections.json
├── templates/                     # HTML templates
├── static/                        # CSS/JS assets
├── requirements.txt               # Python dependencies
├── render.yaml                    # Render deployment config
└── README.md                      # This file
```

## 🔍 Features in Detail

### CV Redaction
- Automatic PII detection and removal
- Supports PDF and DOCX formats
- Multi-column layout support
- Section-wise processing

### Intelligence Extraction
- Skills extraction (core, secondary, frameworks)
- Years of experience calculation
- Seniority level detection
- Domain expertise identification
- Leadership indicators

### Job Matching
- Match score calculation (0-100)
- Verdict generation (SHORTLIST/BACKUP/REJECT)
- Matched requirements identification
- Missing requirements analysis

### Candidate Search
- Quick search by name/skills
- Advanced filters:
  - Verdict
  - Seniority level
  - Match score range
  - Years of experience
  - Required skills
  - Domain expertise

## 💰 Cost

### Free Tier
- Render Free: $0 (sleeps after 15 min)
- Supabase Free: $0 (500MB database)
- Groq Free: $0 (6000 req/day)
- **Total: $0/month**

### Production
- Render Starter: $7/month (always on)
- Supabase Free: $0
- Groq Free: $0
- **Total: $7/month**

## 🛠️ Tech Stack

- **Backend**: Flask, Python 3.11+
- **PDF Processing**: PyMuPDF, pdfplumber
- **PII Detection**: Presidio, spaCy
- **LLM**: Groq, OpenAI, Anthropic, Gemini, Ollama
- **Database**: Supabase (PostgreSQL + pgvector)
- **Embeddings**: sentence-transformers
- **Deployment**: Render, Gunicorn

## 📝 License

Proprietary - All rights reserved

## 🤝 Support

For issues or questions, check the documentation:
- `COMPLETE_USER_GUIDE.md` - Complete usage guide
- `SYSTEM_ARCHITECTURE_VISUAL.md` - System architecture
- `RENDER_DEPLOYMENT_GUIDE.md` - Deployment guide

## ✅ Status

- ✅ Multi-column CV extraction (fixed)
- ✅ PII redaction working
- ✅ Intelligence extraction working
- ✅ Job matching working
- ✅ Candidate search working
- ✅ Supabase integration working
- ✅ Local JSON fallback working
- ✅ Production ready

## 🎉 Ready to Use!

The system is fully functional and ready for deployment. Follow the Quick Start guide to get started.
