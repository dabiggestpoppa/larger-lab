"""Convert RCE markdown reports to PDF and save to desktop."""
import os
import re
from pathlib import Path

desktop = Path(os.path.expanduser('~')) / 'Desktop'

# Check if reportlab is available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

def md_to_pdf(md_path, pdf_path):
    """Convert a markdown file to PDF using reportlab."""
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse markdown into structured elements
    elements = []
    lines = content.split('\n')
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor='#1a1a2e'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3,
        alignment=TA_CENTER,
        textColor='#555555'
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=14,
        spaceBefore=16,
        spaceAfter=8,
        textColor='#16213e',
        borderWidth=0,
        borderPadding=0,
        borderColor=None,
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        textColor='#0f3460',
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        leading=14,
        textColor='#333333',
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_LEFT,
        leading=14,
        textColor='#1a1a2e',
    )
    
    # Parse the markdown
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines
        if not line.strip():
            elements.append(Spacer(1, 4))
            i += 1
            continue
        
        # Title (# Title)
        if line.startswith('# ') and not line.startswith('## '):
            title = line[2:].strip()
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 2))
            i += 1
            continue
        
        # Subtitle line (metadata)
        if line.startswith('**Topic:**') or line.startswith('**Papers') or line.startswith('**Sources') or line.startswith('**Word') or line.startswith('**Confidence'):
            clean = line.replace('**', '').strip()
            elements.append(Paragraph(clean, subtitle_style))
            i += 1
            continue
        
        # Section headers (## Section)
        if line.startswith('## '):
            section = line[3:].strip()
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(section, h1_style))
            elements.append(Spacer(1, 4))
            i += 1
            continue
        
        # Bold lines
        if line.startswith('**') and line.endswith('**'):
            clean = line.replace('**', '').strip()
            elements.append(Paragraph(f'<b>{clean}</b>', bold_style))
            i += 1
            continue
        
        # Regular paragraph
        # Clean markdown formatting
        clean = line.strip()
        clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean)
        clean = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean)
        
        if clean:
            elements.append(Paragraph(clean, body_style))
        
        i += 1
    
    # Build PDF
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    doc.build(elements)
    print(f'PDF saved: {pdf_path}')

# Convert both reports
reports = [
    ('RCE_transfer_entropy_financial_markets_syste.md', 'RCE_Transfer_Entropy_Financial_Markets.pdf'),
    ('RCE_geopolitical_risk_emerging_markets_capit.md', 'RCE_Geopolitical_Risk_Emerging_Markets.pdf'),
]

for md_name, pdf_name in reports:
    md_path = desktop / md_name
    pdf_path = desktop / pdf_name
    
    if not md_path.exists():
        print(f'NOT FOUND: {md_path}')
        continue
    
    if REPORTLAB_OK:
        try:
            md_to_pdf(md_path, pdf_path)
            print(f'  Size: {pdf_path.stat().st_size:,} bytes')
        except Exception as e:
            print(f'ERROR converting {md_name}: {e}')
            # Fallback: save as formatted text
            import shutil
            txt_path = desktop / pdf_name.replace('.pdf', '.txt')
            shutil.copy2(md_path, txt_path)
            print(f'  Fallback: saved as {txt_path.name}')
    else:
        print(f'reportlab not installed. Install with: pip install reportlab')
        # Just copy the md file
        import shutil
        shutil.copy2(md_path, pdf_path.with_suffix('.md'))
        print(f'  Copied MD to: {pdf_path.with_suffix(".md").name}')

print('\nDone!')
