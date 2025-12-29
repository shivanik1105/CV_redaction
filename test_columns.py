import pdfplumber

# Open the PDF
pdf_path = r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    page_width = page.width
    page_height = page.height
    mid_x = page_width / 2
    
    print(f"Page width: {page_width}, Mid point: {mid_x}")
    
    # Extract left column
    left_bbox = (0, 0, mid_x, page_height)
    left_crop = page.crop(left_bbox)
    left_text = left_crop.extract_text(x_tolerance=2, y_tolerance=2)
    
    # Extract right column
    right_bbox = (mid_x, 0, page_width, page_height)
    right_crop = page.crop(right_bbox)
    right_text = right_crop.extract_text(x_tolerance=2, y_tolerance=2)
    
    print("\n=== LEFT COLUMN ===")
    print(left_text[:500] if left_text else "None")
    
    print("\n\n=== RIGHT COLUMN ===")
    print(right_text[:500] if right_text else "None")
