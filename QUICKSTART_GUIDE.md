# Quick Start Guide: CV Anonymization System

## What This System Does

Transforms raw CVs into **anonymized professional profiles** safe for LLM processing by:
- ✅ Removing ALL personal information (names, contact details, demographics)
- ✅ Removing entire sections (education, hobbies, interests, languages known)
- ✅ Preserving 100% of technical skills and work experience
- ✅ No placeholders - clean professional text output

## How to Use

### 1. Basic Usage

```bash
# Process all CVs in samples/ folder
python run_universal_pipeline.py

# Output will be in final_output/ folder
```

### 2. Verify Results

```bash
# Run verification checks
python verify_anonymization.py
```

### 3. Check Specific File

```bash
# View anonymized output
type final_output\REDACTED_filename.txt
```

## What Gets Removed

| Category | Examples |
|----------|----------|
| **Personal Identity** | Names (all forms), Digital footprint (emails, phones, URLs, social media) |
| **Contact Details** | Email addresses, Phone numbers, Physical addresses, LinkedIn/GitHub profiles |
| **Demographics** | Date of birth, Age, Gender, Marital status, Father's/Mother's names, Nationality |
| **Entire Sections** | Education (degrees, universities, dates), Hobbies & Interests, Languages Known, Personal Assets |

## What Gets Preserved

| Category | Examples |
|----------|----------|
| **Technical Skills** | Java, Python, C++, JavaScript, React, Docker, Kubernetes, AWS, Azure |
| **Work Experience** | Company names, Job titles, Project descriptions, Achievements, Employment dates |
| **Certifications** | AWS Certified, PMP, Scrum Master, etc. |
| **Tools & Technologies** | Git, Jenkins, MongoDB, PostgreSQL, Linux, Windows |

## Example: Before → After

### Before (Raw CV)
```
John Smith
john.smith@email.com | +1-234-567-8900
LinkedIn: linkedin.com/in/johnsmith

EDUCATION
Master of Computer Science
MIT, Cambridge
2015-2017

HOBBIES
• Reading
• Hiking
• Photography

Personal Details:
DOB: 01/01/1990
Gender: Male
Marital Status: Married

EXPERIENCE
Senior Software Engineer at Google
- Developed microservices using Java and Spring Boot
- Led team of 5 engineers
```

### After (Anonymized)
```
EXPERIENCE
Senior Software Engineer at Google
- Developed microservices using Java and Spring Boot
- Led team of 5 engineers
```

## Supported CV Formats

- ✅ Naukri format CVs (automatic detection)
- ✅ Standard ATS format
- ✅ Creative/Designer CVs
- ✅ Academic CVs
- ✅ Multi-column layouts
- ✅ Scanned PDFs (with basic text extraction)

## File Naming Convention

Input: `samples/YourCV.pdf`  
Output: `final_output/REDACTED_YourCV.txt`

## Verification Checklist

After processing, the system automatically checks:
- ✓ No education headers or degree mentions
- ✓ No personal section headers (hobbies/interests)
- ✓ No demographics (DOB/gender/marital status)
- ✓ No email addresses
- ✓ No phone numbers (10+ digits)
- ✓ No standalone names (3+ word patterns)
- ✓ Technical terms are preserved

## Troubleshooting

### Issue: Names still appearing
- Check if they're technical terms (e.g., "Mastercard")
- Review the protected_terms list in the code
- These are NOT personal names

### Issue: Education section still there
- The system removes sections with headers like "Education", "Academic", "Qualifications"
- Also removes inline degree mentions (Bachelor, Master, B.Tech, M.Tech, MBA, PhD)
- If persisting, check the specific format in your CV

### Issue: Technical terms removed
- Check the protected_terms list in universal_pipeline_engine.py
- Add your specific technical term to the list if needed

## Advanced Options

### Debug Mode
To see detailed processing logs, check the logger output in the terminal during processing.

### Custom Protected Terms
Edit `universal_pipeline_engine.py` → `_load_protected_terms()` method to add domain-specific technical terms.

### Adjust Removal Patterns
Edit the regex patterns in:
- `_remove_demographics()` - for demographic patterns
- `_remove_personal_sections()` - for personal section markers
- `_remove_education_section()` - for education section detection

## Files Overview

```
samplecvs/
├── run_universal_pipeline.py          # Main entry point
├── universal_pipeline_engine.py        # Core anonymization engine
├── verify_anonymization.py             # Verification script
├── README.md                            # Full documentation
├── IMPLEMENTATION_SUMMARY.md           # Implementation details
├── QUICKSTART.md                        # This file
├── samples/                             # Input PDFs
└── final_output/                        # Anonymized output
    └── REDACTED_*.txt
```

## Quick Commands

```bash
# Process CVs
python run_universal_pipeline.py

# Verify anonymization
python verify_anonymization.py

# Check specific file
type final_output\REDACTED_YourCV.txt

# Count processed files
dir final_output\REDACTED_* | measure
```

## Success Metrics

After running, you should see:
- ✓ 0 personal names in output
- ✓ 0 education sections
- ✓ 0 demographic information
- ✓ 0 contact details
- ✓ 100% technical skills preserved

---

**Need Help?** Check `README.md` for detailed documentation or `IMPLEMENTATION_SUMMARY.md` for technical details.
