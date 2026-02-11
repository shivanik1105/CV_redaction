# Ethical AI & Full Audit Trail Implementation

## 🎯 Core Principles

### 1. **NO AUTO-REJECT POLICY**
**AI systems should support human decision-making, not replace it.**

```
┌──────────────────────────────────────────────────────────┐
│  CRITICAL RULE: AI NEVER REJECTS CANDIDATES              │
│  ══════════════════════════════════════════════════════  │
│  • AI provides SHORTLIST/BACKUP/REVIEW recommendations   │
│  • Recruiters MUST review top 50 candidates              │
│  • Low confidence (<70%) → Human review MANDATORY        │
│  • Only humans make final rejection decisions            │
└──────────────────────────────────────────────────────────┘
```

### 2. **FULL EXPLAINABILITY**
Every decision must be traceable from raw CV to final verdict.

**Audit Trail Chain:**
```
Raw CV Upload 
    ↓ [SHA256 Hash]
Anonymized CV (PII Removed)
    ↓ [Anonymized ID: CAND_XXX]
LLM Analysis (Full Prompt Stored)
    ↓ [Confidence Score]
AI Verdict (SHORTLIST/BACKUP/REVIEW)
    ↓ [Evidence-Based Reasoning]
Human Review (If confidence <70%)
    ↓ [Recruiter Override]
Final Decision
```

---

## 📊 System Architecture

### Verdict Flow

```
                    ┌─────────────────┐
                    │   CV Uploaded   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Anonymization  │
                    │  (PII Removed)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  LLM Analysis   │
                    │  + Confidence   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
       [Confidence ≥70%]            [Confidence <70%]
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌──────────────────┐
    │  AI Verdict:    │          │  HUMAN REVIEW    │
    │  SHORTLIST      │          │   REQUIRED       │
    │  BACKUP         │          │  ⚠️ LOW CONF    │
    │  REVIEW         │          └────────┬─────────┘
    └────────┬────────┘                   │
             │                             │
             └──────────┬──────────────────┘
                        │
                ┌───────▼────────┐
                │  Recruiter     │
                │  Review Queue  │
                └───────┬────────┘
                        │
                ┌───────▼────────┐
                │  Human Final   │
                │  Decision:     │
                │  SHORTLIST /   │
                │  REJECT /      │
                │  HIRED /       │
                │  ON_HOLD       │
                └────────────────┘
```

### Confidence Score Routing

| Confidence | Routing | Action |
|-----------|---------|--------|
| **90-100%** | ✅ Auto-proceed | AI verdict displayed, recruiter can review top 50 |
| **70-89%** | ⚡ Standard flow | AI verdict shown, included in normal review |
| **<70%** | 🔴 **MANDATORY REVIEW** | Immediately routed to human review queue |
| **<50%** | 🚨 **PRIORITY REVIEW** | Unclear CV, AI cannot make recommendation |

---

## 🗄️ Database Schema (Audit Trail Fields)

### cv_intelligence Table

```sql
-- Full Audit Trail
original_cv_hash VARCHAR(64),           -- SHA256 of raw uploaded CV
llm_prompt_used TEXT,                   -- Exact prompt sent to LLM
llm_raw_response TEXT,                  -- Full LLM response (unprocessed)
recruiter_override VARCHAR(20),         -- Human final decision
recruiter_notes TEXT,                   -- Human reviewer comments
recruiter_id VARCHAR(100),              -- Who made the decision
reviewed_at TIMESTAMP,                  -- Timestamp of human review

-- No Auto-Reject Policy
verdict VARCHAR(20) CHECK (verdict IN ('SHORTLIST', 'BACKUP', 'REVIEW')),  -- NO REJECT
confidence_score INTEGER CHECK (confidence_score BETWEEN 0 AND 100),
requires_human_review BOOLEAN DEFAULT FALSE,  -- True if confidence <70%
```

### cv_filename_mapping Table (Secure Backend)

```sql
-- Backend-only table, never exposed to frontend
id UUID PRIMARY KEY,
anonymized_id VARCHAR(20) UNIQUE,       -- CAND_XXX
original_filename VARCHAR(255),         -- Original file name (backend only)
redacted_filename VARCHAR(255),         -- Anonymized filename
upload_timestamp TIMESTAMP,
uploaded_by VARCHAR(100)                -- For multi-user systems
```

---

## 🔍 Audit Trail Example

### Complete Pipeline Trace

```json
{
  "anonymized_id": "CAND_882",
  
  // Step 1: Original CV Tracking
  "original_cv_hash": "a7f3d9e1c4b6f2e8d1c9a4b7e3f1d8c6a2b5e9f3d1c7a4b8e2f6d3c9a1b5e7f4",
  "original_filename": "john_doe_resume.pdf",  // Backend only
  
  // Step 2: LLM Analysis (Full Reproducibility)
  "llm_prompt_used": "You are a professional recruiter AI... [FULL 2000-word PROMPT]",
  "llm_raw_response": "{\"verdict\": \"BACKUP\", \"confidence_score\": 68, ... [FULL JSON]}",
  "llm_provider": "gemini",
  "llm_model": "gemini-2.0-flash",
  
  // Step 3: AI Verdict
  "verdict": "REVIEW",  // Changed from BACKUP due to low confidence
  "confidence_score": 68,
  "match_score": 72,
  "verdict_reason": "5 years Python/AWS matching core requirements. Led 2 microservices projects. Missing Kubernetes (nice-to-have). Low confidence due to vague project descriptions.",
  "requires_human_review": true,  // Triggered by confidence <70%
  
  // Step 4: Human Override (Recruiter Decision)
  "recruiter_override": "SHORTLIST",
  "recruiter_notes": "After phone screening, confirmed strong AWS experience. Projects vague in CV but excellent technical depth in interview. Proceed to technical round.",
  "recruiter_id": "jane.recruiter@company.com",
  "reviewed_at": "2026-02-11T15:30:00Z",
  
  // Timestamps
  "extraction_timestamp": "2026-02-11T14:15:00Z",
  "created_at": "2026-02-11T14:15:00Z",
  "updated_at": "2026-02-11T15:30:00Z"
}
```

---

## 🔐 Security & Privacy

### 1. **Anonymization Layer**
- All personal identifiable information (PII) removed before LLM analysis
- Original filenames stored in secure backend-only table
- Frontend only sees `CAND_XXX` identifiers

### 2. **Data Access Levels**

| Role | Access | Permissions |
|------|--------|-------------|
| **AI System** | Anonymized CV text only | Read-only, no PII |
| **Frontend Dashboard** | Anonymized ID + Intelligence | No original filenames |
| **Backend Service** | Full audit trail | Can link CAND_XXX → original file |
| **Recruiter** | Anonymized profile + override | Can add human decisions |
| **Admin** | Complete audit trail | Full system access for compliance |

### 3. **Audit Trail Storage**

```python
# Example: Retrieving full audit trail
def get_audit_trail(anonymized_id: str) -> dict:
    """Get complete decision trail for compliance"""
    
    # 1. Get intelligence record (AI decision)
    intelligence = supabase.get_candidate(anonymized_id)
    
    # 2. Get original filename (backend only)
    filename = supabase.get_original_filename(anonymized_id)
    
    # 3. Reconstruct decision chain
    return {
        "candidate": anonymized_id,
        "original_cv": intelligence['original_cv_hash'],
        "original_filename": filename,  # Backend only
        "ai_analysis": {
            "prompt": intelligence['llm_prompt_used'],
            "raw_response": intelligence['llm_raw_response'],
            "verdict": intelligence['verdict'],
            "confidence": intelligence['confidence_score'],
            "reasoning": intelligence['verdict_reason']
        },
        "human_review": {
            "required": intelligence['requires_human_review'],
            "override": intelligence['recruiter_override'],
            "notes": intelligence['recruiter_notes'],
            "reviewer": intelligence['recruiter_id'],
            "reviewed_at": intelligence['reviewed_at']
        }
    }
```

---

## 🎓 Best Practices

### For Recruiters

1. **Always Review Top 50**
   - Even if AI says "REVIEW", check the candidate
   - AI cannot see soft skills, cultural fit, potential

2. **Mandatory Review Triggers**
   - Confidence <70% → Human review required
   - Unclear CVs → AI cannot decide confidently
   - Borderline scores (60-79%) → Second opinion recommended

3. **Override Documentation**
   - Add notes explaining your decision
   - Cite phone screen, interview, or additional context
   - Helps refine AI over time

### For Compliance

1. **Audit Trail Retention**
   - Store full audit trail for 2+ years
   - Include original CV hash, LLM prompt, verdicts
   - Enable reconstruction of any decision

2. **Bias Monitoring**
   - Track override rates by verdict type
   - Monitor confidence score distributions
   - Regular AI fairness audits

3. **Candidate Rights**
   - Candidates can request explanation of AI verdict
   - Provide verdict_reason + confidence score
   - Explain human override if applicable

---

## 📈 Dashboard Features

### 1. **Statistics Panel**
```
Total Candidates: 127
Shortlisted: 45
Backup: 38
Needs Review: 44
⚠️ Human Review Required: 23
Recruiter Reviewed: 67
Avg Match Score: 68%
Avg Confidence: 74%
```

### 2. **Human Review Queue**
- Prioritized list of low-confidence candidates
- Confidence score prominently displayed
- One-click override buttons:
  - ✓ SHORTLIST
  - ✗ REJECT
  - ⏸ ON HOLD

### 3. **Candidate Cards**
- ⚠️ Warning badge for low confidence
- ✓ REVIEWED badge for recruiter overrides
- Confidence score color-coded:
  - Green: ≥70%
  - Red: <70%

---

## 🔄 API Endpoints

### Get Review Queue
```bash
GET /api/review-queue?limit=50
```

**Response:**
```json
{
  "success": true,
  "count": 23,
  "message": "23 candidates need human review (confidence <70% or unclear AI verdict)",
  "candidates": [...]
}
```

### Add Recruiter Override
```bash
POST /api/recruiter-override/CAND_882
Content-Type: application/json

{
  "decision": "SHORTLIST",
  "notes": "Strong technical interview performance",
  "recruiter_id": "jane.recruiter@company.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Recruiter override added: SHORTLIST",
  "candidate": {...}
}
```

---

## ⚖️ Legal & Ethical Compliance

### 1. **GDPR Compliance**
- ✅ Right to explanation (verdict_reason stored)
- ✅ Right to human review (mandatory for low confidence)
- ✅ Data minimization (anonymized processing)
- ✅ Audit trail (full decision history)

### 2. **Equal Employment Opportunity (EEO)**
- ✅ No auto-reject = reduces algorithmic bias
- ✅ Human oversight for all borderline cases
- ✅ Transparent AI reasoning stored

### 3. **AI Ethics Principles**
- ✅ **Transparency**: Full prompt and response stored
- ✅ **Accountability**: Human final decision required
- ✅ **Fairness**: Top 50 always reviewed regardless of AI verdict
- ✅ **Explainability**: Evidence-based reasoning with CV citations

---

## 🚀 Deployment Checklist

- [ ] Configure Supabase URL and key
- [ ] Run SQL schema with audit trail fields
- [ ] Test confidence threshold routing (<70%)
- [ ] Verify no "REJECT" verdicts in database
- [ ] Test recruiter override workflow
- [ ] Train recruiters on review queue process
- [ ] Set up audit trail retention policy
- [ ] Document compliance procedures
- [ ] Enable Row Level Security (RLS) on Supabase
- [ ] Implement logging for all human overrides

---

## 📞 Support & Questions

**Ethical AI Decision Flow:**
```
Q: Can AI reject candidates?
A: NO. AI only suggests SHORTLIST/BACKUP/REVIEW. Only humans reject.

Q: What if confidence is 50%?
A: Automatic human review. AI verdict shown as "REVIEW" (not trusted enough).

Q: How do I override AI verdict?
A: Review Queue → Select candidate → Click SHORTLIST/REJECT/ON_HOLD → Add notes

Q: Can I see why AI decided?
A: Yes. verdict_reason field has 2-sentence explanation with CV citations.

Q: How to audit a candidate decision?
A: Backend can trace: original_cv_hash → anonymized_id → llm_prompt → verdict → recruiter_override
```

---

## 📋 Summary

This implementation ensures:

1. **No Algorithmic Bias**: AI never auto-rejects
2. **Human Control**: Recruiters always in the loop
3. **Full Transparency**: Every decision traceable
4. **Ethical AI**: Confidence-based routing protects candidates
5. **Compliance Ready**: GDPR, EEO, AI ethics standards met

**The system supports recruiters, doesn't replace them.** 🤝
