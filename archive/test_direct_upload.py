"""
Test direct upload to see the actual output
"""
from pathlib import Path
from universal_pipeline_engine import PipelineOrchestrator

pdf_path = "samples/Resume -Sunil Durgale.pdf"

print("=" * 80)
print("TESTING DIRECT UPLOAD")
print("=" * 80)
print(f"Processing: {pdf_path}\n")

orchestrator = PipelineOrchestrator(debug=False, config_dir='config')
redacted_text, profile = orchestrator.process_cv(pdf_path)

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(f"CV Type: {profile.cv_type}")
print(f"Length: {len(redacted_text)} characters")
print(f"Lines: {len(redacted_text.split(chr(10)))}")

# Save output
output_file = Path("direct_upload_test.txt")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(redacted_text)

print(f"\n✓ Saved to: {output_file}")

# Show first part
print("\n" + "=" * 80)
print("PREVIEW (First 2000 characters)")
print("=" * 80)
print(redacted_text[:2000])
print("\n... (see full output in direct_upload_test.txt)")
