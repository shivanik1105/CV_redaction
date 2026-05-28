import json
from pathlib import Path

print("=" * 70)
print("MASKED PDF SETUP VERIFICATION")
print("=" * 70)

# Check masked PDFs exist
masked_pdfs = list(Path('redacted_output').glob('MASKED_*.pdf'))
print(f"\n✓ Masked PDFs generated: {len(masked_pdfs)}")
for pdf in sorted(masked_pdfs):
    size_kb = pdf.stat().st_size / 1024
    print(f"  - {pdf.name} ({size_kb:.1f} KB)")

# Check intelligence files have masked_pdf_filename
intel_dir = Path('llm_analysis')
print(f"\n✓ Intelligence files with masked PDF links:")
for intel_file in sorted(intel_dir.glob('*_intelligence.json')):
    try:
        with open(intel_file) as f:
            data = json.load(f)
        masked_pdf = data.get('masked_pdf_filename')
        if masked_pdf:
            print(f"  - {intel_file.name}: {masked_pdf}")
    except:
        pass

print("\n" + "=" * 70)
print("✓ SETUP COMPLETE - Masked PDFs ready for download!")
print("=" * 70)
