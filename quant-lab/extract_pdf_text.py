import fitz, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

pdfs = [
    (r"C:\Users\wifik\Downloads\CEREBUS PHASE 4 DARA.pdf", "phase4_dara"),
    (r"C:\Users\wifik\Downloads\ETH_USD CEREBUS PHASE 4 - Complete Decision Tree & Conditional Mapping.pdf", "eth_phase4_decision_tree"),
    (r"C:\Users\wifik\Downloads\CEREBUS GJ PHASE 6 PLAYBOOK.pdf", "gj_phase6_playbook"),
    (r"C:\Users\wifik\Downloads\CEREBUS PHASE 6 TRADE PLAYBOOK.pdf", "phase6_trade_playbook"),
    (r"C:\Users\wifik\Downloads\CEREBUS GJ DARA.pdf", "gj_dara"),
]

output_dir = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\pdf_extractions"
os.makedirs(output_dir, exist_ok=True)

for pdf_path, name in pdfs:
    if not os.path.exists(pdf_path):
        print(f"NOT FOUND: {pdf_path}")
        continue
    
    print(f"\n=== {name} ===")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    text_pages = 0
    image_pages = 0
    
    all_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            text_pages += 1
            all_text.append(f"--- Page {i} ---\n{text}")
        else:
            image_pages += 1
    
    print(f"  Total pages: {total_pages}")
    print(f"  Text pages: {text_pages}")
    print(f"  Image/empty pages: {image_pages}")
    
    if all_text:
        out_path = os.path.join(output_dir, f"{name}_text.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_text))
        print(f"  Saved text to: {out_path}")
    else:
        print(f"  NO TEXT EXTRACTED — PDF is image-based (needs OCR)")
    
    doc.close()
