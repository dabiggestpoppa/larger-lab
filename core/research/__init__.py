"""
O2C Research Mesh — Autonomous research ingestion, distillation, and agent loops.

This package extends the OCE/SRRA-OPH cognitive field with a sovereign research
substrate that continuously ingests scientific literature, distills papers into
operational doctrine, and spawns research agents on detected knowledge gaps.

Architecture:
    ingestion/   — Source clients (OpenAlex, arXiv, S2), normalizer, cache, scheduler
    distillation/ — Distiller, concept extractor, citation graph, vault writer, doctrine
    agents/      — Gap detector, research agent, evaluator, router, lifecycle, queue

Layer gates:
    L1 GATE: 500 papers ingested, dedup verified, all L1 tests pass
    L2 GATE: 500+ graph nodes, ≥50 papers distilled, ≥1 doctrine extracted
    L3 GATE: First autonomous research cycle completes end-to-end
    L4 GATE: OCE API + frontend pages live

Hard rules (AS enforces):
    - $2/day LLM spend cap, fail-closed
    - 200 vault writes/day cap
    - Max 3 concurrent research agents
    - All agent actions logged to execution journal
    - Every paper note: CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS

See: docs/plans/O2C-RESEARCH-MESH.md
     progress/O2C-RESEARCH-MESH-TASKS.md
"""

__version__ = "0.1.0"
