#!/usr/bin/env python3
"""
Clean placeholders from resume while preserving all actual content and formatting
"""
import re

input_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes_backup\AbhishekKumarDwivedi__cleaned.txt'
output_file = r'c:\Users\shiva\Downloads\samplecvs\redacted_resumes\AbhishekKumarDwivedi__cleaned.txt'

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove empty comma placeholders (preserving actual content)
# Pattern: ", ," or ", , " etc
content = re.sub(r',\s*,\s*,', ',', content)  # ", , ," -> ","
content = re.sub(r',\s*,', ',', content)  # ", ," -> ","

# Clean up leading/trailing commas in special contexts
content = re.sub(r':\s*,\s*', ': ', content)  # ": ," -> ": "
content = re.sub(r'\[\s*,\s*', '[', content)  # "[, " -> "["
content = re.sub(r',\s*\]', ']', content)  # ", ]" -> "]"

# Fix multiple spaces
content = re.sub(r'  +', ' ', content)

print("✓ Placeholders removed successfully!")
print(f"✓ Saved to: {output_file}")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)
