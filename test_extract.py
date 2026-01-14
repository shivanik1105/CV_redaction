import fitz
import pdfplumber

pdf_path = "samples/Resume - Kedarinath.docx...pdf"

print("=" * 80)
print("PyMuPDF (fitz) - dict extraction:")
print("=" * 80)
with fitz.open(pdf_path) as doc:
    page = doc[0]
    print(f"Page size: {page.rect.width} x {page.rect.height}")
    
    # Try different extraction modes
    print("\n--- Mode: text ---")
    text1 = page.get_text("text")
    print(f"Length: {len(text1)} chars")
    print(text1[:500])
    
    print("\n--- Mode: blocks ---")
    text2 = page.get_text("blocks")
    print(f"Number of blocks: {len(text2)}")
    for i, block in enumerate(text2[:10]):
        print(f"Block {i}: {block}")
    
    print("\n--- Mode: dict ---")
    data = page.get_text("dict")
    print(f"Number of blocks in dict: {len(data['blocks'])}")
    for i, block in enumerate(data['blocks'][:5]):
        if 'lines' in block:
            print(f"\nBlock {i} at ({block['bbox']}):")
            for line in block['lines'][:2]:
                for span in line['spans']:
                    print(f"  '{span['text']}' at x={span['bbox'][0]:.1f}")

print("\n" + "=" * 80)
print("pdfplumber extraction:")
print("=" * 80)
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    print(f"Page size: {page.width} x {page.height}")
    
    # Try layout mode
    text3 = page.extract_text(layout=True)
    print(f"\nLayout mode length: {len(text3)} chars")
    print(text3[:500])
    
    # Try getting words with positions
    words = page.extract_words()
    print(f"\n\nTotal words extracted: {len(words)}")
    print("\nFirst 20 words with positions:")
    for i, word in enumerate(words[:20]):
        print(f"{i}: '{word['text']}' at x={word['x0']:.1f}, y={word['top']:.1f}")
