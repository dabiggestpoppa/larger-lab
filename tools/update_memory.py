#!/usr/bin/env python3
"""Update MEMORY.md with latest findings."""
MEMORY_FILE = r"C:\Users\wifik\Desktop\projects\larger-lab\MEMORY.md"
with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('Last Updated: 2026-05-19 21:39 EDT', 'Last Updated: 2026-05-19 23:00 EDT')
old = '- **Multi-asset DMR (2026-05-19):** 94.0% avg WR across 4 pairs (EURUSD, USDCHF, CHFJPY, XAUUSD). 1,930 total trades. ALL 92%+ WR. PRODUCTION READY.\n- **Shaw Pipeline Analysis:**'
new = '- **Multi-asset DMR (2026-05-19):** 94.0% avg WR across 4 pairs. 1,930 total trades. ALL 92%+ WR. PRODUCTION READY.\n- **3-Results Issue (2026-05-19):** Sub-agent wrote wrong strategy code from scratch. Result 3 (4.6% WR) is INVALID. Always use validated WORKING code.\n- **Shaw Pipeline Analysis:**'
content = content.replace(old, new)
with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
    f.write(content)
print("MEMORY.md updated.")
