import fitz
import re

doc = fitz.open(r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final.pdf')

for i in range(len(doc)):
    text = doc[i].get_text()
    
    # K-Means
    for m in re.finditer(r'[Kk]-[Mm]eans', text):
        start = max(0, m.start()-30)
        end = min(len(text), m.end()+60)
        print(f"P{i+1} K-Means: ...{text[start:end]}...")
    
    # Win rates with %
    for m in re.finditer(r'\b(\d{2}\.\d%)\b', text):
        # Skip page numbers and dates
        ctx = text[max(0,m.start()-20):m.end()+20]
        if 'Page' not in ctx and '2026' not in ctx:
            print(f"P{i+1} WR%: ...{ctx}...")
    
    # Tier thresholds
    if 'T1 AU' in text or 'T1 Trig' in text:
        idx = text.find('T1 AU') if 'T1 AU' in text else text.find('T1 Trig')
        print(f"P{i+1} Tier: ...{text[max(0,idx-20):idx+80]}...")

doc.close()
