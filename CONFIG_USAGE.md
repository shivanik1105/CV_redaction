# 🎯 Configuration-Driven CV Redaction Pipeline

## Zero Hardcoded Data ✅

All rules, terms, and patterns now live in JSON config files under `config/`:

```
config/
├── locations.json          # All cities, states, countries
├── protected_terms.json    # Technical terms by category  
├── sections.json           # Sections to remove/preserve
├── pii_patterns.json       # PII regex patterns
└── text_healing.json       # Spacing fix rules
```

---

## 📦 Quick Start

### 1. Normal CV Processing

```bash
# Process CVs (configs auto-created on first run)
python cv_redaction_pipeline.py resume/ final_output/

# With debug output
python cv_redaction_pipeline.py resume/ final_output/ --debug

# Or use the original engine directly
python universal_pipeline_engine.py resume/ final_output/
```

### 2. Add New Data (Without Touching Code!)

```bash
# Add a new city
python cv_redaction_pipeline.py add-city "San Francisco"
python cv_redaction_pipeline.py add-city "Boston"

# Add a state
python cv_redaction_pipeline.py add-state "California"

# Add a country
python cv_redaction_pipeline.py add-country "Canada"

# Add a protected technical term
python cv_redaction_pipeline.py add-term "tensorflow"
python cv_redaction_pipeline.py add-term "kubernetes" --category cloud

# Add a spacing fix rule
python cv_redaction_pipeline.py add-healing "administr at ion" "administration"
python cv_redaction_pipeline.py add-healing "new broken pattern" "fixed"
```

### 3. View Current Configuration

```bash
# Show complete config summary
python cv_redaction_pipeline.py list-config

# List specific items
python cv_redaction_pipeline.py list-cities
python cv_redaction_pipeline.py list-states
python cv_redaction_pipeline.py list-countries
python cv_redaction_pipeline.py list-terms
python cv_redaction_pipeline.py list-terms --category frameworks
python cv_redaction_pipeline.py list-healing
```

### 4. Or Edit JSON Files Directly

**config/locations.json:**
```json
{
  "cities": ["Pune", "Mumbai", "New York"],  // Just add here
  "states": ["Maharashtra", "Karnataka"],
  "countries": ["India", "USA"]
}
```

**config/protected_terms.json:**
```json
{
  "languages": ["python", "java", "javascript"],
  "frameworks": ["react", "django", "flask"],
  "cloud": ["aws", "azure", "kubernetes"]  // Add your terms
}
```

**config/text_healing.json:**
```json
{
  "common_words": {
    "applic at ion": "application",  // Add your fix
    "new broken pattern": "fixed"
  }
}
```

---

## ✅ Key Features

| Feature | Status |
|---------|--------|
| **Automatic Config Creation** | ✅ Runs first time with sensible defaults |
| **Zero Hardcoding** | ✅ All data externalized to JSON |
| **Easy Extension** | ✅ Add cities/terms via CLI or JSON edits |
| **Backward Compatible** | ✅ Same interface as before |
| **Production Ready** | ✅ Logging, error handling, type hints |

---

## 🚀 How It Scales

| Task | Old Way ❌ | New Way ✅ |
|------|-----------|-----------|
| Add 50 cities | Edit Python code | Add 50 lines to JSON |
| Fix new spacing | Write regex in code | One JSON entry |
| Support new tech | Modify protected_terms list | Edit config file |
| Team contribution | Need Python knowledge | Anyone can edit JSON |

---

## 📂 Configuration Files Explained

### 1. locations.json
Locations to redact from CVs:
- **cities**: List of city names to remove
- **states**: List of state/region names to remove
- **countries**: List of country names to remove

### 2. protected_terms.json
Technical terms to PRESERVE (not redact):
- **languages**: Programming languages (python, java, etc.)
- **frameworks**: Frameworks (react, django, etc.)
- **databases**: Database systems (mysql, mongodb, etc.)
- **cloud**: Cloud platforms and tools (aws, docker, etc.)
- **tools**: Development tools (git, jira, etc.)
- **os**: Operating systems (linux, windows, etc.)
- **roles**: Job titles to preserve (engineer, developer, etc.)
- **technical_terms**: Domain-specific technical words

### 3. sections.json
Section headers to identify and process:
- **remove**: Section markers to remove completely (education, personal info)
- **preserve**: Section markers to keep (experience, skills, projects)

### 4. pii_patterns.json
Regular expression patterns for detecting PII:
- **email**: Email address pattern
- **phone**: Phone number patterns
- **url**: URL patterns
- **social**: Social media profile patterns
- **demographics**: Age, gender, DOB, nationality patterns

### 5. text_healing.json
Rules to fix OCR/PDF spacing issues:
- **suffix_patterns**: Common suffix breaks (e.g., "at ion" → "ation")
- **prefix_patterns**: Common prefix breaks (e.g., "c on " → "con")
- **common_words**: Specific word fixes (e.g., "applic at ion" → "application")

---

## 🔧 Advanced Usage

### Custom Config Directory
```bash
python cv_redaction_pipeline.py resume/ output/ --config-dir my_config/
```

### Batch Operations
```bash
# Add multiple cities at once (edit JSON)
nano config/locations.json

# Or use shell loop
for city in "Boston" "Seattle" "Portland"; do
    python cv_redaction_pipeline.py add-city "$city"
done
```

### Validation
```bash
# Test your config changes
python cv_redaction_pipeline.py list-config

# Process a single test file first
mkdir test_output
python cv_redaction_pipeline.py test_input/ test_output/ --debug
```

---

## 💡 Best Practices

1. **Start with defaults**: Run once to generate default configs
2. **Incremental changes**: Add data incrementally and test
3. **Use descriptive names**: Make config entries clear and searchable
4. **Version control**: Commit your config/ directory to git
5. **Test after changes**: Run `list-config` to verify additions
6. **Debug mode**: Use `--debug` flag to see detailed processing

---

## 🐛 Troubleshooting

**Config not found?**
- Configs auto-create on first run
- Check `config/` directory exists
- Use `list-config` to verify

**Changes not applied?**
- Restart the script (configs are cached)
- Check JSON syntax with `python -m json.tool config/locations.json`

**Want to reset?**
- Delete `config/` directory
- Configs will regenerate with defaults on next run

---

## 📞 Examples in Action

### Example 1: Add Support for New Region
```bash
# Company expanding to Europe
python cv_redaction_pipeline.py add-city "Berlin"
python cv_redaction_pipeline.py add-city "London"
python cv_redaction_pipeline.py add-city "Paris"
python cv_redaction_pipeline.py add-country "Germany"
python cv_redaction_pipeline.py add-country "France"

# Verify additions
python cv_redaction_pipeline.py list-cities | grep -E "Berlin|London|Paris"
```

### Example 2: Add New Tech Stack
```bash
# Team adopting new technologies
python cv_redaction_pipeline.py add-term "rust" --category languages
python cv_redaction_pipeline.py add-term "svelte" --category frameworks
python cv_redaction_pipeline.py add-term "supabase" --category cloud

# Verify
python cv_redaction_pipeline.py list-terms --category languages
```

### Example 3: Fix Common OCR Issues
```bash
# Found new spacing pattern in processed CVs
python cv_redaction_pipeline.py add-healing "dat ab ase" "database"
python cv_redaction_pipeline.py add-healing "soft w are" "software"

# Reprocess with fixes
python cv_redaction_pipeline.py resume/ final_output_v2/
```

---

## 🎓 For Non-Programmers

You can update configurations without any Python knowledge:

1. **Open config files**: Use any text editor (Notepad, VS Code)
2. **Add entries**: Just add your text in quotes, separated by commas
3. **Save**: Save the file
4. **Run**: Execute the pipeline again

**Example** - Adding a city to `config/locations.json`:
```json
{
  "cities": [
    "Pune",
    "Mumbai",
    "YourNewCity"  ← Add this line
  ]
}
```

That's it! No code changes needed. 🎉

---

## 📊 Results

After configuration, your pipeline will:
- ✅ Auto-redact all configured locations
- ✅ Preserve all technical terms you specify
- ✅ Fix spacing issues you define
- ✅ Remove PII using your patterns
- ✅ Structure output professionally

All without modifying a single line of Python code!
