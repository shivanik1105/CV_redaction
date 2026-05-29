# CV Redactor - Complete Project Documentation

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Features](#core-features)
4. [Technology Stack](#technology-stack)
5. [Data Flow](#data-flow)
6. [Component Details](#component-details)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Deployment Guide](#deployment-guide)
10. [Configuration](#configuration)
11. [Security & Privacy](#security--privacy)
12. [Performance Optimization](#performance-optimization)
13. [Troubleshooting](#troubleshooting)

---

## 1. Project Overview

### What is CV Redactor?

CV Redactor is an **intelligent resume anonymization and candidate search system** that:

1. **Anonymizes CVs** - Removes all personally identifiable information (PII) using advanced NLP
2. **Extracts Intelligence** - Uses LLMs to extract structured candidate data
3. **Enables Search** - Provides semantic and keyword-based candidate search
4. **Maintains Privacy** - Ensures recruiter bias-free candidate evaluation

### Key Value Propositions

- **Privacy-First**: Complete PII removal with visual black-box masking
- **AI-Powered**: LLM-based intelligence extraction (Groq, OpenAI, Anthropic, Google)
- **Semantic Search**: Vector embeddings for intelligent candidate matching
- **User-Controlled**: Users provide their own API keys (no central key)
- **Production-Ready**: Deployed on Oracle Cloud Free Tier ($0 forever)

### Use Cases

1. **Recruitment Agencies**: Anonymize CVs before sharing with clients
2. **HR Departments**: Bias-free initial screening
3. **Job Boards**: Privacy-compliant candidate databases
4. **Freelance Platforms**: Skill-based matching without personal data

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (Flask Web Application)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
├─────────────────┬───────────────────┬───────────────────────────┤
│  Upload Module  │  Search Module    │  Download Module          │
│  - File Upload  │  - Keyword Search │  - Masked PDF             │
│  - Validation   │  - Semantic Search│  - Original CV            │
│  - Processing   │  - Filters        │  - Intelligence JSON      │
└────────┬────────┴────────┬──────────┴────────┬──────────────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                           │
├──────────────────┬──────────────────┬──────────────────────────┤
│ Redaction Engine │ Intelligence     │ Vector Search Engine     │
│ - PII Detection  │ Extractor        │ - Embeddings             │
│ - Presidio       │ - LLM Analysis   │ - Similarity Search      │
│ - spaCy NER      │ - Structured     │ - Redis Cache            │
│ - Visual Masking │   Output         │                          │
└────────┬─────────┴────────┬─────────┴────────┬─────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                             │
├──────────────────┬──────────────────┬──────────────────────────┤
│ Supabase         │ File System      │ Redis Cache              │
│ - PostgreSQL     │ - Uploads        │ - Embeddings             │
│ - pgvector       │ - Redacted       │ - Search Results         │
│ - Storage Bucket │ - Intelligence   │ - Session Data           │
└──────────────────┴──────────────────┴──────────────────────────┘
```

### Component Interaction Flow

```
User Upload → File Validation → Text Extraction → PII Redaction
     ↓
Visual Masking → LLM Intelligence Extraction → Embedding Generation
     ↓
Database Storage → Search Indexing → Ready for Search
```

---

## 3. Core Features

### 3.1 CV Upload & Processing

**Features:**
- Multi-format support (PDF, DOCX, TXT)
- Async background processing with Celery
- User-provided API keys (no central key)
- Real-time progress tracking
- Automatic duplicate detection

**Process:**
1. User uploads CV file
2. File validated (format, size, content)
3. Text extracted from document
4. PII detected and redacted
5. Visual masked PDF generated
6. LLM extracts intelligence
7. Vector embeddings generated
8. Data stored in Supabase

**Supported Formats:**
- PDF (via PyMuPDF, pdfplumber)
- DOCX (via python-docx)
- TXT (plain text)

### 3.2 PII Detection & Redaction

**Detection Methods:**

1. **Regex-Based** (Fast, High Precision)
   - Email addresses
   - Phone numbers (10+ formats)
   - URLs and social media links
   - LinkedIn/GitHub profiles

2. **Presidio** (Context-Aware)
   - Person names
   - Addresses
   - SSN, credit cards
   - Custom entity recognition

3. **spaCy NER** (NLP-Based)
   - PERSON entities
   - ORG entities
   - GPE (locations)
   - DATE entities

**Redaction Markers:**
```
[REDACTED_EMAIL]
[REDACTED_PHONE]
[REDACTED_NAME]
[REDACTED_ADDRESS]
[REDACTED_URL]
[REDACTED_LINKEDIN]
```

### 3.3 Visual PDF Masking

**Technology:** PyMuPDF (fitz)

**Process:**
1. Open original PDF
2. Search for PII patterns on each page
3. Draw black rectangles over PII locations
4. Preserve original formatting
5. Save masked PDF

**Fallback:** Text-based redaction if visual masking fails

### 3.4 Intelligence Extraction

**LLM Providers Supported:**
- **Groq** (default, fast, free tier)
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- **Google** (Gemini)

**Extracted Fields:**

```json
{
  "anonymized_id": "CAND_A1B2C3D4",
  "years_experience": 8.5,
  "seniority_level": "SENIOR",
  "primary_domain": "Full Stack Web Development",
  "core_technical_skills": ["Python", "React", "PostgreSQL"],
  "secondary_technical_skills": ["Docker", "AWS", "Redis"],
  "key_strengths": ["System design", "Team leadership"],
  "cleaned_narrative": "Senior full-stack engineer...",
  "confidence_score": 95,
  "cv_faithfulness_score": 92.5
}
```

**Quality Metrics:**
- **Confidence Score**: Extraction completeness (0-100)
- **Faithfulness Score**: How accurately skills match CV text (0-100)

### 3.5 Search Capabilities

**1. Keyword Search**
- Skills matching
- Experience range filtering
- Location filtering
- Seniority level filtering

**2. Semantic Search**
- Vector embeddings (sentence-transformers)
- Cosine similarity matching
- Natural language queries
- Context-aware results

**3. Hybrid Search**
- Combines keyword + semantic
- Weighted scoring
- Relevance ranking

**Search Filters:**
```python
{
  "skills": ["Python", "React"],
  "min_experience": 5,
  "max_experience": 10,
  "seniority": ["SENIOR", "LEAD"],
  "location": "Remote",
  "limit": 20
}
```

### 3.6 Download Options

**1. Masked PDF**
- Visual black boxes over PII
- Original formatting preserved
- Ready for sharing

**2. Original CV**
- Only for authorized users
- Audit trail logged
- Access control enforced

**3. Intelligence JSON**
- Structured candidate data
- All extracted fields
- Metadata included

---

## 4. Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | Flask 3.0.0 | HTTP server, routing |
| **WSGI Server** | Gunicorn 21.2.0 | Production server |
| **Task Queue** | Celery 5.3.4 | Async processing |
| **Message Broker** | Redis 5.0.1 | Task queue, caching |

### PDF & Document Processing

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PDF Rendering** | PyMuPDF 1.24.0 | Visual masking |
| **PDF Extraction** | pdfplumber 0.10.3 | Text extraction |
| **PDF Parsing** | pdfminer.six | Advanced parsing |
| **DOCX Processing** | python-docx 1.1.0 | Word documents |
| **Image Processing** | Pillow 10.2.0 | Image handling |

### NLP & AI

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PII Detection** | Presidio 2.2.33 | Advanced PII detection |
| **NLP Engine** | spaCy 3.7.2 | Named entity recognition |
| **Language Model** | en_core_web_sm | English NER model |
| **Embeddings** | sentence-transformers 2.2.2 | Semantic search |
| **ML Utilities** | scikit-learn 1.3.0 | Similarity scoring |

### LLM Providers

| Provider | Library | Models |
|----------|---------|--------|
| **Groq** | groq 1.4.0 | llama-3.1-70b-versatile |
| **OpenAI** | openai 1.54.0 | GPT-4, GPT-3.5 |
| **Anthropic** | anthropic 0.39.0 | Claude 3 |
| **Google** | google-generativeai 0.8.3 | Gemini |

### Database & Storage

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | Supabase (PostgreSQL) | Candidate data |
| **Vector DB** | pgvector | Semantic search |
| **File Storage** | Supabase Storage | CV files |
| **Cache** | Redis | Embeddings, sessions |

### Utilities

| Component | Technology | Purpose |
|-----------|------------|---------|
| **HTTP Client** | httpx 0.26.0 | API calls |
| **Requests** | requests 2.31.0 | HTTP requests |
| **Phone Parsing** | phonenumbers 8.13.26 | Phone validation |
| **Environment** | python-dotenv 1.0.0 | Config management |

---

## 5. Data Flow

### Upload Flow

```
┌──────────────┐
│ User Uploads │
│   CV File    │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ File Validation  │
│ - Format check   │
│ - Size limit     │
│ - Content check  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Text Extraction  │
│ - PDF → Text     │
│ - DOCX → Text    │
│ - TXT → Text     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ PII Detection    │
│ - Regex patterns │
│ - Presidio       │
│ - spaCy NER      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Text Redaction   │
│ - Replace PII    │
│ - Add markers    │
│ - Clean text     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Visual Masking   │
│ - Open PDF       │
│ - Find PII       │
│ - Draw black box │
│ - Save masked    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ LLM Extraction   │
│ - Send to LLM    │
│ - Parse response │
│ - Structure data │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Embedding Gen    │
│ - Build text     │
│ - Generate vector│
│ - Cache in Redis │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Database Storage │
│ - Save to        │
│   Supabase       │
│ - Index vectors  │
└──────────────────┘
```

### Search Flow

```
┌──────────────┐
│ User Query   │
│ "Python dev  │
│  5+ years"   │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Query Parsing    │
│ - Extract skills │
│ - Parse filters  │
│ - Build query    │
└──────┬───────────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Keyword    │  │  Semantic   │  │  Filters    │
│  Search     │  │  Search     │  │  (exp, loc) │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────┬───────┴────────┬───────┘
                ▼                ▼
         ┌──────────────────────────┐
         │  Result Merging          │
         │  - Combine results       │
         │  - Score weighting       │
         │  - Deduplication         │
         └──────┬───────────────────┘
                ▼
         ┌──────────────────────────┐
         │  Ranking & Sorting       │
         │  - Relevance score       │
         │  - Experience match      │
         │  - Skill overlap         │
         └──────┬───────────────────┘
                ▼
         ┌──────────────────────────┐
         │  Return Results          │
         │  - Top N candidates      │
         │  - Metadata included     │
         └──────────────────────────┘
```

---

## 6. Component Details

### 6.1 Universal Redaction Engine

**File:** `universal_pipeline_engine.py`

**Purpose:** Configuration-driven PII detection and redaction

**Key Classes:**
- `UniversalRedactionEngine`: Main redaction logic
- `ConfigLoader`: Loads JSON configurations
- `PipelineOrchestrator`: Coordinates processing

**Configuration Files:**
```
config/
├── locations.json          # Cities, states, countries
├── protected_terms.json    # Technical terms to preserve
├── sections.json           # CV section headers
├── pii_patterns.json       # PII detection patterns
└── text_healing.json       # Spacing fix rules
```

**Features:**
- Zero hardcoded data
- Easy to extend via JSON
- Multi-language support
- Context-aware redaction

### 6.2 CV Intelligence Extractor

**File:** `cv_intelligence_extractor.py`

**Purpose:** LLM-powered structured data extraction

**Key Functions:**
- `extract_intelligence()`: Main extraction
- `compute_cv_faithfulness_score()`: Quality metric
- `is_cv_anonymized()`: Validation check

**LLM Prompt Structure:**
```
SECTION 1 – Professional Summary
SECTION 2 – Key Strengths
SECTION 3 – Experience Breakdown
SECTION 4 – Education
SECTION 5 – Potential Concerns
SECTION 6 – Highlight Achievements
SECTION 7 – Fitment Analysis (if JD provided)
```

**Output Parsing:**
- Prose → Structured JSON
- Field extraction with regex
- Validation and normalization
- Confidence scoring

### 6.3 Vector Search Engine

**File:** `vector_search.py`

**Purpose:** Semantic candidate matching

**Key Classes:**
- `VectorSearchEngine`: Main search engine
- Supports local (sentence-transformers) and API (OpenAI) embeddings

**Embedding Models:**
- **Local**: all-mpnet-base-v2 (768 dims)
- **OpenAI**: text-embedding-3-small (1536 dims)

**Features:**
- Redis caching for embeddings
- Batch processing support
- Cosine similarity scoring
- Configurable thresholds

### 6.4 Flask Application

**File:** `app.py`

**Purpose:** Web interface and API

**Key Routes:**
- `/` - Home page
- `/upload` - CV upload endpoint
- `/search` - Candidate search
- `/download/<type>/<id>` - File downloads
- `/api/candidates` - REST API

**Features:**
- Async upload processing
- Real-time progress tracking
- Session management
- Error handling

---

## 7. Database Schema

### Supabase Tables

#### `cv_intelligence` (Main Table)

```sql
CREATE TABLE cv_intelligence (
    anonymized_id TEXT PRIMARY KEY,
    cleaned_text TEXT,
    cleaned_narrative TEXT,
    years_experience NUMERIC,
    seniority_level TEXT,
    primary_domain TEXT,
    core_technical_skills JSONB,
    secondary_technical_skills JSONB,
    key_strengths JSONB,
    confidence_score INTEGER,
    cv_faithfulness_score NUMERIC,
    embedding vector(768),  -- pgvector
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_skills ON cv_intelligence USING GIN (core_technical_skills);
CREATE INDEX idx_experience ON cv_intelligence (years_experience);
CREATE INDEX idx_seniority ON cv_intelligence (seniority_level);
CREATE INDEX idx_embedding ON cv_intelligence USING ivfflat (embedding vector_cosine_ops);
```

#### `cv_filename_mapping` (File Tracking)

```sql
CREATE TABLE cv_filename_mapping (
    anonymized_id TEXT PRIMARY KEY REFERENCES cv_intelligence(anonymized_id),
    original_filename TEXT,
    redacted_filename TEXT,
    cv_hash TEXT,
    upload_timestamp TIMESTAMP DEFAULT NOW()
);
```

#### `masked_pdf_mapping` (PDF Tracking)

```sql
CREATE TABLE masked_pdf_mapping (
    anonymized_id TEXT PRIMARY KEY,
    masked_pdf_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Supabase Storage Buckets

```
cv-uploads/
├── originals/
│   └── {anonymized_id}/original.pdf
├── masked/
│   └── {anonymized_id}/masked.pdf
└── intelligence/
    └── {anonymized_id}/intelligence.json
```

---

## 8. API Endpoints

### Upload API

**POST** `/upload`

**Request:**
```json
{
  "file": "<binary>",
  "llm_provider": "groq",
  "llm_api_key": "gsk_...",
  "llm_model": "llama-3.1-70b-versatile",
  "job_description": "Optional JD text"
}
```

**Response:**
```json
{
  "success": true,
  "anonymized_id": "CAND_A1B2C3D4",
  "message": "CV processed successfully",
  "intelligence": {
    "years_experience": 8.5,
    "seniority_level": "SENIOR",
    "core_technical_skills": ["Python", "React"]
  }
}
```

### Search API

**POST** `/search`

**Request:**
```json
{
  "query": "Python developer with 5+ years",
  "skills": ["Python", "Django"],
  "min_experience": 5,
  "max_experience": 10,
  "seniority": ["SENIOR"],
  "limit": 20
}
```

**Response:**
```json
{
  "candidates": [
    {
      "anonymized_id": "CAND_A1B2C3D4",
      "years_experience": 8.5,
      "seniority_level": "SENIOR",
      "core_technical_skills": ["Python", "Django", "React"],
      "match_score": 95.5
    }
  ],
  "total": 1,
  "source": "supabase"
}
```

### Download API

**GET** `/download/masked/<anonymized_id>`

Returns masked PDF with black boxes over PII.

**GET** `/download/original/<anonymized_id>`

Returns original CV (access controlled).

**GET** `/download/intelligence/<anonymized_id>`

Returns intelligence JSON.

---

## 9. Deployment Guide

### 9.1 Oracle Cloud Free Tier (Recommended)

**Why Oracle Cloud?**
- $0 forever (no expiration)
- 1-24GB RAM (ARM instances)
- 200GB storage
- 10TB bandwidth/month

**Quick Steps:**

1. **Create Account**
   ```
   - Go to: https://www.oracle.com/cloud/free/
   - Sign up with Slice virtual card (India)
   - Verify email and phone
   ```

2. **Create VM Instance**
   ```
   - Ubuntu 22.04
   - Shape: VM.Standard.A1.Flex (ARM, 24GB RAM)
   - Save SSH key
   - Note public IP
   ```

3. **Configure Firewall**
   ```
   - Security List → Add Ingress Rules
   - Port 80 (HTTP)
   - Port 22 (SSH)
   ```

4. **Deploy Application**
   ```bash
   # Connect via SSH
   ssh -i key.pem ubuntu@YOUR_IP
   
   # Clone repository
   git clone YOUR_REPO
   cd cv-redactor
   
   # Run deployment script
   bash deploy_oracle.sh
   
   # Configure environment
   nano .env
   
   # Setup service
   sudo bash setup_service.sh
   
   # Setup Nginx
   sudo bash setup_nginx.sh
   ```

**Full Guide:** See `ORACLE_DEPLOY_GUIDE.md`

### 9.2 Alternative Platforms

| Platform | Cost | RAM | Setup Time |
|----------|------|-----|------------|
| **Oracle Cloud** | $0 forever | 1-24GB | 45 min |
| **Railway** | $10-15/mo | 8GB | 10 min |
| **Render Starter** | $7/mo | 1GB | 10 min |
| **Google Cloud Run** | ~$5-10/mo | 2GB+ | 60 min |

---

## 10. Configuration

### Environment Variables

**Required:**
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
SUPABASE_SERVICE_KEY=eyJxxx...
FLASK_SECRET_KEY=random_secret_key
```

**Optional:**
```env
# LLM Configuration (fallback if user doesn't provide)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxx
LLM_MODEL=llama-3.1-70b-versatile

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Performance Tuning
UPLOAD_WORKER_COUNT=2
LLM_MAX_CONCURRENT_REQUESTS=1
LLM_MIN_INTERVAL_SECONDS=0.35
QUICK_SEARCH_CACHE_TTL_SECONDS=45

# Embedding Provider
EMBEDDING_PROVIDER=local  # or 'openai'
```

### Configuration Files

**Location:** `config/`

```
config/
├── locations.json          # Geographic data
├── protected_terms.json    # Technical terms
├── sections.json           # CV sections
├── pii_patterns.json       # PII patterns
└── text_healing.json       # Text fixes
```

**Adding New Data:**
```bash
# Add city
python cv_redaction_pipeline.py add-city "Boston"

# Add technical term
python cv_redaction_pipeline.py add-term "tensorflow"

# Add text healing rule
python cv_redaction_pipeline.py add-healing "administr at ion" "administration"
```

---

## 11. Security & Privacy

### 11.1 PII Protection

**Detection Layers:**
1. **Regex Patterns** - Fast, high-precision
2. **Presidio** - Context-aware, ML-based
3. **spaCy NER** - Named entity recognition

**Redaction Methods:**
- Text replacement with markers
- Visual black-box masking
- Metadata stripping

**Validation:**
- Pre-upload anonymization check
- Post-redaction verification
- Faithfulness scoring

### 11.2 Access Control

**User API Keys:**
- Users provide their own LLM API keys
- No central API key stored
- Keys never logged or cached

**File Access:**
- Original CVs: Access controlled
- Masked PDFs: Public (anonymized)
- Intelligence JSON: Public (anonymized)

**Audit Trail:**
- All downloads logged
- Timestamp tracking
- User identification

### 11.3 Data Security

**In Transit:**
- HTTPS enforced (Nginx)
- TLS 1.2+ required
- Secure headers set

**At Rest:**
- Supabase encryption
- File system permissions
- Redis password protection

**Backup:**
- Supabase automatic backups
- Point-in-time recovery
- Export capabilities

---

## 12. Performance Optimization

### 12.1 Caching Strategy

**Redis Caching:**
```python
# Embedding cache
cache_key = f"embedding:{text_hash}"
ttl = 7 days

# Search results cache
cache_key = f"search:{query_hash}"
ttl = 45 seconds

# Candidate list cache
cache_key = "candidates:all"
ttl = 45 seconds
```

**Benefits:**
- 10x faster embedding retrieval
- Reduced LLM API calls
- Lower database load

### 12.2 Async Processing

**Celery Workers:**
```python
# Upload processing
@celery.task
def process_cv_async(file_path, user_config):
    # Extract → Redact → Mask → LLM → Store
    pass

# Batch embedding generation
@celery.task
def generate_embeddings_batch(candidate_ids):
    # Batch process for efficiency
    pass
```

**Benefits:**
- Non-blocking uploads
- Parallel processing
- Better resource utilization

### 12.3 Database Optimization

**Indexes:**
```sql
-- Skills search
CREATE INDEX idx_skills ON cv_intelligence USING GIN (core_technical_skills);

-- Experience range
CREATE INDEX idx_experience ON cv_intelligence (years_experience);

-- Vector search
CREATE INDEX idx_embedding ON cv_intelligence USING ivfflat (embedding vector_cosine_ops);
```

**Query Optimization:**
- Limit result sets
- Use prepared statements
- Connection pooling

### 12.4 Resource Limits

**Memory Management:**
```python
# Gunicorn workers
--workers 2 --threads 2

# LLM concurrency
LLM_MAX_CONCURRENT_REQUESTS=1

# Upload queue
UPLOAD_WORKER_COUNT=2
```

**File Size Limits:**
```python
MAX_CONTENT_LENGTH = 16MB
MAX_UPLOAD_SIZE = 10MB
```

---

## 13. Troubleshooting

### 13.1 Common Issues

#### Upload Fails

**Symptom:** "Upload failed" error

**Causes:**
1. File too large (>16MB)
2. Invalid format
3. No API key provided
4. LLM API error

**Solutions:**
```bash
# Check file size
ls -lh file.pdf

# Validate format
file file.pdf

# Test API key
curl -H "Authorization: Bearer $API_KEY" https://api.groq.com/...

# Check logs
sudo journalctl -u cv-redactor -f
```

#### Search Returns No Results

**Symptom:** Empty search results

**Causes:**
1. No candidates in database
2. Filters too restrictive
3. Supabase connection issue

**Solutions:**
```bash
# Check database
psql -h supabase-url -U postgres -d postgres
SELECT COUNT(*) FROM cv_intelligence;

# Test Supabase connection
python -c "from supabase_storage import SupabaseStorage; s = SupabaseStorage(); print(s.get_all_candidates())"

# Check logs
tail -f /var/log/cv-redactor.log
```

#### Out of Memory

**Symptom:** App crashes, "Killed" in logs

**Causes:**
1. Too many workers
2. Large file processing
3. Insufficient RAM

**Solutions:**
```bash
# Reduce workers
sudo nano /etc/systemd/system/cv-redactor.service
# Change: --workers 1 --threads 1

# Check memory
free -h
top

# Restart service
sudo systemctl restart cv-redactor
```

### 13.2 Debugging

**Enable Debug Mode:**
```python
# In app.py
app.debug = True
logging.basicConfig(level=logging.DEBUG)
```

**Check Logs:**
```bash
# Application logs
sudo journalctl -u cv-redactor -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# System logs
dmesg | tail
```

**Test Components:**
```bash
# Test redaction
python cv_redaction_pipeline.py test.pdf output/

# Test LLM
python -c "from cv_intelligence_extractor import CVIntelligenceExtractor; e = CVIntelligenceExtractor(); print(e.extract_intelligence('test text'))"

# Test vector search
python -c "from vector_search import get_vector_search_engine; e = get_vector_search_engine(); print(e.generate_embedding('test'))"
```

### 13.3 Performance Issues

**Slow Uploads:**
```bash
# Check LLM response time
time curl -X POST https://api.groq.com/...

# Check database latency
psql -h supabase-url -c "SELECT NOW();"

# Monitor resources
htop
```

**Slow Search:**
```bash
# Check index usage
EXPLAIN ANALYZE SELECT * FROM cv_intelligence WHERE ...;

# Rebuild indexes
REINDEX TABLE cv_intelligence;

# Check Redis
redis-cli PING
redis-cli INFO stats
```

---

## 14. Maintenance

### 14.1 Regular Tasks

**Daily:**
- Check logs for errors
- Monitor disk space
- Verify service status

**Weekly:**
- Review upload success rate
- Check database size
- Update dependencies

**Monthly:**
- Backup database
- Review security logs
- Update system packages

### 14.2 Backup & Recovery

**Database Backup:**
```bash
# Export from Supabase
pg_dump -h supabase-url -U postgres -d postgres > backup.sql

# Restore
psql -h supabase-url -U postgres -d postgres < backup.sql
```

**File Backup:**
```bash
# Backup uploads
tar -czf uploads_backup.tar.gz uploads/

# Backup intelligence
tar -czf intelligence_backup.tar.gz llm_analysis/
```

### 14.3 Monitoring

**Health Checks:**
```bash
# Service status
sudo systemctl status cv-redactor

# Disk space
df -h

# Memory usage
free -h

# CPU usage
top
```

**Metrics to Track:**
- Upload success rate
- Average processing time
- Search response time
- Database size
- Error rate

---

## 15. Future Enhancements

### Planned Features

1. **Multi-language Support**
   - Spanish, French, German CVs
   - Language detection
   - Localized PII patterns

2. **Advanced Analytics**
   - Candidate insights dashboard
   - Skill trend analysis
   - Market intelligence

3. **API Improvements**
   - GraphQL API
   - Webhook notifications
   - Batch operations

4. **ML Enhancements**
   - Custom NER models
   - Improved skill extraction
   - Salary prediction

5. **Integration**
   - ATS integration
   - LinkedIn import
   - Email parsing

---

## 16. Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-repo/cv-redactor.git
cd cv-redactor

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env

# Run locally
python app.py
```

### Code Style

- **Python**: PEP 8
- **Docstrings**: Google style
- **Type hints**: Encouraged
- **Testing**: pytest

### Pull Request Process

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit PR

---

## 17. License & Credits

### License

MIT License - See LICENSE file

### Credits

**Core Technologies:**
- Flask, Gunicorn, Celery
- Presidio, spaCy
- sentence-transformers
- Supabase, Redis

**LLM Providers:**
- Groq, OpenAI, Anthropic, Google

**Contributors:**
- [Your Name]
- [Contributors]

---

## 18. Support

### Documentation

- **Quick Start**: `START_HERE_ORACLE.md`
- **Deployment**: `ORACLE_DEPLOY_GUIDE.md`
- **User Guide**: `USER_GUIDE.md`
- **API Docs**: `API_DOCUMENTATION.md`

### Contact

- **Email**: support@cvredactor.com
- **GitHub**: https://github.com/your-repo/cv-redactor
- **Issues**: https://github.com/your-repo/cv-redactor/issues

---

**Last Updated:** May 29, 2026  
**Version:** 2.0.0  
**Status:** Production Ready ✅
