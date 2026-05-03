# CV Processing Caching - Quick Reference

## 🎯 Quick Answer

**No, CVs are NOT reprocessed every time!**

The system automatically caches results and only reprocesses when necessary.

---

## 📊 Cache Behavior

| Scenario | Cached? | API Calls | Time | Cost |
|----------|---------|-----------|------|------|
| First time processing | ❌ No | 100 | 10 min | $0.50 |
| Same CVs, same JD | ✅ Yes | 0 | 5 sec | $0 |
| Same CVs, new JD | ❌ No | 100 | 10 min | $0.50 |
| Force reprocess checked | ❌ No | 100 | 10 min | $0.50 |

---

## 🔄 Processing Flow

### Default (Force reprocess: OFF)

```
For each CV:
  ├─ Check if intelligence file exists
  ├─ Check if JD hash matches
  ├─ If both match → Use cache (instant!)
  └─ If not → Process (API call)
```

### Force Reprocess (Force reprocess: ON)

```
For each CV:
  └─ Ignore cache → Process (API call)
```

---

## ✅ Cache is Used When

- ✅ Intelligence file exists
- ✅ Same job description (or both extraction-only)
- ✅ No errors in cached data
- ✅ Force reprocess is unchecked

---

## ❌ Cache is Ignored When

- ❌ Force reprocess checkbox is checked
- ❌ Job description changed
- ❌ Intelligence file doesn't exist
- ❌ Cached data has errors
- ❌ Mode changed (extraction ↔ matching)

---

## 💾 What Gets Cached

**Location:** `llm_analysis/REDACTED_*_intelligence.json`

**Contains:**
- Extracted skills, experience, domain
- Match score (if JD provided)
- Verdict (if JD provided)
- Embedding vector
- JD hash (for validation)

**Size:** ~10KB per CV

---

## 💡 Best Practices

### ✅ DO

- Leave "Force re-process" unchecked (default)
- Let the system handle caching automatically
- Use consistent JD text for same role

### ❌ DON'T

- Check "Force re-process" unless needed
- Make small JD edits (triggers full reprocess)
- Delete intelligence files unnecessarily

---

## 🔍 When to Force Reprocess

Check "Force re-process" when:
- You updated extraction logic
- You changed LLM model/provider
- You fixed bugs in the pipeline
- You're testing new features
- Cached data seems incorrect

---

## 📈 Real Example

### Scenario: 100 CVs, 3 Processing Runs

**Run 1:** First time
- Processed: 100 CVs
- API calls: 100
- Time: 10 minutes
- Cost: $0.50

**Run 2:** Same JD, force reprocess OFF
- Processed: 0 CVs (all cached!)
- API calls: 0
- Time: 5 seconds
- Cost: $0

**Run 3:** New JD, force reprocess OFF
- Processed: 100 CVs (JD changed)
- API calls: 100
- Time: 10 minutes
- Cost: $0.50

**Total:**
- API calls: 200 (vs 300 without caching)
- Time saved: 10 minutes
- Cost saved: $0.50 (33% savings)

---

## 🎓 How It Works (Simple)

1. **First Processing:**
   ```
   CV → Redact → Extract → Save JSON → Done
   ```

2. **Second Processing (Same JD):**
   ```
   CV → Check JSON → Found! → Return cached → Done (instant!)
   ```

3. **Second Processing (New JD):**
   ```
   CV → Check JSON → JD changed! → Extract → Update JSON → Done
   ```

---

## 🔧 Technical Details

### JD Hash Calculation

```python
jd_hash = hashlib.sha256(job_description.encode()).hexdigest()[:16]
# Example: "a1b2c3d4e5f6g7h8"
```

### Cache Validation

```python
def is_cache_valid(cached, current_jd):
    # Has errors?
    if 'error' in cached:
        return False
    
    # JD mode matches?
    if cached['has_jd_matching'] != bool(current_jd):
        return False
    
    # JD hash matches?
    if current_jd and cached['job_description_hash'] != hash(current_jd):
        return False
    
    return True
```

---

## 📱 UI Indicators

### Response Shows Cache Status

```json
{
  "file": "resume.pdf",
  "status": "success",
  "cached": true,  ← Cache was used!
  "intelligence": {...}
}
```

### Processing Summary

```
Processed: 5 CVs
Cached: 95 CVs
Total: 100 CVs
Time: 1 minute
```

---

## 🎯 Key Takeaways

1. **Caching is automatic** - No configuration needed
2. **Saves time and money** - 67%+ savings on repeat runs
3. **Smart invalidation** - Reprocesses when JD changes
4. **Force reprocess available** - When you need it
5. **Transparent** - Response shows if cache was used

**You're not wasting resources!** The system is designed to be efficient.

---

## 📚 More Information

- Full details: `CV_CACHING_EXPLAINED.md`
- System architecture: `PROJECT_OVERVIEW.md`
- Processing pipeline: `cv_intelligence_extractor.py`
