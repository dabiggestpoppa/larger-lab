"""Extract text from CEREBUS FX v4 manual PDF."""
import PyPDF2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

reader = PyPDF2.PdfReader(r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_Complete_Manual.pdf')
print(f'Total pages: {len(reader.pages)}')

# Extract all text
all_text = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        all_text.append(f'=== PAGE {i+1} ===\n{text}\n')

# Write to file
output_path = r'C:\Users\wifik\Desktop\projects\larger-lab\nautilus\manual_text_full.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(all_text))

print(f'Extracted {len(all_text)} pages to {output_path}')

# Print first 10 pages for inspection
for i, page in enumerate(reader.pages[:10]):
    text = page.extract_text()
    if text:
        print(f'=== PAGE {i+1} ===')
        print(text[:1500])
        print()
