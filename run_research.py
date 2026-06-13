"""Run full research pipeline on both interdisciplinary topics."""
import asyncio, sys, time, os, shutil
sys.path.insert(0, '.')

from core.research.synthesis.sisyphus import SisyphusEngine, SourceDocument
from core.research.ingestion.openalex import OpenAlexIngester, OpenAlexClient
from core.spawn.openrouter_gateway import OpenRouterGateway
from core.research.synthesis.pdf_generator import PDFReportGenerator

async def research_topic(query, topic_name):
    print(f"\n{'='*60}")
    print(f"TOPIC: {topic_name}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    gateway = OpenRouterGateway()
    client = OpenAlexClient()
    ingester = OpenAlexIngester(client=client)
    sisyphus = SisyphusEngine(gateway=gateway)
    pdf_gen = PDFReportGenerator()

    # Ingest
    print("\n[1/5] Ingesting from OpenAlex...")
    works = await ingester.ingest_query(query, limit=8)
    print(f"  Ingested {len(works)} works")
    for i, w in enumerate(works, 1):
        print(f"    {i}. {w.title[:70]}")

    # Prepare sources
    sources = [SourceDocument(
        doc_id=w.canonical_id, title=w.title,
        text=f"{w.title}. {w.abstract}" if w.abstract else w.title,
        source="openalex", authors=[a.display_name for a in w.authors],
        year=w.publication_date[:4] if w.publication_date else "",
        doi=w.doi or "",
    ) for w in works]

    # Synthesize
    print("\n[2/5] Analyzing individual sources (LLM)...")
    print("[3/5] Cross-referencing and synthesizing (LLM)...")
    print("[4/5] Detecting contradictions (LLM)...")
    print("[5/5] Assembling final report (LLM)...")

    start = time.time()
    result = await sisyphus.synthesize(
        query=f"How does {topic_name.lower()} work? What are the key findings, debates, and implications?",
        sources=sources,
    )
    elapsed = time.time() - start

    print(f"\n  Synthesis complete: {result.word_count} words in {elapsed:.1f}s")
    print(f"  Title: {result.title}")

    # Generate PDF
    if result.full_report:
        safe_name = topic_name.replace(" ", "_").replace("x", "x").replace("/", "_")
        md_path = f"data/test_reports/synthesis_{safe_name}.md"
        pdf_path = f"data/reports/{safe_name}.pdf"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(result.full_report)

        pdf_result = pdf_gen.generate(result.full_report, title=result.title or topic_name, output_path=pdf_path)

        md_size = os.path.getsize(md_path) // 1024
        pdf_size = os.path.getsize(pdf_result) // 1024 if pdf_result else 0

        print(f"  Markdown: {md_path} ({md_size} KB)")
        print(f"  PDF: {pdf_result} ({pdf_size} KB)")

        # Copy to desktop
        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        if pdf_result:
            shutil.copy2(pdf_result, os.path.join(desktop, f"{safe_name}.pdf"))
            print(f"  Copied to desktop: {safe_name}.pdf")

    await ingester.close()
    return result

async def main():
    topics = [
        ("emerging markets geopolitical risk institutional quality", "Emerging Markets x Geopolitics"),
        ("information theory entropy trading systems market microstructure", "Information Theory x Trading Systems"),
    ]

    results = []
    for query, name in topics:
        result = await research_topic(query, name)
        results.append((name, result))

    print(f"\n\n{'='*60}")
    print("ALL TOPICS COMPLETE")
    print(f"{'='*60}")
    for name, result in results:
        print(f"\n{name}:")
        print(f"  Words: {result.word_count}")
        print(f"  Title: {result.title}")
        if result.pdf_path:
            print(f"  PDF: {result.pdf_path}")

asyncio.run(main())
