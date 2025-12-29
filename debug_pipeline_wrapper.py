from resume_redactor import ResumePipeline
import os

pdf_path = r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf"
pipeline = ResumePipeline()

print(f"Processing {pdf_path}...")
text = pipeline.extractor.extract(pdf_path)

print("\n=== RAW EXTRACTED TEXT ===")
print(text[:2000]) # First 2000 chars

with open("debug_abinvav_raw.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("\n\n=== POLISHED TEXT ===")
polished = pipeline.redactor.redact(text)
# Skip other steps to isolate
# polished = pipeline.polisher.polish(polished) 
# print(polished[:2000])
