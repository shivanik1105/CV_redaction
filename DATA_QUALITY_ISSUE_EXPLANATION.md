# Data Quality Issue: "0 Years but SENIOR Level"

## The Problem

You noticed: **"Verdict: REVIEW, Experience: 0 years (SENIOR), Domain: Cloud Infrastructure"**

This is inconsistent - someone can't have 0 years of experience and be SENIOR level.

## Root Cause

The LLM (Gemini/GPT) failed to properly extract the `years_experience` field from some CVs. This happens when:

1. **CV format is unclear** - Years not explicitly stated
2. **LLM parsing error** - Model misunderstood the CV structure
3. **Redacted text confusion** - PII redaction removed context clues
4. **Prompt not specific enough** - LLM didn't prioritize years extraction

## Scale of the Issue

Running `python check_data_quality.py` found:

```
⚠️ Found 79 data quality issues:

Zero years but senior level: 20 cases (28% of CVs)
Missing core technical skills: 35 cases (49% of CVs)
Missing primary domain: 24 cases (34% of CVs)
```

Out of ~72 CVs processed, 20 have the "0 years + SENIOR" inconsistency.

## What I Fixed (Frontend)

Updated `templates/dashboard.html` to handle this gracefully:

```javascript
// If years is 0 but seniority is MID/SENIOR/LEAD/EXECUTIVE, show "N/A"
if (yearsExp === 0 && ['MID', 'SENIOR', 'LEAD', 'EXECUTIVE'].includes(seniorityLevel)) {
    yearsExp = 'N/A';
}
```

**Before:**
```
Experience: 0 years (SENIOR)  ← Confusing!
```

**After:**
```
Experience: N/A (SENIOR)  ← Clear that data is missing
```

## Solutions

### Option 1: Re-process CVs with Better Prompt (Recommended)

The LLM extraction prompt needs to be more explicit about years_experience:

```python
# In cv_intelligence_extractor.py, update the prompt to emphasize:
"CRITICAL: Extract total years of professional experience. 
Look for:
- 'X years of experience'
- Date ranges in work history (calculate total)
- 'Since YYYY' (calculate from current year)
If unclear, estimate from job titles and date ranges.
NEVER return 0 unless candidate is truly entry-level/fresher."
```

### Option 2: Manual Fix in Database

For the 20 affected CVs, you can:
1. Look at the original CV
2. Calculate years of experience manually
3. Update in Supabase:

```sql
UPDATE cv_intelligence 
SET years_of_experience = 5.0 
WHERE anonymized_id = 'CAND_396';
```

### Option 3: Accept the Limitation

- Frontend now shows "N/A" instead of "0 years"
- Recruiters can still see seniority level (SENIOR)
- They can review the full CV if needed

## Why This Happens

### Example CV that causes this:

```
Senior Cloud Engineer
Led team of 5 engineers
AWS, Docker, Kubernetes expert
[No explicit "X years of experience" statement]
[Date ranges redacted as PII]
```

The LLM sees:
- Title says "Senior" → seniority_level = SENIOR ✓
- No explicit years statement → years_experience = 0 ✗
- Skills listed → core_technical_skills = [...] ✓

## Recommendation

**For production use, you should:**

1. **Improve the LLM prompt** to better extract years
2. **Re-process the 20 affected CVs** with the improved prompt
3. **Add validation** to flag inconsistencies during extraction

**For now:**
- Frontend displays "N/A" instead of "0 years" for inconsistent data
- System is still usable - seniority level is correct
- Recruiters can review full CVs if years matter

## How to Re-process

If you want to fix this properly:

```bash
# 1. Update the prompt in cv_intelligence_extractor.py
# 2. Re-process affected CVs
python process_all_cvs_smart.py --jd "Your JD" --force-reprocess
```

Or process specific CVs:

```python
# Create a script to re-process only the 20 affected CVs
from cv_intelligence_extractor import CVIntelligenceExtractor

affected_ids = ['CAND_396', 'CAND_187', ...]  # From check_data_quality.py
for cand_id in affected_ids:
    # Re-extract intelligence with improved prompt
    # Update in database
```

## Summary

✅ **Frontend fixed** - Shows "N/A" instead of "0 years" for inconsistent data  
⚠️ **Root cause** - LLM extraction not capturing years_experience properly  
🔧 **Solution** - Re-process CVs with improved prompt (optional)  
📊 **Impact** - 20 out of 72 CVs affected (28%)  

The system is still functional - this is a data quality issue, not a system bug.
