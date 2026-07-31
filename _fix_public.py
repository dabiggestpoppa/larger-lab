"""
Fix remaining PUBLIC issues:
1. Page 2 (Quick Reference Card) - has exact tier thresholds
2. Pages 3, 12-14, 18 - have exact win rates in tables
"""
import fitz
import re

IN = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_v2.pdf'
OUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final_Clean.pdf'

doc = fitz.open(IN)

# Page 2 (index 1) - Quick Reference Card with exact tier thresholds
# This entire page should be removed - it's just a parameter table
# Actually, let's keep it but redact the specific table cells

# For the quick reference card, we need to redact the table rows with exact values
# The table has columns: Pair, Pip, T1 AU, T1 Trig, T2 AU, T2 Trig, T3 AU, T3 Trig, SL Method
page = doc[1]  # Page 2 (0-indexed)
blocks = page.get_text("dict")["blocks"]

for block in blocks:
    if block.get("type") != 0:
        continue
    text = ""
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text += span.get("text", "")
    
    # Redact lines that contain exact pip values in the tier table
    # Pattern: currency pair name followed by numbers
    if re.search(r'(EUR/USD|GBP/USD|USD/CHF|USD/JPY|AUD/USD|USD|CHF|JPY|GBP/AUD|GBP/NZD|GBP/CHF|US500|NAS100|DE30|FR40|HK50|XAU/USD|XAG/USD|ETH/USD|BTC/USD)\s+0\.\d+', text):
        rect = fitz.Rect(block["bbox"])
        page.add_redact_annot(rect, fill=(1, 1, 1))

# Also redact the "Gear Shift" line on page 2
for block in page.get_text("dict")["blocks"]:
    if block.get("type") != 0:
        continue
    text = ""
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text += span.get("text", "")
    if "Gear Shift" in text and "T1+impulse" in text:
        rect = fitz.Rect(block["bbox"])
        page.add_redact_annot(rect, fill=(1, 1, 1))

page.apply_redactions()

# Now handle the exact win rate pages
# These are in the cascade analysis and Monte Carlo sections
# We need to redact the specific percentage values

wr_pages = [2, 11, 12, 13, 17]  # 0-indexed: pages 3, 12, 13, 14, 18

for page_idx in wr_pages:
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
        
        # Redact blocks with exact win rate percentages
        # Look for patterns like "86.4%" or "92.3%" that are clearly results
        if re.search(r'\b[89]\d\.%\s+(WR|win\s+rate|hit\s+rate|accuracy)', text, re.IGNORECASE):
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
        
        # Also redact blocks with exact R-multiples
        if re.search(r'[+-][0-9]+\.[0-9]+R', text):
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
        
        # Redact blocks with exact Monte Carlo ruin probabilities
        if re.search(r'ruin\s+(probability|rate)|Ruin\s+at', text, re.IGNORECASE):
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
    
    page.apply_redactions()

doc.save(OUT)
print(f"PUBLIC final: {len(doc)} pages -> {OUT}")
doc.close()

# Verify
print("\nVerifying...")
doc = fitz.open(OUT)
for i in range(len(doc)):
    text = doc[i].get_text()
    if 'T1 AU' in text and 'T1 Trig' in text:
        print(f"  ⚠️ Tier thresholds still on page {i+1}")
    wr = re.findall(r'\b[89]\d\.%\s+(WR|win)', text, re.IGNORECASE)
    if wr:
        print(f"  ⚠️ Win rates on page {i+1}: {wr[:3]}")
doc.close()
print("Verification complete.")
