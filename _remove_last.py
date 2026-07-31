"""
Remove remaining pages with K-Means references and exact win rates.
These are in the World Markets section (pages 147-178) which contain
asset-specific parameter tables.
"""
import fitz
import re

INPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_FINAL.pdf'
OUTPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_FINAL_Clean.pdf'

doc = fitz.open(INPUT)

# Remove pages from the World Markets section that still have leaks
# These are pages 147-178 (0-indexed: 146-177)
# But let's be precise - only remove pages that still have issues
pages_to_remove = []
for i in range(len(doc)):
    text = doc[i].get_text()
    
    # K-Means references
    if re.search(r'[Kk]-[Mm]eans', text, re.IGNORECASE):
        pages_to_remove.append(i)
        continue
    
    # Exact win rates
    if re.search(r'\b[89]\d\.\d+%\s+(win|WR|hit|accuracy)', text, re.IGNORECASE):
        pages_to_remove.append(i)
        continue
    
    # P90 threshold formulas
    if re.search(r'P90\s+Body\s+\(\d|P90\s+candle\s+close\s*>=\s*\d', text):
        pages_to_remove.append(i)
        continue

print(f"Removing {len(pages_to_remove)} pages: {[p+1 for p in pages_to_remove]}")
for p in reversed(pages_to_remove):
    doc.delete_page(p)

doc.save(OUTPUT)
print(f"PUBLIC: now {len(doc)} pages")
doc.close()

# Final verify
doc = fitz.open(OUTPUT)
issues = 0
for i in range(len(doc)):
    text = doc[i].get_text()
    if re.search(r'[Kk]-[Mm]eans', text, re.IGNORECASE):
        print(f"  ⚠️ K-Means on page {i+1}")
        issues += 1
    if re.search(r'\b[89]\d\.\d+%\s+(win|WR|hit)', text, re.IGNORECASE):
        print(f"  ⚠️ Win Rate on page {i+1}")
        issues += 1
    if re.search(r'P90\s+Body\s+\(\d', text):
        print(f"  ⚠️ P90 on page {i+1}")
        issues += 1
if issues == 0:
    print("  🎉 ALL CLEAN!")
doc.close()
