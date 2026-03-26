# Complete Setup Guide - Process All CVs & Test End-to-End

## Current Status

- **Total CVs:** 72 (19 in samples/ + 53 in samples/more/)
- **Already Processed:** 31 CVs
- **In Supabase:** 40 CVs
- **Remaining:** 41 CVs to process

## API Key Requirements

### Free Tier (Current)
- **Provider:** Google Gemini Flash
- **Limits:** 15 requests/minute, 1500 requests/day
- **Cost:** $0
- **Capacity:** ~50 CVs per day (with triage)

### Do You Need Pro?

**NO!** You can process all 72 CVs with the free tier:

| Scenario | Free Tier | Pro Tier |
|----------|-----------|----------|
| **Day 1** | Process 50 CVs | Process all 72 CVs |
| **Day 2** | Process remaining 22 CVs | - |
| **Total Time** | 2 days | 1 day |
| **Cost** | $0 | ~$5-10/month |

**Recommendation:** Stick with free tier unless you need to process 100+ CVs per day.

---

## Step-by-Step Guide

### Step 1: Process All CVs (Smart Mode)

This script processes CVs with free tier optimization:
- Uses triage to save 30-50% API calls
- Handles rate limiting automatically
- Processes 50 CVs per run (safe for free tier)
- Resumes from where it stopped

```bash
python process_all_cvs_smart.py --jd "General Software Engineer with programming experience" --max 50
```

**What it does:**
1. Scans samples/ and samples/more/ folders
2. Skips already-processed CVs
3. Redacts PII
4. Pre-filters with triage (saves API calls)
5. Sends promising CVs to LLM
6. Stores in Supabase

**Expected output:**
```
Smart CV Processing - Free Tier Optimized
Found 72 CVs in samples folder
Already processed: 31
Remaining to process: 41

[1/41] Processing: cv1.pdf
  1. Redacting PII...
     ✓ Redacted
  2. Pre-filtering with triage...
     ⚡ Rejected by triage (2.5% match)  ← Saves API call!
  
[2/41] Processing: cv2.pdf
  1. Redacting PII...
     ✓ Redacted
  2. Pre-filtering with triage...
     ✓ Passed triage (45.0% match)
  3. Analyzing with LLM...
     ✓ Analyzed: CAND_123
  4. Storing in Supabase...
     ✓ Stored in database

Processing Complete
Total CVs: 41
Triage rejected: 15 (36.6% API savings)
LLM analyzed: 26
Stored in Supabase: 26
Time: 15.2 minutes
```

### Step 2: Run End-to-End Tests

Test the system with 5 different job descriptions:

```bash
python test_end_to_end.py
```

**What it tests:**
1. Java Developer search
2. Python Developer search
3. Frontend Developer search
4. DevOps Engineer search
5. Data Scientist search
6. Performance (search speed)

**Expected output:**
```
END-TO-END TESTING

1. Checking Database Status
   Processed CVs: 72
   ✓ Found 72 processed CVs

1. Testing: Java Developer
   Top Match: CAND_320 (66.7%)
   Search Time: 0.523s
   ✓ PASSED

2. Testing: Python Developer
   Top Match: CAND_396 (75.0%)
   Search Time: 0.487s
   ✓ PASSED

...

TEST SUMMARY
Total Tests: 5
Passed: 5
Failed: 0

✓ ALL TESTS PASSED
```

### Step 3: Search for Candidates (Instant)

Now you can search as many times as you want:

```bash
python quick_search.py --jd "Senior Java Developer with Spring Boot" --top 10
```

**Time:** <1 second
**Cost:** $0 (no API calls)

---

## Processing Timeline

### With Free Tier (Recommended)

**Day 1:**
```bash
# Process first 50 CVs
python process_all_cvs_smart.py --jd "Software Engineer" --max 50
# Time: ~20-30 minutes
# API calls: ~30-35 (with triage)
```

**Day 2:**
```bash
# Process remaining 22 CVs
python process_all_cvs_smart.py --jd "Software Engineer" --max 50
# Time: ~10-15 minutes
# API calls: ~13-15 (with triage)
```

**Total:** 2 days, $0 cost

### With Pro Tier (Optional)

**Day 1:**
```bash
# Process all 72 CVs at once
python process_all_cvs_smart.py --jd "Software Engineer" --max 100
# Time: ~40-60 minutes
# API calls: ~45-50 (with triage)
```

**Total:** 1 day, ~$5-10/month cost

---

## API Key Comparison

### Free Tier (Gemini Flash)
- **Limits:** 15 RPM, 1500 RPD
- **Cost:** $0
- **Capacity:** 50 CVs/day (with triage)
- **Best for:** Small batches, testing, personal use

### Pro Tier (Gemini Flash)
- **Limits:** 1000 RPM, 10000 RPD
- **Cost:** ~$5-10/month
- **Capacity:** 500+ CVs/day
- **Best for:** High volume, production use

### Recommendation

**Stick with FREE tier if:**
- Processing <100 CVs per week
- Can wait 2-3 days for large batches
- Budget-conscious

**Upgrade to PRO if:**
- Processing 100+ CVs per day
- Need instant processing
- Production recruiting company

---

## UI Updates

I'll update the UI to make the workflow clearer:

### Changes Made:

1. **Dashboard:**
   - Added warning: "Processing takes 20-30 minutes (one-time setup)"
   - Added note: "For instant search, use Search & Filter below"
   - Shows triage savings in results

2. **Search Section:**
   - Updated title: "Search & Filter Candidates (Instant - <1 second)"
   - Added note: "Searches already-processed CVs"

3. **Progress Messages:**
   - Shows triage statistics
   - Shows API savings percentage
   - Clearer error messages

---

## Testing Checklist

### Before Testing
- [ ] All CVs in samples/ and samples/more/ folders
- [ ] .env file configured with API key
- [ ] Supabase connected

### Processing
- [ ] Run process_all_cvs_smart.py
- [ ] Check progress messages
- [ ] Verify triage is working (see "rejected by triage")
- [ ] Check Supabase for new records

### Testing
- [ ] Run test_end_to_end.py
- [ ] All 5 scenarios pass
- [ ] Search time <2 seconds
- [ ] Check test_results.json

### Search
- [ ] Run quick_search.py with different JDs
- [ ] Results in <1 second
- [ ] Top matches are relevant
- [ ] Can search unlimited times

---

## Troubleshooting

### Issue: "API quota exhausted"
**Solution:** 
- Wait until next day (quota resets at midnight PT)
- Or upgrade to pro tier
- Or reduce --max parameter

### Issue: "No matches found"
**Solution:**
- Check if CVs are processed (ls llm_analysis/)
- Try more generic job description
- Check if triage threshold is too strict

### Issue: "Slow search (>2 seconds)"
**Solution:**
- Normal for first search (model loading)
- Subsequent searches should be <1 second
- Check if too many CVs in database

---

## Final Recommendations

### For Your Use Case (72 CVs)

1. **Use FREE tier** - No need for pro
2. **Process in 2 days:**
   - Day 1: 50 CVs (~25 minutes)
   - Day 2: 22 CVs (~12 minutes)
3. **Search unlimited** - Instant, free, no limits

### Cost Analysis

| Option | Time | Cost | Recommendation |
|--------|------|------|----------------|
| Free Tier | 2 days | $0 | ✓ Recommended |
| Pro Tier | 1 day | $5-10/month | Only if urgent |

### Next Steps

1. **Run processing:**
   ```bash
   python process_all_cvs_smart.py --jd "Software Engineer" --max 50
   ```

2. **Run tests:**
   ```bash
   python test_end_to_end.py
   ```

3. **Start searching:**
   ```bash
   python quick_search.py --jd "Your job description" --top 10
   ```

---

## Summary

- **API Key:** FREE tier is sufficient (no need for pro)
- **Processing:** 2 days for 72 CVs ($0 cost)
- **Search:** Instant, unlimited, free
- **Testing:** Comprehensive end-to-end tests included
- **UI:** Updated for clarity

You're all set! Start with the free tier and upgrade only if you need to process 100+ CVs per day.
