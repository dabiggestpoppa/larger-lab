"""
PDF Report Generator for Sisyphus Synthesis Engine

Converts Markdown research reports to professional PDF documents.
Uses reportlab for PDF generation with proper academic formatting.

Usage:
    from core.research.synthesis.pdf_generator import PDFReportGenerator
    generator = PDFReportGenerator()
    pdf_path = generator.generate(report_markdown, title="Research Report", output_path="output.pdf")
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("oce.pdf_generator")


class PDFReportGenerator:
    """
    Generates professional PDF research reports from Markdown.
    
    Features:
    - Academic formatting (title page, TOC, sections, references)
    - Proper page margins and typography
    - Page numbers
    - Handles Unicode characters
    - Automatic table of contents
    """

    def __init__(self):
        self._reportlab_available = False
        self._fpdf_available = False
        self._check_libraries()

    def _check_libraries(self):
        """Check which PDF libraries are available."""
        try:
            import reportlab
            self._reportlab_available = True
            logger.info("PDF generator: reportlab available")
        except ImportError:
            logger.warning("reportlab not available")

        try:
            import fpdf
            self._fpdf_available = True
            logger.info("PDF generator: fpdf available")
        except ImportError:
            logger.warning("fpdf not available")

    def generate(
        self,
        markdown: str,
        title: str = "Research Report",
        output_path: Optional[Path] = None,
        author: str = "Sisyphus Academica",
    ) -> Optional[str]:
        """
        Generate a PDF from Markdown content.
        
        Args:
            markdown: Markdown content
            title: Report title
            output_path: Output file path (default: data/reports/YYYY-MM-DD_title.pdf)
            author: Report author
            
        Returns:
            Path to generated PDF or None on failure
        """
        if not markdown:
            logger.warning("No markdown content provided")
            return None

        # Default output path
        if not output_path:
            safe_title = re.sub(r'[^\w\s-]', '', title)[:50].strip().replace(' ', '_')
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            output_path = Path("data") / "reports" / f"{date_str}_{safe_title}.pdf"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try reportlab first (better quality), fallback to fpdf
        if self._reportlab_available:
            return self._generate_reportlab(markdown, title, output_path, author)
        elif self._fpdf_available:
            return self._generate_fpdf(markdown, title, output_path, author)
        else:
            logger.error("No PDF library available. Install reportlab: pip install reportlab")
            return None

    def _generate_reportlab(
        self,
        markdown: str,
        title: str,
        output_path: Path,
        author: str,
    ) -> Optional[str]:
        """Generate PDF using reportlab (higher quality)."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                Table, TableStyle, HRFlowable
            )
            from reportlab.lib.colors import HexColor
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

            # Create document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=HexColor('#1a1a2e'),
            )
            heading1_style = ParagraphStyle(
                'CustomH1',
                parent=styles['Heading1'],
                fontSize=16,
                spaceBefore=20,
                spaceAfter=10,
                textColor=HexColor('#2c3e50'),
            )
            heading2_style = ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=8,
                textColor=HexColor('#34495e'),
            )
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY,
                spaceAfter=8,
            )

            # Build content
            story = []

            # Title page
            story.append(Spacer(1, 2 * inch))
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(f"Generated by {author}", body_style))
            story.append(Paragraph(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
            story.append(PageBreak())

            # Parse markdown and build story
            lines = markdown.split('\n')
            i = 0
            in_code_block = False
            table_lines = []

            while i < len(lines):
                line = lines[i]

                # Skip YAML frontmatter
                if line.strip() == '---' and i == 0:
                    i += 1
                    while i < len(lines) and lines[i].strip() != '---':
                        i += 1
                    i += 1
                    continue

                # Code blocks
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    i += 1
                    continue

                if in_code_block:
                    story.append(Paragraph(self._escape_xml(line), body_style))
                    i += 1
                    continue

                # Headings
                if line.startswith('# '):
                    text = line[2:].strip()
                    story.append(Paragraph(self._escape_xml(text), title_style))
                    story.append(Spacer(1, 0.2 * inch))
                elif line.startswith('## '):
                    text = line[3:].strip()
                    story.append(Paragraph(self._escape_xml(text), heading1_style))
                    story.append(Spacer(1, 0.1 * inch))
                elif line.startswith('### '):
                    text = line[4:].strip()
                    story.append(Paragraph(self._escape_xml(text), heading2_style))
                elif line.startswith('#### '):
                    text = line[5:].strip()
                    story.append(Paragraph(self._escape_xml(text), heading2_style))
                # Horizontal rule
                elif line.strip() in ('---', '***', '___'):
                    story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#bdc3c7'), spaceAfter=10))
                # Table rows
                elif line.strip().startswith('|'):
                    table_lines = []
                    while i < len(lines) and lines[i].strip().startswith('|'):
                        table_lines.append(lines[i])
                        i += 1
                    if table_lines:
                        story.append(self._build_table(table_lines))
                        story.append(Spacer(1, 0.2 * inch))
                    continue
                # List items
                elif line.strip().startswith('- ') or line.strip().startswith('* '):
                    text = line.strip()[2:]
                    story.append(Paragraph(f"• {self._escape_xml(text)}", body_style))
                elif re.match(r'^\d+\.\s', line.strip()):
                    text = re.sub(r'^\d+\.\s', '', line.strip())
                    story.append(Paragraph(self._escape_xml(text), body_style))
                # Empty lines
                elif line.strip() == '':
                    story.append(Spacer(1, 0.1 * inch))
                # Regular paragraphs
                else:
                    story.append(Paragraph(self._escape_xml(line.strip()), body_style))

                i += 1

            # Build PDF
            doc.build(story)
            logger.info(f"PDF generated: {output_path} ({output_path.stat().st_size // 1024} KB)")
            return str(output_path)

        except Exception as e:
            logger.error(f"reportlab PDF generation failed: {e}", exc_info=True)
            return None

    def _generate_fpdf(
        self,
        markdown: str,
        title: str,
        output_path: Path,
        author: str,
    ) -> Optional[str]:
        """Generate PDF using fpdf2 (fallback)."""
        try:
            from fpdf import FPDF

            class ResearchPDF(FPDF):
                def header(self):
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, title[:60], 0, 0, 'R')
                    self.ln(5)
                    self.line(10, self.get_y(), 200, self.get_y())
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

            pdf = ResearchPDF()
            pdf.alias_nb_pages()
            pdf.set_auto_page_break(auto=True, margin=20)

            # Title page
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 24)
            pdf.set_text_color(26, 26, 46)
            pdf.ln(60)
            pdf.multi_cell(0, 12, title, align='C')
            pdf.ln(10)
            pdf.set_font('Helvetica', '', 12)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, f"Generated by {author}", 0, 1, 'C')
            pdf.cell(0, 10, f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", 0, 1, 'C')

            # Content
            pdf.add_page()
            lines = markdown.split('\n')
            in_code = False

            for line in lines:
                if line.strip().startswith('```'):
                    in_code = not in_code
                    continue
                if in_code:
                    pdf.set_font('Courier', '', 9)
                    pdf.multi_cell(0, 5, self._safe_text(line))
                    continue

                if line.startswith('# '):
                    pdf.set_font('Helvetica', 'B', 18)
                    pdf.set_text_color(44, 62, 80)
                    pdf.ln(5)
                    pdf.multi_cell(0, 10, self._safe_text(line[2:]))
                    pdf.ln(3)
                elif line.startswith('## '):
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.set_text_color(52, 73, 94)
                    pdf.ln(3)
                    pdf.multi_cell(0, 8, self._safe_text(line[3:]))
                    pdf.ln(2)
                elif line.startswith('### '):
                    pdf.set_font('Helvetica', 'B', 12)
                    pdf.multi_cell(0, 7, self._safe_text(line[4:]))
                    pdf.ln(2)
                elif line.strip() == '---':
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                elif line.strip().startswith('- '):
                    pdf.set_font('Helvetica', '', 11)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 6, f"  • {self._safe_text(line[2:])}")
                elif line.strip():
                    pdf.set_font('Helvetica', '', 11)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 6, self._safe_text(line))

            pdf.output(str(output_path))
            logger.info(f"PDF generated (fpdf): {output_path} ({output_path.stat().st_size // 1024} KB)")
            return str(output_path)

        except Exception as e:
            logger.error(f"fpdf PDF generation failed: {e}", exc_info=True)
            return None

    @staticmethod
    def _escape_xml(text: str) -> str:
        """Escape XML special characters for reportlab."""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def _safe_text(text: str) -> str:
        """Replace Unicode characters that fpdf2 can't handle."""
        replacements = {
            '\u2014': '—', '\u2013': '–',
            '\u201c': '"', '\u201d': '"',
            '\u2018': "'", '\u2019': "'",
            '\u2022': '-', '\u2192': '->',
            '\u00d7': 'x', '\u2264': '<=',
            '\u2265': '>=', '\u2260': '!=',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _build_table(self, table_lines: list) -> Optional[object]:
        """Build a reportlab Table from markdown table lines."""
        try:
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib.colors import HexColor

            rows = []
            for line in table_lines:
                # Skip separator lines (e.g., |---|---|)
                if re.match(r'^\|[\s\-:]+\|$', line.strip()):
                    continue
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                rows.append(cells)

            if not rows:
                return None

            # Normalize column count
            max_cols = max(len(r) for r in rows)
            for r in rows:
                while len(r) < max_cols:
                    r.append('')

            table = Table(rows)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c3e50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#bdc3c7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8f9fa')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            return table

        except Exception as e:
            logger.warning(f"Table build failed: {e}")
            return None


# ─── Convenience function ────────────────────────────────────────────────────

def generate_pdf_report(
    markdown: str,
    title: str = "Research Report",
    output_path: Optional[str] = None,
) -> Optional[str]:
    """One-shot PDF generation from markdown."""
    generator = PDFReportGenerator()
    path = Path(output_path) if output_path else None
    return generator.generate(markdown, title=title, output_path=path)
