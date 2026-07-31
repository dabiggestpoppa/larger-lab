#!/usr/bin/env python3
"""Build a professional PDF from The Hidden Physics of Trading manuscript."""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Colors
DARK_BG = HexColor('#1a1a2e')
TEXT_DARK = HexColor('#2d2d2d')
TEXT_MEDIUM = HexColor('#444444')
ACCENT = HexColor('#c96442')
LIGHT_GRAY = HexColor('#999999')
WHITE = HexColor('#ffffff')

# Page setup
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.75 * inch

def build_pdf():
    output_path = os.path.join(os.path.dirname(__file__), "The_Hidden_Physics_of_Trading.pdf")
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="The Hidden Physics of Trading",
        author="CEREBUS",
        subject="Market Theory"
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'BookTitle', parent=styles['Title'],
        fontSize=36, leading=42,
        textColor=ACCENT,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=14, leading=18,
        textColor=TEXT_MEDIUM,
        alignment=TA_CENTER,
        spaceAfter=40,
        fontName='Helvetica-Oblique'
    )
    
    chapter_style = ParagraphStyle(
        'ChapterTitle', parent=styles['Heading1'],
        fontSize=24, leading=30,
        textColor=ACCENT,
        alignment=TA_CENTER,
        spaceBefore=40,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    phase_style = ParagraphStyle(
        'PhaseTitle', parent=styles['Heading2'],
        fontSize=12, leading=16,
        textColor=LIGHT_GRAY,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=20,
        fontName='Helvetica-Oblique'
    )
    
    body_style = ParagraphStyle(
        'BodyText', parent=styles['Normal'],
        fontSize=11, leading=17,
        textColor=TEXT_DARK,
        alignment=TA_JUSTIFY,
        spaceBefore=6,
        spaceAfter=6,
        fontName='Helvetica',
        firstLineIndent=24
    )
    
    body_no_indent = ParagraphStyle(
        'BodyNoIndent', parent=body_style,
        firstLineIndent=0
    )
    
    observation_style = ParagraphStyle(
        'Observation', parent=styles['Normal'],
        fontSize=10, leading=15,
        textColor=TEXT_MEDIUM,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=12,
        fontName='Helvetica-Oblique',
        leftIndent=36,
        rightIndent=36,
        borderColor=ACCENT,
        borderWidth=0,
        borderPadding=8
    )
    
    seed_style = ParagraphStyle(
        'Seed', parent=styles['Normal'],
        fontSize=10, leading=15,
        textColor=ACCENT,
        alignment=TA_LEFT,
        spaceBefore=16,
        spaceAfter=6,
        fontName='Helvetica-Bold-Oblique',
        leftIndent=24
    )
    
    glossary_term_style = ParagraphStyle(
        'GlossaryTerm', parent=styles['Normal'],
        fontSize=11, leading=16,
        textColor=ACCENT,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )
    
    glossary_def_style = ParagraphStyle(
        'GlossaryDef', parent=styles['Normal'],
        fontSize=10, leading=15,
        textColor=TEXT_MEDIUM,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=8,
        fontName='Helvetica',
        leftIndent=24
    )
    
    final_words_style = ParagraphStyle(
        'FinalWords', parent=body_style,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        textColor=TEXT_MEDIUM,
        fontSize=12, leading=18,
        firstLineIndent=0
    )
    
    # Read manuscript
    manuscript_path = os.path.join(os.path.dirname(__file__), "02-revised-manuscript.md")
    with open(manuscript_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse into story elements
    story = []
    
    # Title page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("THE HIDDEN PHYSICS OF TRADING", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Why Price Movement Isn't Random", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Understanding The Real Mechanics Behind Financial Markets", subtitle_style))
    story.append(Spacer(1, 2 * inch))
    story.append(HRFlowable(width="60%", thickness=1, color=ACCENT, spaceAfter=20, spaceBefore=20, hAlign='CENTER'))
    story.append(Paragraph("A Foundational Market Theory Book", ParagraphStyle(
        'tagline', parent=body_style, alignment=TA_CENTER, fontName='Helvetica-Oblique',
        textColor=LIGHT_GRAY, firstLineIndent=0
    )))
    story.append(PageBreak())
    
    # Parse markdown content
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Skip the title (already on title page)
        if line.startswith('# THE HIDDEN PHYSICS'):
            i += 1
            continue
        if line.startswith('### *Why Price Movement'):
            i += 1
            continue
        
        # Chapter headings
        if line.startswith('## CHAPTER') or line.startswith('## FINAL CHAPTER') or line.startswith('## INTRODUCTION'):
            # Extract chapter title
            chapter_title = line.replace('## ', '').strip()
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(chapter_title.upper(), chapter_style))
            story.append(HRFlowable(width="40%", thickness=1, color=ACCENT, spaceAfter=20, spaceBefore=6, hAlign='CENTER'))
            i += 1
            continue
        
        # Phase headers
        if line.startswith('*(Phase') or line.startswith('*(Phase'):
            phase_text = line.strip('()*').strip()
            story.append(Paragraph(phase_text, phase_style))
            i += 1
            continue
        
        # Book 2 Seed
        if line.startswith('### 📦 Book 2 Seed'):
            i += 1
            # Collect seed text
            seed_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('*(Phase'):
                seed_lines.append(lines[i].strip())
                i += 1
            if seed_lines:
                seed_text = ' '.join(seed_lines)
                story.append(Paragraph(f"Book 2 Seed: {seed_text}", seed_style))
            continue
        
        # Market Observation Example
        if line.startswith('> **Market Observation Example:**'):
            obs_text = line.replace('> **Market Observation Example:**', '').strip()
            story.append(Paragraph(f"Market Observation Example: {obs_text}", observation_style))
            i += 1
            continue
        
        # Glossary
        if line.startswith('## GLOSSARY'):
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph("GLOSSARY OF KEY TERMS", chapter_style))
            story.append(HRFlowable(width="40%", thickness=1, color=ACCENT, spaceAfter=20, spaceBefore=6, hAlign='CENTER'))
            i += 1
            continue
        
        if line.startswith('**') and line.endswith('**') and ':' not in line:
            term = line.strip('*').strip()
            story.append(Paragraph(term, glossary_term_style))
            i += 1
            continue
        
        if line.startswith('**') and ':' in line:
            # Glossary term with inline definition
            parts = line.split('**')
            if len(parts) >= 3:
                term = parts[1].strip()
                definition = parts[2].strip().lstrip(':').strip()
                story.append(Paragraph(term, glossary_term_style))
                story.append(Paragraph(definition, glossary_def_style))
                i += 1
                continue
        
        # Final words section
        if line.startswith('## FINAL WORDS'):
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph("FINAL WORDS", chapter_style))
            story.append(HRFlowable(width="40%", thickness=1, color=ACCENT, spaceAfter=20, spaceBefore=6, hAlign='CENTER'))
            i += 1
            continue
        
        # Italic closing lines
        if line.startswith('*If markets operate') or line.startswith('*If price movement') or line.startswith('*Then the question'):
            story.append(Paragraph(line.strip('*').strip(), final_words_style))
            i += 1
            continue
        
        if line.startswith('*That question led') or line.startswith('*And eventually') or line.startswith('*But that is'):
            story.append(Paragraph(line.strip('*').strip(), final_words_style))
            i += 1
            continue
        
        # Regular body text
        if line.startswith('#'):
            # Skip already handled headings
            i += 1
            continue
        
        if line == '---':
            story.append(Spacer(1, 20))
            story.append(HRFlowable(width="30%", thickness=0.5, color=LIGHT_GRAY, spaceAfter=20, spaceBefore=10, hAlign='CENTER'))
            i += 1
            continue
        
        if line == '**END**':
            story.append(Spacer(1, inch))
            story.append(HRFlowable(width="60%", thickness=1, color=ACCENT, spaceAfter=20, spaceBefore=20, hAlign='CENTER'))
            story.append(Paragraph("END", ParagraphStyle(
                'End', parent=body_style, alignment=TA_CENTER, fontName='Helvetica-Bold',
                textColor=ACCENT, firstLineIndent=0, fontSize=14
            )))
            i += 1
            continue
        
        # Regular paragraph
        if line:
            # Clean markdown formatting
            clean_line = line
            # Remove bold markers
            clean_line = clean_line.replace('**', '')
            # Remove italic markers
            clean_line = clean_line.replace('*', '')
            
            story.append(Paragraph(clean_line, body_style))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f"PDF created: {output_path}")
    return output_path

if __name__ == '__main__':
    build_pdf()
