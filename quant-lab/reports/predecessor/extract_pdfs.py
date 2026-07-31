"""Extract text from CEREBUS predecessor PDFs using PyMuPDF."""
import fitz  # PyMuPDF
import os
import sys

DOWNLOADS = r"C:\Users\wifik\Downloads"
OUTPUT = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\predecessor"
os.makedirs(OUTPUT, exist_ok=True)

FILES = [
    ("CEREBUS_FX_v4_Complete_Manual (1).pdf", "cerebus_manual_v4.txt", 30),
    ("CEREBUS v18.2.5  3 market final form master scroll (1).pdf", "cerebus_master_scroll.txt", 30),
    ("cerebus dual incomplete  bydatry (1).pdf", "cerebus_dual_incomplete.txt", 30),
    ("CEREBUS GJ PHASE 6 PLAYBOOK.pdf", "cerebus_gj_phase6.txt", 30),
    ("CEREBUS GJ PHASE 1-2.pdf", "cerebus_gj_phase1_2.txt", 30),
    ("CEREBUS GJ DARA.pdf", "cerebus_gj_dara.txt", 30),
    ("Crypto Fibonacci Trading Model - BTC & ETH Complete Manual.pdf", "crypto_fibonacci.txt", 30),
    ("CROSS ASSET MASTER FILE 3 FINAL FORM.pdf", "cross_asset_master.txt", 30),
    ("cerebus cross asset master file FINAL FORM 1.pdf", "cross_asset_master_1.txt", 30),
    ("CEREBUS CROSS ASSET MASTER FILE 3.2.pdf", "cross_asset_master_32.txt", 30),
    ("Phase 1B OILUSD Session Bifurcation Analysis - Complete Research Report.pdf", "oilusd_bifurcation.txt", 30),
    ("Phase 1B Cross-Asset Analysis_ EURUSD vs OILUSD - Complete Research Report.pdf", "cross_asset_analysis.txt", 30),
]

def extract_pdf(pdf_name, txt_name, max_pages=30):
    pdf_path = os.path.join(DOWNLOADS, pdf_name)
    txt_path = os.path.join(OUTPUT, txt_name)
    
    if not os.path.exists(pdf_path):
        print(f"❌ {pdf_name} not found")
        return
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_to_read = min(max_pages, total_pages)
        
        text = ""
        for i in range(pages_to_read):
            page = doc[i]
            text += f"\n\n--- PAGE {i+1} ---\n\n"
            text += page.get_text()
        
        doc.close()
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"✅ {pdf_name} → {txt_name} ({pages_to_read}/{total_pages} pages, {len(text)} chars)")
    except Exception as e:
        print(f"❌ {pdf_name}: {e}")

def main():
    print("=" * 60)
    print("CEREBUS Predecessor PDF Extraction")
    print("=" * 60)
    print()
    
    for pdf_name, txt_name, max_pages in FILES:
        extract_pdf(pdf_name, txt_name, max_pages)
    
    print()
    print("=" * 60)
    print("Extraction complete!")
    print(f"Output directory: {OUTPUT}")
    
    # List output files
    print()
    print("Output files:")
    for f in os.listdir(OUTPUT):
        if f.endswith('.txt'):
            size = os.path.getsize(os.path.join(OUTPUT, f))
            print(f"  {f} ({size/1024:.1f} KB)")

if __name__ == "__main__":
    main()
