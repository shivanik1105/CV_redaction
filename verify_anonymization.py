"""Verification script for CV anonymization"""
import os
import re

def verify_anonymization():
    output_dir = 'final_output'
    files = [f for f in os.listdir(output_dir) if f.startswith('REDACTED_')]
    
    print('\n' + '='*60)
    print('CV ANONYMIZATION - VERIFICATION REPORT')
    print('='*60 + '\n')
    print(f'Total files processed: {len(files)}\n')
    
    # Initialize counters
    checks = {
        'Education headers': 0,
        'Personal sections (hobbies/interests)': 0,
        'Demographics (DOB/gender/marital)': 0,
        'Email addresses': 0,
        'Phone numbers (10+ digits)': 0,
        'Names (3+ word patterns)': 0
    }
    
    # Check each file
    for filename in files:
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for education headers
            if re.search(r'(?i)^(education|academic|qualification)s?\s*$', content, re.MULTILINE):
                checks['Education headers'] += 1
            
            # Check for personal sections
            if re.search(r'(?i)(hobbies|personal interests|activities and interest)', content):
                checks['Personal sections (hobbies/interests)'] += 1
            
            # Check for demographics
            if re.search(r'(?i)(date of birth|dob|gender|marital status)', content):
                checks['Demographics (DOB/gender/marital)'] += 1
            
            # Check for emails
            if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content):
                checks['Email addresses'] += 1
            
            # Check for phone numbers
            if re.search(r'\+?\d{10,}', content):
                checks['Phone numbers (10+ digits)'] += 1
            
            # Check for standalone names (3+ word capitalized patterns on own line)
            matches = re.findall(r'(?m)^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,}\s*$', content)
            if matches:
                checks['Names (3+ word patterns)'] += len(matches)
        
        except Exception as e:
            print(f'Error reading {filename}: {e}')
    
    # Display results
    print('Anonymization Checks:')
    print('-' * 60)
    all_passed = True
    for check_name, count in checks.items():
        status = '✓ PASS' if count == 0 else f'✗ FOUND: {count}'
        color = '\033[92m' if count == 0 else '\033[91m'  # Green or Red
        reset = '\033[0m'
        print(f'  {color}{status:15}{reset}  {check_name}')
        if count > 0:
            all_passed = False
    
    print('-' * 60)
    if all_passed:
        print('\n\033[92m✓ ALL ANONYMIZATION CHECKS PASSED!\033[0m\n')
    else:
        print('\n\033[93m⚠ Some items detected (review context to confirm)\033[0m\n')
    
    # Technical content preservation check
    print('Technical Content Preservation:')
    print('-' * 60)
    sample_file = files[0] if files else None
    if sample_file:
        with open(os.path.join(output_dir, sample_file), 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common technical terms
        tech_terms_found = []
        tech_patterns = [
            (r'(?i)\b(java|python|c\+\+|javascript|typescript)\b', 'Programming languages'),
            (r'(?i)\b(aws|azure|gcp|cloud)\b', 'Cloud platforms'),
            (r'(?i)\b(docker|kubernetes|jenkins)\b', 'DevOps tools'),
            (r'(?i)\b(react|angular|vue|node\.?js)\b', 'Frameworks'),
        ]
        
        for pattern, category in tech_patterns:
            if re.search(pattern, content):
                tech_terms_found.append(category)
        
        if tech_terms_found:
            print(f'  \033[92m✓ Technical terms preserved\033[0m: {", ".join(tech_terms_found)}')
        else:
            print('  \033[93m⚠ No common technical terms found in sample\033[0m')
    
    print('-' * 60 + '\n')

if __name__ == '__main__':
    verify_anonymization()
