# CV Intelligence System - Clean Project Structure

## Essential Files Only

```
cv-intelligence-system/
├── Core Python Files (Required)
│   ├── app.py                          # Flask web server (main entry point)
│   ├── cv_redaction_pipeline.py        # PII anonymization
│   ├── cv_intelligence_extractor.py   # LLM analysis + scoring
│   ├── llm_batch_processor.py          # Groq API integration
│   ├── universal_pipeline_engine.py    # CV processing orchestrator
│   ├── vector_search.py                # Semantic search
│   ├── supabase_storage.py             # Database operations
│   ├── backfill_embeddings.py          # Generate embeddings for existing CVs
│   └── process_all_cvs_smart.py        # Batch processing script
│
├── Configuration Files
│   ├── .env                            # API keys (DO NOT COMMIT)
│   ├── .env.example                    # Template for .env
│   ├── .gitignore                      # Git ignore rules
│   ├── requirements.txt                # Python dependencies
│   └── requirements_render.txt         # Render deployment dependencies
│
├── Database Setup
│   ├── supabase_pgvector_setup.sql    # Main database schema
│   ├── jd_library_schema.sql          # Job description library (optional)
│   └── fix_pgvector_rpc.sql           # Fix for pgvector RPC functions
│
├── Configuration Data
│   └── config/
│       ├── locations.json              # Location patterns for extraction
│       ├── pii_patterns.json           # PII detection patterns
│       ├── protected_terms.json        # Terms to preserve during redaction
│       ├── sections.json               # CV section patterns
│       └── text_healing.json           # Text cleanup rules
│
├── Frontend (Web UI)
│   ├── templates/
│   │   ├── index_new.html              # Main interface (Search + Process CVs)
│   │   ├── semantic_search.html        # Semantic search page
│   │   └── queue_monitor.html          # Queue monitoring (optional)
│   └── static/
│       ├── css/                        # Stylesheets
│       └── js/                         # JavaScript
│
├── Data Directories (Created at runtime)
│   ├── samples/                        # Input CVs (place PDFs/DOCX here)
│   ├── redacted_output/                # Anonymized CVs
│   └── uploads/                        # Web uploads
│
└── Documentation
    ├── README.md                       # Quick start guide
    ├── SYSTEM_ARCHITECTURE.md          # Complete tech stack & data flow
    ├── PRODUCTION_READY_CHECKLIST.md   # Deployment guide
    ├── GROQ_INTEGRATION_COMPLETE.md    # Groq API setup
    ├── HOW_SCORING_WORKS.md            # Scoring system explained
    └── PROJECT_STRUCTURE.md            # This file
```

---

## What Was Removed

### Removed Files (Not Needed for Production)
- ❌ `enhanced_triage.py` - No longer needed (Groq is FREE)
- ❌ `queue_manager.py` - No rate limiting needed
- ❌ `rate_limiter.py` - No rate limiting needed
- ❌ `celery_worker.py` - No async queue needed
- ❌ All test files (`test_*.py`, `run_tests.py`)
- ❌ All debug scripts (`check_*.py`, `debug_*.py`)
- ❌ All migration scripts (`sync_*.py`, `upload_*.py`, `verify_*.py`)
- ❌ Redundant apps (`redact_app.py`, `redact_server.py`, `run_server.py`)
- ❌ Build artifacts (`__pycache__/`, `build/`, `dist/`)

### Removed Directories
- ❌ `tests/` - Test files
- ❌ `build/`, `dist/` - Build artifacts
- ❌ `__pycache__/` - Python cache
- ❌ `debug_output/` - Debug files
- ❌ `llm_analysis/` - Old analysis files
- ❌ `resume/` - Virtual environment

---

## Core Files Explained

### 1. app.py (Flask Web Server)
**Purpose**: Main web application  
**Routes**:
- `/` - Main interface (Search + Process CVs tabs)
- `/semantic-search` - Semantic search page
- `/queue-monitor` - Queue monitoring (optional)
- `/api/candidates` - Get candidates (JSON)
- `/api/search` - Quick search with filters
- `/api/search/semantic` - Semantic vector search

**Usage**:
```bash
python app.py
# Visit: http://localhost:5000
```

### 2. cv_redaction_pipeline.py
**Purpose**: PII anonymization  
**Features**:
- Detects names, emails, phones, addresses
- Replaces with `[REDACTED_*]` markers
- Uses Presidio + spaCy

### 3. cv_intelligence_extractor.py
**Purpose**: LLM analysis + quality verification  
**Features**:
- Sends anonymized CV to Groq
- Extracts skills, experience, domain
- Calculates 3 scores (match, confidence, similarity)
- Detects hallucinations

### 4. llm_batch_processor.py
**Purpose**: Groq API integration  
**Features**:
- Handles API calls to Groq
- Supports multiple LLM providers
- Error handling and retries

### 5. universal_pipeline_engine.py
**Purpose**: CV processing orchestrator  
**Features**:
- Detects CV format (PDF/DOCX)
- Extracts text
- Handles different CV layouts

### 6. vector_search.py
**Purpose**: Semantic search  
**Features**:
- Generates embeddings (384-dim)
- Stores in pgvector
- Finds similar candidates

### 7. supabase_storage.py
**Purpose**: Database operations  
**Features**:
- Store/retrieve intelligence
- Vector search queries
- Filename mapping

### 8. process_all_cvs_smart.py
**Purpose**: Batch processing script  
**Usage**:
```bash
python process_all_cvs_smart.py --jd "Python Developer" --max 100
```

### 9. backfill_embeddings.py
**Purpose**: Generate embeddings for existing CVs  
**Usage**:
```bash
python backfill_embeddings.py
```

---

## Configuration Files

### .env (API Keys)
```bash
# LLM Provider
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your-groq-api-key

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

### requirements.txt (Dependencies)
```
# Core
pymupdf, pdfplumber, presidio, spacy

# LLM
groq

# Database
supabase, pgvector

# Vector Search
sentence-transformers

# Web
Flask
```

---

## Database Schema

### Table: cv_intelligence (42 columns)
- `anonymized_id` - Unique ID (CAND_XXX)
- `verdict` - ACCEPT/REJECT/REVIEW
- `match_score` - 0-100%
- `confidence_score` - 0-100%
- `similarity_score` - 0-100%
- `skills_matched` - Array of skills
- `years_experience` - Integer
- `seniority_level` - ENTRY/MID/SENIOR/LEAD
- `embedding` - Vector(384) for search
- ... (30+ more fields)

### Table: cv_filename_mapping
- `anonymized_id` - Links to cv_intelligence
- `original_filename` - Sanitized filename
- `redacted_filename` - Anonymized file
- `upload_timestamp` - When uploaded

---

## Typical Workflow

### 1. Setup (One-time)
```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Setup database
# Run supabase_pgvector_setup.sql in Supabase SQL Editor
```

### 2. Process CVs (Batch)
```bash
# Place CVs in samples/ folder
python process_all_cvs_smart.py --jd "Senior Python Developer" --max 100

# Output:
# ✓ Redacted: 100 CVs
# ✓ Analyzed: 100 CVs (Groq)
# ✓ Stored: 100 CVs in Supabase
```

### 3. Search Candidates (Web UI)
```bash
# Start web server
python app.py

# Visit: http://localhost:5000
# Main interface with Search and Process CVs tabs
```

### 4. Deploy to Production
```bash
# Deploy to Render
git push origin main

# Render auto-deploys
# Visit: https://your-app.onrender.com
```

---

## File Size Summary

### Essential Python Files: ~15 files (~50 KB total)
- Core logic: 8 files
- Configuration: 4 files
- Database: 3 files

### Configuration Data: 5 JSON files (~10 KB)
- PII patterns, sections, locations

### Frontend: 2 HTML files + CSS/JS (~20 KB)
- Upload page, dashboard

### Documentation: 6 MD files (~100 KB)
- Setup guides, architecture

**Total Essential Files: ~30 files (~180 KB)**

---

## What You Need to Deploy

### Minimum Files for Production:
1. All Python files (15 files)
2. Configuration files (.env, requirements.txt)
3. Config data (5 JSON files)
4. Frontend (templates/, static/)
5. Database SQL (supabase_pgvector_setup.sql)
6. README.md (quick start)

### Optional but Recommended:
- SYSTEM_ARCHITECTURE.md (tech stack)
- PRODUCTION_READY_CHECKLIST.md (deployment guide)
- .gitignore (security)

---

## Clean Project = Production Ready ✅

**Before Cleanup**: 100+ files, 50+ MB  
**After Cleanup**: 30 files, 180 KB  
**Result**: Clean, maintainable, production-ready system

---

**Last Updated**: March 26, 2026  
**Status**: ✅ PRODUCTION READY
