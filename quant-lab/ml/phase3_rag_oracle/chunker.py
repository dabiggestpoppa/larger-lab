"""
RAG Oracle — Smart Chunking Engine
===================================
Chunks PDF text by CEREBUS Decision Nodes (not naive 500-word blocks).

Chunk Types:
- Temporal Rules: "Wednesday PM", "12 PM Hard Exit", "Monday London Anchor"
- Structural States: "132% Kill-Switch", "T3 Max Accuracy", "Regime FAILED"
- Asset Personalities: "Oil Bifurcation", "EURUSD Aligned"

Every chunk tagged with: [Asset], [Session], [State], [Pattern], [Timeframe]
"""
from __future__ import annotations

import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

# Decision node patterns for classification
TEMPORAL_KEYWORDS = [
    "wednesday", "thursday", "friday", "monday", "tuesday",
    "12pm", "12:00", "noon", "hard exit", "16:00", "17:00",
    "london", "new york", "ny session", "asian session",
    "monday london", "weekly", "session", "time block",
    "bifurcation", "overlap", "activation window",
]

STRUCTURAL_KEYWORDS = [
    "132%", "132 pct", "kill switch", "kill-switch", "invalidation",
    "rekey", "re-key", "fibonacci", "fib", "extension", "retrace",
    "t1", "t2", "t3", "t4", "tier", "tier 1", "tier 2", "tier 3",
    "regime", "confirmed", "caution", "failed", "no-go", "no go",
    "ilm", "ielm", "wilm", "zone", "density zone", "dz",
    "occ", "extreme", "impulse", "pullback", "anchor",
    "mlr", "monday london range", "asian range", "ar",
    "au", "atomic unit", "deficit", "gear shift",
    "alpha", "beta", "gamma", "delta", "3-leg", "ab-cd",
    "stall", "dmr", "deep state", "200%", "168%",
]

ASSET_KEYWORDS = [
    "eurusd", "gbpusd", "usdchf", "usdjpy", "audusd", "nzdusd",
    "usdcad", "eurgbp", "eurjpy", "euraud", "eurchf",
    "gbpjpy", "gbpaud", "gbpcad", "gbpchf", "gbpnzd",
    "oil", "oilusd", "wti", "brent",
    "xauusd", "xagusd", "gold", "silver",
    "btcusd", "ethusd", "crypto",
    "us500", "spx", "sp500", "dax", "de30", "nas100", "hk50",
    "fr40", "cac",
]


@dataclass
class Chunk:
    """A single chunk of manual text with metadata tags."""
    text: str
    source: str  # filename
    page: int
    chunk_type: str  # temporal/structural/asset/general
    tags: dict = field(default_factory=dict)
    asset: str = "GENERAL"
    session: str = "ANY"
    state: str = "ANY"
    pattern: str = "ANY"
    timeframe: str = "ANY"

    def to_dict(self):
        return asdict(self)


def classify_chunk(text: str) -> tuple[str, dict]:
    """Classify a chunk by type and extract tags."""
    text_lower = text.lower()

    # Count keyword matches (use word-boundary regex to avoid false positives)
    def count_matches(keywords, text):
        score = 0
        for kw in keywords:
            # Use word boundary for short keywords (<=3 chars), substring for longer
            if len(kw) <= 3:
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text):
                    score += 1
            else:
                if kw in text:
                    score += 1
        return score

    temporal_score = count_matches(TEMPORAL_KEYWORDS, text_lower)
    structural_score = count_matches(STRUCTURAL_KEYWORDS, text_lower)
    asset_score = count_matches(ASSET_KEYWORDS, text_lower)

    # Determine type
    scores = {
        "temporal": temporal_score,
        "structural": structural_score,
        "asset": asset_score,
    }
    chunk_type = max(scores, key=scores.get)
    if scores[chunk_type] == 0:
        chunk_type = "general"

    # Extract tags
    tags = {}
    if temporal_score > 0:
        tags["temporal"] = True
    if structural_score > 0:
        tags["structural"] = True
    if asset_score > 0:
        tags["asset"] = True

    return chunk_type, tags


def extract_asset(text: str) -> str:
    """Extract asset from text."""
    text_upper = text.upper()
    asset_map = {
        "EURUSD": "EURUSD", "EUR/USD": "EURUSD",
        "GBPUSD": "GBPUSD", "GBP/USD": "GBPUSD",
        "USDCHF": "USDCHF", "USD/CHF": "USDCHF",
        "USDJPY": "USDJPY", "USD/JPY": "USDJPY",
        "AUDUSD": "AUDUSD", "AUD/USD": "AUDUSD",
        "NZDUSD": "NZDUSD", "NZD/USD": "NZDUSD",
        "OILUSD": "OILUSD", "OIL/USD": "OILUSD", "WTI": "OILUSD",
        "XAUUSD": "XAUUSD", "XAU/USD": "XAUUSD", "GOLD": "XAUUSD",
        "XAGUSD": "XAGUSD", "XAG/USD": "XAGUSD", "SILVER": "XAGUSD",
        "BTCUSD": "BTCUSD", "BTC/USD": "BTCUSD",
        "ETHUSD": "ETHUSD", "ETH/USD": "ETHUSD",
        "US500": "US500", "SPX": "US500", "SP500": "US500",
        "DE30": "DE30", "DAX": "DE30",
    }
    for key, val in asset_map.items():
        if key in text_upper:
            return val
    return "GENERAL"


def chunk_text(text: str, source: str = "unknown", page: int = 0,
               max_chunk_size: int = 1000, overlap: int = 200) -> list[Chunk]:
    """
    Smart chunking: split by decision nodes, not by character count.
    Tries to keep related concepts together.
    """
    chunks = []

    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text.strip())

    current_text = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph would exceed max size, save current chunk
        if len(current_text) + len(para) > max_chunk_size and current_text:
            chunk_type, tags = classify_chunk(current_text)
            asset = extract_asset(current_text)
            chunks.append(Chunk(
                text=current_text.strip(),
                source=source,
                page=page,
                chunk_type=chunk_type,
                tags=tags,
                asset=asset,
            ))
            # Keep overlap
            current_text = current_text[-overlap:] + "\n\n" + para
        else:
            current_text += "\n\n" + para if current_text else para

    # Don't forget the last chunk
    if current_text.strip():
        chunk_type, tags = classify_chunk(current_text)
        asset = extract_asset(current_text)
        chunks.append(Chunk(
            text=current_text.strip(),
            source=source,
            page=page,
            chunk_type=chunk_type,
            tags=tags,
            asset=asset,
        ))

    return chunks


def chunk_pdf_text(full_text: str, filename: str,
                   pages_per_chunk: int = 3) -> list[Chunk]:
    """Chunk a full PDF text into decision-node-aware chunks."""
    all_chunks = []

    # Try to split by pages (common patterns)
    page_splits = re.split(r'(?:Page\s+\d+|---\s*Page\s*\d+\s*---|\f)', full_text)

    for i, page_text in enumerate(page_splits):
        if not page_text.strip():
            continue
        page_chunks = chunk_text(page_text, source=filename, page=i)
        all_chunks.extend(page_chunks)

    return all_chunks
