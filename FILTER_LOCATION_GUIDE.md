# Where Are The Filter Options? 🎯

## Visual Guide

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 CV Intelligence System                                   │
│  AI-Powered Candidate Screening & Matching                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📊 Dashboard  │  🔍 Search  │  ⚙️ Process CVs             │  ← CLICK "SEARCH" TAB
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔍 Search & Filter Candidates                               │
│                                                               │
│  ⚡ Instant search with advanced filters. Results in <1s     │
│                                                               │
│  Job Description (Optional - for keyword matching)           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Enter job description for keyword matching...        │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  🎯 Advanced Filters  ← FILTERS ARE HERE!                   │
│                                                               │
│  ┌──────────────┬──────────────┬──────────────┬─────────┐  │
│  │ Verdict      │ Seniority    │ Min Match    │ Min     │  │
│  │ [All      ▼] │ [All      ▼] │ Score        │ Confid. │  │
│  │              │              │ [e.g., 70  ] │ [e.g.60]│  │
│  └──────────────┴──────────────┴──────────────┴─────────┘  │
│                                                               │
│  ┌──────────────┬──────────────┬──────────────┬─────────┐  │
│  │ Min Years    │ Max Years    │ Required     │ Primary │  │
│  │ Experience   │ Experience   │ Skills       │ Domain  │  │
│  │ [e.g., 3   ] │ [e.g., 10  ] │ [Python,AWS] │ [Web  ] │  │
│  └──────────────┴──────────────┴──────────────┴─────────┘  │
│                                                               │
│  [🔍 Search Candidates]  [🔄 Clear Filters]                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Instructions

### Step 1: Open the Search Tab
1. Go to http://localhost:5000
2. Click on the **"🔍 Search"** tab (second tab)

### Step 2: Scroll Down (if needed)
- The filters are right below the Job Description text area
- Look for the heading **"🎯 Advanced Filters"**

### Step 3: Use the Filters
You'll see 8 filter fields arranged in a grid:

**Row 1:**
- Verdict dropdown
- Seniority Level dropdown
- Min Match Score input
- Min Confidence input

**Row 2:**
- Min Years Experience input
- Max Years Experience input
- Required Skills input
- Primary Domain input

---

## Filter Details

### 1. Verdict Filter
**Dropdown options:**
- All (default)
- SHORTLIST
- BACKUP
- REVIEW
- REJECT

**Example:** Select "SHORTLIST" to see only shortlisted candidates

---

### 2. Seniority Level Filter
**Dropdown options:**
- All (default)
- ENTRY
- MID
- SENIOR
- LEAD
- EXECUTIVE

**Example:** Select "SENIOR" to see only senior-level candidates

---

### 3. Min Match Score (%)
**Input field:** Enter a number between 0-100

**Example:** Enter "70" to see only candidates with 70%+ match score

---

### 4. Min Confidence (%)
**Input field:** Enter a number between 0-100

**Example:** Enter "60" to see only candidates with 60%+ confidence

---

### 5. Min Years Experience
**Input field:** Enter a number (can be decimal like 3.5)

**Example:** Enter "3" to see only candidates with 3+ years experience

---

### 6. Max Years Experience
**Input field:** Enter a number (can be decimal like 10.5)

**Example:** Enter "10" to see only candidates with up to 10 years experience

---

### 7. Required Skills
**Input field:** Enter comma-separated skills

**Example:** Enter "Python, AWS, Docker" to find candidates with ALL these skills

**Note:** Search is case-insensitive and partial match

---

### 8. Primary Domain
**Input field:** Enter domain name

**Example:** Enter "Web Development" to find candidates in web development

**Note:** Search is case-insensitive and partial match

---

## How to Use Filters

### Example 1: Find Senior Python Developers
```
Seniority Level: SENIOR
Required Skills: Python
Min Years Experience: 5
```

### Example 2: Find High-Confidence Shortlisted Candidates
```
Verdict: SHORTLIST
Min Confidence: 80
```

### Example 3: Find Mid-Level AWS Experts
```
Seniority Level: MID
Required Skills: AWS
Min Years Experience: 3
Max Years Experience: 7
```

### Example 4: Combine with Job Description
```
Job Description: [Enter your JD here]
Verdict: SHORTLIST
Min Match Score: 70
Required Skills: Python, React
```

---

## Buttons

### 🔍 Search Candidates
- Click this to execute the search with your filters
- Results appear instantly (<1 second)

### 🔄 Clear Filters
- Click this to reset all filters to default
- Clears job description and all filter fields

---

## What You'll See in Results

After clicking "Search Candidates", you'll see:

```
┌─────────────────────────────────────────────────────────────┐
│  Search Results (X matches)                                  │
│  ✓ Found X matches in 0.027s                                │
└─────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┐
│  CAND_123    │  CAND_456    │  CAND_789    │
│  85% Match   │  78% Match   │  72% Match   │
│              │              │              │
│  Verdict:    │  Verdict:    │  Verdict:    │
│  SHORTLIST   │  BACKUP      │  SHORTLIST   │
│              │              │              │
│  Experience: │  Experience: │  Experience: │
│  5 years     │  3 years     │  7 years     │
│  (SENIOR)    │  (MID)       │  (SENIOR)    │
│              │              │              │
│  Domain:     │  Domain:     │  Domain:     │
│  Web Dev     │  Cloud       │  Backend     │
│              │              │              │
│  Skills:     │  Skills:     │  Skills:     │
│  Python AWS  │  AWS Docker  │  Python Go   │
│  React Node  │  Kubernetes  │  PostgreSQL  │
└──────────────┴──────────────┴──────────────┘
```

---

## Troubleshooting

### "I don't see the filters!"
**Solution:** 
1. Make sure you're on the **Search** tab (not Dashboard or Process CVs)
2. Scroll down below the Job Description text area
3. Look for "🎯 Advanced Filters" heading

### "Filters don't work!"
**Solution:**
1. Make sure you clicked "🔍 Search Candidates" button
2. Check if you have CVs in the database (Dashboard should show count > 0)
3. Try clearing filters and searching again

### "No results found"
**Solution:**
1. Your filters might be too strict
2. Click "🔄 Clear Filters" and try again
3. Try with just one or two filters instead of all

---

## Summary

✅ Filters are in the **Search** tab  
✅ Look for **"🎯 Advanced Filters"** heading  
✅ 8 filter options available  
✅ Can combine filters with job description  
✅ Results are instant (<1 second)  

The filters were always there - now they're more visible with the 🎯 icon!
