# 🔍 Redaction Markers Reference Guide

## What Are Redaction Markers?

Instead of silently removing sensitive content, the pipeline now adds **markers** (placeholders) to show exactly what was redacted. This helps you understand what's being filtered out.

---

## 📋 Complete List of Markers

### Personal Identifiable Information (PII)

| Marker | What It Replaces | Example |
|--------|------------------|---------|
| `[REDACTED_EMAIL]` | Email addresses | `john.doe@gmail.com` → `[REDACTED_EMAIL]` |
| `[REDACTED_PHONE]` | Phone numbers | `+91-9876543210` → `[REDACTED_PHONE]` |
| `[REDACTED_URL]` | Website URLs | `https://myportfolio.com` → `[REDACTED_URL]` |
| `[REDACTED_SOCIAL]` | LinkedIn/GitHub profiles | `linkedin.com/in/johndoe` → `[REDACTED_SOCIAL]` |
| `[REDACTED_CONTACT_LINE]` | Contact information lines | `Email: john@email.com` → `[REDACTED_CONTACT_LINE]` |

### Names

| Marker | What It Replaces | Example |
|--------|------------------|---------|
| `[REDACTED_NAME]` | Full names from filename | `John Smith` (from filename) → `[REDACTED_NAME]` |
| `[NAME]` | Capitalized name patterns | `John Smith` → `[NAME]` |
| `[NAME_ARTIFACT]` | Name-like artifacts | Standalone capitalized words → `[NAME_ARTIFACT]` |

### Locations

| Marker | What It Replaces | Example |
|--------|------------------|---------|
| `[LOCATION]` | Cities, states, countries | `Pune, Maharashtra, India` → `[LOCATION][LOCATION][LOCATION]` |

### Removed Sections

| Marker | What It Replaces | Section Type |
|--------|------------------|--------------|
| `[REMOVED_SECTION_EDUCATION]` | Education section | Degrees, universities, dates |
| `[REMOVED_SECTION_PERSONAL]` | Personal details section | Hobbies, interests, languages |
| `[REMOVED_SECTION_DECLARATION]` | Declaration section | Declaration statements |

### Demographics

| Marker | What It Replaces | Example |
|--------|------------------|---------|
| `[REDACTED_DOB]` | Date of birth | `DOB: 01/01/1990` → `[REDACTED_DOB]` |
| `[REDACTED_GENDER]` | Gender information | `Gender: Male` → `[REDACTED_GENDER]` |
| `[REDACTED_MARITAL]` | Marital status | `Marital Status: Single` → `[REDACTED_MARITAL]` |
| `[REDACTED_AGE]` | Age information | `Age: 30 years` → `[REDACTED_AGE]` |
| `[REDACTED_NATIONALITY]` | Nationality | `Nationality: Indian` → `[REDACTED_NATIONALITY]` |
| `[REDACTED_FAMILY_INFO]` | Father's/Mother's name | `Father's Name: XYZ` → `[REDACTED_FAMILY_INFO]` |
| `[REDACTED_ID_INFO]` | ID documents | `Passport Validity: 2025` → `[REDACTED_ID_INFO]` |

### Document Artifacts

| Marker | What It Replaces | Example |
|--------|------------------|---------|
| `[PAGE_NUMBER]` | Page numbers | `Page 1 of 3` → `[PAGE_NUMBER]` |

---

## 📊 Example: Before vs After

### Original CV Excerpt:
```
John Smith
Email: john.smith@email.com
Phone: +91-9876543210
Location: Pune, Maharashtra, India

OBJECTIVE: 
Software engineer with 5 years experience...

EDUCATION:
Bachelor of Engineering
University of Pune, 2018
```

### With Markers:
```
[REDACTED_NAME]
[REDACTED_CONTACT_LINE]
[REDACTED_PHONE]
[LOCATION][LOCATION][LOCATION]

OBJECTIVE: 
Software engineer with 5 years experience...

[REMOVED_SECTION_EDUCATION]
```

---

## 🎯 Why Are Markers Useful?

### 1. **Debugging**
Identify if the pipeline is removing too much or too little content.

### 2. **Quality Control**
Verify that sensitive information is properly redacted.

### 3. **Understanding Gaps**
See which parts of the CV are missing in the final output.

### 4. **Configuration Tuning**
Adjust config files based on what's being removed:
- Too many `[NAME]` markers? → Check name detection rules
- Missing locations? → Add to `config/locations.json`
- Wrong sections removed? → Update `config/sections.json`

---

## 🔧 How to Use This Information

### Step 1: Review Output with Markers
```bash
python cv_redaction_pipeline.py samples final_output_with_markers
```

### Step 2: Check for Issues
Look at the output files and identify problematic markers:
- **Too aggressive?** Too many `[NAME]` or `[LOCATION]` markers?
- **Missing content?** Important info marked as `[REMOVED_SECTION_*]`?
- **False positives?** Technical terms marked as `[NAME]`?

### Step 3: Adjust Configuration
Based on what you see, update the config files:

**If cities are missing:**
```bash
python cv_redaction_pipeline.py add-city "MissingCity"
```

**If technical terms are being removed:**
```bash
python cv_redaction_pipeline.py add-term "TechnicalTerm"
```

**If wrong sections are removed:**
Edit `config/sections.json` directly:
```json
{
  "remove": {
    "education": ["education", "academic"],
    "personal": ["personal details", "hobbies"]
  },
  "preserve": ["experience", "skills", "projects"]
}
```

### Step 4: Test Again
```bash
python cv_redaction_pipeline.py samples final_output_v2
```

---

## 🔄 Comparison Workflow

### Compare Old vs New:
```powershell
# Old output (without markers)
Get-Content final_output\CV.txt

# New output (with markers)
Get-Content final_output_with_markers\CV.txt

# See what changed
Compare-Object (Get-Content final_output\CV.txt) (Get-Content final_output_with_markers\CV.txt)
```

---

## 💡 Pro Tips

1. **Search for specific markers:**
   ```powershell
   Get-ChildItem final_output_with_markers -Filter "*.txt" | Select-String "\[REDACTED_"
   ```

2. **Count markers by type:**
   ```powershell
   (Get-Content file.txt | Select-String "\[NAME\]").Matches.Count
   ```

3. **Find files with many name removals:**
   ```powershell
   Get-ChildItem final_output_with_markers -Filter "*.txt" | 
   ForEach-Object { 
       $count = (Get-Content $_.FullName | Select-String "\[NAME\]").Matches.Count
       [PSCustomObject]@{File=$_.Name; NameCount=$count}
   } | Sort-Object NameCount -Descending
   ```

---

## 🎓 Common Patterns

### Pattern 1: Multiple Names Detected
```
[NAME] working as [NAME] at [NAME]
```
**Fix:** These might be job titles or company names. Add to protected terms:
```bash
python cv_redaction_pipeline.py add-term "JobTitle" --category roles
```

### Pattern 2: Location Overload
```
[LOCATION][LOCATION][LOCATION][LOCATION]
```
**This is normal** - It means multiple locations were found in sequence.

### Pattern 3: Section Completely Gone
```
[REMOVED_SECTION_EDUCATION]
```
**Expected behavior** - Education section is configured to be removed.

---

## 📞 Need to Remove Markers?

If you want clean output without markers after debugging, you can:

1. **Post-process** to remove markers:
   ```python
   import re
   text = open('file.txt').read()
   clean = re.sub(r'\[.*?\]', '', text)
   ```

2. **Or modify the code** to not add markers (revert to empty strings)

---

## ✅ Summary

Markers help you:
- 📍 **See** what's being removed
- 🔍 **Debug** redaction rules
- ⚙️ **Tune** configurations
- ✨ **Improve** output quality

Use them during testing and configuration tuning, then decide if you want them in production output!
