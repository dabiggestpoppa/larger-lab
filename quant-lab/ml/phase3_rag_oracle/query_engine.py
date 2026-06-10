"""
RAG Oracle — Query Engine
===========================
Converts live market state into vector queries.
Retrieves matching manual rules with page citations.
Formats alerts with deterministic state + AI brain trust + Oracle directive.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from .vector_store import RAGVectorStore


class RAGQueryEngine:
    """Query engine that converts market state to manual rule retrieval."""

    def __init__(self, vector_store: RAGVectorStore):
        self.store = vector_store

    def query_market_state(self, features: dict, symbol: str) -> list[dict]:
        """
        Given current market state features, retrieve relevant manual rules.

        Features expected:
        - regime_status: CONFIRMED/CAUTION/FAILED/NO-GO
        - ilm_state: Daily/IELM/WILM/Misaligned
        - day_of_week: 0=Mon ... 4=Fri
        - session: asian/london/ny/black
        - is_wednesday_pm: 0/1
        - dist_to_132_pips: float
        - tier: T1/T2/T3/T4
        - bias: Bullish/Bearish
        """
        # Build query text from market state
        query_parts = []

        # Regime
        regime = features.get("regime_status", "UNKNOWN")
        query_parts.append(f"Regime {regime}")

        # ILM state
        ilm = features.get("ilm_state", "")
        if ilm and ilm != "UNKNOWN":
            query_parts.append(f"ILM {ilm}")

        # Day of week
        dow = features.get("day_of_week", -1)
        day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}
        if dow in day_names:
            query_parts.append(day_names[dow])
            if dow == 2 and features.get("is_wednesday_pm", 0):
                query_parts.append("Wednesday PM bifurcation")

        # Session
        session = features.get("session", "")
        if session:
            query_parts.append(f"{session} session")

        # Kill switch proximity
        dist_132 = features.get("dist_to_132_pips", 999)
        if dist_132 < 10:
            query_parts.append("132% kill switch imminent CRITICAL")
        elif dist_132 < 25:
            query_parts.append("132% kill switch approaching")

        # Tier
        tier = features.get("tier", "")
        if tier:
            query_parts.append(f"Tier {tier}")

        # Bias
        bias = features.get("bias", "")
        if bias:
            query_parts.append(bias)

        query_text = ". ".join(query_parts)

        # Determine asset filter
        asset = self._symbol_to_asset(symbol)

        # Query vector store
        results = self.store.query(
            query_text=query_text,
            n_results=5,
            asset_filter=asset if asset != "GENERAL" else None,
        )

        return results

    def format_alert(self, features: dict, symbol: str,
                     regime: str, confidence: float,
                     pattern: str, time_to_delivery: float) -> str:
        """
        Format a rich Markdown alert with:
        - Deterministic State (Micro/Macro)
        - AI Brain Trust (regime, confidence, pattern)
        - Oracle Directive (RAG-retrieved manual rules)
        """
        # Get RAG oracle directives
        rag_results = self.query_market_state(features, symbol)

        # Build alert
        lines = [
            f"🚨 **CEREBUS GUARDIAN ALERT ({symbol})** 🚨",
            "",
            f"📊 **DETERMINISTIC STATE**",
            f"• Regime: {regime} ({confidence:.0%} confidence)",
            f"• Pattern: {pattern}",
            f"• Time-to-Delivery: {time_to_delivery:.1f}h",
        ]

        # Add key distances
        dist_132 = features.get("dist_to_132_pips", None)
        if dist_132 is not None:
            lines.append(f"• 132% Kill-Switch: {dist_132:.1f} pips")

        dist_25 = features.get("dist_to_25_pips", None)
        if dist_25 is not None:
            lines.append(f"• -25% Target: {dist_25:.1f} pips")

        # ILM state
        ilm = features.get("ilm_state", "")
        if ilm:
            ilm_names = {0: "Daily ILM", 1: "IELM", 2: "WILM", 3: "Misaligned"}
            lines.append(f"• ILM: {ilm_names.get(ilm, ilm)}")

        # Session
        session = features.get("session", "")
        if session:
            lines.append(f"• Session: {session}")

        lines.extend([
            "",
            f"🧠 **AI BRAIN TRUST**",
            f"• Model: XGBoost Regime Classifier (87% CV)",
            f"• Prediction: {regime} @ {confidence:.0%}",
        ])

        # Oracle directive
        lines.extend([
            "",
            f"📖 **ORACLE DIRECTIVE**",
        ])

        if rag_results:
            for i, result in enumerate(rag_results[:3]):
                text = result["text"][:300]
                source = result["metadata"].get("source", "?")
                page = result["metadata"].get("page", "?")
                lines.append(f"  {i+1}. _{text}..._")
                lines.append(f"     — *{source}, p{page}*")
        else:
            lines.append("  No specific manual directive. Use standard protocol.")

        # Action protocol
        lines.extend([
            "",
            f"⚡ **ACTION PROTOCOL**",
        ])

        if dist_132 is not None and dist_132 < 10:
            lines.append("  🛑 CRITICAL: 132% kill-switch within 10 pips. Reduce size 50% or EXIT.")
        elif regime == "CONFIRMED" and confidence > 0.85:
            lines.append("  ✅ HIGH CONFIDENCE: Scale in 50% at current boundary.")
        elif regime == "CAUTION":
            lines.append("  ⚠️ CAUTION: Reduce size. Await confirmation.")
        elif regime == "FAILED":
            lines.append("  ❌ FAILED: No new entries. Manage existing positions only.")
        else:
            lines.append("  ⏳ STAND BY: Alignment threshold not met.")

        return "\n".join(lines)

    @staticmethod
    def _symbol_to_asset(symbol: str) -> str:
        """Convert trading symbol to asset name for filtering."""
        s = symbol.upper().replace(".", "").replace("/", "")
        mapping = {
            "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "USDCHF": "USDCHF",
            "USDJPY": "USDJPY", "AUDUSD": "AUDUSD", "NZDUSD": "NZDUSD",
            "USDCAD": "USDCAD", "EURGBP": "EURGBP", "EURJPY": "EURJPY",
            "GBPJPY": "GBPJPY", "XAUUSD": "XAUUSD", "XAGUSD": "XAGUSD",
            "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD",
            "US500": "US500", "DE30": "DE30", "FR40": "FR40",
            "OILUSD": "OILUSD", "OIL": "OILUSD",
        }
        return mapping.get(s, "GENERAL")
