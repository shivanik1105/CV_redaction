"""
Test pdfplumber extraction
"""
import sys
import pdfplumber

if len(sys.argv) < 2:
    print("Usage: python test_pdfplumber.py <pdf_path>")
    sys.exit(1)

pdf_path = sys.argv[1]

print("=" * 80)
print("PDFPLUMBER EXTRACTION TEST")
print("=" * 80)
print(f"File: {pdf_path}\n")

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num}")
        print(f"{'='*80}\n")
        
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print(f"Total lines: {len(lines)}\n")
            
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}: {line}")
        else:
            print("No text extracted")

print(f"\n{'='*80}")
print("EXTRACTION COMPLETE")
print(f"{'='*80}\n")
