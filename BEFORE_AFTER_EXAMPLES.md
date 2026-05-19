# Before & After: Redaction Fix Examples

## Overview
This document shows examples of what was being masked before the fix and what should be visible after.

---

## Example 1: Job Description

### BEFORE (Over-Masked) ❌
```
████████████████████████████████████████████████████
████████████████████████████████████████████████████
Build linux / unix applications using C, C++, shell
script., Unix, Multithreading, data structure and
algorithms, socket programming, TCP & UDP Sockets,
STL.Design, build, and maintain efficient, reusable,
and reliable C++ code maintain Debian and Red hat
packages and other build environment.
```

### AFTER (Correctly Masked) ✅
```
[REDACTED NAME]
[REDACTED EMAIL]
Build linux / unix applications using C, C++, shell
script., Unix, Multithreading, data structure and
algorithms, socket programming, TCP & UDP Sockets,
STL.Design, build, and maintain efficient, reusable,
and reliable C++ code maintain Debian and Red hat
packages and other build environment.
```

**What Changed**: Only the name and email are masked. The job description is fully visible.

---

## Example 2: Company and Job Title

### BEFORE (Over-Masked) ❌
```
2017
████████████████████████████████████████████████████
Forbes Technosys Ltd
->Build linux / unix applications using C++ and QT
platform ->Designed, coded, implemented and tested
new features and modules for the derivatives system
```

### AFTER (Correctly Masked) ✅
```
2017
Senior Software Engineer
Forbes Technosys Ltd
->Build linux / unix applications using C++ and QT
platform ->Designed, coded, implemented and tested
new features and modules for the derivatives system
```

**What Changed**: Job title and company name are now visible. Only personal info at the top is masked.

---

## Example 3: Technical Skills Section

### BEFORE (Over-Masked) ❌
```
████████████████████████████████████████████████████
Android internals.
Proficient in modern Android technologies including Kotlin, Jetpack Compose, Coroutines, and MVVM architecture for
████████████████████████████████████████████████████
```

### AFTER (Correctly Masked) ✅
```
Technical Skills
Android internals.
Proficient in modern Android technologies including Kotlin, Jetpack Compose, Coroutines, and MVVM architecture for
building scalable applications.
```

**What Changed**: Section header and technical content are fully visible.

---

## Example 4: Work Experience with Dates

### BEFORE (Over-Masked) ❌
```
214 Days
████████████████████████████████████████████████████
WLP-FO is standards framework for authorization
switching. Need to create acquiring instance for
Australia and New Zealand Banking Group Create
Interface Base24 on ISO8583 using WLPFO protocol
guidelines.
```

### AFTER (Correctly Masked) ✅
```
214 Days
Senior System Engineer (Oct 2021 – till date)
WLP-FO is standards framework for authorization
switching. Need to create acquiring instance for
Australia and New Zealand Banking Group Create
Interface Base24 on ISO8583 using WLPFO protocol
guidelines.
```

**What Changed**: Job title with dates and project description are visible.

---

## What Gets Masked vs. Preserved

### ✅ PRESERVED (Visible in PDF)

#### Job Titles
- Senior Software Engineer
- Lead Developer
- System Architect
- Project Manager
- Technical Consultant

#### Company Names
- Forbes Technosys Ltd
- Harman International
- Microsoft Corporation
- Worldline India Pvt Ltd
- John Deere

#### Technical Content
- Programming languages: C++, Python, Java, JavaScript, Kotlin
- Frameworks: React, Angular, Spring Boot, Django
- Tools: Docker, Kubernetes, AWS, Azure, Git
- Technical terms: API, REST, JSON, SQL, NoSQL
- Job descriptions and responsibilities
- Project details and achievements

#### Dates and Durations
- 2018-2021
- Oct 2021 – till date
- 5 years experience
- 214 Days

---

### ❌ MASKED (Black Boxes in PDF)

#### Personal Information
- Full name (in header)
- Email addresses
- Phone numbers
- LinkedIn URLs
- GitHub profiles
- Personal addresses
- Date of birth
- Marital status
- Father's/Mother's name

#### Contact Lines
- Email: john@example.com
- Phone: +91 9876543210
- Contact: 123-456-7890
- LinkedIn: linkedin.com/in/johndoe

---

## Pattern Recognition Examples

### Example: Line with PII + Job Content
**Line**: "Build linux applications using C++ and maintain Debian packages"

**Analysis**:
- Contains job content: ✅ "Build", "applications", "C++"
- Contains PII: ❌ No email/phone/URL
- **Result**: Line is PRESERVED ✅

---

### Example: Line with PII Only
**Line**: "Email: john.doe@example.com | Phone: +91 9876543210"

**Analysis**:
- Contains job content: ❌ No job-related keywords
- Contains PII: ✅ Email and phone
- **Result**: Line is MASKED ❌

---

### Example: Company Name in Header
**Line**: "Forbes Technosys Ltd"

**Analysis**:
- Location: Below top 15% of page
- Contains: "Ltd" (company indicator)
- **Result**: Line is PRESERVED ✅

---

### Example: Name in Header
**Line**: "John Smith"

**Analysis**:
- Location: Within top 15% of page
- Pattern: 2 capitalized words
- No job keywords
- **Result**: Line is MASKED ❌

---

## Testing Your Fix

### Test Case 1: Upload a CV with Job Descriptions
**Expected**: Job descriptions should be fully visible, only name/email/phone masked

### Test Case 2: Upload a CV with Company Names
**Expected**: Company names like "Harman International" should be visible

### Test Case 3: Upload a CV with Technical Skills
**Expected**: Programming languages and frameworks should be visible

### Test Case 4: Upload a CV with Contact Info
**Expected**: Email, phone, LinkedIn should be masked with black boxes

---

## Common Issues and Solutions

### Issue: Job titles are still being masked
**Solution**: Check if the job title is in the top 15% of the page. If yes, it might be mistaken for a name. Add the title to the skip_patterns.

### Issue: Company names are being masked
**Solution**: Verify the company name contains keywords like "Ltd", "Inc", "Corporation", "International", "Global", "Solutions", "Technologies", or "Systems".

### Issue: Personal info is NOT being masked
**Solution**: Check the PII patterns in `config/pii_patterns.json`. Ensure email/phone/URL patterns are correct.

### Issue: Technical terms are being masked
**Solution**: Add the terms to the job_content_indicators patterns in `redaction_runner.py`.

---

## Summary

The fix makes the redaction system **context-aware**:
- It understands the difference between personal info and professional content
- It preserves job-related information while masking PII
- It uses pattern matching to identify what should be kept vs. masked

**Result**: Better privacy protection + Better job matching accuracy
