# 📋 Quick Reference Card

## Most Common Commands

### Processing CVs
```bash
# Basic usage (configs auto-created first time)
python cv_redaction_pipeline.py resume/ final_output/

# With debug output
python cv_redaction_pipeline.py resume/ final_output/ --debug
```

### Adding Data (No code changes!)
```bash
# Locations
python cv_redaction_pipeline.py add-city "Boston"
python cv_redaction_pipeline.py add-state "California"  
python cv_redaction_pipeline.py add-country "Canada"

# Technical terms
python cv_redaction_pipeline.py add-term "tensorflow"
python cv_redaction_pipeline.py add-term "svelte" --category frameworks

# Fix spacing issues
python cv_redaction_pipeline.py add-healing "dat ab ase" "database"
```

### Viewing Configuration
```bash
# Show everything
python cv_redaction_pipeline.py list-config

# Show specific items
python cv_redaction_pipeline.py list-cities
python cv_redaction_pipeline.py list-terms
python cv_redaction_pipeline.py list-terms --category cloud
```

## Config Files Location

```
config/
├── locations.json          → Cities, states, countries to redact
├── protected_terms.json    → Technical terms to preserve
├── sections.json           → Section markers
├── pii_patterns.json       → PII detection regex
└── text_healing.json       → Fix OCR spacing issues
```

## Edit JSON Directly

**config/locations.json:**
```json
{
  "cities": [
    "Pune",
    "Mumbai", 
    "YourCity"  ← Add here
  ]
}
```

**config/protected_terms.json:**
```json
{
  "languages": ["python", "rust"],  ← Add here
  "cloud": ["aws", "kubernetes"]
}
```

**config/text_healing.json:**
```json
{
  "common_words": {
    "administr at ion": "administration",  ← Add patterns
    "your broken text": "fixed text"
  }
}
```

## Key Benefits

✅ **Zero hardcoded data** - Everything in JSON  
✅ **Easy to extend** - Add data via CLI or JSON edits  
✅ **No Python knowledge** required for config changes  
✅ **Team-friendly** - Non-developers can contribute  
✅ **Version control** - Track config changes in git  

## Troubleshooting

**Configs not found?**
→ They auto-create on first run. Use `list-config` to verify.

**Changes not applying?**
→ Check JSON syntax: `python -m json.tool config/locations.json`

**Want to reset?**
→ Delete `config/` folder, it will regenerate with defaults.

## Need Help?

```bash
python cv_redaction_pipeline.py --help
```

📖 Full documentation: [CONFIG_USAGE.md](CONFIG_USAGE.md)
