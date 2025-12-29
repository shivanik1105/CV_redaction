import pdfplumber

# Open the PDF
pdf_path = r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    # Try different extraction methods
    print("=== Method 1: Basic extract_text() ===")
    text1 = page.extract_text()
    print(text1[:500] if text1 else "None")
    
    print("\n\n=== Method 2: extract_text(layout=True) ===")
    text2 = page.extract_text(layout=True)
    print(text2[:500] if text2 else "None")
    
    print("\n\n=== Method 3: extract_text(x_tolerance=3, y_tolerance=3) ===")
    text3 = page.extract_text(x_tolerance=3, y_tolerance=3)
    print(text3[:500] if text3 else "None")
