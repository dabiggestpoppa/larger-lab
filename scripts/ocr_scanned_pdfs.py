"""
OCR scanned PDFs using pdf2image + pytesseract (local, no API needed).
"""
import os, sys, time
from pathlib import Path

downloads = Path(r'C:\Users\wifik\Downloads')
output_dir = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\predecessor')
output_dir.mkdir(parents=True, exist_ok=True)

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
poppler_bin = r'C:\Users\wifik\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin'

print(f"Tesseract: {tesseract_path}")
print(f"Poppler bin: {poppler_bin}")
print(f"Tesseract exists: {os.path.exists(tesseract_path)}")
print(f"Poppler exists: {os.path.exists(poppler_bin)}")

import pytesseract
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = tesseract_path

scanned_pdfs = [
    ('CEREBUS GJ PHASE 6 PLAYBOOK.pdf', 'CEREBUS_GJ_PHASE_6_PLAYBOOK'),
    ('CEREBUS GJ PHASE 1-2.pdf', 'CEREBUS_GJ_PHASE_1-2'),
    ('CEREBUS GJ DARA.pdf', 'CEREBUS_GJ_DARA'),
    ('CROSS ASSET MASTER FILE 3 FINAL FORM.pdf', 'CROSS_ASSET_MASTER_FILE_3_FINAL_FORM'),
    ('cerebus cross asset master file FINAL FORM 1.pdf', 'cerebus_cross_asset_master_file_FINAL_FORM_1'),
    ('CEREBUS CROSS ASSET MASTER FILE 3.2.pdf', 'CEREBUS_CROSS_ASSET_MASTER_FILE_3.2'),
]

for pdf_name, base_name in scanned_pdfs:
    pdf_path = downloads / pdf_name
    if not pdf_path.exists():
        print(f"MISSING: {pdf_name}")
        continue
    
    txt_path = output_dir / (base_name + '.txt')
    if txt_path.exists() and txt_path.stat().st_size > 100:
        print(f"SKIP (already done): {base_name}")
        continue
    
    print(f"\nProcessing: {pdf_name}...")
    start = time.time()
    
    try:
        print(f"  Converting PDF to images...")
        images = convert_from_path(str(pdf_path), dpi=300, poppler_path=poppler_bin)
        print(f"  {len(images)} pages converted in {time.time()-start:.1f}s")
        
        text_parts = []
        for i, img in enumerate(images):
            print(f"  OCR page {i+1}/{len(images)}...", end=' ', flush=True)
            page_start = time.time()
            text = pytesseract.image_to_string(img, lang='eng')
            text_parts.append(f'\n--- Page {i+1} ---\n')
            text_parts.append(text)
            print(f"({time.time()-page_start:.1f}s, {len(text)} chars)")
        
        full_text = '\n'.join(text_parts)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        total_time = time.time() - start
        print(f"  SAVED: {base_name}.txt ({len(full_text)} chars, {total_time:.1f}s total)")
        
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\nDONE")
