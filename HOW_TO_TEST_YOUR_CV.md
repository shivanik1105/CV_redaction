# How to Test Your Multi-Column CV

## Quick Start

Save your CV (e.g., "Resume-Sunil-Durgale.pdf") in this directory, then run:

```bash
python quick_test.py "Resume-Sunil-Durgale.pdf"
```

This will:
1. ✓ Extract text from your PDF
2. ✓ Detect the CV layout type
3. ✓ Apply proper multi-column reading (row-by-row)
4. ✓ Redact all PII (names, emails, phones, addresses)
5. ✓ Show you the first 50 lines
6. ✓ Save the complete output to `test_redaction_output.txt`

## What to Look For

Open `test_redaction_output.txt` and verify:

### ✓ Proper Section Order
Sections should appear in a logical sequence:
```
Contact Info / Name
Summary / Objective
Professional Experience
Skills
Education
Certifications
```

### ✓ No Mixed Content
Each section should be complete and coherent:
- ✗ BAD: Skills appearing in the middle of work experience
- ✓ GOOD: All skills grouped together in one section

### ✓ Proper Redaction
Personal information should be redacted:
- Names → `[REDACTED_NAME]`
- Emails → `[REDACTED_EMAIL]`
- Phone numbers → `[REDACTED_PHONE]`
- Addresses → `[REDACTED_LOCATION]`
- Company names → `[REDACTED_COMPANY]` (if configured)

### ✓ Preserved Structure
- Section headers are clear
- Bullet points are maintained
- Dates and durations are intact
- Job titles and roles are readable

## Example Output

For a 2-column CV like Sunil Durgale's resume, you should see:

```
[REDACTED_EMAIL]
[REDACTED_PHONE]
[REDACTED_LOCATION]

WWW:
https://www.linkedin.com/in/[REDACTED_NAME]/

[REDACTED_NAME]

Summary
Results-driven Sales Operations Manager known for highly productive and efficient
task completion. Possess specialized skills in strategic planning, CRM management,
and data analysis essential for optimizing sales processes.

Professional Experience
[REDACTED_COMPANY] - Sales and Revenue Operations Manager
[REDACTED_LOCATION]
07/2021 - 04/2025

• Streamlined CRM management within Growth Squad for optimal efficiency.
• Responsible for renewing orders based on subscription.
• Streamlined sales processes to enhance team efficiency and reduce bottlenecks.
...

Technical Skills
• Sales Operations
• Revenue Operations
• Quote and Contracts Creation
• HubSpot CRM
• Salesforce
...

Education
03/2014
Bachelor Of Science:
Computer Science
[REDACTED_LOCATION]
...
```

## If the Output Looks Good

Start the GUI and test with the web interface:

```bash
python app_launcher.py
```

The browser will open automatically to http://localhost:5000/redactor

Upload your CV and verify the redaction works correctly in the GUI.

## If There Are Issues

### Issue: Sections are still mixed up

**Try:**
1. Check if your CV has more than 2 columns
2. Look at the "CV Type" in the test output
3. If it says `MULTI_COLUMN`, the system is using a different pipeline

**Solution:**
- Review `TESTING_MULTICOLUMN_CV.md` for troubleshooting
- Check if the column gap is being detected (should be >40px)

### Issue: Too much or too little redaction

**Try:**
1. Review `config/pii_patterns.json` for PII patterns
2. Check `config/protected_terms.json` for terms to preserve
3. Update `config/locations.json` for location data

**Solution:**
- Add missing patterns to the config files
- Restart the test after updating configs

### Issue: Text extraction is incomplete

**Try:**
1. Check if the PDF is a scanned image
2. Verify the PDF has a text layer (not just an image)

**Solution:**
- Use OCR preprocessing for scanned PDFs
- Convert to DOCX format if possible
- Check the console output for error messages

## Alternative Test Methods

### Method 1: Using app_launcher.py

```bash
python app_launcher.py --test "Resume-Sunil-Durgale.pdf"
```

### Method 2: Using PowerShell script (Windows)

```powershell
.\test_cv_redaction.ps1 "Resume-Sunil-Durgale.pdf"
```

### Method 3: Using Bash script (Linux/Mac)

```bash
chmod +x test_cv_redaction.sh
./test_cv_redaction.sh "Resume-Sunil-Durgale.pdf"
```

## Understanding the Fix

The system now reads 2-column CVs **row-by-row** instead of **column-by-column**.

**Before (Column-by-Column):**
```
Read entire left column → Read entire right column
Result: Sections out of order
```

**After (Row-by-Row):**
```
Read row 1 (left to right) → Read row 2 (left to right) → ...
Result: Natural reading order maintained
```

See `MULTICOLUMN_FIX_SUMMARY.md` for detailed technical explanation.

## Files You'll Get

After running the test:

1. `test_redaction_output.txt` - Full redacted CV text
2. Console output - Preview and summary

## Next Steps

1. **Run the test:**
   ```bash
   python quick_test.py "your-cv.pdf"
   ```

2. **Review the output:**
   - Open `test_redaction_output.txt`
   - Check section order
   - Verify redaction quality

3. **If satisfied:**
   ```bash
   python app_launcher.py
   ```
   Upload your CV through the GUI

4. **If issues:**
   - Read `TESTING_MULTICOLUMN_CV.md`
   - Check `MULTICOLUMN_FIX_SUMMARY.md`
   - Adjust config files if needed

## Questions?

- **Testing:** See `TESTING_MULTICOLUMN_CV.md`
- **Technical Details:** See `MULTICOLUMN_FIX_SUMMARY.md`
- **General Usage:** See main `README.md`

## Summary

The multi-column CV extraction has been fixed to read row-by-row, maintaining proper section order. Test your CV with the provided scripts, verify the output, and then use the GUI for production use.

**Ready to test? Run:**
```bash
python quick_test.py "your-cv.pdf"
```
