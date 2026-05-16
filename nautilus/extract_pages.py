"""Extract specific pages from CEREBUS FX v4 manual PDF."""
import PyPDF2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

reader = PyPDF2.PdfReader(r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_Complete_Manual.pdf')

# Extract pages for remaining strategies
# Part 4: Stall-Harvest (pages 20-29)
# Part 5: P90P Distribution Tracker (pages 30+)
# Part 7: Monday Asian Float (pages 38+)
# Part 8: Daily Asian Float (pages 43+)
# Part 9: Full-Day Range Regime (pages 51+)
# Part 10: Dual-Engine (pages 58+)
# Part 11: Failure Repair (pages 78+)
# Part 12: Two Plays (pages 79+)

pages_to_extract = list(range(19, 80))  # Pages 20-80 (0-indexed: 19-79)

for i in pages_to_extract:
    if i < len(reader.pages):
        text = reader.pages[i].extract_text()
        if text:
            print(f'=== PAGE {i+1} ===')
            print(text)
            print()
