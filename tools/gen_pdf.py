#!/usr/bin/env python3
"""Generate PDF from CEREBUS Vol 2 markdown using fpdf2."""
import os
import re

md_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_STRATEGIES_COMPLETE.md'
pdf_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2.pdf'

with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Try importing fpdf2
try:
    from fpdf import FPDF
    print("fpdf2 available")
except ImportError:
    print("fpdf2 not available, installing...")
    os.system("python -m pip install fpdf2")
    from fpdf import FPDF

class CEREBUS_PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'CEREBUS FX - Strategies Complete Reference Vol II', 0, 0, 'C')
            self.ln(5)
            self.set_draw_color(26, 58, 94)
            self.set_line_width(0.5)
            self.line(10, 15, 200, 15)
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(13, 43, 78)
        self.set_fill_color(240, 244, 248)
        self.cell(0, 12, title, 0, 1, 'L', fill=True)
        self.ln(2)

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(26, 74, 122)
        self.cell(0, 8, title, 0, 1, 'L')
        self.set_draw_color(26, 74, 122)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def subsection_title(self, title):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(42, 90, 140)
        self.cell(0, 7, title, 0, 1, 'L')
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 9.5)
        self.set_text_color(26, 26, 26)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet_text(self, text):
        self.set_font('Helvetica', '', 9.5)
        self.set_text_color(26, 26, 26)
        x = self.get_x()
        self.cell(4, 5, chr(8226))
        self.multi_cell(0, 5, text)
        self.ln(1)

    def table_row(self, cells, widths, is_header=False):
        if is_header:
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(255, 255, 255)
            self.set_fill_color(13, 43, 78)
        else:
            self.set_font('Helvetica', '', 8)
            self.set_text_color(26, 26, 26)
            self.set_fill_color(244, 246, 249)

        max_h = 6
        for i, (cell, w) in enumerate(zip(cells, widths)):
            self.cell(w, max_h, str(cell), 1, 0, 'L', fill=(is_header or (not is_header)))
        self.ln()

    def code_block(self, text):
        self.set_font('Courier', '', 8)
        self.set_text_color(68, 68, 68)
        self.set_fill_color(240, 240, 240)
        self.multi_cell(0, 4, text, 0, 'L', fill=True)
        self.ln(3)

    def blockquote(self, text):
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(68, 68, 68)
        self.set_fill_color(248, 249, 250)
        self.set_draw_color(26, 74, 122)
        self.cell(0, 5, text, 0, 1, 'L', fill=True)
        self.ln(2)


pdf = CEREBUS_PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# Parse markdown and build PDF
lines = content.split('\n')
i = 0
in_table = False
table_rows = []
table_widths = []
in_code = False
code_lines = []

# Estimate column widths for tables (A4 = 190mm usable)
DEFAULT_TABLE_WIDTHS = None

def flush_table(pdf, rows, widths):
    if not rows:
        return
    for j, row in enumerate(rows):
        pdf.table_row(row, widths, is_header=(j==0))
    pdf.ln(3)

while i < len(lines):
    line = lines[i]

    # Code blocks
    if line.startswith('```'):
        if in_code:
            pdf.code_block('\n'.join(code_lines))
            code_lines = []
            in_code = False
        else:
            in_code = True
        i += 1
        continue

    if in_code:
        code_lines.append(line)
        i += 1
        continue

    # Tables
    if line.startswith('|') and line.endswith('|'):
        cells = [c.strip() for c in line.strip('|').split('|')]
        # Skip separator rows
        if all(re.match(r'^[-:]+$', c.replace(' ', '')) for c in cells if c):
            i += 1
            continue
        if not in_table:
            in_table = True
            table_rows = []
            # Calculate widths based on number of columns
            n = len(cells)
            w = 190 / n
            table_widths = [w] * n
        table_rows.append(cells)
        i += 1
        continue
    else:
        if in_table:
            flush_table(pdf, table_rows, table_widths)
            in_table = False
            table_rows = []

    # Headings
    if line.startswith('# ') and not line.startswith('## '):
        title = line[2:].strip()
        pdf.add_page()
        pdf.chapter_title(title)
        i += 1
        continue

    if line.startswith('## '):
        title = line[3:].strip()
        pdf.section_title(title)
        i += 1
        continue

    if line.startswith('### '):
        title = line[4:].strip()
        pdf.subsection_title(title)
        i += 1
        continue

    if line.startswith('#### '):
        title = line[5:].strip()
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(58, 106, 156)
        pdf.cell(0, 6, title, 0, 1, 'L')
        pdf.ln(1)
        i += 1
        continue

    # Horizontal rule
    if line.strip() == '---':
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, self_y := pdf.get_y(), 200, self_y)
        pdf.ln(4)
        i += 1
        continue

    # Blockquotes
    if line.startswith('> '):
        pdf.blockquote(line[2:].strip())
        i += 1
        continue

    # Bullet points
    if line.startswith('- ') or line.startswith('* '):
        pdf.bullet_text(line[2:].strip())
        i += 1
        continue

    # Numbered lists
    num_match = re.match(r'^\d+\.\s+(.*)', line)
    if num_match:
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(26, 26, 26)
        pdf.multi_cell(0, 5, f'  {num_match.group(0).strip()}')
        pdf.ln(1)
        i += 1
        continue

    # Empty lines
    if line.strip() == '':
        pdf.ln(2)
        i += 1
        continue

    # Regular text
    # Clean markdown formatting
    text = line.strip()
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # italic
    text = re.sub(r'`(.*?)`', r'\1', text)  # inline code
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # links
    if text:
        pdf.body_text(text)
    i += 1

# Flush remaining table
if in_table:
    flush_table(pdf, table_rows, table_widths)

pdf.output(pdf_path)
print(f"PDF generated: {pdf_path}")
print(f"Size: {os.path.getsize(pdf_path):,} bytes")
