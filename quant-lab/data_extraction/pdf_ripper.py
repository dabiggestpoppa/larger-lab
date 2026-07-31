"""
PDF RIPPER — Cerebus PDF Stats Extraction
==========================================
Rips stats from 50+ PDFs. Handles text, tables, and scanned pages.
Hunts for: Hit Rates, Sample Sizes, Fib Levels, Timeframes.
"""

import os
import re
import json
from pathlib import Path

PDF_DIRS = [
    r"C:\Users\wifik\Downloads",
    r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\predecessor",
    r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports",
]
OUTPUT_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\holy_grail_extracted\pdf_stats"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regex patterns for CEREBUS physics
PAT_HIT_RATE = re.compile(r'(\d{2,3}\.?\d*)\s*%')
PAT_SAMPLE = re.compile(r'(\d{1,5})\s*(?:trades|days|weeks|candles|sessions|loops|patterns|events)', re.IGNORECASE)
PAT_FIB = re.compile(r'(-?\d{2,3}(?:\.\d+)?)\s*%')
PAT_FIB_LEVEL = re.compile(r'(25|50|61\.8|72|78\.6|88|100|132|168|23\.6)\s*%')
PAT_SUCCESS = re.compile(r'(?:success|hit|completion)\s*(?:rate)?[:\s]*(\d{2,3}\.?\d*)%', re.IGNORECASE)
PAT_TIME = re.compile(r'(\d{1,3})\s*(?:hrs?|hours?|days?)', re.IGNORECASE)
PAT_ASSET = re.compile(r'(EURUSD|USDCHF|GBPUSD|USDJPY|EURGBP|EURJPY|EURAUD|EURCHF|EURGBP|GBPJPY|GBPAUD|GBPCAD|GBPCHF|GBPNZD|USDCAD|AUDUSD|NZDUSD|USDCHF|XAUUSD|XAGUSD|BTCUSD|ETHUSD|OILUSD|DE30|FR40|US500|NAS100|HK50)', re.IGNORECASE)

EXTRACTED_DB = []


def extract_text_pymupdf(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text()
            pages.append({"page": i, "text": text, "is_scanned": len(text.strip()) < 50})
        doc.close()
        return pages
    except ImportError:
        print(f"  WARNING: PyMuPDF not installed. Skipping {pdf_path}")
        return []
    except Exception as e:
        print(f"  ERROR reading {pdf_path}: {e}")
        return []


def extract_tables_pdfplumber(pdf_path):
    """Extract tables from PDF using pdfplumber."""
    try:
        import pdfplumber
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table in page_tables:
                    tables.append({"page": i, "table": table})
        return tables
    except ImportError:
        return []
    except Exception as e:
        print(f"  ERROR extracting tables from {pdf_path}: {e}")
        return []


def hunt_stats(text, source, page_num, stat_type="text"):
    """Hunt for CEREBUS stats in text."""
    results = []

    # Find all hit rates
    hit_rates = PAT_HIT_RATE.findall(text)
    samples = PAT_SAMPLE.findall(text)
    fib_levels = PAT_FIB_LEVEL.findall(text)
    success_rates = PAT_SUCCESS.findall(text)
    times = PAT_TIME.findall(text)
    assets = PAT_ASSET.findall(text)

    if hit_rates or samples or fib_levels:
        results.append({
            'source': source,
            'page': page_num,
            'type': stat_type,
            'hit_rates': hit_rates[:20],
            'sample_sizes': samples[:10],
            'fib_levels': list(set(fib_levels))[:20],
            'success_rates': success_rates[:10],
            'times': times[:10],
            'assets': list(set(assets))[:5],
            'raw_snippet': text[:500] if len(text) > 500 else text
        })

    return results


def process_pdf(pdf_path):
    """Process a single PDF file."""
    filename = os.path.basename(pdf_path)
    print(f"  Processing: {filename}")

    # Extract text
    pages = extract_text_pymupdf(pdf_path)
    if not pages:
        return

    # Extract tables
    tables = extract_tables_pdfplumber(pdf_path)

    # Hunt stats in text
    for page_data in pages:
        if page_data['is_scanned']:
            print(f"    Page {page_data['page']}: SCANNED (needs OCR)")
            continue
        stats = hunt_stats(page_data['text'], filename, page_data['page'], "text")
        EXTRACTED_DB.extend(stats)

    # Hunt stats in tables
    for table_data in tables:
        for row in table_data['table']:
            row_text = " ".join([str(cell) for cell in row if cell])
            stats = hunt_stats(row_text, filename, table_data['page'], "table")
            EXTRACTED_DB.extend(stats)

    print(f"    Found {len([s for s in EXTRACTED_DB if s['source'] == filename])} stat clusters")


def find_pdfs():
    """Find all PDFs in the search directories."""
    pdfs = []
    for d in PDF_DIRS:
        if os.path.exists(d):
            for f in os.listdir(d):
                if f.lower().endswith('.pdf'):
                    pdfs.append(os.path.join(d, f))
    return pdfs


def main():
    print("=" * 60)
    print("PDF RIPPER — Cerebus PDF Stats Extraction")
    print("=" * 60)

    pdfs = find_pdfs()
    print(f"Found {len(pdfs)} PDFs\n")

    for i, pdf_path in enumerate(pdfs):
        print(f"[{i+1}/{len(pdfs)}]", end=" ")
        process_pdf(pdf_path)

    # Save results
    output_path = os.path.join(OUTPUT_DIR, "pdf_master_stats.json")
    with open(output_path, 'w') as f:
        json.dump(EXTRACTED_DB, f, indent=2)

    print(f"\n{'='*60}")
    print(f"PDF EXTRACTION COMPLETE")
    print(f"  PDFs processed: {len(pdfs)}")
    print(f"  Stat clusters found: {len(EXTRACTED_DB)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
