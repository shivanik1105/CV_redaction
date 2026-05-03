"""
Debug script to see raw text extraction from PDF
"""
import sys
import fitz  # PyMuPDF

if len(sys.argv) < 2:
    print("Usage: python debug_extraction.py <pdf_path>")
    sys.exit(1)

pdf_path = sys.argv[1]

print("=" * 80)
print("RAW PDF TEXT EXTRACTION DEBUG")
print("=" * 80)
print(f"File: {pdf_path}\n")

with fitz.open(pdf_path) as doc:
    for page_num, page in enumerate(doc, 1):
        print(f"\n{'='*80}")
        print(f"PAGE {page_num}")
        print(f"{'='*80}\n")
        
        # Get page dimensions
        page_width = page.rect.width
        page_height = page.rect.height
        print(f"Page size: {page_width} x {page_height}\n")
        
        # Get all text blocks with coordinates
        blocks = page.get_text("dict")["blocks"]
        
        print(f"Total blocks found: {len(blocks)}\n")
        
        text_blocks = []
        for i, block in enumerate(blocks):
            if "lines" in block:
                bbox = block["bbox"]
                text = "\n".join([
                    " ".join([span["text"] for span in line["spans"]])
                    for line in block["lines"]
                ]).strip()
                
                if text:
                    x_center = (bbox[0] + bbox[2]) / 2
                    column = "LEFT" if x_center < page_width / 2 else "RIGHT"
                    
                    print(f"Block {i+1} [{column}]:")
                    print(f"  Position: X={bbox[0]:.1f}-{bbox[2]:.1f}, Y={bbox[1]:.1f}-{bbox[3]:.1f}")
                    # Handle unicode characters safely
                    safe_text = text[:100].encode('utf-8', errors='replace').decode('utf-8')
                    print(f"  Text: {safe_text}{'...' if len(text) > 100 else ''}")
                    print()
                    
                    text_blocks.append({
                        'text': text,
                        'x0': bbox[0],
                        'y0': bbox[1],
                        'x1': bbox[2],
                        'y1': bbox[3],
                        'column': column
                    })
        
        # Analyze column split
        x_centers = [(b['x0'] + b['x1']) / 2 for b in text_blocks]
        sorted_x = sorted(set(x_centers))
        
        print(f"\n{'='*80}")
        print("COLUMN ANALYSIS")
        print(f"{'='*80}\n")
        
        # Find gaps
        max_gap = 0
        gap_position = None
        for i in range(len(sorted_x) - 1):
            gap = sorted_x[i + 1] - sorted_x[i]
            if gap > max_gap:
                max_gap = gap
                gap_position = (sorted_x[i] + sorted_x[i + 1]) / 2
        
        print(f"Largest gap: {max_gap:.1f} pixels at X={gap_position:.1f}")
        print(f"Page midpoint: {page_width/2:.1f}")
        
        if max_gap > 40:
            print(f"\n✓ Two-column layout detected (gap > 40px)")
            print(f"  Column boundary: X={gap_position:.1f}")
            
            left_blocks = [b for b in text_blocks if (b['x0'] + b['x1']) / 2 < gap_position]
            right_blocks = [b for b in text_blocks if (b['x0'] + b['x1']) / 2 >= gap_position]
            
            print(f"  Left column: {len(left_blocks)} blocks")
            print(f"  Right column: {len(right_blocks)} blocks")
            
            print(f"\n{'='*80}")
            print("LEFT COLUMN CONTENT")
            print(f"{'='*80}\n")
            for b in sorted(left_blocks, key=lambda x: x['y0']):
                safe_text = b['text'][:80].encode('utf-8', errors='replace').decode('utf-8')
                print(f"Y={b['y0']:.1f}: {safe_text}{'...' if len(b['text']) > 80 else ''}")
            
            print(f"\n{'='*80}")
            print("RIGHT COLUMN CONTENT")
            print(f"{'='*80}\n")
            for b in sorted(right_blocks, key=lambda x: x['y0']):
                safe_text = b['text'][:80].encode('utf-8', errors='replace').decode('utf-8')
                print(f"Y={b['y0']:.1f}: {safe_text}{'...' if len(b['text']) > 80 else ''}")
        else:
            print(f"\n✗ Single column layout (gap <= 40px)")

print(f"\n{'='*80}")
print("DEBUG COMPLETE")
print(f"{'='*80}\n")
