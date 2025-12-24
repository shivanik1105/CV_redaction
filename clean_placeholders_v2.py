#!/usr/bin/env python3
"""
Remove empty placeholders from redacted resume while preserving formatting
"""
import re

def clean_placeholders_v2(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    for line in lines:
        # Remove patterns like ", , " (empty placeholders between commas)
        line = re.sub(r',\s*,\s*,', ',', line)
        line = re.sub(r',\s*,', ',', line)
        
        # Remove leading commas after colons/brackets
        line = re.sub(r':\s*,\s+', ': ', line)
        line = re.sub(r'\[\s*,\s+', '[', line)
        line = re.sub(r',\s*\]', ']', line)
        
        # Fix patterns like "HAL, , JavaScript" to "HAL, JavaScript"
        line = re.sub(r',\s+,', ',', line)
        
        # Fix "and  word" (double space) to "and word"
        line = re.sub(r'\s\s+', ' ', line)
        
        # Remove standalone ", " before end of line or before capital letters in odd contexts
        # But preserve legitimate commas in lists
        
        cleaned_lines.append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"✓ Placeholders cleaned while preserving formatting!")
    print(f"✓ Output saved to: {output_file}")

if __name__ == '__main__':
    # First restore from a backup source
    import shutil
    
    # We need to get the original that wasn't broken
    # Let me read the formatted file from earlier
    final_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__final.txt'
    cleaned_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__cleaned.txt'
    
    # Copy cleaned to final to restore
    shutil.copy(cleaned_file, final_file + '.temp')
    
    print("Cleaning placeholders...")
    clean_placeholders_v2(final_file + '.temp', final_file)
    
    import os
    os.remove(final_file + '.temp')
