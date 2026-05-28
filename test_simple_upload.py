#!/usr/bin/env python3
"""
Simple test to process a CV and see what fails
"""

import sys
from pathlib import Path

# Test CV processing
test_pdf = Path("uploads/20260406_211457_Resume_-Sunil_Durgale.pdf")
if not test_pdf.exists():
    print(f"ERROR: Test PDF not found: {test_pdf}")
    sys.exit(1)

print(f"OK: Test PDF found: {test_pdf.name}")
print(f"   Size: {test_pdf.stat().st_size} bytes")

# Try to extract text
print("\nTesting text extraction...")
try:
    from universal_pipeline_engine import PipelineOrchestrator
    orchestrator = PipelineOrchestrator(config_dir='config')
    text = orchestrator.extract_text_from_cv(str(test_pdf))
    print(f"OK: Text extraction successful: {len(text)} characters")
    print(f"   First 300 chars:\n{text[:300]}")
except Exception as e:
    print(f"ERROR: Text extraction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to redact text
print("\nTesting text redaction...")
try:
    from universal_pipeline_engine import UniversalRedactionEngine
    engine = UniversalRedactionEngine(config_dir='config')
    redacted = engine.redact(text, filename=str(test_pdf))
    print(f"OK: Text redaction successful: {len(redacted)} characters")
    print(f"   First 300 chars:\n{redacted[:300]}")
except Exception as e:
    print(f"ERROR: Text redaction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to generate embedding
print("\nTesting embedding generation...")
try:
    from vector_search import get_vector_search_engine
    engine = get_vector_search_engine()
    embedding = engine.generate_embedding(redacted[:1000])  # Use first 1000 chars
    print(f"OK: Embedding generation successful: {len(embedding)} dimensions")
except Exception as e:
    print(f"ERROR: Embedding generation failed: {e}")
    import traceback
    traceback.print_exc()

# Try LLM extraction (this might fail if no API key or Supabase issue)
print("\nTesting LLM intelligence extraction...")
try:
    from cv_intelligence_extractor import extract_cv_intelligence
    intelligence = extract_cv_intelligence(
        cv_text=redacted,
        job_description=None,
        original_filename=test_pdf.name
    )
    print(f"OK: LLM extraction successful")
    print(f"   Anonymized ID: {intelligence.get('anonymized_id')}")
    print(f"   Skills found: {len(intelligence.get('skills', []))}")
except Exception as e:
    print(f"ERROR: LLM extraction failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete!")
print("="*60)
