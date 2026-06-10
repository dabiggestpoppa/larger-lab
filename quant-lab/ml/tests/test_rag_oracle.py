"""
Tests for Phase 3: RAG Oracle
================================
Tests chunking, vector store, query engine, and guardian pipeline.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from phase3_rag_oracle.chunker import (
    chunk_text, chunk_pdf_text, classify_chunk, extract_asset,
    TEMPORAL_KEYWORDS, STRUCTURAL_KEYWORDS, ASSET_KEYWORDS,
)
from phase3_rag_oracle.vector_store import RAGVectorStore
from phase3_rag_oracle.query_engine import RAGQueryEngine


class TestChunker:
    """Test smart chunking by decision nodes."""

    def test_classify_temporal(self):
        text = "Wednesday PM is the bifurcation window. If -25% is not hit by 16:00 UTC, reduce size."
        chunk_type, tags = classify_chunk(text)
        assert chunk_type == "temporal"
        assert tags.get("temporal") is True

    def test_classify_structural(self):
        text = "The 132% kill-switch level is the structural invalidation point. Price breaching this level triggers a rekey sequence."
        chunk_type, tags = classify_chunk(text)
        assert chunk_type == "structural"
        assert tags.get("structural") is True

    def test_classify_asset(self):
        text = "EURUSD and GBPUSD have different volatility profiles. OilUSD bifurcation patterns differ from forex pairs like EURUSD."
        chunk_type, tags = classify_chunk(text)
        assert chunk_type == "asset"
        assert tags.get("asset") is True

    def test_classify_general(self):
        text = "Successful trading requires patience and discipline over many years of practice."
        chunk_type, tags = classify_chunk(text)
        assert chunk_type == "general"

    def test_extract_asset_eurusd(self):
        assert extract_asset("EURUSD shows strong momentum") == "EURUSD"
        assert extract_asset("The EUR/USD pair is trending") == "EURUSD"

    def test_extract_asset_gbpusd(self):
        assert extract_asset("GBPUSD is approaching the 132% level") == "GBPUSD"

    def test_extract_asset_oil(self):
        assert extract_asset("OILUSD is in a stall zone") == "OILUSD"

    def test_extract_asset_general(self):
        assert extract_asset("The market is moving higher") == "GENERAL"

    def test_chunk_text_basic(self):
        text = "First paragraph about Wednesday PM rules.\n\nSecond paragraph about 132% kill-switch.\n\nThird paragraph about EURUSD specifics."
        chunks = chunk_text(text, source="test.pdf", page=1)
        assert len(chunks) >= 1
        assert all(c.source == "test.pdf" for c in chunks)
        assert all(c.page == 1 for c in chunks)

    def test_chunk_text_preserves_content(self):
        text = "The 132% kill-switch is the most important structural level. When price breaches this level, the entire weekly anchor is invalidated and a rekey sequence begins."
        chunks = chunk_text(text, source="test.pdf", page=0)
        assert len(chunks) >= 1
        full_text = " ".join(c.text for c in chunks)
        assert "132%" in full_text
        assert "kill-switch" in full_text
        assert "rekey" in full_text

    def test_chunk_pdf_text(self):
        text = "Page 1 content about Asian Range.\n\nPage 2 content about London session.\n\nPage 3 content about NY session."
        chunks = chunk_pdf_text(text, filename="manual.pdf")
        assert len(chunks) >= 1

    def test_temporal_keywords_coverage(self):
        """Ensure we have good temporal keyword coverage."""
        assert "wednesday" in TEMPORAL_KEYWORDS
        assert "12pm" in TEMPORAL_KEYWORDS or "12:00" in TEMPORAL_KEYWORDS
        assert "hard exit" in TEMPORAL_KEYWORDS
        assert "monday london" in TEMPORAL_KEYWORDS

    def test_structural_keywords_coverage(self):
        """Ensure we have good structural keyword coverage."""
        assert "132%" in STRUCTURAL_KEYWORDS
        assert "kill switch" in STRUCTURAL_KEYWORDS
        assert "rekey" in STRUCTURAL_KEYWORDS
        assert "regime" in STRUCTURAL_KEYWORDS
        assert "ilm" in STRUCTURAL_KEYWORDS


class TestVectorStore:
    """Test ChromaDB vector store."""

    @pytest.fixture
    def temp_store(self):
        """Create a temporary vector store."""
        temp_dir = tempfile.mkdtemp()
        store = RAGVectorStore(persist_dir=temp_dir)
        yield store
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ingest_and_query(self, temp_store):
        """Test basic ingestion and querying."""
        from phase3_rag_oracle.chunker import Chunk

        chunks = [
            Chunk(
                text="Wednesday PM bifurcation window. If -25% not hit by 16:00 UTC, reduce size 50%.",
                source="manual.pdf",
                page=1,
                chunk_type="temporal",
                asset="GENERAL",
            ),
            Chunk(
                text="132% kill-switch level. When breached, triggers rekey sequence.",
                source="manual.pdf",
                page=2,
                chunk_type="structural",
                asset="GENERAL",
            ),
            Chunk(
                text="EURUSD Monday London Range anchor. 07:00-15:00 UTC window.",
                source="manual.pdf",
                page=3,
                chunk_type="asset",
                asset="EURUSD",
            ),
        ]

        count = temp_store.ingest_chunks(chunks)
        assert count == 3
        assert temp_store.count() == 3

    def test_query_returns_results(self, temp_store):
        """Test that queries return relevant results."""
        from phase3_rag_oracle.chunker import Chunk

        chunks = [
            Chunk(text="Wednesday PM bifurcation rules for trading.", source="test.pdf", page=0,
                  chunk_type="temporal", asset="GENERAL"),
            Chunk(text="132% kill-switch invalidation level.", source="test.pdf", page=1,
                  chunk_type="structural", asset="GENERAL"),
        ]
        temp_store.ingest_chunks(chunks)

        results = temp_store.query("Wednesday PM bifurcation", n_results=2)
        assert len(results) >= 1

    def test_query_with_asset_filter(self, temp_store):
        """Test querying with asset filter."""
        from phase3_rag_oracle.chunker import Chunk

        chunks = [
            Chunk(text="EURUSD specific rules for Monday trading.", source="test.pdf", page=0,
                  chunk_type="asset", asset="EURUSD"),
            Chunk(text="GBPUSD specific rules for Tuesday trading.", source="test.pdf", page=1,
                  chunk_type="asset", asset="GBPUSD"),
        ]
        temp_store.ingest_chunks(chunks)

        results = temp_store.query("Monday trading rules", n_results=5, asset_filter="EURUSD")
        # Should prefer EURUSD chunk
        if results:
            assert results[0]["metadata"]["asset"] == "EURUSD"


class TestQueryEngine:
    """Test RAG query engine."""

    @pytest.fixture
    def engine(self):
        """Create a query engine with test data."""
        temp_dir = tempfile.mkdtemp()
        store = RAGVectorStore(persist_dir=temp_dir)

        from phase3_rag_oracle.chunker import Chunk
        chunks = [
            Chunk(text="Wednesday PM: If -25% not hit by 16:00 UTC, reduce size 50% or EXIT. Bifurcation day.", source="manual.pdf", page=0,
                  chunk_type="temporal", asset="GENERAL"),
            Chunk(text="132% Kill-Switch: When breached, EXIT immediately. Wait for 78.6% rekey retest.", source="manual.pdf", page=1,
                  chunk_type="structural", asset="GENERAL"),
            Chunk(text="Regime CONFIRMED: Scale in 50% at current boundary. Trail stop to BE at -25%.", source="manual.pdf", page=2,
                  chunk_type="structural", asset="GENERAL"),
            Chunk(text="EURUSD specific: Monday London Range anchor at 07:00-15:00 UTC. Asian range T2 delivery to -25%.", source="manual.pdf", page=3,
                  chunk_type="asset", asset="EURUSD"),
        ]
        store.ingest_chunks(chunks)
        engine = RAGQueryEngine(store)
        yield engine
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_query_market_state(self, engine):
        """Test querying with market state features."""
        features = {
            "regime_status": "CONFIRMED",
            "ilm_state": 0,
            "day_of_week": 2,  # Wednesday
            "session": "london",
            "is_wednesday_pm": 1,
            "dist_to_132_pips": 45.0,
            "tier": "T2",
            "bias": "Bullish",
        }
        results = engine.query_market_state(features, "EURUSD")
        assert len(results) >= 1

    def test_format_alert(self, engine):
        """Test alert formatting."""
        features = {
            "regime_status": "CONFIRMED",
            "ilm_state": 0,
            "day_of_week": 1,
            "session": "london",
            "is_wednesday_pm": 0,
            "dist_to_132_pips": 45.0,
            "dist_to_25_pips": 12.0,
            "tier": "T2",
            "bias": "Bullish",
        }
        alert = engine.format_alert(
            features=features,
            symbol="EURUSD",
            regime="CONFIRMED",
            confidence=0.92,
            pattern="Alpha 3-Leg",
            time_to_delivery=18.0,
        )
        assert "CEREBUS GUARDIAN ALERT" in alert
        assert "EURUSD" in alert
        assert "CONFIRMED" in alert
        assert "92%" in alert


class TestGuardianPipeline:
    """Test Guardian alert pipeline."""

    def test_config_defaults(self):
        from phase4_guardian.guardian import GuardianConfig
        config = GuardianConfig()
        assert config.MIN_CONFIDENCE == 0.85
        assert config.HARD_EXIT_HOUR_UTC == 17
        assert config.WEDNESDAY_PM_HOUR_UTC == 16

    def test_hard_exit_12pm(self):
        from phase4_guardian.guardian import GuardianConfig
        config = GuardianConfig()
        assert config.HARD_EXIT_HOUR_UTC == 17  # 12PM EST

    def test_wednesday_pm_rule(self):
        from phase4_guardian.guardian import GuardianConfig
        config = GuardianConfig()
        assert config.WEDNESDAY_PM_HOUR_UTC == 16  # 12PM EST

    def test_alignment_check(self):
        from phase4_guardian.guardian import GuardianConfig
        config = GuardianConfig()
        # Test that alignment thresholds are reasonable
        assert 0.5 < config.MIN_CONFIDENCE < 1.0
        assert config.MAX_DIST_TO_132_PIPS > 0
        assert config.MAX_DIST_TO_TARGET_PIPS > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
