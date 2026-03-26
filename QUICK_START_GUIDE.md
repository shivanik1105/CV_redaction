# Quick Start Guide - Fixed Frontend

## What Was Fixed

✅ **Dashboard N/A Issue** - Now shows real candidate data  
✅ **Advanced Filters** - Clearly visible in Search tab with 🎯 icon  
✅ **Upload Tab** - Removed (not needed for your workflow)  
✅ **Data Mapping** - Fixed Supabase column name mismatches  

---

## How to Use the System

### Step 1: Restart Flask App (if needed)

```bash
# Stop current Flask app (Ctrl+C in the terminal where it's running)
# Then restart:
python app.py
```

### Step 2: Open the Frontend

Open your browser and go to: **http://localhost:5000**

You'll see three tabs:
- 📊 Dashboard
- 🔍 Search  
- ⚙️ Process CVs

---

## Tab Guide

### 📊 Dashboard Tab

**What it shows:**
- Total CVs in database
- Shortlisted candidates
- Candidates needing review
- Average match score
- Recent candidates (last 10)

**What you'll see now (FIXED):**
- Real candidate IDs (CAND_XXX)
- Actual verdicts (SHORTLIST/BACKUP/REVIEW)
- Real experience years and seniority levels
- Actual domains and skills
- NO MORE "N/A" everywhere!

---

### 🔍 Search Tab

**Two ways to search:**

#### Option 1: Keyword Search (with Job Description)
1. Enter a job description in the text area
2. Optionally set filters below
3. Click "🔍 Search Candidates"
4. Get instant results (<1 second)

#### Option 2: Filter-Only Search
1. Leave job description empty
2. Set any combination of filters:
   - **Verdict** - SHORTLIST/BACKUP/REVIEW/REJECT
   - **Seniority Level** - ENTRY/MID/SENIOR/LEAD/EXECUTIVE
   - **Min Match Score** - e.g., 70 (only candidates with 70%+ match)
   - **Min Confidence** - e.g., 60 (only candidates with 60%+ confidence)
   - **Min Years Experience** - e.g., 3 (3+ years)
   - **Max Years Experience** - e.g., 10 (up to 10 years)
   - **Required Skills** - e.g., "Python, AWS, Docker" (comma-separated)
   - **Primary Domain** - e.g., "Web Development"
3. Click "🔍 Search Candidates"

**Filter Examples:**

```
Example 1: Senior Python Developers
- Seniority Level: SENIOR
- Required Skills: Python
- Min Years Experience: 5

Example 2: High-Confidence Shortlisted Candidates
- Verdict: SHORTLIST
- Min Confidence: 80

Example 3: AWS Experts with 3-7 Years Experience
- Required Skills: AWS
- Min Years Experience: 3
- Max Years Experience: 7
```

---

### ⚙️ Process CVs Tab

**When to use:** ONE-TIME ONLY (to build your database)

**What it does:**
- Processes all CVs in the `samples` folder
- Extracts intelligence using LLM
- Stores results in Supabase
- Takes 20-30 minutes for 100 CVs

**How to use:**
1. Enter a job description
2. Click "📂 Process All Sample CVs"
3. Wait for completion
4. After this, use Search tab for instant results

**Note:** You mentioned "25 CVs remaining" - this is because the script has a daily limit to protect your free API quota. Run it again tomorrow to process the rest, or increase the limit in `process_all_cvs_smart.py`.

---

## Common Questions

### Q: Why is the dashboard still showing N/A?
**A:** Restart the Flask app to load the updated code:
```bash
# Press Ctrl+C in the Flask terminal
python app.py
```

### Q: Where are the filter options?
**A:** In the Search tab, scroll down below the Job Description field. You'll see "🎯 Advanced Filters" heading with 8 filter options.

### Q: Do I need the Upload tab?
**A:** No, it's been removed. You have a better workflow:
1. Put CVs in `samples` folder
2. Use "Process CVs" tab (one-time)
3. Use "Search" tab (instant, unlimited)

### Q: Why does processing take so long?
**A:** Processing is ONE-TIME setup (20-30 min for 100 CVs). After that, searching is instant (<1 second). This is the correct workflow for recruiting companies.

### Q: How do I process the remaining 25 CVs?
**A:** Run this command:
```bash
python process_all_cvs_smart.py --jd "Software Engineer" --max 100
```

Or wait until tomorrow (free API quota resets daily).

---

## Troubleshooting

### Dashboard shows "0 Total CVs"
**Cause:** No CVs processed yet  
**Solution:** Go to "Process CVs" tab and process your sample CVs

### Search returns no results
**Cause:** Filters too strict or no CVs match  
**Solution:** 
- Try clearing filters (click "🔄 Clear Filters")
- Try with just job description (no filters)
- Check if CVs are processed (Dashboard should show count > 0)

### "25 CVs remaining" message
**Cause:** Daily API quota limit (safety feature)  
**Solution:** 
- Wait until tomorrow (quota resets at midnight PT)
- Or increase limit: Edit `process_all_cvs_smart.py`, change `max_per_day=50` to `max_per_day=100`

---

## Next Steps

1. ✅ Restart Flask app
2. ✅ Open http://localhost:5000
3. ✅ Check Dashboard (should show real data now)
4. ✅ Try Search with filters
5. ✅ Process remaining CVs if needed

---

## Summary

Your frontend is now fully functional with:
- ✅ Real data in Dashboard (no more N/A)
- ✅ 8 advanced filter options in Search tab
- ✅ Clean 3-tab interface (removed Upload)
- ✅ Instant search (<1 second)
- ✅ Proper data mapping from Supabase

Enjoy your CV Intelligence System! 🎯
