#!/usr/bin/env python3
"""
Diagnostic script to test CV upload processing
"""

import sys
from pathlib import Path

# Test if we can import the required modules
print("Testing imports...")
try:
    from redaction_runner import mask_document_to_pdf, extract_cv_text_no_redaction, scrub_pii_text
    print("✅ redaction_runner imports OK")
except Exception as e:
    print(f"❌ redaction_runner import failed: {e}")
    sys.exit(1)

try:
    from cv_intelligence_extractor import extract_cv_intelligence
    print("✅ cv_intelligence_extractor imports OK")
except Exception as e:
    print(f"❌ cv_intelligence_extractor import failed: {e}")
    sys.exit(1)

try:
    from vector_search import get_vector_search_engine
    print("✅ vector_search imports OK")
except Exception as e:
    print(f"❌ vector_search import failed: {e}")
    sys.exit(1)

# Test if config directory exists
config_dir = Path("config")
if config_dir.exists():
    print(f"✅ Config directory exists: {config_dir.absolute()}")
    config_files = list(config_dir.glob("*.json"))
    print(f"   Found {len(config_files)} config files:")
    for f in config_files:
        print(f"   - {f.name}")
else:
    print(f"❌ Config directory not found: {config_dir.absolute()}")

# Test if we can create a simple masked PDF
test_pdf = Path("shivani kinagi.pdf")
if test_pdf.exists():
    print(f"\n✅ Test PDF found: {test_pdf.name}")
    print("Testing PDF masking...")
    try:
        output_dir = Path("redacted_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "TEST_MASKED.pdf"
        
        result = mask_document_to_pdf(
            test_pdf,
            output_path=output_path,
            config_dir=config_dir,
            debug=True
        )
        print(f"✅ PDF masking successful: {result}")
        
        # Test text extraction
        print("Testing text extraction from masked PDF...")
        text = extract_cv_text_no_redaction(
            result,
            config_dir=config_dir,
            debug=True
        )
        print(f"✅ Text extraction successful: {len(text)} characters")
        print(f"   First 200 chars: {text[:200]}")
        
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"⚠️  Test PDF not found: {test_pdf.name}")
    print("   Skipping PDF processing test")

# Test vector search engine
print("\nTesting vector search engine...")
try:
    engine = get_vector_search_engine()
    print("✅ Vector search engine loaded")
    
    # Test embedding generation
    test_text = "Senior Software Engineer with 5 years of experience in Python and React"
    embedding = engine.generate_embedding(test_text)
    print(f"✅ Embedding generation successful: {len(embedding)} dimensions")
    
except Exception as e:
    print(f"❌ Vector search engine failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Diagnostic complete!")
print("="*60)
