#!/usr/bin/env python3
"""
Batch Format All Resumes
Applies comprehensive formatting improvements to all cleaned resumes
"""

import re
import os
from pathlib import Path

def format_resume(content):
    """Apply all formatting improvements"""
    
    # Remove empty placeholders
    # Remove ", ," patterns
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r'^,\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\s*,$', '', content, flags=re.MULTILINE)
    
    # Remove empty brackets
    content = re.sub(r'\[\s*\]', '', content)
    content = re.sub(r'\(\s*\)', '', content)
    
    # Remove multiple spaces
    content = re.sub(r' {2,}', ' ', content)
    
    # Remove trailing spaces
    content = re.sub(r' +$', '', content, flags=re.MULTILINE)
    
    # Remove multiple blank lines (keep max 2)
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # Fix date formatting in experience sections
    # Match patterns like "YYYY-MM to YYYY-MM" or "Month YYYY to Month YYYY"
    def fix_dates(match):
        text = match.group(0)
        # Convert "to present" to "- Present"
        text = re.sub(r'\s+to\s+present\b', ' - Present', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+to\s+till\s+date\b', ' - Present', text, flags=re.IGNORECASE)
        # Convert "to" to "-" in date ranges
        text = re.sub(r'(\d{4}(?:-\d{2})?)\s+to\s+(\d{4}(?:-\d{2})?)', r'\1 - \2', text, flags=re.IGNORECASE)
        return text
    
    content = re.sub(r'\d{4}(?:-\d{2})?\s+to\s+(?:present|\d{4}(?:-\d{2})?)', fix_dates, content, flags=re.IGNORECASE)
    
    # Add PROJECT: prefix where missing (look for common project patterns)
    lines = content.split('\n')
    formatted_lines = []
    for i, line in enumerate(lines):
        # Check if line looks like a project title (often has company name or starts with capital letter after bullet)
        if re.match(r'^\s*[•●○▪︎-]\s+[A-Z]', line) and 'PROJECT:' not in line.upper():
            # Check if it's not already a PROJECT line and looks like a project description
            if not re.match(r'^\s*[•●○▪︎-]\s+(?:Developed|Implemented|Created|Built|Designed|Led|Managed)', line):
                # This might be a project title
                if ':' in line and len(line.strip()) < 100:
                    line = re.sub(r'^(\s*[•●○▪︎-]\s+)', r'\1PROJECT: ', line)
        formatted_lines.append(line)
    
    content = '\n'.join(formatted_lines)
    
    # Ensure proper spacing around section headers
    # Look for common section headers and ensure they have blank lines before/after
    section_headers = [
        'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE',
        'PROFESSIONAL SUMMARY', 'SUMMARY', 'PROFILE',
        'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES',
        'PROJECTS', 'KEY PROJECTS',
        'CERTIFICATIONS', 'EDUCATION'
    ]
    
    for header in section_headers:
        # Add separators before major sections
        pattern = rf'(?<!\n)\n({header})\n(?!\n)'
        content = re.sub(pattern, r'\n\1\n==================================================\n', content, flags=re.IGNORECASE)
    
    # Clean up over-separated content
    content = re.sub(r'={50,}\n={50,}', '=' * 50, content)
    
    return content


def process_all_resumes(input_dir, output_dir):
    """Process all cleaned resume files"""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Find all cleaned files
    cleaned_files = list(input_path.glob('*_cleaned.txt'))
    
    print(f"\n{'='*60}")
    print(f"BATCH FORMATTING ALL RESUMES")
    print(f"{'='*60}")
    print(f"Found {len(cleaned_files)} files to format\n")
    
    success_count = 0
    failed_count = 0
    
    for file_path in cleaned_files:
        try:
            print(f"Processing: {file_path.name}")
            
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply formatting
            formatted_content = format_resume(content)
            
            # Save formatted version
            output_file = output_path / file_path.name.replace('_cleaned.txt', '_formatted.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"  ✓ Saved: {output_file.name}\n")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            failed_count += 1
    
    print(f"{'='*60}")
    print(f"SUMMARY: {success_count} successful, {failed_count} failed")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    process_all_resumes('redacted_resumes', 'redacted_resumes')
