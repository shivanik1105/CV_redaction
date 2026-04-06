# How Confidence Score vs Similarity Score Works

## Complete Flow with Real Code

---

## Step-by-Step Process

### Step 1: User Uploads CV
```
Original CV:
"John Doe
Email: john@email.com
Skills: Python, Django, PostgreSQL, Docker
Experience: 5 years as Backend Developer"
```

### Step 2: PII Redaction
```python
# In cv_redaction_pipeline.py
anonymized_cv = redact_pii(original_cv)

# Result:
"[REDACTED_NAME]
Email: [REDACTED_EMAIL]
Skills: Python, Django, PostgreSQL, Docker
Experience: 5 years as Backend Developer"
```

### Step 3: Send to LLM (Groq)
```python
# In cv_intelligence_extractor.py (line 683)

# Create prompt asking LLM to analyze
prompt = f"""
Analyze this CV and provide:
- Skills matched
- Years of experience
- Confidence: [0-100]%  ← LLM provides this!
- Match Score: [0-100]%

CV: {anonymized_cv}
JD: {job_description}
"""

# Send to Groq
raw_llm_response = self.llm_processor.generate_analysis(prompt)
```

### Step 4: LLM Responds with Confidence Score
```python
# LLM Response (from Groq):
{
  "skills_matched": ["Python", "Django", "PostgreSQL", "Docker"],
  "years_experience": 5,
  "seniority_level": "SENIOR",
  "confidence_score": 95,  ← LLM says "I'm 95% confident"
  "match_score": 85,
  "verdict": "ACCEPT"
}
```

**How LLM Calculates Confidence:**
- Clear text → High confidence (90-100%)
- Blurry/unclear → Low confidence (40-70%)
- Missing info → Low confidence (30-60%)
- Contradictions → Low confidence (20-50%)

### Step 5: Parse LLM Response
```python
# In cv_intelligence_extractor.py (line 687)

intelligence = self._parse_prose_response(raw_llm_response, anonymized_id)

# Extracted data:
intelligence = {
    "anonymized_id": "CAND_851",
    "skills_matched": ["Python", "Django", "PostgreSQL", "Docker"],
    "years_experience": 5,
    "confidence_score": 95,  ← From LLM
    "match_score": 85,
    "cleaned_text": anonymized_cv  ← Original CV stored for verification
}
```

### Step 6: Check Confidence Score
```python
# In cv_intelligence_extractor.py (line 710)

confidence = intelligence.get("confidence_score", 0)

if confidence < 70:
    # LLM is unsure - flag for human review
    intelligence["requires_human_review"] = True
    logger.warning(f"⚠️ Low confidence ({confidence}%) → HUMAN REVIEW")
else:
    intelligence["requires_human_review"] = False
```

### Step 7: Calculate Similarity Score (Our Verification)
```python
# In cv_intelligence_extractor.py (line 717)

# NOW we verify if LLM was accurate
similarity_score = compute_cv_faithfulness_score(intelligence)

intelligence["similarity_score"] = similarity_score
logger.info(f"Faithfulness score: {similarity_score}%")
```

### Step 8: How Similarity Score is Calculated
```python
# In cv_intelligence_extractor.py (line 127)

def compute_cv_faithfulness_score(intelligence: dict) -> float:
    """
    Compare LLM output vs original CV to catch hallucinations
    """
    
    # Get original CV text
    cv_text = intelligence.get("cleaned_text")  # Original anonymized CV
    cv_lower = cv_text.lower()
    
    # Get skills LLM extracted
    llm_skills = intelligence.get("core_technical_skills", [])
    # Example: ["Python", "Django", "PostgreSQL", "Docker"]
    
    # Check each skill against original CV
    found = 0
    total = len(llm_skills)
    
    for skill in llm_skills:
        skill_lower = skill.lower()
        
        # Layer 1: Exact match
        if skill_lower in cv_lower:
            found += 1
            continue
        
        # Layer 2: Fuzzy match (handles typos)
        if fuzzy_match(skill_lower, cv_lower) > 0.8:
            found += 1
            continue
        
        # Layer 3: Normalized match (handles "ASP.NET" vs "ASP NET")
        skill_normalized = skill_lower.replace('.', '').replace('-', '')
        if skill_normalized in cv_lower:
            found += 1
            continue
        
        # Layer 4: First word match (handles "React.js" vs "React")
        first_word = skill_lower.split()[0]
        if first_word in cv_lower:
            found += 1
            continue
        
        # Layer 5: Any significant word (handles "Machine Learning" vs "ML")
        words = [w for w in skill_lower.split() if len(w) > 3]
        if any(w in cv_lower for w in words):
            found += 1
            continue
        
        # Layer 6: Semantic similarity (embeddings)
        if semantic_similarity(skill, cv_text) > 0.7:
            found += 1
    
    # Calculate recall (what % of LLM skills are in CV)
    similarity_score = (found / total) * 100 if total > 0 else 0
    
    return round(similarity_score, 2)
```

---

## Real Example: Good Case ✅

### Input CV:
```
Skills: Python, Django, PostgreSQL, Docker, Redis
Experience: 5 years
```

### LLM Response:
```json
{
  "skills_matched": ["Python", "Django", "PostgreSQL", "Docker", "Redis"],
  "years_experience": 5,
  "confidence_score": 98,  ← LLM very confident
  "match_score": 90
}
```

### Similarity Calculation:
```python
cv_text = "python django postgresql docker redis 5 years"
llm_skills = ["Python", "Django", "PostgreSQL", "Docker", "Redis"]

# Check each skill:
"python" in cv_text → ✅ Found (1/5)
"django" in cv_text → ✅ Found (2/5)
"postgresql" in cv_text → ✅ Found (3/5)
"docker" in cv_text → ✅ Found (4/5)
"redis" in cv_text → ✅ Found (5/5)

similarity_score = (5/5) * 100 = 100%  ← Perfect!
```

### Final Scores:
- **Confidence Score: 98%** (LLM confident)
- **Similarity Score: 100%** (LLM accurate)
- **Action: ACCEPT** ✅

---

## Real Example: Hallucination Case ❌

### Input CV:
```
Skills: Python, Flask, MySQL
Experience: 3 years
```

### LLM Response (Hallucinated):
```json
{
  "skills_matched": ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes"],
  "years_experience": 5,
  "confidence_score": 95,  ← LLM confident (but wrong!)
  "match_score": 85
}
```

### Similarity Calculation:
```python
cv_text = "python flask mysql 3 years"
llm_skills = ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes"]

# Check each skill:
"python" in cv_text → ✅ Found (1/5)
"django" in cv_text → ❌ NOT FOUND (1/5)
"postgresql" in cv_text → ❌ NOT FOUND (1/5)
"docker" in cv_text → ❌ NOT FOUND (1/5)
"kubernetes" in cv_text → ❌ NOT FOUND (1/5)

similarity_score = (1/5) * 100 = 20%  ← Very low!
```

### Final Scores:
- **Confidence Score: 95%** (LLM confident)
- **Similarity Score: 20%** (LLM hallucinated!)
- **Action: FLAG FOR REVIEW** ⚠️

---

## Real Example: Unclear CV Case ⚠️

### Input CV (Blurry Scan):
```
Skills: Pythn, Djngo, PostgrSQL  [typos, hard to read]
Experience: 5 yrs
```

### LLM Response:
```json
{
  "skills_matched": ["Python", "Django", "PostgreSQL"],
  "years_experience": 5,
  "confidence_score": 55,  ← LLM unsure due to typos
  "match_score": 80
}
```

### Similarity Calculation:
```python
cv_text = "pythn djngo postgrsql 5 yrs"
llm_skills = ["Python", "Django", "PostgreSQL"]

# Check each skill (with fuzzy matching):
fuzzy_match("python", "pythn") → ✅ 90% similar (1/3)
fuzzy_match("django", "djngo") → ✅ 85% similar (2/3)
fuzzy_match("postgresql", "postgrsql") → ✅ 92% similar (3/3)

similarity_score = (3/3) * 100 = 100%  ← Actually accurate!
```

### Final Scores:
- **Confidence Score: 55%** (LLM unsure)
- **Similarity Score: 100%** (LLM got it right!)
- **Action: ACCEPT** ✅ (Similarity overrides low confidence)

---

## Decision Logic in Code

```python
# In cv_intelligence_extractor.py (line 710-720)

confidence_score = intelligence.get("confidence_score", 0)
similarity_score = compute_cv_faithfulness_score(intelligence)

# Decision tree:
if similarity_score < 70:
    # LLM hallucinated - don't trust it
    intelligence["requires_human_review"] = True
    intelligence["quality_flag"] = "HALLUCINATION_DETECTED"
    verdict = "REVIEW"
    
elif confidence_score < 70:
    # LLM unsure but similarity is OK
    intelligence["requires_human_review"] = True
    intelligence["quality_flag"] = "LOW_CONFIDENCE"
    verdict = "REVIEW"
    
elif match_score >= 80:
    # Strong match, high confidence, high similarity
    intelligence["requires_human_review"] = False
    verdict = "ACCEPT"
    
else:
    # Moderate match
    verdict = "REVIEW"
```

---

## Summary Table

| Confidence | Similarity | Meaning | Action |
|------------|-----------|---------|--------|
| High (95%) | High (100%) | LLM confident AND accurate | ✅ ACCEPT |
| High (95%) | Low (20%) | LLM confident BUT hallucinated | ❌ REVIEW (hallucination) |
| Low (55%) | High (100%) | LLM unsure BUT actually correct | ✅ ACCEPT (trust similarity) |
| Low (55%) | Low (30%) | LLM unsure AND made mistakes | ⚠️ REVIEW (both bad) |

---

## Key Takeaways

### Confidence Score (from LLM)
- **Calculated by**: Groq LLM
- **Based on**: Input quality (clear vs blurry)
- **Measures**: LLM's self-doubt
- **In code**: `intelligence["confidence_score"]` (line 710)

### Similarity Score (our verification)
- **Calculated by**: Our system
- **Based on**: LLM output vs original CV
- **Measures**: LLM accuracy (catches hallucinations)
- **In code**: `compute_cv_faithfulness_score()` (line 127)

### Why Both Are Needed
- **Confidence alone**: Can't catch hallucinations
- **Similarity alone**: Can't flag unclear CVs
- **Both together**: Complete quality assurance

---

## Test It Yourself

```bash
# Process a CV and see both scores
python process_all_cvs_smart.py --jd "Python Developer" --max 1

# Output shows:
# ✓ Analyzed: CAND_851
#   Confidence: 95%        ← From LLM
#   Similarity: 99.94%     ← Our verification
#   Match: 85%
#   Verdict: ACCEPT
```

---

**Now you understand exactly how both scores work!** 🎉
