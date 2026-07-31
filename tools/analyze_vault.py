"""Analyze vault: doctrine, contradictions, gaps."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.research.distillation.doctrine import DoctrineExtractor
from core.research.distillation.contradictions import ContradictionDetector
from core.research.agents.gap_detector import GapDetector
from core.research.distillation.graph_store import GraphStore

async def main():
    print("=" * 70)
    print("VAULT ANALYSIS")
    print("=" * 70)
    
    # Doctrine extraction
    print("\n[1/3] DOCTRINE EXTRACTION")
    de = DoctrineExtractor()
    doctrines = de.extract_from_vault()
    print(f"  Doctrines extracted: {len(doctrines)}")
    for d in doctrines[:5]:
        print(f"    - {d}")
    
    # Contradiction detection
    print("\n[2/3] CONTRADICTION DETECTION")
    cd = ContradictionDetector()
    vault_papers = Path(r"C:\Users\wifik\Downloads\o2c\research\papers")
    papers = []
    for md in vault_papers.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        papers.append({"path": str(md), "content": content})
    contradictions = cd.detect(papers)
    print(f"  Contradictions found: {len(contradictions)}")
    for c in contradictions[:3]:
        p1 = c.get("paper1", "")[:40]
        p2 = c.get("paper2", "")[:40]
        print(f"    - {p1} vs {p2}")
    
    # Knowledge gap analysis
    print("\n[3/3] KNOWLEDGE GAP ANALYSIS")
    gs = GraphStore()
    gd = GapDetector()
    gaps = gd.find_gaps()
    print(f"  Gaps detected: {len(gaps)}")
    for g in gaps[:5]:
        desc = g.get("description", "")[:60]
        print(f"    - {desc}")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())