
import fitz

def extract_test(file_path):
    print(f"--- SORT=TRUE (Current) ---")
    with fitz.open(file_path) as doc:
        for page in doc:
            blocks = page.get_text("blocks", sort=True)
            for b in blocks:
                if b[6] == 0:
                    text = " ".join(b[4].split())
                    if "SKILLS" in text or "EXPERIENCE" in text or "Senior" in text:
                        print(f"Block: {text[:50]}...")

    print(f"\n--- SORT=FALSE (Stream) ---")
    with fitz.open(file_path) as doc:
        for page in doc:
            blocks = page.get_text("blocks", sort=False)
            for b in blocks:
                if b[6] == 0:
                    text = " ".join(b[4].split())
                    if "SKILLS" in text or "EXPERIENCE" in text or "Senior" in text:
                        print(f"Block: {text[:50]}...")

extract_test("samples/Naukri_AbhinavVinodSolapurkar[5y_8m].pdf")
