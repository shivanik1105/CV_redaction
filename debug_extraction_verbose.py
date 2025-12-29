import pdfplumber

def extract_verbose(pdf_path):
    print(f"Processing: {pdf_path}")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        all_text = []
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i+1} ---")
            page_width = page.width
            page_height = page.height
            print(f"Dimensions: {page_width}x{page_height}")
            
            words = page.extract_words(x_tolerance=2, y_tolerance=2)
            if not words: print("No words!")
            
            # DEBUG: Print first 50 words with coords
            print("\n[WORD MAPPING]:")
            for i, w in enumerate(words[:50]):
                print(f"{i}: '{w['text']}' ({w['x0']:.1f}, {w['top']:.1f}) - ({w['x1']:.1f}, {w['bottom']:.1f})")
            
            # Find specific keywords
            print("\n[KEYWORD LOCATIONS]:")
            for w in words:
                if w['text'] in ['Abhinav', 'problem', 'technical,', 'motivated', 'enhance']:
                    print(f"'{w['text']}': y={w['top']:.1f}-{w['bottom']:.1f}, x={w['x0']:.1f}-{w['x1']:.1f}")
            
            x_coords = sorted(set([w['x0'] for w in words]))
            gaps = []
            for j in range(len(x_coords) - 1):
                gap_size = x_coords[j+1] - x_coords[j]
                if gap_size > 10:
                    gap_center = (x_coords[j] + x_coords[j+1]) / 2
                    if 0.2 * page_width < gap_center < 0.8 * page_width:
                        gaps.append((gap_center, gap_size))
            
            split_point = max(gaps, key=lambda x: x[1])[0] if gaps else page_width/2
            print(f"Split point: {split_point}")
            
            header_bottom = 0
            for w in words:
                if w['x0'] < split_point < w['x1']:
                    header_bottom = max(header_bottom, w['bottom'])
            
            y_cutoff = header_bottom + 5 if header_bottom > 0 else 0
            print(f"Y Cutoff: {y_cutoff}")
            
            parts = []
            
            # Header
            if y_cutoff > 0:
                header_bbox = (0, 0, page_width, y_cutoff)
                header_crop = page.crop(header_bbox)
                header_text = header_crop.extract_text(x_tolerance=2, y_tolerance=2)
                if header_text:
                    print(f"\n[HEADER TEXT PREVIEW]:\n{header_text[:100]}...")
                    parts.append(header_text.strip())
            
            # Left
            left_bbox = (0, y_cutoff, split_point, page_height)
            left_crop = page.crop(left_bbox)
            left_text = left_crop.extract_text(x_tolerance=2, y_tolerance=2)
            if left_text:
                print(f"\n[LEFT TEXT PREVIEW]:\n{left_text[:100]}...")
                parts.append(left_text.strip())
                
            # Right
            right_bbox = (split_point, y_cutoff, page_width, page_height)
            right_crop = page.crop(right_bbox)
            right_text = right_crop.extract_text(x_tolerance=2, y_tolerance=2)
            if right_text:
                print(f"\n[RIGHT TEXT PREVIEW]:\n{right_text[:100]}...")
                parts.append(right_text.strip())
                
            page_full = "\n\n".join(parts)
            print(f"\n[FULL PAGE JOINED (First 200 chars)]:\n{page_full[:200]}")
            all_text.append(page_full)

if __name__ == "__main__":
    extract_verbose(r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf")
