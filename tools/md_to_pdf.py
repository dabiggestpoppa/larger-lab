import markdown
from weasyprint import HTML
import os

md_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_STRATEGIES_COMPLETE.md'
pdf_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_STRATEGIES_COMPLETE.html'

with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc'])

full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>CEREBUS FX — Strategies Complete Reference (Vol II)</title>
<style>
@page {{ size: A4; margin: 15mm; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #1a1a1a; }}
h1 {{ font-size: 18pt; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; padding-bottom: 5px; page-break-before: always; }}
h1:first-of-type {{ page-break-before: avoid; }}
h2 {{ font-size: 14pt; color: #2a5a8c; margin-top: 20px; }}
h3 {{ font-size: 12pt; color: #3a6a9c; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt; }}
th {{ background: #1a3a5c; color: white; padding: 6px 8px; text-align: left; }}
td {{ border: 1px solid #ccc; padding: 5px 8px; }}
tr:nth-child(even) {{ background: #f5f5f5; }}
code {{ background: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-size: 9pt; }}
pre {{ background: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
blockquote {{ border-left: 3px solid #1a3a5c; padding-left: 10px; color: #555; }}
.page-break {{ page-break-after: always; }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""

with open(pdf_path, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"HTML saved to: {pdf_path}")
print("To convert to PDF, open in browser and print to PDF, or use weasyprint directly.")
