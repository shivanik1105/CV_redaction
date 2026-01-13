import fitz

pdf_path = "samples/Naukri_MayurPatil[3y_2m].pdf"

with fitz.open(pdf_path) as doc:
    page = doc[0]
    page_width = page.rect.width
    page_height = page.rect.height
    
    print(f"Page width: {page_width}, Page height: {page_height}")
    print(f"\n=== Text Elements with Coordinates ===\n")
    
    blocks = page.get_text("dict")["blocks"]
    
    text_elements = []
    for block in blocks:
        if block.get("type") == 0:  # Text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        bbox = span["bbox"]
                        x0, y0, x1, y1 = bbox
                        text_elements.append({
                            'text': text,
                            'x0': x0,
                            'y0': y0,
                            'x1': x1,
                            'y1': y1
                        })
    
    # Show first 50 elements with coordinates
    for i, elem in enumerate(text_elements[:50]):
        print(f"{i:3d}. x0={elem['x0']:6.2f} | {elem['text'][:60]}")
    
    # Analyze x-positions
    x_positions = sorted(set(elem['x0'] for elem in text_elements))
    print(f"\n=== Unique X positions (first 20) ===")
    for i, x in enumerate(x_positions[:20]):
        print(f"{i:3d}. x={x:.2f}")
    
    # Find gaps
    print(f"\n=== Large gaps in X positions ===")
    for i in range(len(x_positions) - 1):
        gap = x_positions[i + 1] - x_positions[i]
        if gap > 30 and page_width * 0.15 < x_positions[i] < page_width * 0.80:
            print(f"Gap of {gap:.2f}px at x={x_positions[i]:.2f} to x={x_positions[i+1]:.2f}")
            split = (x_positions[i] + x_positions[i + 1]) / 2
            print(f"  → Potential split point: {split:.2f}")
