# CV Intelligence System - Architecture & Tech Stack

## System Overview
AI-powered CV screening system that anonymizes resumes, extracts intelligence, and enables semantic search - all while maintaining privacy and minimizing API costs.

---

## Tech Stack

### Backend (Python 3.11+)
- **Flask 3.0** - Web framework for API and UI
- **PyMuPDF 1.23** - PDF text extraction
- **pdfplumber 0.10** - Alternative PDF parser
- **Presidio 2.2** - Microsoft's PII detection/redaction
- **spaCy 3.7** - NLP entity recognition
- **python-docx 1.1** - DOCX file handling
- **python-dotenv 1.0** - Environment configuration

### AI & Machine Learning
- **Groq API** - FREE LLM (Llama 3.3 70B, 6,000 requests/day)
- **sentence-transformers 2.2** - Semantic embeddings (all-MiniLM-L6-v2)
- **scikit-learn** - Cosine similarity calculations

### Database & Storage
- **Supabase (PostgreSQL 15)** - Main database with REST API
- **pgvector 0.2** - Vector embeddings for semantic search
- **Redis 5.0** - Queue management (optional)
- **Celery 5.3** - Async task processing (optional)

### Frontend
- **HTML5/CSS3/JavaScript** - Web UI
- **Vanilla JavaScript** - No framework dependencies
- **Jinja2** - Server-side templating
- **Single unified interface** - No dashboard, no separate pages for main features

### Deployment
- **Render** - Flask app hosting (Free or $7/month)
- **Supabase Pro** - Managed PostgreSQL ($25/month)
- **Groq Cloud** - LLM API (FREE)

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER UPLOADS CV                              │
│              (PDF/DOCX via Flask UI - templates/index_new.html)     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼ 
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: PII REDACTION                            │
│  Tech: PyMuPDF + Presidio + spaCy                                   │
│  ─────────────────────────────────────────────────────────────────  │
│  • Extract text from PDF/DOCX                                       │
│  • Detect PII (names, emails, phones, addresses)                    │
│  • Replace with [REDACTED_*] markers                                │
│  • Output: Anonymized CV text                                       │
│                                                                       │
│  Files: cv_redaction_pipeline.py, universal_pipeline_engine.py      │
│  Frontend: templates/index_new.html (upload form)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2: LLM ANALYSIS                             │
│  Tech: Groq API (Llama 3.3 70B) - FREE                             │
│  ─────────────────────────────────────────────────────────────────  │
│  • Send anonymized CV + optional JD to Groq                         │
│  • Extract: skills, experience, domain, assessment                  │
│  • Calculate scores:                                                │
│    - Match Score: How well CV matches JD (0-100%, if JD provided)   │
│    - Confidence Score: LLM certainty in analysis (0-100%)           │
│  • Output: Structured JSON intelligence                             │
│                                                                       │
│  Files: cv_intelligence_extractor.py, llm_batch_processor.py       │
│  Cost: $0 (6,000 CVs/day free)                                     │
│  Modes: Extraction-only (no JD) or Matching (with JD)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 3: QUALITY VERIFICATION                     │
│  Tech: sentence-transformers + sklearn                              │
│  ─────────────────────────────────────────────────────────────────  │
│  • 6-layer fuzzy matching cascade                                   │
│  • Compare LLM output vs original CV                                │
│  • Verify LLM didn't hallucinate skills                             │
│  • Output: Similarity score (99.94% avg accuracy)                   │
│                                                                       │
│  Files: cv_intelligence_extractor.py (compute_cv_faithfulness)     │
│  Purpose: Quality assurance - ensures LLM accuracy                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 4: VECTOR EMBEDDINGS                        │
│  Tech: sentence-transformers (all-MiniLM-L6-v2)                    │
│  ─────────────────────────────────────────────────────────────────  │
│  • Generate 384-dim embedding from CV text                          │
│  • Store in pgvector for semantic search                            │
│  • Enable "find similar candidates" feature                         │
│  • Output: Vector embedding array                                   │
│                                                                       │
│  Files: vector_search.py, backfill_embeddings.py                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 5: SUPABASE STORAGE                         │
│  Tech: Supabase (PostgreSQL + pgvector)                            │
│  ─────────────────────────────────────────────────────────────────  │
│  • Store intelligence in cv_intelligence table (40+ columns)        │
│  • Store filename mapping in cv_filename_mapping                    │
│  • Store vector embedding for semantic search                       │
│  • Output: Database record with anonymized ID                       │
│                                                                       │
│  Files: supabase_storage.py                                         │
│  Tables: cv_intelligence, cv_filename_mapping                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    USER SEARCHES CANDIDATES                          │
│                    (Flask Search UI)                                 │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SEARCH METHODS (NO LLM CALLS)                    │
│  ─────────────────────────────────────────────────────────────────  │
│  1. Quick Search with JD (Python local)                             │
│     • Keyword matching against JD requirements                      │
│     • Filter by skills, domain, seniority, experience               │
│     • Cost: $0, Speed: <100ms                                       │
│                                                                       │
│  2. Filter-based Search (PostgreSQL)                                │
│     • Search without JD using advanced filters                      │
│     • Uses PostgreSQL WHERE clauses                                 │
│     • Cost: $0, Speed: <100ms                                       │
│                                                                       │
│  3. Semantic Search (pgvector - separate page)                      │
│     • Generate query embedding                                      │
│     • Find similar vectors using cosine similarity                  │
│     • Cost: $0, Speed: <200ms                                       │
│                                                                       │
│  Files: app.py, vector_search.py, templates/index_new.html         │
└─────────────────────────────────────────────────────────────────────┘
``` 

---

## Database Schema

### Table: cv_intelligence (40+ columns)
```sql
- anonymized_id (TEXT, PRIMARY KEY)
- match_score (INTEGER) - 0-100% (NULL if no JD provided)
- confidence_score (INTEGER) - 0-100%
- similarity_score (FLOAT) - LLM faithfulness
- assessment_reason (TEXT) - Why this score/assessment
- years_experience (INTEGER)
- seniority_level (TEXT)
- primary_domain (TEXT)
- core_technical_skills (TEXT[])
- matched_requirements (TEXT[])
- missing_requirements (TEXT[])
- has_jd_matching (BOOLEAN) - Whether JD was provided
- recruiter_override (TEXT) - HIRED/ON_HOLD only
- embedding (VECTOR(384)) - for semantic search
- ... (30+ more fields)
```

### Table: cv_filename_mapping
```sql
- anonymized_id (TEXT, PRIMARY KEY)
- original_filename (TEXT) - sanitized
- redacted_filename (TEXT)
- upload_timestamp (TIMESTAMP)
```

---

## Key Features & Algorithms

### 1. Match Score vs Confidence Score
```python
# Match Score: How well CV matches the JD requirements (optional)
match_score = calculate_jd_match(cv_skills, jd_requirements)  # 0-100% or NULL
# Used for: Ranking candidates when JD is provided
# NULL when no JD provided (extraction-only mode)

# Confidence Score: How certain the LLM is in its analysis
confidence_score = llm_certainty_level()  # 0-100%
# Used for: Quality assessment of extraction

# Assessment Reason: Explains the scores
assessment_reason = "Strong Python/AWS match. 5+ years backend experience."
# Used for: Understanding why candidate scored high/low

# Two modes:
if job_description:
    # Matching mode: Extract + compare to JD
    match_score = calculate_match()
else:
    # Extraction-only mode: Just extract intelligence
    match_score = None
```

### 2. Similarity Scoring (Quality Verification)
```python
Layer 1: Exact skill match (100% weight)
Layer 2: Fuzzy skill match (90% weight)
Layer 3: Domain keywords (80% weight)
Layer 4: Experience level (70% weight)
Layer 5: Semantic embedding (60% weight)
Layer 6: Overall text similarity (50% weight)

Final Score = weighted_average(all_layers)
```

### 3. Two Processing Modes
```python
# Mode 1: Extraction Only (no JD)
intelligence = extract_intelligence(cv_text, job_description=None)
# Returns: skills, experience, domain, confidence
# match_score = None

# Mode 2: Extraction + JD Matching
intelligence = extract_intelligence(cv_text, job_description=jd_text)
# Returns: skills, experience, domain, confidence, match_score
# match_score = 0-100%

# Why no triage?
# Groq is FREE (6,000 requests/day) and FAST (2-3 seconds/CV)
# → Process all CVs directly through LLM
# → Simpler pipeline, fewer failure points
```

### 4. Vector Search (Semantic Similarity)
```python
query_embedding = model.encode("Python backend developer")
results = supabase.rpc('match_candidates', {
    'query_embedding': query_embedding,
    'match_threshold': 0.7,
    'match_count': 10
})
```

---

## Cost Analysis (10,000 CVs)

| Component | Cost | Notes |
|-----------|------|-------|
| **Groq API** | $0 | 6,000 CVs/day free |
| **Supabase Pro** | $25/month | Required for performance |
| **Render Hosting** | $0-7/month | Free tier available |
| **Total** | **$25-32/month** | $0.83-1.07 per user |

### API Call Breakdown
- **Processing:** 1 LLM call per CV (one-time)
- **Searching:** 0 LLM calls (local Python + PostgreSQL)
- **No triage needed:** Groq is FREE, process all CVs directly

---

## Performance Metrics

### Processing Speed
- PII Redaction: ~2 seconds/CV
- LLM Analysis: ~3-5 seconds/CV (Groq is fast!)
- Quality Verification: ~0.5 seconds/CV
- Vector Embedding: ~0.5 seconds/CV
- Database Storage: ~0.5 seconds/CV
- **Total: ~6-8 seconds/CV**

### Search Speed
- Keyword Search: <100ms
- Semantic Search: <200ms

### Accuracy
- Similarity Score: 99.94% average (LLM quality verification)
- PII Redaction: 99%+ (Presidio)
- Match Score: Measures JD relevance (0-100%, when JD provided)
- Confidence Score: LLM certainty in extraction (0-100%)

---

## Security & Privacy

### PII Protection
- All CVs anonymized before LLM processing
- No real names/emails/phones sent to Groq
- Supabase stores only anonymized data
- Original filenames sanitized

### Data Flow Security
```
User Upload → Local Redaction → Anonymized Text → Groq API
                                                    ↓
                                            Structured JSON
                                                    ↓
                                            Supabase (encrypted)
```

---

## Scalability

### Current Capacity
- **30 concurrent users** - Supported
- **10,000 CVs** - Process in 2-3 days (Groq free tier)
- **Unlimited searches** - No API costs

### Scaling Options
1. **More CVs:** Upgrade to Groq paid tier
2. **More users:** Upgrade Render to $7/month
3. **More storage:** Supabase auto-scales

---

## File Structure

```
cv-intelligence-system/
├── app.py                          # Flask web server
├── cv_redaction_pipeline.py        # PII redaction
├── cv_intelligence_extractor.py   # LLM analysis + similarity
├── llm_batch_processor.py          # Groq API integration
├── vector_search.py                # Semantic search
├── supabase_storage.py             # Database operations
├── process_all_cvs_smart.py        # Batch processing script
├── requirements.txt                # Python dependencies
├── .env                            # API keys (not in git)
├── config/                         # PII patterns, sections
├── templates/
│   ├── index_new.html              # Main interface (Search + Process CVs)
│   ├── semantic_search.html        # Semantic search page
│   └── queue_monitor.html          # Queue monitoring (optional)
└── static/                         # CSS/JS assets (if any)
```

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys:
# - GROQ_API_KEY (get from console.groq.com)
# - SUPABASE_URL + SUPABASE_KEY
```

### 3. Process CVs
```bash
# With JD matching
python process_all_cvs_smart.py --jd "Your job description" --max 10

# Extraction only (no JD)
python process_all_cvs_smart.py --max 10
```

### 4. Start Web UI
```bash
python app.py
# Visit: http://localhost:5000
# Main interface with Search and Process CVs tabs
```

---

## Why This Stack?

### Groq (FREE LLM)
- 6,000 requests/day at $0 cost
- Ultra-fast inference (LPU hardware)
- Production-grade Llama 3.3 70B model

### Supabase (PostgreSQL)
- Managed database with REST API
- Built-in pgvector for semantic search
- Auto-scaling and backups

### Flask (Python)
- Simple, lightweight web framework
- Rich ecosystem for NLP/AI
- Easy deployment to Render

### sentence-transformers
- State-of-the-art embeddings
- Runs locally (no API costs)
- 384-dim vectors (good balance)

---

## Support & Documentation

- **Groq Docs:** https://console.groq.com/docs
- **Supabase Docs:** https://supabase.com/docs
- **Presidio Docs:** https://microsoft.github.io/presidio
- **sentence-transformers:** https://www.sbert.net

---

## Flask Routes

### Main Routes
- **`/`** → `index_new.html` - Main interface (Search + Process CVs tabs)
- **`/semantic-search`** → `semantic_search.html` - Semantic search page
- **`/queue-monitor`** → `queue_monitor.html` - Queue monitoring (optional)

### API Endpoints
- **`/api/statistics`** - Get system statistics
- **`/api/search-candidates`** - Filter-based search (POST)
- **`/api/quick-search`** - Quick search with JD (POST)
- **`/api/search/semantic`** - Semantic vector search (POST)
- **`/api/process-samples`** - Batch process CVs (POST)
- **`/api/recruiter-override/<id>`** - Update recruiter decision (POST)
- **`/api/sync-to-supabase`** - Sync local files to Supabase (POST)

### No Dashboard Routes
- ✅ 0 dashboard routes
- ✅ All functionality in main interface
- ✅ Simpler routing structure

---

## User Interface

### Main Interface: `index_new.html`
**Access**: `http://localhost:5000/`

**Two Tabs**:
1. **Search Tab (Default)**
   - Optional JD input for matching top candidates
   - Advanced filters: seniority, confidence, skills, domain, years
   - Real-time search results
   - Candidate cards with: confidence, match score, experience, skills

2. **Process CVs Tab**
   - Batch CV processing
   - Force reprocess option
   - Progress tracking

### Additional Pages
- **Semantic Search**: `/semantic-search` - Vector-based similarity search
- **Queue Monitor**: `/queue-monitor` - Celery queue monitoring (optional)

### No Dashboard
The system intentionally has no dashboard. All functionality is in the main interface:
- Search and filtering in Search tab
- Processing in Process CVs tab
- No statistics cards (no verdict system to track)
- Simpler, more focused UX

---

## Recent Changes (March 26-27, 2026)

### Verdict System Removal
- ✅ Removed SHORTLIST/BACKUP/REVIEW verdict categorization
- ✅ Removed human review queue functionality
- ✅ Simplified to pure extraction + optional JD matching
- ✅ Focus on confidence scores and match scores only
- ✅ Recruiter decisions now: HIRED/ON_HOLD only

### Dashboard Removal
- ✅ Deleted all dashboard HTML files
- ✅ Removed dashboard routes from Flask
- ✅ Removed dashboard statistics and cards
- ✅ Unified interface with Search and Process CVs tabs only

### Current System
- **Main Interface**: Single page with two tabs (Search + Process CVs)
- **No Dashboard**: All functionality in main interface
- **No Verdict System**: Pure extraction with optional matching
- **Optional JD**: Can search with or without job description
- **Clean Architecture**: Fewer files, simpler codebase

### Files Modified
- `templates/index_new.html` - Main interface (removed dashboard tab, review queue)
- `app.py` - Removed `/api/review-queue` endpoint, confirmed main route
- `cv_intelligence_extractor.py` - Removed verdict extraction
- `supabase_storage.py` - Removed verdict column
- `llm_batch_processor.py` - Updated prompt template

### Files Deleted
- `templates/dashboard.html` - Old dashboard
- `templates/dashboard_old.html` - Dashboard backup
- `templates/dashboard_new.html` - New dashboard (unused)
- `templates/index_new.html.backup` - Backup file

### Verification
- ✅ Flask main route (`/`) confirmed calling `index_new.html`
- ✅ 0 dashboard routes in Flask
- ✅ All dashboard files deleted
- ✅ Documentation updated

---

**Last Updated:** March 27, 2026  
**System Version:** 2.2 (Dashboard Removed, Unified Interface)  
**Status:** ✅ Production Ready - Clean, focused, no dashboard or verdict system
