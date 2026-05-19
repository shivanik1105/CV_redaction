# CV Redaction Over-Masking Fix

## Problem
The CV redaction system was masking too much content, including:
- Job descriptions and responsibilities
- Company names and job titles
- Technical skills and experience details
- Project descriptions

This was happening because the PDF redaction logic was too aggressive in identifying and masking entire lines.

## Root Cause
The issue was in `redaction_runner.py` in the `redact_pdf_to_file()` function. The function was:

1. **Redacting too much of the top section** (22% of page height) - catching job titles and company names
2. **Redacting entire lines with postal codes** - even when they were part of job descriptions
3. **Redacting entire lines with any PII pattern** - even when the line contained important job content

## Changes Made

### 1. Reduced Top Section Redaction Area
**File**: `redaction_runner.py`, line ~445
- **Before**: Redacted top 22% of page
- **After**: Redacted only top 15% of page (more conservative)
- **Impact**: Job titles and company names below the header are now preserved

### 2. Added Skip Patterns for Job-Related Content
**File**: `redaction_runner.py`, line ~450-456
- **Added patterns to skip**:
  - Job titles: engineer, developer, architect, manager, consultant, analyst, lead, senior, junior, principal
  - Company indicators: pvt, ltd, limited, inc, corporation, corp, llc, llp
  - Technical terms: software, system, technical, project, product, data, web, mobile, cloud, devops
  - Section headers: experience, skills, education, certification, projects, achievements

### 3. More Restrictive Name Pattern Matching
**File**: `redaction_runner.py`, line ~460-463
- **Before**: Matched 1-4 word capitalized phrases
- **After**: Matches only 2-3 word phrases (more restrictive)
- **Impact**: Longer job descriptions and company names are no longer mistaken for names

### 4. Smarter Postal Code Redaction
**File**: `redaction_runner.py`, line ~476-488
- **Before**: Redacted any line with 5-6 digit numbers
- **After**: Checks if line contains job indicators (dates, job titles, companies) before redacting
- **Impact**: Job descriptions with numbers (like "ISO8583" or dates) are preserved

### 5. Context-Aware PII Redaction
**File**: `redaction_runner.py`, line ~490-512
- **Before**: Redacted entire line if it contained any PII pattern
- **After**: Checks if line contains job-related content before redacting
- **Added job content indicators**:
  - Action verbs: build, develop, design, implement, manage, lead, create, maintain, optimize
  - Technical terms: application, system, software, platform, service, api, database, framework
  - Context words: experience, project, role, responsibilities, achievements, skills
  - Technologies: c++, python, java, javascript, react, angular, node, sql, aws, azure, docker, kubernetes
  - Date ranges: 2018-2021, etc.

## Testing Recommendations

1. **Test with sample CVs** that have:
   - Job descriptions with technical details
   - Company names and job titles
   - Date ranges and project descriptions
   - Mixed content (personal info + professional content)

2. **Verify that PII is still redacted**:
   - Email addresses
   - Phone numbers
   - LinkedIn/GitHub URLs
   - Personal addresses
   - Names in the header section

3. **Check that professional content is preserved**:
   - Job titles and company names
   - Technical skills and tools
   - Project descriptions
   - Work experience details

## Expected Behavior After Fix

### Should Still Be Redacted (Black Boxes):
- ✅ Candidate name in header (top 15% of page)
- ✅ Email addresses
- ✅ Phone numbers
- ✅ LinkedIn/GitHub URLs
- ✅ Personal addresses (without job context)
- ✅ Contact information lines

### Should NOT Be Redacted (Visible):
- ✅ Job titles (e.g., "Senior Software Engineer")
- ✅ Company names (e.g., "Harman", "Forbes Technosys Ltd")
- ✅ Job descriptions and responsibilities
- ✅ Technical skills (e.g., "C++", "Python", "React")
- ✅ Project descriptions
- ✅ Work experience details
- ✅ Date ranges (e.g., "2018-2021")
- ✅ Technical terms and frameworks

## How to Test the Fix

1. **Clear any cached masked PDFs**:
   ```bash
   # Remove old cached PDFs to force regeneration
   rm -rf masked_pdfs_cache/*
   ```

2. **Re-upload a CV** through the application

3. **Download the masked PDF** and verify:
   - Personal info (name, email, phone) is masked
   - Job content (titles, companies, descriptions) is visible

4. **Check the preview** in the UI to ensure text extraction is working correctly

## Additional Notes

- The text-based redaction in `universal_pipeline_engine.py` is separate and handles text extraction
- This fix specifically addresses the **PDF visual redaction** (black boxes)
- Both systems work together: text redaction for search/matching, PDF redaction for privacy
- The fix maintains privacy while improving accuracy of job matching

## Rollback Instructions

If this fix causes issues, you can revert by:
```bash
git checkout HEAD~1 redaction_runner.py
```

Or manually restore the original values:
- Change `top_threshold` back to `0.22`
- Remove the skip_patterns checks
- Remove the job_indicators checks
- Remove the job_content_indicators checks
