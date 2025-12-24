#!/usr/bin/env python3
"""
Remove empty placeholders from redacted resume
"""
import re

def clean_placeholders(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove standalone comma-space-comma patterns (empty placeholders)
    content = re.sub(r',\s*,\s*,', ',', content)  # Triple commas
    content = re.sub(r',\s*,', ',', content)  # Double commas
    
    # Remove leading/trailing commas with spaces in lists
    content = re.sub(r':\s*,\s*', ': ', content)  # Colon followed by comma
    content = re.sub(r'\[\s*,\s*', '[', content)  # Opening bracket followed by comma
    content = re.sub(r',\s*\]', ']', content)  # Comma before closing bracket
    content = re.sub(r'\(\s*,\s*', '(', content)  # Opening paren followed by comma
    content = re.sub(r',\s*\)', ')', content)  # Comma before closing paren
    
    # Remove comma-space at end of sentences before periods
    content = re.sub(r',\s*\.', '.', content)
    
    # Remove extra spaces after cleaning commas
    content = re.sub(r'\s+,', ',', content)
    content = re.sub(r',\s+,', ',', content)
    
    # Clean up "and  " (double space) patterns
    content = re.sub(r'\band\s\s+', 'and ', content)
    content = re.sub(r'\bwith\s\s+', 'with ', content)
    
    # Clean up patterns like "C and  low" to "C and low"
    content = re.sub(r'\s\s+', ' ', content)
    
    # Remove standalone commas in the middle of text
    content = re.sub(r'\s,\s([A-Z])', r' \1', content)  # ", Word" -> " Word"
    
    # Fix specific broken patterns
    content = re.sub(r'and\s+low level', 'and low level', content)
    content = re.sub(r'with\s+and Google', 'with Google', content)
    content = re.sub(r'closely with\s+and', 'closely with', content)
    content = re.sub(r'worked with\s+,', 'worked with', content)
    
    # Clean empty list items like "[, ]" or "[, ], ,"
    content = re.sub(r'\[,\s*\]', '[]', content)
    
    # Fix "C), deep" to "C, deep" or "C), deep" - check context
    content = re.sub(r'\(UML\) and\s*,\s*,\s*C\)', '(UML, C)', content)
    content = re.sub(r'design\(UML\) and\s*,\s*,\s*C\),', 'design (UML, C),', content)
    
    # Fix "Platform: , Android" to "Platform: Android"
    content = re.sub(r'Platform:\s*,\s*', 'Platform: ', content)
    content = re.sub(r'Programming:\s*,\s*', 'Programming: ', content)
    
    # Fix multiple commas in technology lists
    content = re.sub(r',\s*,\s*([A-Z])', r', \1', content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Placeholders cleaned!")
    print(f"✓ Output saved to: {output_file}")

if __name__ == '__main__':
    input_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__final.txt'
    output_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__final.txt'
    clean_placeholders(input_file, output_file)
