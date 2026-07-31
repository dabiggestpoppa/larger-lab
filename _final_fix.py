"""
Final fix: remove remaining problematic pages from PUBLIC version.
The World Markets section (p147-178) contains too many exact values to redact block-by-block.
Remove those pages entirely from PUBLIC.
"""
import fitz

PUBLIC_IN = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final.pdf'
PUBLIC_OUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_v2.pdf'

doc = fitz.open(PUBLIC_IN)

# Find pages that still have K-Means, exact win rates, or tier thresholds
pages_to_remove = []
for i in range(len(doc)):
    text = doc[i].get_text()
    
    # K-Means references
    if 'k-means' in text.lower() and ('cluster' in text.lower() or 'centroid' in text.lower() or 'threshold' in text.lower()):
        pages_to_remove.append(i)
        continue
    
    # Exact tier threshold tables (the quick reference cards)
    if 'T1 AU' in text and 'T1 Trig' in text and 'T2 AU' in text:
        pages_to_remove.append(i)
        continue
    
    # Exact win rate percentages in results tables
    import re
    wr_count = len(re.findall(r'\b[89]\d\.%\s+(win|WR|hit)', text, re.IGNORECASE))
    if wr_count >= 3:
        pages_to_remove.append(i)
        continue

print(f"Removing {len(pages_to_remove)} more pages from PUBLIC:")
for p in pages_to_remove:
    print(f"  Page {p+1}")

for p in reversed(pages_to_remove):
    doc.delete_page(p)

doc.save(PUBLIC_OUT)
print(f"\nPUBLIC: now {len(doc)} pages -> {PUBLIC_OUT}")
doc.close()

# Also fix FULL - remove remaining code pages
FULL_IN = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_Final.pdf'
FULL_OUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_v2.pdf'

doc = fitz.open(FULL_IN)
pages_to_remove = []
for i in range(len(doc)):
    text = doc[i].get_text()
    if 'import pandas' in text and 'def ' in text:
        pages_to_remove.append(i)

print(f"\nRemoving {len(pages_to_remove)} code pages from FULL:")
for p in pages_to_remove:
    print(f"  Page {p+1}")

for p in reversed(pages_to_remove):
    doc.delete_page(p)

doc.save(FULL_OUT)
print(f"FULL: now {len(doc)} pages")
doc.close()

print("\nDone!")
