#!/usr/bin/env python3
"""Generate CEREBUS Vol 2 PDF using fpdf2."""
import os, re

md_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2_STRATEGIES_COMPLETE.md'
pdf_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\CEREBUS_VOL2.pdf'

with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

from fpdf import FPDF

def no_emoji(s):
    return re.sub(r'[^\x00-\x7F]+', '', s).strip()

def unmd(s):
    s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)
    s = re.sub(r'\*(.*?)\*', r'\1', s)
    s = re.sub(r'`(.*?)`', r'\1', s)
    s = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', s)
    return no_emoji(s)

class PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font('helvetica', 'I', 7)
        self.set_text_color(150)
        self.cell(0, 8, f'Page {self.page_no()}', new_x='CENTER')

pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(10, 10, 10)

lines = content.split('\n')
i = 0
in_code = False
code_lines = []
in_table = False
table_rows = []

def draw_table(rows):
    if not rows:
        return
    n = len(rows[0])
    cw = min(185 / n, 42)
    for ri, row in enumerate(rows):
        if all(re.match(r'^[-:]+$', c.replace(' ', '')) for c in row if c):
            continue
        for c in row:
            t = unmd(c.strip())[:26]
            if ri == 0:
                pdf.set_font('helvetica', 'B', 7)
                pdf.set_text_color(255, 255, 255)
                pdf.set_fill_color(13, 43, 78)
            else:
                pdf.set_font('helvetica', '', 7)
                pdf.set_text_color(30, 30, 30)
            pdf.cell(cw, 5, t, border=1, fill=(ri == 0))
        pdf.ln()
    pdf.ln(2)

while i < len(lines):
    line = lines[i]

    # Code block
    if line.startswith('```'):
        if in_code:
            pdf.set_font('courier', '', 7)
            pdf.set_fill_color(240, 240, 240)
            for cl in code_lines[:25]:
                pdf.cell(0, 3.5, unmd(cl)[:130], new_x='LMARGIN', new_y='NEXT', fill=True)
            pdf.ln(2)
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

    # Table
    if line.startswith('|') and line.endswith('|'):
        cells = [c.strip() for c in line.strip('|').split('|')]
        if not all(re.match(r'^[-:]+$', c.replace(' ', '')) for c in cells if c):
            table_rows.append(cells)
        i += 1
        continue
    elif table_rows:
        draw_table(table_rows)
        table_rows = []

    # Skip HTML tags
    if re.match(r'^\s*<\w+.*>\s*$', line):
        i += 1
        continue

    # H1
    if re.match(r'^#\s+', line) and not re.match(r'^##\s+', line):
        pdf.add_page()
        t = unmd(re.sub(r'^#\s+', '', line))
        if t:
            pdf.set_font('helvetica', 'B', 15)
            pdf.set_text_color(13, 43, 78)
            pdf.set_fill_color(235, 240, 245)
            pdf.cell(0, 11, t, new_x='LMARGIN', new_y='NEXT', fill=True)
            pdf.ln(3)
        i += 1
        continue

    # H2
    if re.match(r'^##\s+', line):
        t = unmd(re.sub(r'^##\s+', '', line))
        if t:
            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(26, 74, 122)
            pdf.cell(0, 8, t, new_x='LMARGIN', new_y='NEXT')
            pdf.set_draw_color(26, 74, 122)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
        i += 1
        continue

    # H3
    if re.match(r'^###\s+', line):
        t = unmd(re.sub(r'^###\s+', '', line))
        if t:
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(42, 90, 140)
            pdf.cell(0, 6, t, new_x='LMARGIN', new_y='NEXT')
            pdf.ln(1)
        i += 1
        continue

    # H4
    if re.match(r'^####\s+', line):
        t = unmd(re.sub(r'^####\s+', '', line))
        if t:
            pdf.set_font('helvetica', 'B', 9)
            pdf.set_text_color(58, 106, 156)
            pdf.cell(0, 5, t, new_x='LMARGIN', new_y='NEXT')
            pdf.ln(1)
        i += 1
        continue

    # HR
    if line.strip() == '---':
        pdf.ln(2)
        i += 1
        continue

    # Blockquote
    if line.startswith('> '):
        pdf.set_font('helvetica', 'I', 8)
        pdf.set_text_color(80, 80, 80)
        pdf.set_fill_color(248, 249, 250)
        pdf.set_x(12)
        pdf.multi_cell(180, 4, unmd(line[2:]), fill=True)
        pdf.ln(1)
        i += 1
        continue

    # Bullet
    m = re.match(r'^[-*]\s+(.*)', line)
    if m:
        pdf.set_font('helvetica', '', 8.5)
        pdf.set_text_color(30, 30, 30)
        pdf.set_x(14)
        pdf.multi_cell(180, 4, f'* {unmd(m.group(1))}')
        i += 1
        continue

    # Numbered
    m = re.match(r'^(\d+)\.\s+(.*)', line)
    if m:
        pdf.set_font('helvetica', '', 8.5)
        pdf.set_text_color(30, 30, 30)
        pdf.set_x(14)
        pdf.multi_cell(180, 4, f'{m.group(1)}. {unmd(m.group(2))}')
        i += 1
        continue

    # Empty
    if line.strip() == '':
        pdf.ln(1.5)
        i += 1
        continue

    # Normal text
    t = unmd(line.strip())
    if t:
        pdf.set_font('helvetica', '', 8.5)
        pdf.set_text_color(30, 30, 30)
        pdf.set_x(10)
        pdf.multi_cell(185, 4, t)
    i += 1

if table_rows:
    draw_table(table_rows)

pdf.output(pdf_path)
size = os.path.getsize(pdf_path)
print(f"PDF: {pdf_path}")
print(f"Size: {size:,} bytes ({size/1024:.0f} KB)")
