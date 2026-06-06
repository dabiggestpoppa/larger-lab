"""
L1 — Knowledge Acquisition Layer

Source clients pull structured research metadata from external APIs,
normalize to a canonical schema, deduplicate, and cache locally.

Components:
    openalex_client.py  — OpenAlex API wrapper (PM)
    arxiv_client.py     — arXiv API wrapper (PM2)
    s2_client.py        — Semantic Scholar API wrapper (PM)
    sources.py          — Source registry + domain filter (CC)
    models.py           — Normalized paper schema (CC)
    scheduler.py        — APScheduler-based ingestion scheduler (RL)
    cache.py            — SQLite cache + dedup layer (PM)
    rate_limit.py       — Token bucket rate limiter + retry (PM2)

All clients return List[Paper] where Paper is the canonical schema from models.py.
"""

from .models import Paper, PaperStatus, Author, Concept

__all__ = ["Paper", "PaperStatus", "Author", "Concept"]
