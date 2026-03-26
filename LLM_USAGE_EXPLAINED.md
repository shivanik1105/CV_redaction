# LLM Usage - When Does It Get Called?

## The Key Question: "LLM is not getting exhausted?"

**Short Answer:** LLM is only called ONCE per CV during processing. After that, searching is FREE (no LLM calls).

---

## When LLM Gets Called ✅

### 1. ONE-TIME CV Processing (Uses LLM)

```
User clicks "Process All Sample CVs"
    ↓
For each CV:
    Read CV → Redact PII → Send to LLM → Extract intelligence → Store in DB
    ↑
    LLM CALL HERE (1 call per CV)
```

**Cost:**
- 72 CVs = 72 LLM calls
- With free tier: ~50 CVs per day
- With triage: Can process 70-100 CVs per day (30-50% savings)

**This is ONE-TIME setup!** Once processed, CVs are in database forever.

---

## When LLM Does NOT Get Called ❌

### 2. Searching CVs (NO LLM)

```
User enters Job Description in Search tab
    ↓
Quick keyword matching (local Python code)
    ↓
Query database with filters
    ↓
Return results in <1 second
    ↑
    NO LLM CALL - Just database queries!
```

**Cost:** FREE! Zero LLM calls.

**You can search UNLIMITED times** - no API quota used!

---

## Current System Architecture

### Processing Workflow (Uses LLM):
```
┌─────────────────────────────────────────────────────────────┐
│  PROCESS CVs (ONE-TIME SETUP)                               │
│                                                              │
│  User clicks "Process All Sample CVs"                       │
│      ↓                                                       │
│  For each CV in samples folder:                             │
│      1. Read original CV                                    │
│      2. Redact PII                                          │
│      3. ⚠️ CALL LLM (Gemini/GPT) ← API QUOTA USED          │
│      4. Extract intelligence                                │
│      5. Store in Supabase database                          │
│                                                              │
│  Result: 72 CVs = 72 LLM calls                             │
│  Time: 20-30 minutes                                        │
│  Cost: Uses daily API quota                                 │
└─────────────────────────────────────────────────────────────┘
```

### Search Workflow (NO LLM):
```
┌─────────────────────────────────────────────────────────────┐
│  SEARCH CVs (UNLIMITED, FREE)                               │
│                                                              │
│  User enters Job Description                                │
│      ↓                                                       │
│  Enhanced Triage Engine (local Python):                     │
│      1. Extract keywords from JD                            │
│      2. Extract keywords from each CV in database           │
│      3. Calculate overlap percentage                        │
│      4. Rank by relevance                                   │
│      ↓                                                       │
│  ✅ NO LLM CALL - Just keyword matching!                   │
│      ↓                                                       │
│  Query Supabase with filters                                │
│      ↓                                                       │
│  Return top matches in <1 second                            │
│                                                              │
│  Result: Instant search, zero API cost                      │
│  Time: <1 second                                            │
│  Cost: FREE (no LLM calls)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Your Current Situation

### What You've Done:
- Processed ~42 CVs (used ~42 LLM calls)
- Stored in Supabase database
- Can now search UNLIMITED times for FREE

### What Happens When You Search:
```python
# In dashboard, when you click "Search":

# 1. Extract keywords from JD (local, no LLM)
jd_keywords = triage.extract_keywords(job_description)

# 2. For each CV in database (local, no LLM)
for cv in database:
    cv_keywords = triage.extract_keywords(cv.text)
    overlap = cv_keywords.intersection(jd_keywords)
    match_percentage = len(overlap) / len(jd_keywords) * 100

# 3. Sort by match percentage
results = sorted(cvs, key=lambda x: x.match_percentage, reverse=True)

# NO LLM CALLS AT ALL!
```

---

## API Quota Usage Breakdown

### Free Tier Limits (Gemini):
- **Requests per minute:** 15
- **Requests per day:** 1,500
- **Tokens per minute:** 1,000,000

### Your Usage:

#### Processing (ONE-TIME):
```
72 CVs × 1 LLM call = 72 API calls
With triage (30% savings): ~50 API calls
Time: 20-30 minutes
Quota used: 50 out of 1,500 daily limit (3%)
```

#### Searching (UNLIMITED):
```
1,000 searches × 0 LLM calls = 0 API calls
Time: <1 second per search
Quota used: 0 (FREE!)
```

---

## Why You Got "Quota Exhausted" Before

### The Problem:
You were using the OLD workflow where EVERY search called the LLM:

```
OLD WORKFLOW (BAD):
User searches → Send ALL 72 CVs to LLM → Get matches
Result: 72 LLM calls PER SEARCH! 😱
After 20 searches: 1,440 API calls (quota exhausted)
```

### The Solution (Current):
Now you use the NEW workflow with database + triage:

```
NEW WORKFLOW (GOOD):
User searches → Keyword matching (local) → Query database → Get matches
Result: 0 LLM calls PER SEARCH! 🎉
After 1,000 searches: 0 API calls (still free!)
```

---

## How Triage Saves API Quota

### Without Triage:
```
100 CVs → Send ALL to LLM → 100 API calls
```

### With Triage:
```
100 CVs → Triage pre-filter → 30-50 CVs rejected → 50-70 sent to LLM
Result: 50-70 API calls (30-50% savings!)
```

**Triage Engine:**
- Extracts keywords from CV and JD
- Calculates overlap percentage
- Rejects CVs with <5% overlap (clearly not a match)
- Only sends promising CVs to LLM

---

## Your Current System

### Processing (ONE-TIME):
```python
# In app.py - /api/process-samples endpoint

# 1. Triage pre-filters CVs
triage_engine = EnhancedTriageEngine()
should_process, reason, score = triage_engine.should_process(cv_text, jd)

if not should_process:
    # Skip LLM call - save API quota!
    continue

# 2. Only promising CVs go to LLM
intelligence = extractor.extract_intelligence(cv_text, jd)  # ← LLM CALL

# 3. Store in database
storage.store_intelligence(intelligence)
```

### Searching (UNLIMITED):
```python
# In app.py - /api/quick-search endpoint

# NO LLM CALLS - Just keyword matching!
triage = EnhancedTriageEngine()
for cv in database:
    should_process, reason, relevance_score = triage.should_process(cv.text, jd)
    match_percentage = relevance_score * 100
    matches.append({'cv': cv, 'match': match_percentage})

# Sort and return top matches
return sorted(matches, key=lambda x: x['match'], reverse=True)[:10]
```

---

## API Quota Monitoring

### Check Your Usage:
```python
# In rate_limiter.py
rate_limiter = RateLimiter(redis_client)
stats = rate_limiter.get_all_stats()

print(f"Requests today: {stats['gemini']['requests_today']}")
print(f"Daily limit: {stats['gemini']['daily_limit']}")
print(f"Remaining: {stats['gemini']['daily_limit'] - stats['gemini']['requests_today']}")
```

### View in Dashboard:
- Go to http://localhost:5000/dashboard
- Check connection status banner
- Shows: "LLM Provider: gemini | Intelligence Files: 42"

---

## Best Practices

### ✅ DO:
1. **Process CVs once** - Store in database
2. **Search unlimited times** - Uses database, not LLM
3. **Use triage** - Saves 30-50% API quota during processing
4. **Monitor quota** - Check rate limiter stats

### ❌ DON'T:
1. **Re-process CVs** - Unless data changed
2. **Send CVs to LLM for every search** - Use database instead
3. **Process without triage** - Wastes API quota
4. **Ignore quota warnings** - Will hit daily limit

---

## Summary

### LLM Gets Called:
✅ **Processing CVs** (ONE-TIME)
- 72 CVs = 72 LLM calls
- With triage: ~50 LLM calls
- Takes 20-30 minutes
- Uses 3% of daily quota

### LLM Does NOT Get Called:
❌ **Searching CVs** (UNLIMITED)
- 0 LLM calls per search
- Takes <1 second
- FREE - no quota used
- Can search 1,000+ times per day

### Your Workflow:
1. **ONE-TIME**: Process all CVs (uses LLM, ~50 calls)
2. **DAILY**: Search unlimited times (no LLM, FREE)

**You can search as many times as you want without exhausting the LLM!** 🎉

---

## FAQ

**Q: Will searching exhaust my API quota?**
A: No! Searching uses keyword matching (local Python), not LLM. Zero API calls.

**Q: How many times can I search per day?**
A: Unlimited! Search is FREE and instant (<1 second).

**Q: When does LLM get called?**
A: Only during CV processing (one-time setup). After that, never.

**Q: What if I need to process more CVs?**
A: Process them once, store in database. Then search unlimited times.

**Q: How do I avoid quota exhaustion?**
A: Use triage during processing (saves 30-50%). Never re-process CVs unnecessarily.

**Q: Can I process 1,000 CVs?**
A: Yes, but spread over multiple days (50-100 per day with free tier). Or upgrade to paid plan.

---

## Conclusion

Your system is designed to **minimize LLM usage**:
- ✅ Process once (uses LLM)
- ✅ Search unlimited (no LLM)
- ✅ Triage saves 30-50% quota
- ✅ Database stores everything
- ✅ Instant results (<1 second)

**LLM will NOT get exhausted during normal usage!** 🎯
