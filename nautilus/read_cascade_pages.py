"""Read cascade pages from manual."""
import PyPDF2, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
reader = PyPDF2.PdfReader(r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_Complete_Manual.pdf')
for i in range(9, 30):
    text = reader.pages[i].extract_text()
    if text:
        print(f'=== PAGE {i+1} ===')
        print(text)
        print()
