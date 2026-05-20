import markdown
import os

md_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_STRATEGIES_COMPLETE.md'
html_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2.html'

with open(md_path, 'r', encoding='utf-8') as f:
    md = f.read()

body = markdown.markdown(md, extensions=['tables', 'fenced_code', 'toc'])

STYLE = """
@page { size: A4; margin: 12mm 15mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 9.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 18pt; color: #0d2b4e; border-bottom: 2px solid #0d2b4e; padding-bottom: 6px; margin-top: 24px; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 14pt; color: #1a4a7a; border-bottom: 1px solid #1a4a7a; padding-bottom: 3px; margin-top: 18px; }
h3 { font-size: 11.5pt; color: #2a5a8c; }
h4 { font-size: 10pt; color: #3a6a9c; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8.5pt; }
th { background: #0d2b4e; color: white; padding: 5px 7px; text-align: left; }
td { border: 1px solid #ccc; padding: 4px 7px; }
tr:nth-child(even) { background: #f4f6f9; }
pre { background: #f0f0f0; padding: 8px; border-radius: 4px; font-size: 8.5pt; }
code { background: #f0f0f0; padding: 1px 3px; border-radius: 2px; }
blockquote { border-left: 3px solid #1a4a7a; padding: 4px 10px; margin: 6px 0; color: #444; background: #f8f9fa; }
ul,ol { padding-left: 20px; margin: 4px 0; }
li { margin: 2px 0; }
"""

html = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n<title>CEREBUS FX - Strategies Complete Reference Vol II</title>\n<style>\n' + STYLE + '</style>\n</head>\n<body>\n' + body + '\n</body>\n</html>'

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML generated:", html_path)
print("Size:", os.path.getsize(html_path), "bytes")
print("Open in browser -> Ctrl+P -> Save as PDF")
