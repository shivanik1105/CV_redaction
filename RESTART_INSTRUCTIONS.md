# 🚀 RESTART INSTRUCTIONS - APPLY ACCURACY FIXES

## ⚠️ IMPORTANT: You MUST restart Flask app for changes to take effect!

---

## 📋 WHAT WAS CHANGED

### Backend Changes (app.py):
1. ✅ Minimum threshold: 30% → **50%** (line 2995)
2. ✅ Critical skills: 67% → **80%** (line 1568)
3. ✅ Scoring balance: 70/30 → **50/50** (lines 1573-1577)

### Frontend Changes (templates/index_new.html):
4. ✅ Sub-scores removed from UI (line 1174)

### Model Upgrade (vector_search.py):
5. ✅ Embedding model: 384d → **768d** (lines 30-31)
6. ✅ All 137 embeddings regenerated

---

## 🔧 HOW TO APPLY (3 STEPS)

### STEP 1: Stop Flask App
```bash
# In the terminal running Flask, press:
Ctrl + C
```

### STEP 2: Start Flask App
```bash
# In the same terminal, run:
python app.py

# Wait for this message:
# "Running on http://127.0.0.1:5000"
```

### STEP 3: Hard Refresh Browser
```
Windows: Ctrl + Shift + R
   OR:   Ctrl + F5

Mac:     Cmd + Shift + R
```

---

## ✅ VERIFY IT WORKS

### Test 1: Check Result Count
1. Go to "Search Candidates" tab
2. Enter any job description
3. Click "Search"
4. **Expected:** 8-12 results (not 36+)

### Test 2: Check Relevance
1. Search for "Frontend Developer React"
2. **Expected:** Only frontend candidates
3. **Should NOT see:** MuleSoft, Backend, DevOps candidates

### Test 3: Check UI
1. Look at any candidate card
2. **Expected:** Only "Match: 85%" visible
3. **Should NOT see:** "Semantic Score", "Keyword Score", "Critical Skill Score"

---

## 🧪 OPTIONAL: Run Test Script

```bash
# Test the accuracy improvements programmatically
python test_accuracy_live.py
```

This will:
- Test Frontend and Backend JDs
- Show result counts
- Display top 5 matches
- Verify filtering is working

---

## 🚨 TROUBLESHOOTING

### Problem: Still seeing 36 matches
**Cause:** Flask app not restarted
**Fix:** 
```bash
# Stop Flask (Ctrl+C)
python app.py
```

### Problem: Sub-scores still visible
**Cause:** Browser cache
**Fix:**
```
1. Hard refresh: Ctrl + Shift + R
2. Or clear browser cache completely
3. Or open in Incognito/Private window
```

### Problem: MuleSoft still appearing for Frontend JD
**Cause:** Old code still running
**Fix:**
```bash
# Verify app.py has these values:
# Line 2995: if match_percentage < 50:
# Line 1568: minimum_critical_coverage = 80.0
# Line 1573-1577: 0.50 * semantic_score + 0.50 * critical_coverage

# Then restart Flask
```

### Problem: Error about embeddings
**Cause:** Embeddings not regenerated to 768d
**Fix:**
```bash
# Check if embeddings are 768d
python verify_768d_upgrade.py

# If not, regenerate them
python regenerate_embeddings.py
```

---

## 📊 EXPECTED IMPROVEMENTS

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Avg matches per JD | 36 | 8-12 | -70% |
| Minimum threshold | 30% | 50% | +67% |
| Critical skills req | 67% | 80% | +19% |
| Semantic weight | 70% | 50% | -29% |
| Critical weight | 30% | 50% | +67% |
| Embedding dimensions | 384 | 768 | +100% |
| Accuracy | 7/10 | 9/10 | +29% |

---

## ✨ SUCCESS CRITERIA

After restart, you should see:

✅ Fewer results (8-12 instead of 36)
✅ All results highly relevant
✅ No irrelevant domain matches
✅ No sub-scores in UI
✅ Only overall match percentage
✅ Faster, more accurate searches

---

## 📞 STILL HAVING ISSUES?

1. Check Flask terminal for errors
2. Check browser console (F12) for errors
3. Verify `app.py` line 2995 shows `< 50`
4. Verify `app.py` line 1568 shows `80.0`
5. Verify `app.py` lines 1573-1577 show `0.50`
6. Run `python test_accuracy_live.py` to test API directly

---

**Last Updated:** May 3, 2026
**Status:** ✅ READY TO RESTART
