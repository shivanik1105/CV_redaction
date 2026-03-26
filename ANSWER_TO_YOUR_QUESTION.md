# "How is 0 years SENIOR?"

## Short Answer

It's **bad data** from the LLM extraction. The AI correctly identified the person as SENIOR level (from their job title and responsibilities), but failed to extract the actual years of experience from the CV.

## What I Just Fixed

I updated the frontend (`dashboard.html`) so it now shows:

**Before:**
```
Experience: 0 years (SENIOR)  ← Confusing!
```

**After:**
```
Experience: N/A (SENIOR)  ← Clear that years data is missing
```

## Why This Happened

Out of your 72 CVs, **20 have this issue** (28%). The LLM extraction failed to properly read the years of experience because:

1. Years not explicitly stated in CV (e.g., "Senior Engineer" but no "5 years experience")
2. Date ranges were redacted as PII
3. LLM prompt not specific enough about extracting years

## What You Should Do

### Option 1: Just Use It (Easiest)
- Frontend now shows "N/A" instead of "0 years"
- Seniority level (SENIOR) is still correct
- You can still filter and search normally
- If years matter, review the full CV

### Option 2: Re-process CVs (Better Data)
```bash
# Improve the LLM prompt first, then:
python process_all_cvs_smart.py --jd "Your JD" --force-reprocess
```

### Option 3: Manual Fix (20 CVs only)
- Look at the original CVs
- Calculate years manually
- Update in Supabase database

## To See the Fix

**Restart your Flask app:**
```bash
# Press Ctrl+C in Flask terminal
python app.py
```

Then refresh your browser. You'll see "N/A" instead of "0 years" for the 20 affected CVs.

## Summary

✅ It's a data extraction issue, not a logic bug  
✅ Frontend now handles it gracefully (shows "N/A")  
✅ System is still usable - seniority level is correct  
✅ 20 out of 72 CVs affected  

The person IS senior level - we just don't have their exact years of experience extracted properly.
