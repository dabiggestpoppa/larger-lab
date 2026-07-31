"""
Generate PDF Research Report - Direct approach.
"""
import asyncio, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.spawn.openrouter_gateway import OpenRouterGateway


async def main():
    print("=" * 70)
    print("GENERATING PDF RESEARCH REPORT")
    print("=" * 70)

    # Get distilled notes from vault
    vault_papers = Path(r"C:\Users\wifik\Downloads\o2c\research\papers")
    notes = []
    for md_file in list(vault_papers.rglob("*.md"))[:5]:
        notes.append(md_file.read_text(encoding="utf-8"))

    notes_text = "\n\n---\n\n".join(notes)

    # Generate report with LLM
    gateway = OpenRouterGateway()
    prompt = f"""Generate a comprehensive academic research report synthesizing these paper notes:

{notes_text[:5000]}

Format as a formal research report with:
- Executive Summary
- Introduction  
- Literature Review
- Methodology
- Findings
- Discussion
- Conclusion
- References

Write 1500-2000 words in academic style."""

    print("\n[1/2] Generating report content via LLM...")
    report_md = await gateway.complete(prompt, model="nvidia/nemotron-3-ultra-550b-a55b:free")

    if not report_md:
        print("❌ LLM failed to generate report")
        return

    print(f"✅ Generated {len(report_md)} characters")

    # Convert to PDF
    print("\n[2/2] Converting to PDF...")
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch

    output_path = Path(r"C:\Users\wifik\Downloads\o2c\research\reports")
    output_path.mkdir(parents=True, exist_ok=True)
    pdf_file = output_path / f"research_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"

    doc = SimpleDocTemplate(str(pdf_file), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    for line in report_md.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 12))
            continue
        if line.startswith('# '):
            story.append(Paragraph(line[2:], styles['Title']))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], styles['Heading1']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['Heading2']))
        else:
            story.append(Paragraph(line, styles['Normal']))

    doc.build(story)
    print(f"\n✅ PDF REPORT GENERATED: {pdf_file}")
    print(f"   Size: {pdf_file.stat().st_size} bytes")


if __name__ == "__main__":
    asyncio.run(main())