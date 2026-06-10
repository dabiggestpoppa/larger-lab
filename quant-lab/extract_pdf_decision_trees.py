"""
Extract decision trees and playbooks from Cerebus PDFs.
All PDFs contain text + graphs (no scanned images).
"""
import fitz, json, re, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PDF_DIR = Path(r"C:\Users\wifik\Downloads")
OUTPUT_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\pdf_extractions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Key PDFs with decision trees and playbooks
TARGET_PDFS = [
    "ETH_USD CEREBUS PHASE 4 - Complete Decision Tree & Conditional Mapping.pdf",
    "CEREBUS PHASE 4 DARA.pdf",
    "CEREBUS GJ PHASE 6 PLAYBOOK.pdf",
    "CEREBUS PHASE 6 TRADE PLAYBOOK.pdf",
    "CEREBUS PHASE 3 INTRAWEEK ANATOMY.pdf",
    "CEREBUS PHASE 5 ILM VARIANTS.pdf",
    "CEREBUS_FX_v4_Complete_Manual.pdf",
    "CEREBUS_FX_Cheat_Sheet.pdf",
    "Crypto Fibonacci Trading Model - BTC & ETH Complete Manual.pdf",
    "oil Re-Keying Analysis.pdf",
    "oil re-keying intraday pt1.pdf",
    "Phase 1B Cross-Asset Analysis_ EURUSD vs OILUSD - Complete Research Report.pdf",
    "Phase 1B OILUSD Session Bifurcation Analysis - Complete Research Report.pdf",
]

extracted = {}

for pdf_name in TARGET_PDFS:
    pdf_path = PDF_DIR / pdf_name
    if not pdf_path.exists():
        print(f"NOT FOUND: {pdf_name}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_name}")
    print(f"{'='*60}")
    
    try:
        doc = fitz.open(pdf_path)
        full_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                full_text.append({
                    "page": page_num,
                    "text": text
                })
        
        doc.close()
        
        # Save extracted text
        output_path = OUTPUT_DIR / f"{pdf_name.replace('.pdf', '')}_full.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            for page_data in full_text:
                f.write(f"\n--- PAGE {page_data['page']} ---\n")
                f.write(page_data['text'])
        
        extracted[pdf_name] = {
            "pages": len(full_text),
            "total_chars": sum(len(p["text"]) for p in full_text),
            "output": str(output_path)
        }
        
        print(f"  Pages with text: {len(full_text)}")
        print(f"  Total chars: {sum(len(p['text']) for p in full_text)}")
        
        # Look for decision tree / playbook keywords
        decision_tree_pages = []
        for page_data in full_text:
            text_lower = page_data["text"].lower()
            if any(kw in text_lower for kw in ["decision tree", "playbook", "if ", "then ", "entry rule", 
                                                    "exit rule", "trigger", "condition", "node", "branch",
                                                    "fibonacci", "extension", "rekey", "invalidat"]):
                decision_tree_pages.append(page_data["page"])
        
        if decision_tree_pages:
            print(f"  Decision tree pages: {decision_tree_pages[:10]}")
        
    except Exception as e:
        print(f"  ERROR: {e}")

# Save summary
summary_path = OUTPUT_DIR / "extraction_summary.json"
with open(summary_path, 'w') as f:
    json.dump(extracted, f, indent=2)

print(f"\n\n{'='*60}")
print(f"EXTRACTION COMPLETE")
print(f"{'='*60}")
print(f"PDFs processed: {len(extracted)}")
for name, info in extracted.items():
    print(f"  {name}: {info['pages']} pages, {info['total_chars']} chars")
