import fitz
import re

doc = fitz.open(r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final.pdf')

for i in range(len(doc)):
    text = doc[i].get_text()
    
    # Win rates with % - look for patterns like "86.4%" or "92.3%"
    for m in re.finditer(r'\b(\d{2,3}\.\d)%', text):
        ctx = text[max(0,m.start()-40):m.end()+40]
        # Skip if it's clearly a page number or date
        if 'Page' in ctx or '2026' in ctx or 'EST' in ctx:
            continue
        print(f"P{i+1}: ...{ctx}...")

doc.close()
