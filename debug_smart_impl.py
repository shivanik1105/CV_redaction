import pdfplumber

def debug_extract(pdf_path):
    print(f"Processing: {pdf_path}")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        all_text = []
        for i, page in enumerate(pdf.pages):
            print(f"\n--- Page {i+1} ---")
            page_width = page.width
            page_height = page.height
            print(f"Dimensions: {page_width}x{page_height}")
            
            # Words for analysis
            words = page.extract_words(x_tolerance=2, y_tolerance=2)
            if not words:
                print("No words found!")
                continue
                
            x_coords = sorted(set([w['x0'] for w in words]))
            print(f"Unique X coords count: {len(x_coords)}")
            
            # Gap detection logic
            gaps = []
            for j in range(len(x_coords) - 1):
                gap_size = x_coords[j+1] - x_coords[j]
                if gap_size > 10:
                    gap_center = (x_coords[j] + x_coords[j+1]) / 2
                    if 0.2 * page_width < gap_center < 0.8 * page_width:
                        gaps.append((gap_center, gap_size))
            
            if gaps:
                best_gap = max(gaps, key=lambda x: x[1])
                split_point = best_gap[0]
                print(f"Found split point: {split_point} (gap size: {best_gap[1]})")
                
                # Check for words crossing the split point (headers)
                crossing_words = []
                for w in words:
                    if w['x0'] < split_point < w['x1']:
                        crossing_words.append(w)
                
                header_bottom = 0
                if crossing_words:
                    print(f"Found {len(crossing_words)} words crossing the split line:")
                    for w in crossing_words:
                        print(f"  '{w['text']}' at y={w['top']:.2f}-{w['bottom']:.2f}")
                        header_bottom = max(header_bottom, w['bottom'])
                    
                    print(f"Header ends at y={header_bottom:.2f}")
                else:
                    print("No words cross the split line.")
                
                # Add buffer
                y_cutoff = header_bottom + 5
                
                # Extract Header
                header_bbox = (0, 0, page_width, y_cutoff)
                header_crop = page.crop(header_bbox)
                header_text = header_crop.extract_text(x_tolerance=2, y_tolerance=2)
                print(f"\nHEADER (0-{y_cutoff:.2f}):")
                print("-" * 20)
                print(header_text[:200] if header_text else "[EMPTY]")
                print("-" * 20)
                
                # Extract Left Column
                left_bbox = (0, y_cutoff, split_point, page_height)
                left_crop = page.crop(left_bbox)
                left_text = left_crop.extract_text(x_tolerance=2, y_tolerance=2)
                print(f"\nLEFT COLUMN ({y_cutoff:.2f}-end):")
                print("-" * 20)
                print(left_text[:200] if left_text else "[EMPTY]")
                print("-" * 20)
                
                # Extract Right Column
                right_bbox = (split_point, y_cutoff, page_width, page_height)
                right_crop = page.crop(right_bbox)
                right_text = right_crop.extract_text(x_tolerance=2, y_tolerance=2)
                print(f"\nRIGHT COLUMN ({y_cutoff:.2f}-end):")
                print("-" * 20)
                print(right_text[:200] if right_text else "[EMPTY]")
                print("-" * 20)
            else:
                split_point = page_width / 2
                print(f"No gap found, defaulting to: {split_point}")

if __name__ == "__main__":
    debug_extract(r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf")
