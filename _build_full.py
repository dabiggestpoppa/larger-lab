import fitz
import re

INPUT = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_Redacted.pdf'

SKIP = set(range(209, 215))  # Code appendix only

CODE_REGEX = re.compile(
    r'import\s+pandas|import\s+numpy|from\s+sklearn|'
    r'def\s+discover|def\s+validate|def\s+run_|'
    r'KMeans\s*\(|pd\.read_csv|pd\.DataFrame|'
    r'pip\s+install|CSV\s+format:|OHLCV\s*\|\s*UTC|'
    r'#\s*USAGE:|#\s*RUN:|CODE\s+[0-9]\s+—',
    re.IGNORECASE
)

doc = fitz.open(INPUT)
out = fitz.open()
skipped = 0
redacted = 0

for i in range(len(doc)):
    if i in SKIP:
        skipped += 1
        continue
    out.insert_pdf(doc, from_page=i, to_page=i)
    page = out[out.page_count - 1]
    
    blocks = page.get_text('dict')['blocks']
    page_redacted = False
    for block in blocks:
        if block.get('type') != 0:
            continue
        text = ''
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text += span.get('text', '')
        if CODE_REGEX.search(text):
            page.add_redact_annot(fitz.Rect(block['bbox']), fill=(1, 1, 1), text='')
            page_redacted = True
    if page_redacted:
        page.apply_redactions()
        redacted += 1

total = out.page_count
out.save(OUTPUT, garbage=4, deflate=True)
out.close()
doc.close()

print(f'FULL: {total} pages ({skipped} removed, {redacted} redacted)')
print(f'  -> {OUTPUT}')
