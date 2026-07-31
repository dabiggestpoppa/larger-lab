"""
Extract text from all Cerebus PDFs in downloads folder.
Outputs structured text files for ML model training.
"""
import fitz  # PyMuPDF
import os, json, re, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
OUTPUT_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\pdf_extractions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Find all Cerebus-related PDFs
pdfs = sorted([f for f in DOWNLOADS.glob("*.pdf") if "cerebus" in f.name.lower() or "CEREBUS" in f.name])
print(f"Found {len(pdfs)} Cerebus PDFs")

# Also get other trading-related PDFs
other_pdfs = sorted([f for f in DOWNLOADS.glob("*.pdf") if any(k in f.name.lower() for k in ["fib", "trading", "quant", "oil", "crypto", "eth", "btc"])])
print(f"Found {len(other_pdfs)} other trading PDFs")

all_pdfs = pdfs + [p for p in other_pdfs if p not in pdfs]
print(f"Total PDFs to extract: {len(all_pdfs)}")

extracted = {}
for pdf_path in all_pdfs:
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()

        # Save extracted text
        out_file = OUTPUT_DIR / f"{pdf_path.stem}.txt"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(text)

        # Extract key stats using regex
        stats = {}
        # Look for percentage patterns
        pct_matches = re.findall(r'(\d+\.?\d*)%', text)
        if pct_matches:
            stats['percentages'] = [float(p) for p in pct_matches[:50]]

        # Look for Fibonacci levels
        fib_matches = re.findall(r'(\d+\.?\d*)%', text)
        fib_levels = re.findall(r'(23\.6|38\.2|50|61\.8|72|78\.6|88|100|127|132|161\.8|168|261\.8)', text)
        if fib_levels:
            stats['fib_levels_found'] = list(set(fib_levels))

        # Look for sequence patterns
        seq_patterns = re.findall(r'((?:\d+\.?\d*%?\s*[-→]\s*){2,}\d+\.?\d*%?)', text)
        if seq_patterns:
            stats['sequences'] = seq_patterns[:20]

        extracted[pdf_path.name] = {
            'file': str(pdf_path),
            'size_kb': round(pdf_path.stat().st_size / 1024, 1),
            'pages': len(doc),
            'chars': len(text),
            'stats': stats
        }

        print(f"  Extracted: {pdf_path.name} ({len(text)} chars, {len(doc)} pages)")
    except Exception as e:
        print(f"  ERROR: {pdf_path.name}: {e}")

# Save manifest
manifest_path = OUTPUT_DIR / "_manifest.json"
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(extracted, f, indent=2, default=str, ensure_ascii=False)

print(f"\nExtracted {len(extracted)} PDFs to {OUTPUT_DIR}")
print(f"Manifest saved to: {manifest_path}")
