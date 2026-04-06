# Filename Mapping Solution

## Problem Statement

When CVs are anonymized, we need to maintain a secure mapping between:
- **Original filename** (e.g., "John_Doe_Resume.pdf")
- **Anonymized ID** (e.g., "CAND_882")
- **Anonymized filename** (e.g., "REDACTED_20240405_123456_JohnDoe.txt")

This mapping must be:
1. **Secure** - Not exposed to frontend/users
2. **Reliable** - Survive database outages
3. **Queryable** - Support bidirectional lookup
4. **Recoverable** - Can be rebuilt if lost

## Solution: Three-Tier Storage Architecture

### Tier 1: Supabase Database (Primary)
**Table: `cv_filename_mapping`**

```sql
CREATE TABLE cv_filename_mapping (
    anonymized_id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    anonymized_filename TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mapping_original ON cv_filename_mapping(original_filename);
```

**Advantages:**
- Centralized, backed up, queryable
- Supports multiple users/sessions
- Integrated with main database

**Disadvantages:**
- Requires network connection
- Single point of failure if Supabase is down

### Tier 2: Local JSON File (Fallback)
**File: `filename_mappings.json`**

```json
{
  "CAND_882": {
    "original_filename": "John_Doe_Resume.pdf",
    "anonymized_filename": "REDACTED_20240405_123456_JohnDoe.txt",
    "created_at": "2024-04-05T12:34:56",
    "last_updated": "2024-04-05T12:34:56"
  },
  "CAND_883": {
    "original_filename": "Jane_Smith_CV.docx",
    "anonymized_filename": "REDACTED_20240405_123500_JaneSmith.txt",
    "created_at": "2024-04-05T12:35:00",
    "last_updated": "2024-04-05T12:35:00"
  }
}
```

**Advantages:**
- Works offline
- Fast local lookups
- No network dependency
- Easy to backup/version control

**Disadvantages:**
- Not shared across machines
- Requires manual sync

### Tier 3: Embedded in Intelligence Files (Recovery)
**File: `llm_analysis/CAND_882_intelligence.json`**

Each intelligence JSON already contains:
```json
{
  "anonymized_id": "CAND_882",
  "original_filename": "John_Doe_Resume.pdf",
  "redacted_filename": "REDACTED_20240405_123456_JohnDoe.txt",
  ...
}
```

**Advantages:**
- Self-contained records
- Can rebuild mappings from intelligence files
- No additional storage needed

**Disadvantages:**
- Requires parsing all files for bulk queries
- Not optimized for lookups

## Implementation

### 1. FilenameMappingManager Class

```python
from filename_mapping_manager import FilenameMappingManager

# Initialize manager
manager = FilenameMappingManager()

# Store mapping (tries Supabase, always stores locally)
result = manager.store_mapping(
    anonymized_id="CAND_882",
    original_filename="John_Doe_Resume.pdf",
    anonymized_filename="REDACTED_20240405_123456_JohnDoe.txt",
    supabase_storage=storage  # Optional
)

# Lookup by anonymized ID
mapping = manager.get_mapping("CAND_882", supabase_storage=storage)
# Returns: {'original_filename': '...', 'anonymized_filename': '...'}

# Reverse lookup by original filename
anon_id = manager.reverse_lookup_by_original("John_Doe_Resume.pdf", storage)
# Returns: "CAND_882"

# Get all mappings
all_mappings = manager.get_all_mappings(supabase_storage=storage)

# Sync from intelligence files (recovery)
stats = manager.sync_from_intelligence_files()
# Returns: {'synced': 10, 'skipped': 5, 'errors': 0, 'total_mappings': 15}

# Export to CSV (backup)
manager.export_mappings_csv("backup_mappings.csv", storage)
```

### 2. CLI Management Tool

```bash
# List all mappings
python manage_filename_mappings.py list

# Lookup by anonymized ID
python manage_filename_mappings.py lookup --id CAND_882

# Lookup by original filename
python manage_filename_mappings.py lookup --original "John_Doe_Resume.pdf"

# Sync from intelligence files (rebuild local cache)
python manage_filename_mappings.py sync

# Export to CSV for backup
python manage_filename_mappings.py export --output mappings_backup.csv

# Show statistics
python manage_filename_mappings.py stats

# Use local storage only (offline mode)
python manage_filename_mappings.py list --local-only
```

### 3. Integration with app.py

Update the `_persist_intelligence` function:

```python
from filename_mapping_manager import FilenameMappingManager

# Initialize manager (once at app startup)
filename_manager = FilenameMappingManager()

def _persist_intelligence(intelligence, redacted_filename, original_filename=None):
    """Save intelligence and filename mapping"""
    # ... existing code ...
    
    # Store filename mapping
    anonymized_id = intelligence.get('anonymized_id')
    if anonymized_id:
        mapping_result = filename_manager.store_mapping(
            anonymized_id=anonymized_id,
            original_filename=original_filename or redacted_filename,
            anonymized_filename=redacted_filename,
            supabase_storage=get_supabase_storage()
        )
        
        persistence['mapping_stored_in_supabase'] = mapping_result['stored_in_supabase']
        persistence['mapping_stored_locally'] = mapping_result['stored_locally']
    
    return persistence
```

## Usage Examples

### Example 1: Store Mapping During CV Processing

```python
# After CV is processed and anonymized
result = filename_manager.store_mapping(
    anonymized_id="CAND_882",
    original_filename="John_Doe_Resume.pdf",
    anonymized_filename="REDACTED_20240405_123456_JohnDoe.txt",
    supabase_storage=storage
)

print(result)
# {
#   'stored_in_supabase': True,
#   'stored_locally': True,
#   'supabase_error': None
# }
```

### Example 2: Retrieve Original Filename

```python
# When you need to show the original filename to admin
original = filename_manager.get_original_filename("CAND_882", storage)
print(f"Original file: {original}")
# Output: Original file: John_Doe_Resume.pdf
```

### Example 3: Find Candidate by Original Filename

```python
# User asks: "What happened to John_Doe_Resume.pdf?"
anon_id = filename_manager.reverse_lookup_by_original(
    "John_Doe_Resume.pdf",
    storage
)
print(f"Anonymized as: {anon_id}")
# Output: Anonymized as: CAND_882
```

### Example 4: Recover from Database Loss

```bash
# If Supabase data is lost, rebuild from intelligence files
python manage_filename_mappings.py sync

# Output:
# ✓ Sync complete:
#   - Synced: 150
#   - Skipped: 0
#   - Errors: 0
#   - Total mappings: 150
```

### Example 5: Backup Mappings

```bash
# Regular backup to CSV
python manage_filename_mappings.py export --output backup_$(date +%Y%m%d).csv

# Commit to version control
git add filename_mappings.json backup_20240405.csv
git commit -m "Backup filename mappings"
```

## Automatic Fallback Behavior

The system automatically handles failures:

```python
# If Supabase is down, automatically uses local storage
mapping = manager.get_mapping("CAND_882", supabase_storage=None)
# Still works! Uses local JSON file

# If local file is corrupted, can rebuild from intelligence files
stats = manager.sync_from_intelligence_files()
# Rebuilds local cache from intelligence JSONs
```

## Security Considerations

1. **Backend Only**: Filename mappings are NEVER sent to frontend
2. **Access Control**: Supabase RLS policies restrict access
3. **Local File**: `filename_mappings.json` should be in `.gitignore`
4. **Audit Trail**: All mappings include timestamps

## Maintenance Tasks

### Daily
- Automatic: Mappings stored during CV processing

### Weekly
```bash
# Verify mapping integrity
python manage_filename_mappings.py stats

# Export backup
python manage_filename_mappings.py export --output weekly_backup.csv
```

### Monthly
```bash
# Full sync from intelligence files
python manage_filename_mappings.py sync

# Verify Supabase vs Local consistency
python manage_filename_mappings.py list > supabase_mappings.txt
python manage_filename_mappings.py list --local-only > local_mappings.txt
diff supabase_mappings.txt local_mappings.txt
```

### Recovery Scenarios

**Scenario 1: Supabase is down**
- System automatically uses local JSON file
- No action needed

**Scenario 2: Local file deleted**
```bash
# Rebuild from Supabase
python manage_filename_mappings.py list  # Fetches from Supabase, saves locally
```

**Scenario 3: Both Supabase and local file lost**
```bash
# Rebuild from intelligence files
python manage_filename_mappings.py sync
```

**Scenario 4: Need to migrate to new database**
```bash
# Export from old system
python manage_filename_mappings.py export --output migration.csv

# Import to new system (write custom import script or use CSV)
```

## Performance

- **Local lookup**: <1ms (JSON file)
- **Supabase lookup**: 10-50ms (network + query)
- **Sync from intelligence files**: ~100ms per file
- **Export to CSV**: ~50ms for 1000 records

## File Locations

```
project/
├── filename_mappings.json          # Local mapping cache
├── filename_mapping_manager.py     # Core manager class
├── manage_filename_mappings.py     # CLI tool
├── llm_analysis/                   # Intelligence files (tier 3)
│   ├── CAND_882_intelligence.json
│   └── CAND_883_intelligence.json
└── backups/                        # CSV backups
    ├── mappings_20240405.csv
    └── mappings_20240412.csv
```

## Summary

This three-tier solution provides:
- ✅ **Reliability**: Multiple storage tiers with automatic fallback
- ✅ **Security**: Backend-only, never exposed to frontend
- ✅ **Recoverability**: Can rebuild from intelligence files
- ✅ **Performance**: Fast local lookups with database backup
- ✅ **Maintainability**: Simple CLI tools for management
- ✅ **Scalability**: Works offline and online

The system automatically handles failures and provides multiple recovery paths, ensuring filename mappings are never lost.
