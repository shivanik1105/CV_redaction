# Data Flow Diagram - How Data Gets Stored

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. CV UPLOAD                                  │
│                                                                   │
│  User uploads: JohnDoe_Resume.pdf                               │
│  Contains: Name, Email, Phone, Address, Work History            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    2. PII REDACTION                              │
│                                                                   │
│  Pipeline removes:                                               │
│  - Names → [NAME]                                               │
│  - Emails → [EMAIL]                                             │
│  - Phones → [PHONE]                                             │
│  - Addresses → [ADDRESS]                                        │
│                                                                   │
│  Output: REDACTED_20260326_153924_JohnDoe.pdf                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    3. LLM EXTRACTION                             │
│                                                                   │
│  Input: Redacted CV + Job Description                           │
│  LLM: Gemini 2.5 Flash                                          │
│                                                                   │
│  Extracts:                                                       │
│  ✓ Years of experience: 5.5                                     │
│  ✓ Seniority: SENIOR                                            │
│  ✓ Skills: [Python, AWS, Docker, ...]                          │
│  ✓ Domain: Cloud Infrastructure                                 │
│  ✓ Verdict: SHORTLIST                                           │
│  ✓ Confidence: 85%                                              │
│  ✓ Match Score: 78%                                             │
│  ✓ Reasoning: "Strong Python and AWS skills..."                │
│                                                                   │
│  Output: JSON Intelligence Data                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    4. DATA MAPPING                               │
│                                                                   │
│  Python: supabase_storage.store_intelligence()                  │
│                                                                   │
│  Maps JSON to Database Columns:                                 │
│  {                                                               │
│    "anonymized_id": "CAND_767",                                │
│    "years_of_experience": 5.5,                                  │
│    "career_level": "SENIOR",                                    │
│    "key_skills": ["Python", "AWS", "Docker"],                  │
│    "domain_expertise": ["Cloud Infrastructure", "DevOps"],     │
│    "verdict": "SHORTLIST",                                      │
│    "confidence_score": 85,                                      │
│    "overall_summary": "Experienced backend developer...",      │
│    "evidence_based_reasoning": "Strong Python and AWS...",     │
│    "llm_raw_response": "{...full JSON backup...}"              │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    5. DATABASE STORAGE                           │
│                                                                   │
│  Supabase PostgreSQL                                            │
│                                                                   │
│  Table: cv_intelligence                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ id: 550e8400-e29b-41d4-a716-446655440000               │  │
│  │ anonymized_id: CAND_767                                 │  │
│  │ years_of_experience: 5.5                                │  │
│  │ career_level: SENIOR                                    │  │
│  │ key_skills: ["Python", "AWS", "Docker"]                │  │
│  │ domain_expertise: ["Cloud Infrastructure", "DevOps"]   │  │
│  │ verdict: SHORTLIST                                      │  │
│  │ confidence_score: 85                                    │  │
│  │ overall_summary: "Experienced backend developer..."    │  │
│  │ evidence_based_reasoning: "Strong Python and AWS..."   │  │
│  │ llm_raw_response: "{...full JSON backup...}"           │  │
│  │ embedding: [0.123, -0.456, ..., 0.321] (384 dims)     │  │
│  │ created_at: 2026-03-26 10:30:00                        │  │
│  │ updated_at: 2026-03-26 10:30:00                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Table: cv_filename_mapping (Security)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ anonymized_id: CAND_767                                 │  │
│  │ original_filename: JohnDoe_Resume.pdf                   │  │
│  │ anonymized_filename: REDACTED_20260326_JohnDoe.pdf     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    6. VECTOR EMBEDDING (Optional)                │
│                                                                   │
│  Input: overall_summary text                                     │
│  Model: all-MiniLM-L6-v2                                        │
│                                                                   │
│  "Experienced backend developer specializing in Python..."      │
│                    ↓                                             │
│  [0.123, -0.456, 0.789, ..., 0.321]  (384 numbers)            │
│                    ↓                                             │
│  Stored in embedding column                                      │
│                                                                   │
│  Used for: Semantic similarity search                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    7. SEARCH & RETRIEVAL                         │
│                                                                   │
│  Frontend → API → Database                                       │
│                                                                   │
│  Search Methods:                                                 │
│  1. SQL Filters (instant)                                       │
│     WHERE verdict = 'SHORTLIST'                                 │
│     AND career_level = 'SENIOR'                                 │
│     AND years_of_experience >= 5                                │
│                                                                   │
│  2. Keyword Search (instant)                                    │
│     WHERE key_skills @> '["Python"]'                            │
│                                                                   │
│  3. Semantic Search (<100ms)                                    │
│     SELECT * FROM match_cv_embeddings(                          │
│       query_embedding,                                           │
│       similarity_threshold,                                      │
│       limit                                                      │
│     )                                                            │
│                                                                   │
│  Results returned to dashboard                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Transformation Example

### Input (Original CV):
```
John Doe
john.doe@email.com
+1-555-123-4567
123 Main St, City, State

EXPERIENCE:
Senior Software Engineer at TechCorp (2019-2024)
- Led team of 5 engineers
- Migrated infrastructure to AWS
- Reduced costs by 40%

SKILLS:
Python, AWS, Docker, Kubernetes, PostgreSQL
```

### After Redaction:
```
[NAME]
[EMAIL]
[PHONE]
[ADDRESS]

EXPERIENCE:
Senior Software Engineer at [COMPANY] (2019-2024)
- Led team of 5 engineers
- Migrated infrastructure to AWS
- Reduced costs by 40%

SKILLS:
Python, AWS, Docker, Kubernetes, PostgreSQL
```

### After LLM Extraction (JSON):
```json
{
  "anonymized_id": "CAND_767",
  "years_experience": 5.0,
  "seniority_level": "SENIOR",
  "core_technical_skills": ["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"],
  "primary_domain": "Cloud Infrastructure",
  "secondary_domains": ["DevOps", "Backend Development"],
  "leadership_indicators": ["Led team of 5 engineers"],
  "highlight_achievements": ["Reduced costs by 40%", "Migrated infrastructure to AWS"],
  "verdict": "SHORTLIST",
  "confidence_score": 85,
  "match_score": 78,
  "verdict_reason": "Strong Python and AWS skills match requirements. 5+ years experience aligns with senior role.",
  "cleaned_narrative": "Experienced backend developer specializing in Python, AWS, and Docker with proven leadership in cloud migration projects."
}
```

### Stored in Database:
```sql
INSERT INTO cv_intelligence (
  anonymized_id,
  years_of_experience,
  career_level,
  key_skills,
  domain_expertise,
  verdict,
  confidence_score,
  overall_summary,
  evidence_based_reasoning,
  llm_raw_response
) VALUES (
  'CAND_767',
  5.0,
  'SENIOR',
  '["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"]',
  '["Cloud Infrastructure", "DevOps", "Backend Development"]',
  'SHORTLIST',
  85,
  'Experienced backend developer specializing in Python, AWS, and Docker with proven leadership in cloud migration projects.',
  'Strong Python and AWS skills match requirements. 5+ years experience aligns with senior role.',
  '{...full JSON backup...}'
);
```

---

## What Gets Stored vs What Doesn't

### ✅ STORED (Safe, Anonymized):
- Anonymized ID (CAND_767)
- Years of experience (5.0)
- Seniority level (SENIOR)
- Skills (Python, AWS, Docker)
- Domain (Cloud Infrastructure)
- Verdict (SHORTLIST)
- Confidence score (85%)
- Professional summary
- Reasoning

### ❌ NOT STORED (PII Removed):
- Real name (John Doe)
- Email (john.doe@email.com)
- Phone (+1-555-123-4567)
- Address (123 Main St)
- Company names (TechCorp)
- Any personally identifiable information

### 🔒 STORED SEPARATELY (Security Table):
- Original filename (JohnDoe_Resume.pdf)
- Mapping to anonymized ID
- Only accessible by backend
- Never exposed to frontend

---

## Database Query Examples

### 1. Find all SENIOR candidates with Python:
```sql
SELECT anonymized_id, career_level, key_skills, confidence_score
FROM cv_intelligence
WHERE career_level = 'SENIOR'
  AND key_skills @> '["Python"]'
ORDER BY confidence_score DESC;
```

### 2. Find candidates with 5+ years experience:
```sql
SELECT anonymized_id, years_of_experience, verdict
FROM cv_intelligence
WHERE years_of_experience >= 5.0
  AND verdict = 'SHORTLIST'
ORDER BY years_of_experience DESC;
```

### 3. Semantic search for "cloud engineer":
```sql
SELECT * FROM match_cv_embeddings(
  '[0.123, -0.456, ...]'::vector(384),  -- Query embedding
  0.7,  -- Similarity threshold
  10    -- Number of results
);
```

---

## Summary

**Data Flow:**
1. CV Upload → 2. PII Redaction → 3. LLM Extraction → 4. Data Mapping → 5. Database Storage → 6. Vector Embedding → 7. Search & Retrieval

**What's Stored:**
- 42 columns of structured intelligence
- ~10-20 KB per candidate
- 100% anonymized (no PII)
- Fully searchable (SQL + vector)

**Security:**
- PII removed before storage
- Original filenames in separate table
- Complete audit trail
- Row-level security enabled

Your data is **secure, structured, and searchable**! 🎯
