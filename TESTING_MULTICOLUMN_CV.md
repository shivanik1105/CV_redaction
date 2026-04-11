# Testing Multi-Column CV Redaction

## Overview

This document explains how to test the improved multi-column CV extraction and redaction system.

## What Was Fixed

The previous implementation read 2-column CVs by reading the entire left column first, then the entire right column. This caused sections to be mixed up and out of order.

### Example Problem (Before Fix):
For a CV with:
- Left column: Contact Info, Technical Skills, Education, Certifications
- Right column: Name, Summary, Professional Experience

The output would be:
```
Contact Info
Technical Skills
Education
Certifications
[separator]
Name
Summary
Professional Experience
```

This mixed up the logical flow of the CV.

### Solution (After Fix):
The new implementation reads 2-column CVs **row-by-row** (top to bottom), reading left-to-right within each row. This maintains the natural reading order and keeps related content together.

Now the output follows the visual layout:
```
Name | Contact Info
Summary | Technical Skills
Professional Experience | Education
... | Certifications
```

## How to Test

### Method 1: Using the Test Script (Recommended)

**Windows (PowerShell):**
```powershell
.\test_cv_redaction.ps1 "path\to\your\cv.pdf"
```

**Linux/Mac (Bash):**
```bash
chmod +x test_cv_redaction.sh
./test_cv_redaction.sh "path/to/your/cv.pdf"
```

### Method 2: Using app_launcher.py Directly

```bash
python app_launcher.py --test "path/to/your/cv.pdf"
```

This will:
1. Extract text from the PDF
2. Detect the CV type and layout
3. Apply redaction rules
4. Save the output to `test_redaction_output.txt`
5. Display a preview in the console

### Method 3: Using the GUI

After testing with the command line, you can start the GUI normally:

```bash
python app_launcher.py
```

Then upload your CV through the web interface and verify the redaction output.

## What to Check

When reviewing the test output (`test_redaction_output.txt`), verify:

1. **Section Order**: Sections should appear in a logical order
   - Contact information near the top
   - Summary/Objective early
   - Professional Experience in the main body
   - Skills, Education, Certifications in appropriate places

2. **No Mixed Content**: Content from different sections should not be interleaved
   - Skills should be grouped together
   - Work experience entries should be complete and sequential
   - Education entries should be together

3. **Proper Redaction**: PII should be redacted
   - Names → `[REDACTED_NAME]`
   - Emails → `[REDACTED_EMAIL]`
   - Phone numbers → `[REDACTED_PHONE]`
   - Addresses → `[REDACTED_LOCATION]`

4. **Preserved Structure**: The document structure should be maintained
   - Section headers should be clear
   - Bullet points should be preserved
   - Dates and durations should be intact

## Technical Details

### Changes Made

**File: `universal_pipeline_engine.py`**
- Modified `StandardATSPipeline.extract_text()` method
- Changed from column-by-column reading to row-by-row reading
- Added intelligent row grouping based on Y-position proximity (15px tolerance)
- Maintains left-to-right order within each row

**File: `app_launcher.py`**
- Added `--test` mode for command-line testing
- Provides detailed output and preview
- Saves test results to `test_redaction_output.txt`

### Algorithm

1. **Detect 2-column layout**:
   - Find significant gaps (>40px) in X-positions
   - Verify both columns have substantial content (≥3 blocks each)

2. **Group blocks into rows**:
   - Sort all blocks by Y-position (top to bottom)
   - Group blocks within 15px vertically as same row
   - Sort each row left-to-right by X-position

3. **Generate output**:
   - Concatenate text from each row
   - Maintain natural reading order

## Troubleshooting

### Issue: Sections still mixed up

**Possible causes:**
- CV has unusual layout (3+ columns, complex graphics)
- Column detection failed (gap too small)

**Solution:**
- Check the debug output to see detected column boundary
- Adjust `y_tolerance` parameter if needed (currently 15px)
- Consider using `MultiColumnPipeline` for complex layouts

### Issue: Text extraction incomplete

**Possible causes:**
- PDF is scanned image (no text layer)
- PDF uses unusual fonts or encoding

**Solution:**
- Use OCR preprocessing
- Convert to DOCX format
- Check if pdfplumber fallback is triggered

### Issue: Over-redaction or under-redaction

**Possible causes:**
- PII patterns not matching
- Protected terms not configured

**Solution:**
- Review `config/pii_patterns.json`
- Update `config/protected_terms.json`
- Check `config/locations.json` for location data

## Example Test Output

```
================================================================================
TESTING CV EXTRACTION AND REDACTION
================================================================================
Input file: Resume-Sunil-Durgale.pdf

Profile detected:
  Type: CVType.STANDARD_ATS
  Confidence: 85.00%

✓ Redaction complete!
✓ Output saved to: test_redaction_output.txt

Preview (first 1000 characters):
--------------------------------------------------------------------------------
[REDACTED_EMAIL]
[REDACTED_PHONE]
[REDACTED_LOCATION]

WWW:
https://www.linkedin.com/in/[REDACTED_NAME]/

Technical Skills
• Sales Operations
• Revenue Operations
• Quote and Contracts Creation
...
--------------------------------------------------------------------------------

✓ Test completed successfully!
  Review the full output in test_redaction_output.txt
```

## Next Steps

After verifying the test output:

1. If the output looks good, proceed to use the GUI
2. If there are issues, review the troubleshooting section
3. For persistent issues, check the logs or contact support

## Support

For issues or questions:
- Check the main README.md
- Review the architecture documentation
- Examine the debug output files
