
import logging
from paddleocr import PaddleOCR
import fitz

logging.basicConfig(level=logging.DEBUG)
pdf_path = "samples/Anandprakash_Tandale_Resume (2).pdf"

print("--- TEST 1: PaddleOCR(use_angle_cls=False) ---")
try:
    ocr = PaddleOCR(lang='en', use_angle_cls=False)
    doc = fitz.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap()
    img_path = "debug_anand.png"
    pix.save(img_path)
    
    # Call without cls arg
    result = ocr.ocr(img_path)
    print(f"Paddle Result: {result is not None}")
except Exception as e:
    print(f"Paddle Failed: {e}")

print("--- TEST 2: Pytesseract ---")
try:
    import pytesseract
    from PIL import Image
    text = pytesseract.image_to_string(Image.open(img_path))
    print(f"Tesseract Result: {len(text)} chars")
except Exception as e:
    print(f"Tesseract Failed: {e}")
