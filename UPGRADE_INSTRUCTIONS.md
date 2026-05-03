# 🚀 Quick Upgrade Instructions

## Current Status
✅ **Model Configuration:** Updated to all-mpnet-base-v2 (768d)  
❌ **Database Schema:** Still at 384d - needs upgrade  
❌ **Embeddings:** Need regeneration with new model

## 📋 Complete These 2 Steps

### Step 1: Upgrade Database Schema (30 seconds)

1. Open your **Supabase Dashboard**
2. Go to **SQL Editor**
3. Copy and paste the contents of `supabase_upgrade_to_768d.sql`
4. Click **Run**

**What it does:**
- Drops old 384d embedding column
- Creates new 768d embedding column
- Updates RPC functions
- Recreates vector index

### Step 2: Regenerate All Embeddings (15-20 minutes)

Run this command in your terminal:

```bash
python regenerate_embeddings.py --force
```

**What it does:**
- Fetches all 139 candidates
- Generates new 768d embeddings with better model
- Updates database
- Shows progress for each candidate

**Expected output:**
```
============================================================
FORCE REGENERATE ALL EMBEDDINGS (MODEL UPGRADE)
============================================================

✓ Connected to Supabase
✓ Loaded embedding model: all-mpnet-base-v2
  Dimensions: 768

Generating embeddings for 139 candidates...
  [1/139] ✓ CAND_001 (768d)
  [2/139] ✓ CAND_002 (768d)
  ...
  [139/139] ✓ CAND_849 (768d)

✓ Successfully generated: 139
🎉 Semantic search is now enabled with upgraded model!
```

## ✅ Verify Upgrade

After completing both steps, run:

```bash
python check_upgrade_status.py
```

Should show:
```
✅ UPGRADE COMPLETE!

All systems ready:
  ✓ Model configured for 768d
  ✓ Database schema upgraded
  ✓ All embeddings regenerated
```

## 🧪 Test Improved Accuracy

Run the test suite:

```bash
python test_15_real_jds.py
```

**Expected improvements:**
- Average top match: **63.3%** (was 56.6%)
- Relevant JDs: **5/5** (was 4/5)
- Better contextual understanding

## 🎯 Expected Results

### Before (384d model)
```
Model: all-MiniLM-L6-v2
Dimensions: 384
Avg Top Score: 56.6%
Relevant JDs: 4/5
```

### After (768d model)
```
Model: all-mpnet-base-v2
Dimensions: 768
Avg Top Score: 63.3%
Relevant JDs: 5/5
```

**Improvement: +11.7% better accuracy** 🎉

## 📚 Additional Resources

- **Full Guide:** `EMBEDDING_MODEL_UPGRADE_GUIDE.md`
- **Benchmark Results:** `MODEL_COMPARISON_RESULTS.md`
- **SQL Migration:** `supabase_upgrade_to_768d.sql`
- **Status Check:** `python check_upgrade_status.py`

## 🚨 Troubleshooting

**Issue:** "Embedding dimension mismatch"  
**Fix:** Make sure you ran Step 1 (database schema upgrade) first

**Issue:** "Model download failed"  
**Fix:** First-time download is 420MB, wait for it to complete

**Issue:** Script shows errors  
**Fix:** Check your Supabase connection and credentials

---

**Questions?** Review the full guide in `EMBEDDING_MODEL_UPGRADE_GUIDE.md`
