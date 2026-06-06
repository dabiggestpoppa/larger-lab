"""
L2 — Distillation + Knowledge Graph Layer

Converts raw paper metadata into operational doctrine (markdown notes) and
builds a queryable knowledge graph in SQLite.

Components:
    distiller.py        — Rule-based paper distiller (CC)
    concepts.py         — Concept extractor from OpenAlex/abstract (PM)
    citation_graph.py   — Citation graph builder (PM2)
    vault_writer.py     — Paper → markdown note writer (CC)
    graph_store.py      — SQLite knowledge graph wrapper (CC)
    llm_distill.py      — LLM-assisted distillation (opt-in, cost-bounded) (AS)
    doctrine.py         — Recurring pattern → doctrine extractor (AS)
    contradictions.py   — Contradiction detector (RL)

Every distilled note follows:
    CAUSE / METHOD / RESULT / LIMITATIONS / APPLICATION / LINKS
"""

__all__ = []
