import pdfplumber

pdf_path = "samples/Resume - Kedarinath.docx...pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    
    print("First 30 words:")
    for i, word in enumerate(words[:30]):
        print(f"{i}: '{word['text']}' | x0={word['x0']:.1f}, x1={word['x1']:.1f}, top={word['top']:.1f}")
