"""Extract text from the CEREBUS FX v4 PDF manual."""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab")

try:
    import PyPDF2
    reader = PyPDF2.PdfReader(r"C:\Users\wifik\Desktop\projects\larger-lab\docs\CEREBUS_FX_v4_Complete_Manual.pdf")
    print(f"Total pages: {len(reader.pages)}")
    
    # Extract all text
    all_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            all_text.append(f"--- PAGE {i+1} ---\n{text}")
    
    full_text = "\n\n".join(all_text)
    
    # Save to file
    output_path = r"C:\Users\wifik\Desktop\projects\larger-lab\docs\CEREBUS_manual_text.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    print(f"Extracted text saved to {output_path}")
    print(f"Total chars: {len(full_text)}")
    print(f"\n--- FIRST 3000 CHARS ---")
    print(full_text[:3000])
    print(f"\n--- LAST 1000 CHARS ---")
    print(full_text[-1000:])

except ImportError:
    print("PyPDF2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2", "-q"])
    print("PyPDF2 installed. Re-run this script.")
