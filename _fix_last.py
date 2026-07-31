"""
Fix the last 3 remaining leaks in PUBLIC:
1. K-Means on pages 147, 151
2. P90 Threshold on page 19
3. Exact Win Rates on pages 13, 79, 126, 130, 135
"""
import fitz
import re

INPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final_Redacted.pdf'
OUTPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_FINAL.pdf'

doc = fitz.open(INPUT)

# Fix specific pages
for page_idx in [12, 18, 78, 125, 129, 134, 146, 150]:  # 0-indexed
    if page_idx >= len(doc):
        continue
    page = doc[page_idx]
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if block.get("type") != 0:
            continue
        text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text += span.get("text", "")
            text += "\n"
        text = text.strip()
        if not text:
            continue
        
        should_redact = False
        
        # K-Means
        if re.search(r'[Kk]-[Mm]eans', text, re.IGNORECASE):
            should_redact = True
        
        # P90 Threshold formulas
        if re.search(r'P90\s+Body\s+\(\d|P90\s+candle\s+close\s*>=\s*\d', text):
            should_redact = True
        
        # Exact win rates (XX.X% followed by win/WR/hit)
        if re.search(r'\b[89]\d\.\d+%\s+(win|WR|hit|accuracy)', text, re.IGNORECASE):
            should_redact = True
        
        if should_redact:
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
    
    page.apply_redactions()

doc.save(OUTPUT)
print(f"Done! {len(doc)} pages -> {OUTPUT}")
doc.close()

# Verify
doc = fitz.open(OUTPUT)
print("\nVerification:")
for i in range(len(doc)):
    text = doc[i].get_text()
    if 'k-means' in text.lower() and ('cluster' in text.lower() or 'threshold' in text.lower()):
        print(f"  ⚠️ K-Means on page {i+1}")
    if re.search(r'P90\s+Body\s+\(\d', text):
        print(f"  ⚠️ P90 Threshold on page {i+1}")
    if re.search(r'\b[89]\d\.\d+%\s+(win|WR|hit)', text, re.IGNORECASE):
        print(f"  ⚠️ Win Rate on page {i+1}")
doc.close()
print("Done.")
