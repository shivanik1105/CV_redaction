import fitz

# Open the PDF
pdf_path = r"samples\Naukri_AbhinavVinodSolapurkar[5y_8m].pdf"
doc = fitz.open(pdf_path)

page = doc[0]
words = page.get_text("words")

print(f"Total words: {len(words)}")
print(f"Page width: {page.rect.width}")
print(f"Mid point: {page.rect.width / 2}")

# Analyze x-coordinates
x_coords = [w[0] for w in words]
mid_point = page.rect.width / 2

left_words = sum(1 for x in x_coords if x < mid_point)
right_words = sum(1 for x in x_coords if x >= mid_point)

print(f"\nLeft column words: {left_words}")
print(f"Right column words: {right_words}")
print(f"Is 2-column: {left_words > 10 and right_words > 10}")

# Show first 20 words with positions
print("\nFirst 20 words:")
for i, word in enumerate(words[:20]):
    x0, y0, x1, y1, word_text, block_no, line_no, word_no = word
    col = "LEFT" if x0 < mid_point else "RIGHT"
    print(f"{i:2d}. [{col:5s}] x={x0:6.1f} y={y0:6.1f} '{word_text}'")

# Try the extraction logic
left_col = [w for w in words if w[0] < mid_point]
right_col = [w for w in words if w[0] >= mid_point]

left_col.sort(key=lambda w: (round(w[1] / 5) * 5, w[0]))
right_col.sort(key=lambda w: (round(w[1] / 5) * 5, w[0]))

sorted_words = left_col + right_col

print("\n=== LEFT COLUMN (first 30 words) ===")
for i, word in enumerate(left_col[:30]):
    print(f"{word[4]}", end=" ")
    if (i + 1) % 10 == 0:
        print()

print("\n\n=== RIGHT COLUMN (first 30 words) ===")
for i, word in enumerate(right_col[:30]):
    print(f"{word[4]}", end=" ")
    if (i + 1) % 10 == 0:
        print()

doc.close()
