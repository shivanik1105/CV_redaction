#!/usr/bin/env python3
"""
Test script to verify the redaction fix is working correctly.

This script checks that:
1. PII is still being redacted (privacy maintained)
2. Job content is no longer being over-redacted (accuracy improved)
"""

import re
from pathlib import Path


def test_skip_patterns():
    """Test that job-related patterns are correctly identified"""
    
    skip_patterns = [
        r"(?i)\b(resume|curriculum\s+vitae|cv|profile|summary|objective)\b",
        r"(?i)\b(engineer|developer|architect|manager|consultant|analyst|lead|senior|junior|principal)\b",
        r"(?i)\b(pvt|ltd|limited|inc|corporation|corp|llc|llp|international|global|solutions|technologies|systems)\b",
        r"(?i)\b(software|system|technical|project|product|data|web|mobile|cloud|devops)\b",
        r"(?i)\b(experience|skills|education|certification|projects|achievements)\b",
    ]
    
    # Test cases that SHOULD be skipped (not redacted)
    should_skip = [
        "Senior Software Engineer",
        "Forbes Technosys Ltd",
        "Harman International",
        "Software Developer at Microsoft",
        "Technical Skills",
        "Work Experience",
        "Project Manager",
        "Cloud Architect",
        "Data Analyst",
    ]
    
    # Test cases that SHOULD be redacted
    should_redact = [
        "John Smith",
        "Jane Doe",
        "Amit Kumar",
        "Priya Sharma",
    ]
    
    print("Testing Skip Patterns...")
    print("=" * 60)
    
    for text in should_skip:
        matches = any(re.search(pat, text) for pat in skip_patterns)
        status = "✅ PASS" if matches else "❌ FAIL"
        print(f"{status}: '{text}' - Should skip: {matches}")
    
    print()
    for text in should_redact:
        matches = any(re.search(pat, text) for pat in skip_patterns)
        status = "✅ PASS" if not matches else "❌ FAIL"
        print(f"{status}: '{text}' - Should redact: {not matches}")
    
    print()


def test_job_indicators():
    """Test that job content indicators are correctly identified"""
    
    job_indicators = [
        r"\d{4}\s*[-–]\s*\d{4}",  # Date ranges like 2018-2021
        r"(?i)\b(engineer|developer|architect|manager|consultant|analyst|lead)\b",
        r"(?i)\b(pvt|ltd|limited|inc|corporation|corp)\b",
        r"(?i)\b(experience|project|role|position|responsibilities)\b",
    ]
    
    # Lines that SHOULD be identified as job content
    job_lines = [
        "Software Engineer at Harman (2018-2021)",
        "Forbes Technosys Ltd - Senior Developer",
        "Project responsibilities included system design",
        "Lead Engineer position at Microsoft",
        "Experience: 5 years in software development",
    ]
    
    # Lines that SHOULD NOT be identified as job content
    non_job_lines = [
        "123456 Main Street, Pune",
        "Email: john@example.com",
        "Phone: +91 9876543210",
        "Date of Birth: 15/08/1990",
    ]
    
    print("Testing Job Indicators...")
    print("=" * 60)
    
    for text in job_lines:
        matches = any(re.search(pat, text) for pat in job_indicators)
        status = "✅ PASS" if matches else "❌ FAIL"
        print(f"{status}: '{text[:50]}...' - Is job content: {matches}")
    
    print()
    for text in non_job_lines:
        matches = any(re.search(pat, text) for pat in job_indicators)
        status = "✅ PASS" if not matches else "❌ FAIL"
        print(f"{status}: '{text}' - Is NOT job content: {not matches}")
    
    print()


def test_job_content_indicators():
    """Test that job content with PII is correctly handled"""
    
    job_content_indicators = [
        r"(?i)\b(build|develop|design|implement|manage|lead|create|maintain|optimize|proficient|experienced|skilled)\b",
        r"(?i)\b(application|system|software|platform|service|api|database|framework|technology|technologies)\b",
        r"(?i)\b(experience|project|role|responsibilities|achievements|skills|expertise|knowledge)\b",
        r"(?i)\b(c\+\+|python|java|javascript|react|angular|node|sql|aws|azure|docker|kubernetes|android|ios|kotlin)\b",
        r"\d{4}\s*[-–]\s*\d{4}",  # Date ranges
    ]
    
    # Lines with PII but also job content (SHOULD be preserved)
    preserve_lines = [
        "Build linux/unix applications using C++, shell script",
        "Designed and implemented new features for the derivatives system",
        "Experience working with remote data via REST API, JSON",
        "Proficient in modern Android technologies including Kotlin, Jetpack Compose",
        "WLP-FO is standards framework for authorization switching",
    ]
    
    # Lines with PII and NO job content (SHOULD be redacted)
    redact_lines = [
        "Email: john.doe@example.com",
        "Contact: +91 9876543210",
        "LinkedIn: linkedin.com/in/johndoe",
        "Address: 123 Main St, Pune 411001",
    ]
    
    print("Testing Job Content Indicators...")
    print("=" * 60)
    
    for text in preserve_lines:
        matches = any(re.search(pat, text) for pat in job_content_indicators)
        status = "✅ PASS" if matches else "❌ FAIL"
        print(f"{status}: '{text[:50]}...' - Has job content: {matches}")
    
    print()
    for text in redact_lines:
        matches = any(re.search(pat, text) for pat in job_content_indicators)
        status = "✅ PASS" if not matches else "❌ FAIL"
        print(f"{status}: '{text}' - No job content: {not matches}")
    
    print()


def main():
    print("\n" + "=" * 60)
    print("CV REDACTION FIX - PATTERN TESTS")
    print("=" * 60 + "\n")
    
    test_skip_patterns()
    test_job_indicators()
    test_job_content_indicators()
    
    print("=" * 60)
    print("Test complete! Review results above.")
    print("=" * 60 + "\n")
    
    print("Next steps:")
    print("1. Clear cached masked PDFs: rm -rf masked_pdfs_cache/*")
    print("2. Re-upload a CV through the application")
    print("3. Download the masked PDF and verify:")
    print("   - Personal info (name, email, phone) is masked")
    print("   - Job content (titles, companies, descriptions) is visible")
    print()


if __name__ == "__main__":
    main()
