# Quick Fix Guide: CV Redaction Over-Masking

## Problem Summary
The CV redaction system was masking too much content with black boxes, including:
- Job descriptions and responsibilities  
- Company names and job titles
- Technical skills and experience
- Project descriptions

## Solution Applied
Modified `redaction_runner.py` to be more selective about what gets masked in PDFs.

## What Changed

### 1. Reduced Header Redaction Area
- **Before**: Top 22% of page
- **After**: Top 15% of page only

### 2. Added Smart Pattern Detection
The system now recognizes and preserves:
- **Job titles**: engineer, developer, architect, manager, consultant, analyst, lead, senior, junior, principal
- **Company types**: pvt, ltd, limited, inc, corporation, corp, llc, llp, international, global, solutions, technologies, systems
- **Technical terms**: software, system, technical, project, product, data, web, mobile, cloud, devops
- **Action verbs**: build, develop, design, implement, manage, lead, create, maintain, optimize, proficient, experienced, skilled
- **Technologies**: c++, python, java, javascript, react, angular, node, sql, aws, azure, docker, kubernetes, android, ios, kotlin
- **Date ranges**: 2018-2021, etc.

### 3. Context-Aware Redaction
Lines are only redacted if they:
- Contain PII (email, phone, URL) **AND**
- Do NOT contain job-related content

## Testing

Run the test script to verify patterns:
```bash
python test_redaction_fix.py
```

All tests should pass (✅).

## How to Apply the Fix

### Step 1: Clear Cached PDFs
```bash
# Windows PowerShell
Remove-Item -Recurse -Force masked_pdfs_cache\*

# Linux/Mac
rm -rf masked_pdfs_cache/*
```

### Step 2: Restart the Application
```bash
python app.py
```

### Step 3: Test with a CV
1. Upload a CV through the web interface
2. Download the masked PDF
3. Verify:
   - ✅ Personal info (name, email, phone) is masked with black boxes
   - ✅ Job content (titles, companies, descriptions) is visible

## Expected Results

### Should Be Masked (Black Boxes):
- ✅ Candidate name in header
- ✅ Email addresses
- ✅ Phone numbers  
- ✅ LinkedIn/GitHub URLs
- ✅ Personal addresses
- ✅ Contact information

### Should Be Visible:
- ✅ Job titles (e.g., "Senior Software Engineer")
- ✅ Company names (e.g., "Harman International", "Forbes Technosys Ltd")
- ✅ Job descriptions (e.g., "Build linux/unix applications using C++")
- ✅ Technical skills (e.g., "Python", "React", "AWS")
- ✅ Project descriptions
- ✅ Work experience details
- ✅ Date ranges (e.g., "2018-2021")

## Troubleshooting

### If job content is still being masked:
1. Check if the cached PDF exists and delete it
2. Verify the patterns in `redaction_runner.py` match the test script
3. Check the application logs for errors

### If personal info is NOT being masked:
1. Verify the PII patterns in `config/pii_patterns.json`
2. Check that email/phone/URL patterns are working
3. Review the redaction logs

## Files Modified
- `redaction_runner.py` - Main PDF redaction logic
- `test_redaction_fix.py` - Test script (new)
- `REDACTION_FIX_SUMMARY.md` - Detailed documentation (new)
- `QUICK_FIX_GUIDE.md` - This file (new)

## Rollback
If you need to revert the changes:
```bash
git checkout HEAD~1 redaction_runner.py
```

## Support
If issues persist:
1. Check the test results: `python test_redaction_fix.py`
2. Review the detailed documentation: `REDACTION_FIX_SUMMARY.md`
3. Check application logs for errors
4. Verify config files in `config/` directory
