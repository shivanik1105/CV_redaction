# CV Intelligence System - Quick Reference

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Configure
cp .env.example .env
# Add your GROQ_API_KEY and SUPABASE credentials

# Run
python app.py
# Visit: http://localhost:5000
```

---

## 📊 Understanding Scores

### Match Score (e.g., 67%)
- **What**: How well candidate matches Job Description
- **Range**: 0-100% (NULL if no JD)
- **90-100%**: Excellent match
- **70-89%**: Good match
- **50-69%**: Moderate match (your 67%)
- **0-49%**: Poor match

### Confidence Score (e.g., 70%)
- **What**: How confident AI is in extraction
- **Range**: 0-100% (always present)
- **80-100%**: High confidence
- **60-79%**: Medium confidence (your 70%)
- **40-59%**: Low confidence
- **0-39%**: Very low confidence

### Similarity Score
- **What**: How accurately LLM captured CV
- **Range**: 0-100%
- **System Average**: 99.94%

---

## 🔍 Search Methods

### 1. Quick Search (with JD)
```
Enter JD → System matches keywords → Ranked by match score
Speed: <100ms | Cost: $0
```

### 2. Filter Search (no JD)
```
Set filters → PostgreSQL query → Filtered results
Speed: <100ms | Cost: $0
```

### 3. Semantic Search
```
Natural language query → Vector similarity → Similar candidates
Speed: <200ms | Cost: $0
```

---

## ⚙️ Processing Pipeline

```
Upload CV (PDF/DOCX)
  ↓ 2 sec
Redact PII (Presidio)
  ↓ 3-5 sec
LLM Analysis (Groq)
  ↓ 0.5 sec
Quality Check (6-layer)
  ↓ 0.5 sec
Generate Embedding
  ↓ 0.5 sec
Store in Supabase
  ↓
Done! (~6-8 sec total)
```

---

## 💰 Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Groq API | $0 | 6,000 CVs/day free |
| Supabase | $25/mo | Pro plan |
| Render | $0-7/mo | Free or Starter |
| **Total** | **$25-32/mo** | **$0.0025/CV** |

---

## 🔐 Security

- ✅ All CVs anonymized before AI
- ✅ No PII sent to Groq
- ✅ Encrypted database storage
- ✅ Sanitized filenames

---

## 📁 Key Files

```
app.py                          # Flask server
cv_intelligence_extractor.py   # LLM extraction
cv_redaction_pipeline.py        # PII redaction
supabase_storage.py             # Database
vector_search.py                # Semantic search
templates/index_new.html        # Main UI
```

---

## 🌐 URLs

```
Main Interface:    http://localhost:5000/
Semantic Search:   http://localhost:5000/semantic-search
Queue Monitor:     http://localhost:5000/queue-monitor
```

---

## 🛠️ Common Commands

```bash
# Process CVs with JD
python process_all_cvs_smart.py --jd "Your JD" --max 10

# Process without JD
python process_all_cvs_smart.py --max 10

# Force reprocess
python process_all_cvs_smart.py --force --max 10

# Backfill embeddings
python backfill_embeddings.py

# Test Groq connection
python -c "from llm_batch_processor import LLMBatchProcessor; print('OK')"
```

---

## 🐛 Troubleshooting

**Groq API Error**
```bash
# Check key
echo $GROQ_API_KEY
```

**Supabase Error**
```bash
# Test connection
python -c "from supabase_storage import SupabaseStorage; SupabaseStorage()"
```

**spaCy Error**
```bash
# Download model
python -m spacy download en_core_web_sm
```

---

## 📞 Support

- **Full Docs**: `COMPLETE_SYSTEM_ARCHITECTURE.md`
- **Groq**: https://console.groq.com/docs
- **Supabase**: https://supabase.com/docs

---

**Version**: 2.2 | **Updated**: March 27, 2026
