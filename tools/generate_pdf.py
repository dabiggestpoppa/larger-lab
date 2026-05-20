#!/usr/bin/env python3
"""Generate a print-ready HTML from CEREBUS Vol 2 markdown for browser PDF export."""
import markdown
import os
import sys

md_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_STRATEGIES_COMPLETE.md'
html_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2.html'

with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

body_html = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'toc', 'nl2br'])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CEREBUS FX — Strategies Complete Reference Vol II</title>
<style>
@page {{
  size: A4;
  margin: 12mm 15mm;
  @bottom-center {{ content: counter(page); font-size: 9pt; color: #888; }}
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.45;
  color: #1a1a1a;
  max-width: 100%;
}}
h1 {{
  font-size: 20pt;
  color: #0d2b4e;
  border-bottom: 3px solid #0d2b4e;
  padding-bottom: 8px;
  margin-top: 30px;
  page-break-before: always;
}}
h1:first-of-type {{ page-break-before: avoid; }}
h2 {{
  font-size: 15pt;
  color: #1a4a7a;
  border-bottom: 1px solid #1a4a7a;
  padding-bottom: 4px;
  margin-top: 22px;
}}
h3 {{ font-size: 12pt; color: #2a5a8c; margin-top: 16px; }}
h4 {{ font-size: 10.5pt; color: #3a6a9c; }}
p {{ margin: 6px 0; }}
table {{
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 8.5pt;
}}
th {{
  background: #0d2b4e;
  color: white;
  padding: 5px 7px;
  text-align: left;
  font-weight: 600;
}}
td {{
  border: 1px solid #ccc;
  padding: 4px 7px;
}}
tr:nth-child(even) {{ background: #f4f6f9; }}
tr:hover {{ background: #e8eef5; }}
code {{ background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 8.5pt; }}
pre {{
  background: #f0f0f0;
  padding: 10px;
  border-radius: 5px;
  overflow-x: auto;
  font-size: 8.5pt;
  border-left: 3px solid #1a4a7a;
}}
blockquote {{
  border-left: 3px solid #1a4a7a;
  padding: 6px 12px;
  margin: 8px 0;
  color: #444;
  background: #f8f9fa;
  border-radius: 0 4px 4px 0;
}}
hr {{ border: none; border-top: 1px solid #ccc; margin: 16px 0; }}
ul, ol {{ padding-left: 20px; margin: 4px 0; }}
li {{ margin: 2px 0; }}
.toc {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; }}
@media print {{
  body {{ font-size: 9pt; }}
  h1 {{ font-size: 16pt; }}
  h2 {{ font-size: 13pt; }}
  table {{ font-size: 8pt; }}
  .no-print {{ display: none; }}
}}
</style>
</head>
<body>
{body_html}
</body>
</html>"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML generated: {html_path}")
print(f"   Open in browser -> Ctrl+P -> Save as PDF")
print(f"   File size: {os.path.getsize(html_path):,} bytes")
