# Filename Mapping Architecture - Visual Guide

## The Problem

```
Original CV Upload
"John_Doe_Resume.pdf"
         ↓
    Anonymization
         ↓
    "CAND_882"
         ↓
    ❓ How to map back?
```

## The Solution: Three-Tier Storage

```
┌─────────────────────────────────────────────────────────────┐
│                    CV PROCESSING FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. Upload CV
   "John_Doe_Resume.pdf"
         │
         ↓
2. Anonymize
   Generate ID: "CAND_882"
   Create file: "REDACTED_20240405_123456_JohnDoe.txt"
         │
         ↓
3. Store Mapping (THREE PLACES)
         │
         ├─────────────────────────────────────────┐
         │                                         │
         ↓                                         ↓
   ┌─────────────┐                          ┌──────────────┐
   │  TIER 1:    │                          │   TIER 2:    │
   │  Supabase   │                          │  Local JSON  │
   │  Database   │                          │     File     │
   └─────────────┘                          └──────────────┘
         │                                         │
         │  cv_filename_mapping table              │  filename_mappings.json
         │  ┌──────────────────────┐              │  {
         │  │ anonymized_id        │              │    "CAND_882": {
         │  │ original_filename    │              │      "original": "...",
         │  │ anonymized_filename  │              │      "anonymized": "..."
         │  │ created_at           │              │    }
         │  └──────────────────────┘              │  }
         │                                         │
         └─────────────┬───────────────────────────┘
                       │
                       ↓
                 ┌──────────────┐
                 │   TIER 3:    │
                 │ Intelligence │
                 │    Files     │
                 └──────────────┘
                       │
                       │  CAND_882_intelligence.json
                       │  {
                       │    "anonymized_id": "CAND_882",
                       │    "original_filename": "...",
                       │    "redacted_filename": "..."
                       │  }
```

## Storage Tier Details

### Tier 1: Supabase Database (Primary)

```
┌────────────────────────────────────────────────────────┐
│              SUPABASE DATABASE                         │
│                                                        │
│  Table: cv_filename_mapping                           │
│  ┌──────────────┬─────────────────┬─────────────────┐│
│  │ anonymized_id│ original_filename│ anonymized_file ││
│  ├──────────────┼─────────────────┼─────────────────┤│
│  │ CAND_882     │ John_Doe.pdf    │ REDACTED_...    ││
│  │ CAND_883     │ Jane_Smith.docx │ REDACTED_...    ││
│  │ CAND_884     │ Bob_Lee.pdf     │ REDACTED_...    ││
│  └──────────────┴─────────────────┴─────────────────┘│
│                                                        │
│  ✓ Centralized                                        │
│  ✓ Backed up                                          │
│  ✓ Multi-user                                         │
│  ✗ Requires network                                   │
└────────────────────────────────────────────────────────┘
```

### Tier 2: Local JSON File (Fallback)

```
┌────────────────────────────────────────────────────────┐
│           LOCAL JSON FILE                              │
│                                                        │
│  File: filename_mappings.json                         │
│  {                                                     │
│    "CAND_882": {                                      │
│      "original_filename": "John_Doe_Resume.pdf",     │
│      "anonymized_filename": "REDACTED_...",          │
│      "created_at": "2024-04-05T12:34:56",           │
│      "last_updated": "2024-04-05T12:34:56"          │
│    },                                                 │
│    "CAND_883": { ... },                              │
│    "CAND_884": { ... }                               │
│  }                                                     │
│                                                        │
│  ✓ Works offline                                      │
│  ✓ Fast (<1ms)                                        │
│  ✓ No network needed                                  │
│  ✗ Not shared across machines                        │
└────────────────────────────────────────────────────────┘
```

### Tier 3: Intelligence Files (Recovery)

```
┌────────────────────────────────────────────────────────┐
│         INTELLIGENCE JSON FILES                        │
│                                                        │
│  llm_analysis/                                        │
│  ├── CAND_882_intelligence.json                       │
│  │   {                                                │
│  │     "anonymized_id": "CAND_882",                  │
│  │     "original_filename": "John_Doe_Resume.pdf",   │
│  │     "redacted_filename": "REDACTED_...",          │
│  │     "verdict": "SHORTLIST",                       │
│  │     ...                                            │
│  │   }                                                │
│  ├── CAND_883_intelligence.json                       │
│  └── CAND_884_intelligence.json                       │
│                                                        │
│  ✓ Self-contained                                     │
│  ✓ Can rebuild everything                             │
│  ✗ Slow for bulk queries                              │
└────────────────────────────────────────────────────────┘
```

## Lookup Flow

### Forward Lookup (ID → Filename)

```
User Query: "What's the original file for CAND_882?"
         │
         ↓
   ┌─────────────────┐
   │ Try Supabase    │
   │ (10-50ms)       │
   └────────┬────────┘
            │
            ├─ Success? → Return result
            │
            ↓ Fail/Timeout
   ┌─────────────────┐
   │ Try Local JSON  │
   │ (<1ms)          │
   └────────┬────────┘
            │
            ├─ Success? → Return result
            │
            ↓ Not found
   ┌─────────────────┐
   │ Search          │
   │ Intelligence    │
   │ Files           │
   └────────┬────────┘
            │
            └─ Return result or "Not found"
```

### Reverse Lookup (Filename → ID)

```
User Query: "Find CAND ID for John_Doe_Resume.pdf"
         │
         ↓
   ┌─────────────────┐
   │ Try Supabase    │
   │ WHERE original  │
   │ = 'John_Doe...' │
   └────────┬────────┘
            │
            ├─ Success? → Return CAND_882
            │
            ↓ Fail/Timeout
   ┌─────────────────┐
   │ Search Local    │
   │ JSON by value   │
   └────────┬────────┘
            │
            └─ Return CAND_882 or "Not found"
```

## CLI Tool Architecture

```
┌──────────────────────────────────────────────────────────┐
│         manage_filename_mappings.py                      │
│                                                          │
│  Commands:                                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ list      → Show all mappings                      │ │
│  │ lookup    → Find specific mapping                  │ │
│  │ sync      → Rebuild from intelligence files        │ │
│  │ export    → Create CSV backup                      │ │
│  │ stats     → Show statistics                        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Uses:                                                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │ FilenameMappingManager                             │ │
│  │  ├─ store_mapping()                                │ │
│  │  ├─ get_mapping()                                  │ │
│  │  ├─ reverse_lookup_by_original()                   │ │
│  │  ├─ get_all_mappings()                             │ │
│  │  ├─ sync_from_intelligence_files()                 │ │
│  │  └─ export_mappings_csv()                          │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Failure Scenarios & Recovery

### Scenario 1: Supabase Down

```
CV Upload → Store Mapping
                │
                ↓
         Try Supabase
                │
                ✗ TIMEOUT
                │
                ↓
         Store Local JSON ✓
                │
                ↓
         Continue Processing
         (No user impact!)
```

### Scenario 2: Local File Deleted

```
User: "Lookup CAND_882"
         │
         ↓
   Try Supabase ✓
         │
         ↓
   Return result
         │
         ↓
   Auto-save to local JSON
   (Rebuilds cache)
```

### Scenario 3: Both Lost

```
Admin: "python manage_filename_mappings.py sync"
         │
         ↓
   Scan llm_analysis/
         │
         ├─ CAND_882_intelligence.json → Extract mapping
         ├─ CAND_883_intelligence.json → Extract mapping
         ├─ CAND_884_intelligence.json → Extract mapping
         │
         ↓
   Rebuild filename_mappings.json
         │
         ↓
   ✓ Recovered 167 mappings!
```

## Integration with app.py

```
┌──────────────────────────────────────────────────────────┐
│                    app.py                                │
│                                                          │
│  CV Upload Handler                                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 1. Receive CV file                                 │ │
│  │ 2. Anonymize → Generate CAND_882                   │ │
│  │ 3. Extract intelligence                            │ │
│  │ 4. Store intelligence in Supabase                  │ │
│  │ 5. ┌────────────────────────────────────────────┐ │ │
│  │    │ NEW: Store filename mapping                │ │ │
│  │    │                                            │ │ │
│  │    │ filename_manager.store_mapping(            │ │ │
│  │    │   anonymized_id="CAND_882",               │ │ │
│  │    │   original_filename="John_Doe.pdf",       │ │ │
│  │    │   anonymized_filename="REDACTED_...",     │ │ │
│  │    │   supabase_storage=storage                │ │ │
│  │    │ )                                          │ │ │
│  │    │                                            │ │ │
│  │    │ → Stores in Supabase ✓                    │ │ │
│  │    │ → Stores in Local JSON ✓                  │ │ │
│  │    └────────────────────────────────────────────┘ │ │
│  │ 6. Return success to user                          │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────┐
│   CV File   │
│ John_Doe.pdf│
└──────┬──────┘
       │
       ↓
┌─────────────────┐
│  Anonymization  │
│  CAND_882       │
└────────┬────────┘
         │
         ├──────────────────────────────────────┐
         │                                      │
         ↓                                      ↓
┌──────────────────┐                  ┌──────────────────┐
│  Intelligence    │                  │  Filename        │
│  Extraction      │                  │  Mapping         │
│                  │                  │                  │
│  • Skills        │                  │  Store in:       │
│  • Experience    │                  │  1. Supabase     │
│  • Verdict       │                  │  2. Local JSON   │
│  • Embedding     │                  │  3. Intel File   │
└────────┬─────────┘                  └──────────────────┘
         │
         ↓
┌──────────────────┐
│  Store in        │
│  Supabase        │
│  • Intelligence  │
│  • Embedding     │
│  • Mapping       │
└──────────────────┘
```

## Performance Comparison

```
┌────────────────────────────────────────────────────────┐
│              LOOKUP PERFORMANCE                        │
│                                                        │
│  Method              Time        Network    Offline   │
│  ─────────────────────────────────────────────────────│
│  Supabase Query      10-50ms     Required   ✗        │
│  Local JSON          <1ms        None       ✓        │
│  Intelligence Scan   100ms/file  None       ✓        │
│                                                        │
│  Recommendation: Try Supabase first, fallback to JSON │
└────────────────────────────────────────────────────────┘
```

## Security Model

```
┌────────────────────────────────────────────────────────┐
│                  SECURITY LAYERS                       │
│                                                        │
│  Frontend (User)                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ ✗ NO ACCESS to filename mappings                │ │
│  │ ✓ Only sees anonymized IDs (CAND_882)           │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Backend (Admin)                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ ✓ Can lookup mappings via CLI                   │ │
│  │ ✓ Can export backups                             │ │
│  │ ✓ Can sync/recover mappings                      │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Storage                                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Supabase: RLS policies restrict access           │ │
│  │ Local JSON: File system permissions              │ │
│  │ Intelligence: Backend-only directory             │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Summary

```
┌────────────────────────────────────────────────────────┐
│              KEY BENEFITS                              │
│                                                        │
│  ✓ Three-tier redundancy                              │
│  ✓ Automatic fallback                                 │
│  ✓ Works online and offline                           │
│  ✓ Fast lookups (<1ms local, 10-50ms Supabase)       │
│  ✓ Can rebuild from intelligence files                │
│  ✓ CLI tools for management                           │
│  ✓ CSV export for backups                             │
│  ✓ Secure (backend-only)                              │
│  ✓ Zero breaking changes                              │
│  ✓ Production-ready                                   │
└────────────────────────────────────────────────────────┘
```

## Quick Reference

```bash
# List all mappings
python manage_filename_mappings.py list

# Lookup by ID
python manage_filename_mappings.py lookup --id CAND_882

# Lookup by filename
python manage_filename_mappings.py lookup --original "John_Doe.pdf"

# Rebuild from intelligence files
python manage_filename_mappings.py sync

# Export backup
python manage_filename_mappings.py export --output backup.csv

# Show statistics
python manage_filename_mappings.py stats
```
