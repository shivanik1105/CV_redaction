#!/usr/bin/env python3
"""
Format the cleaned resume file for better readability
"""
import re

def format_resume(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove contact placeholders
    content = re.sub(r'E:\s+\|\s+M:\s*\n', '', content)
    content = re.sub(r'L:\s+\|\s+,\s+india\s*\n', '', content)
    
    # Remove Education section completely
    content = re.sub(
        r'Education\s*\n.*?B\.E\. in Telecommunication\s*\n',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Format project entries with [startup] or [contractor]
    content = re.sub(r'\n\[startup\]', '\n\n--------------------------------------------------\nPROJECT: [Startup]', content)
    content = re.sub(r'\n\[contractor\]', '\n\n--------------------------------------------------\nPROJECT: [Contractor]', content)
    
    # Fix section headers
    content = re.sub(r'\n={3,}\n', '\n' + '=' * 50 + '\n', content)
    content = re.sub(r'\n-{3,}\n', '\n' + '-' * 50 + '\n', content)
    
    # Add separators before major project descriptions that don't already have them
    lines = content.split('\n')
    formatted_lines = []
    prev_line = ''
    
    for i, line in enumerate(lines):
        # Check if this looks like a project title (not preceded by separator)
        if (line.strip() and 
            not line.startswith('--') and 
            not line.startswith('==') and
            i > 0 and
            prev_line.strip() and
            not prev_line.startswith('--') and
            not prev_line.startswith('==') and
            ('Platform:' in line or 'Programming:' in line or 
             (line.strip().endswith('development') and 'Description:' not in line))):
            # Add separator before this line
            if len(formatted_lines) > 0 and not formatted_lines[-1].startswith('--'):
                formatted_lines.append('')
                formatted_lines.append('-' * 50)
        
        formatted_lines.append(line)
        prev_line = line
    
    content = '\n'.join(formatted_lines)
    
    # Clean up multiple blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Formatted resume saved to: {output_file}")

if __name__ == '__main__':
    input_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__cleaned.txt'
    output_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__formatted.txt'
    format_resume(input_file, output_file)
