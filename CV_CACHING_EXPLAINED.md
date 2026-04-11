# CV Processing Caching System - Explained

## Quick Answer

**No, the system does NOT reprocess all CVs every time!**

The system has intelligent caching that:
- ✅ Skips already processed CVs automatically
- ✅ Reuses cached results when the job description hasn't changed
- ✅ Only reprocesses when you explicitly check "Force re-process"

---

## How Caching Works

### 1. First Time Processing

```
CV Upload → Redaction → Intelligence Extraction → Save to:
                                                   ├─ Local JSON file
                                                   ├─ Supabase (if configured)
                                                   └─ Embedding vector
```

**Files Created:**
- `redacted_output/REDACTED_20240406_123456_resume.txt`
- `llm_analysis/REDACTED_20240406_123456_resume_intelligence.json`

### 2. Second Time (Same CV, Same JD)

```
CV Upload → Check cache → Found! → Return cached result ✓
                                    (No API calls, instant!)
```

**What's checked:**
- Does intelligence JSON file exist?
- Was it processed with the same job description?
- Is the JD hash matching?

### 3. Second Time (Same CV, Different JD)

```
CV Upload → Check cache → JD changed! → Reprocess with new JD
```

**Why reprocess:**
- Match score depends on the job description
- Different JD = different matching requirements
- Need fresh analysis for accurate results

---

## The Caching Logic (Code)

### Step 1: Check if Intelligence File Exists

```python
def _load_cached_intelligence(redacted_filename: str):
    """Load previously saved intelligence file"""
    intelligence_path = Path('llm_analysis') / f"{redacted_filename}_intelligence.json"
    
    if intelligence_path.exists():
        return json.load(intelligence_path)
    
    return None  # No cache found
```

### Step 2: Verify Cache is Compatible

```python
def _is_cached_result_compatible(intelligence, job_description):
    """Ensure cached result matches current JD mode"""
    
    # Skip if there's an error in cached data
    if 'error' in intelligence:
        return False
    
    # Check if JD mode matches
    cached_has_jd = bool(intelligence.get('has_jd_matching'))
    requested_has_jd = bool(job_description)
    
    if cached_has_jd != requested_has_jd:
        return False  # Mode changed (extraction-only vs matching)
    
    # If no JD, cache is valid
    if not requested_has_jd:
        return True
    
    # If JD provided, check if it's the same JD
    cached_jd_hash = intelligence.get('job_description_hash')
    current_jd_hash = hashlib.sha256(job_description.encode()).hexdigest()[:16]
    
    return cached_jd_hash == current_jd_hash
```

### Step 3: Use Cache or Reprocess

```python
def process_redacted_cv_text(redacted_text, redacted_filename, job_description, force_reprocess=False):
    """Process CV with caching"""
    
    # Check force reprocess flag
    if not force_reprocess:
        # Try to load cached result
        cached = _load_cached_intelligence(redacted_filename)
        
        # Check if cache is compatible
        if _is_cached_result_compatible(cached, job_description):
            return {
                'success': True,
                'cached': True,  # ← Indicates cache hit
                'intelligence': cached,
                'embedding_generated': bool(cached.get('embedding'))
            }
    
    # No cache or force reprocess → Run full pipeline
    intelligence = extractor.extract_intelligence(redacted_text, job_description)
    
    # Save for future use
    save_intelligence_json(redacted_filename, intelligence)
    
    return {
        'success': True,
        'cached': False,  # ← Indicates fresh processing
        'intelligence': intelligence
    }
```

---

## UI Checkbox: "Force re-process"

### When Unchecked (Default)

```
Process CVs → Check each CV:
              ├─ Already processed with same JD? → Skip (use cache)
              ├─ Already processed with different JD? → Reprocess
              └─ Never processed? → Process
```

**Result:**
- Fast processing (most CVs use cache)
- No unnecessary API calls
- Cost-effective

### When Checked

```
Process CVs → Ignore all caches → Reprocess everything
```

**Use when:**
- You updated the extraction logic
- You want fresh analysis
- You suspect cached data is stale
- You changed LLM provider/model

---

## Cache Invalidation Scenarios

### Cache is USED when:
✅ Same CV, same JD (or both extraction-only)
✅ Intelligence file exists and has no errors
✅ JD hash matches (if JD was provided)

### Cache is IGNORED when:
❌ Force reprocess checkbox is checked
❌ JD changed (different hash)
❌ Mode changed (extraction-only ↔ matching)
❌ Intelligence file has errors
❌ Intelligence file doesn't exist

---

## Example Scenarios

### Scenario 1: Process 100 CVs First Time

```
Action: Click "Process All Sample CVs"
Force reprocess: Unchecked

Result:
- 100 CVs processed
- 100 API calls made
- 100 intelligence files created
- Time: ~10 minutes
- Cost: ~$0.50
```

### Scenario 2: Process Same 100 CVs Again (Same JD)

```
Action: Click "Process All Sample CVs"
Force reprocess: Unchecked

Result:
- 100 CVs checked
- 0 API calls made (all cached!)
- 0 new files created
- Time: ~5 seconds
- Cost: $0
```

### Scenario 3: Process Same 100 CVs with New JD

```
Action: Add new job description → Click "Process All Sample CVs"
Force reprocess: Unchecked

Result:
- 100 CVs checked
- 100 API calls made (JD changed!)
- 100 intelligence files updated
- Time: ~10 minutes
- Cost: ~$0.50
```

### Scenario 4: Force Reprocess Everything

```
Action: Check "Force re-process" → Click "Process All Sample CVs"
Force reprocess: Checked

Result:
- 100 CVs processed
- 100 API calls made (cache ignored)
- 100 intelligence files overwritten
- Time: ~10 minutes
- Cost: ~$0.50
```

---

## What Gets Cached

### Intelligence JSON File Contains:

```json
{
  "anonymized_id": "ANON_ABC123",
  "job_description_hash": "a1b2c3d4e5f6g7h8",
  "has_jd_matching": true,
  "match_score": 85,
  "verdict": "SHORTLIST",
  "confidence_score": 92,
  "years_experience": 8,
  "seniority_level": "Senior",
  "core_technical_skills": ["Python", "Django", "PostgreSQL"],
  "primary_domain": "Backend Development",
  "cleaned_narrative": "...",
  "embedding": [0.123, 0.456, ...],
  "analysis_date": "2024-04-06T10:30:00"
}
```

**Key Fields for Caching:**
- `job_description_hash` - Identifies which JD was used
- `has_jd_matching` - Whether JD matching was performed
- `embedding` - Semantic vector (reused if exists)

---

## Performance Impact

### Without Caching (Hypothetical)

```
100 CVs × 3 processing runs = 300 API calls
Time: 30 minutes
Cost: $1.50
```

### With Caching (Actual)

```
Run 1: 100 CVs → 100 API calls (first time)
Run 2: 100 CVs → 0 API calls (cached)
Run 3: 100 CVs → 0 API calls (cached)

Total: 100 API calls
Time: 10 minutes + 10 seconds
Cost: $0.50

Savings: 67% time, 67% cost
```

---

## Best Practices

### 1. Default Behavior (Recommended)
- Leave "Force re-process" unchecked
- Let the system use caching automatically
- Only reprocess when needed

### 2. When to Force Reprocess
- After updating extraction prompts
- After changing LLM model
- After fixing bugs in extraction logic
- When testing new features

### 3. JD Management
- Use consistent JD text for same role
- Small JD changes = full reprocessing
- Consider JD versioning for tracking

### 4. Cache Maintenance
- Intelligence files are small (~10KB each)
- Safe to keep indefinitely
- Can delete to force fresh processing
- Supabase acts as backup

---

## Monitoring Cache Usage

### In the UI Response

```json
{
  "file": "resume.pdf",
  "status": "success",
  "cached": true,  ← Cache was used!
  "intelligence": {...}
}
```

### In the Logs

```
✓ Loaded cached intelligence for REDACTED_20240406_123456_resume.txt
✓ Cache compatible with current JD
✓ Skipping API call (using cache)
```

---

## Summary

**The system is smart about caching:**

1. ✅ Automatically caches all processed CVs
2. ✅ Reuses cache when JD hasn't changed
3. ✅ Invalidates cache when JD changes
4. ✅ Respects "Force re-process" checkbox
5. ✅ Saves time and money
6. ✅ Provides instant results for cached CVs

**You only pay for processing once per CV per JD!**

---

## Technical Details

### Cache Storage Locations

1. **Local JSON Files** (Primary cache)
   - Location: `llm_analysis/*.json`
   - Fast access
   - Always available
   - Survives restarts

2. **Supabase Database** (Backup/sync)
   - Location: `cv_intelligence` table
   - Shared across instances
   - Enables search
   - Optional

3. **Embedding Vectors** (Semantic search)
   - Location: `cv_embeddings` table
   - Cached in intelligence JSON
   - Reused if exists
   - Expensive to regenerate

### Cache Key Components

```python
cache_key = {
    'redacted_filename': 'REDACTED_20240406_123456_resume.txt',
    'job_description_hash': 'a1b2c3d4e5f6g7h8',
    'has_jd_matching': True
}
```

### Cache Validation

```python
def is_cache_valid(cached_intelligence, current_jd):
    # Check 1: No errors in cache
    if 'error' in cached_intelligence:
        return False
    
    # Check 2: JD mode matches
    if cached_intelligence['has_jd_matching'] != bool(current_jd):
        return False
    
    # Check 3: JD hash matches (if applicable)
    if current_jd:
        if cached_intelligence['job_description_hash'] != hash_jd(current_jd):
            return False
    
    return True
```

---

**Bottom Line:** The system is designed to be efficient. You're not wasting money reprocessing CVs unnecessarily!
