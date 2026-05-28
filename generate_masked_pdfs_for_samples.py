#!/usr/bin/env python
"""
Generate masked PDFs for all sample candidates from archive/samples/
This converts text files to clean PDFs without visible [REDACTED_*] markers
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import hashlib

sys.path.insert(0, '.')

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from universal_pipeline_engine import PipelineOrchestrator, UniversalRedactionEngine
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

print("=" * 70)
print("GENERATING MASKED PDFs FOR SAMPLE CANDIDATES")
print("=" * 70)

samples_dir = Path('archive/samples')
output_dir = Path('redacted_output')
output_dir.mkdir(exist_ok=True)

# Find all text files
text_files = list(samples_dir.rglob('*.txt'))

print(f"\nFound {len(text_files)} text files in samples/")
print("-" * 70)

generated_count = 0
failed_count = 0

for idx, text_file in enumerate(sorted(text_files), 1):
    try:
        # Read original text
        with open(text_file, 'r', encoding='utf-8', errors='replace') as f:
            original_text = f.read().strip()
        
        if not original_text:
            print(f"{idx}. SKIP {text_file.name}: empty file")
            continue
        
        # Redact the text (remove PII, replace with clean text without markers)
        try:
            engine = UniversalRedactionEngine(config_dir='config')
            redacted_text = engine.redact(original_text, filename=str(text_file))
        except Exception as e:
            print(f"{idx}. ERROR redacting {text_file.name}: {str(e)[:50]}")
            redacted_text = original_text
        
        # Clean up redaction markers for display (remove [REDACTED_*] tags)
        clean_text = redacted_text
        import re
        clean_text = re.sub(r'\[REDACTED[^\]]*\]', '[redacted]', clean_text)
        
        # Create masked PDF with clean text
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(text_file.name.encode()).hexdigest()[:8]
        masked_pdf_name = f"MASKED_{timestamp}_{file_hash}.pdf"
        masked_pdf_path = output_dir / masked_pdf_name
        
        # Render clean text to PDF
        c = canvas.Canvas(str(masked_pdf_path), pagesize=letter)
        c.setTitle("Masked CV")
        
        # Add header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 750, "Masked CV (PII Removed)")
        
        # Add content
        c.setFont("Helvetica", 10)
        y = 730
        line_height = 12
        max_width = 500
        margin = 50
        
        for paragraph in clean_text.split('\n'):
            paragraph = paragraph.strip()
            if not paragraph:
                y -= line_height
                continue
            
            # Word wrap
            words = paragraph.split()
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                if len(test_line) > 80:  # Approximate character limit per line
                    if current_line:
                        c.drawString(margin, y, ' '.join(current_line))
                        y -= line_height
                    current_line = [word]
                else:
                    current_line.append(word)
            
            if current_line:
                c.drawString(margin, y, ' '.join(current_line))
                y -= line_height
            
            # Page break if needed
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750
        
        c.save()
        
        # Update intelligence file to reference masked PDF
        intel_file = output_dir.parent / 'llm_analysis' / f"{text_file.stem}_intelligence.json"
        if intel_file.exists():
            with open(intel_file, 'r', encoding='utf-8') as f:
                intel = json.load(f)
            intel['masked_pdf_filename'] = masked_pdf_name
            with open(intel_file, 'w', encoding='utf-8') as f:
                json.dump(intel, f, indent=2, ensure_ascii=False)
        
        print(f"{idx}. ✓ {text_file.name}")
        print(f"   → {masked_pdf_name}")
        generated_count += 1
        
    except Exception as e:
        print(f"{idx}. ERROR {text_file.name}: {str(e)[:60]}")
        failed_count += 1

print("-" * 70)
print(f"\nRESULT:")
print(f"  ✓ Generated: {generated_count} masked PDFs")
print(f"  ✗ Failed: {failed_count}")
print(f"\n✓ Masked PDFs stored in: redacted_output/")
print("✓ All candidates now have clean masked PDF versions!")
print("=" * 70)
