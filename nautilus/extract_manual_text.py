"""Extract text from CEREBUS FX v4 PDF manual."""
import sys
import os

pdf_path = r"C:\Users\wifik\Desktop\projects\larger-lab\docs\CEREBUS_FX_v4_Complete_Manual.pdf"
output_path = r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\manual_text.txt"

try:
    import PyPDF2
    reader = PyPDF2.PdfReader(pdf_path)
    print(f"Total pages: {len(reader.pages)}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                f.write(f"\n--- PAGE {i+1} ---\n")
                f.write(text)
                f.write("\n")
    
    print(f"Extracted text written to {output_path}")
    print(f"Total pages: {len(reader.pages)}")
    
    # Print first 3000 chars for preview
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Total chars: {len(content)}")
    print("\n--- FIRST 3000 CHARS ---")
    print(content[:3000])
    
except ImportError:
    print("PyPDF2 not installed. Installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "PyPDF2"], check=True)
    print("PyPDF2 installed. Re-run this script.")
