import pdfplumber

# Open the PDF
pdf_path = r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    # Get all words with their bounding boxes
    words = page.extract_words(x_tolerance=2, y_tolerance=2)
    
    # Analyze x-coordinates to find the gap between columns
    x_coords = sorted([w['x0'] for w in words])
    
    print(f"Total words: {len(words)}")
    print(f"Page width: {page.width}")
    print(f"\nX-coordinate distribution (first 50 words):")
    
    for i, x in enumerate(x_coords[:50]):
        print(f"{i:3d}. x={x:6.2f}")
    
    # Find the gap - look for the largest gap in x-coordinates
    gaps = []
    for i in range(len(x_coords) - 1):
        gap = x_coords[i+1] - x_coords[i]
        if gap > 10:  # Significant gap
            gaps.append((x_coords[i], x_coords[i+1], gap))
    
    print(f"\n\nSignificant gaps (> 10 points):")
    for left, right, gap in sorted(gaps, key=lambda x: x[2], reverse=True)[:10]:
        print(f"Gap from {left:.2f} to {right:.2f} = {gap:.2f} points")
    
    # Find the best column split point
    if gaps:
        # Use the largest gap in the middle region of the page
        mid_region_gaps = [(l, r, g) for l, r, g in gaps if 200 < l < 400]
        if mid_region_gaps:
            best_gap = max(mid_region_gaps, key=lambda x: x[2])
            split_point = (best_gap[0] + best_gap[1]) / 2
            print(f"\n\nBest split point: {split_point:.2f}")
        else:
            split_point = page.width / 2
            print(f"\n\nUsing default split point: {split_point:.2f}")
    else:
        split_point = page.width / 2
        print(f"\n\nNo gaps found, using default split point: {split_point:.2f}")
