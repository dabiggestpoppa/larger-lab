"""
Tests for OCE Structural Memory Engine (Phase 4).
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from structural_memory import (
    StructuralMemory,
    MemoryEntry,
    MemoryLayer,
    MemoryStats,
)


@pytest.fixture
def mem(tmp_path):
    """Create a StructuralMemory with a temp DB for each test."""
    db_path = tmp_path / "test_memory.db"
    return StructuralMemory(db_path=db_path)


@pytest.fixture
def populated_mem(mem):
    """StructuralMemory pre-populated with entries across all layers."""
    now = datetime.now(timezone.utc)

    mem.store(MemoryEntry(
        layer=MemoryLayer.WORK,
        content={"task": "build API", "status": "in_progress"},
        tags=["api", "dev"],
        source="observer-alpha",
        created_at=now - timedelta(hours=2),
    ))
    mem.store(MemoryEntry(
        layer=MemoryLayer.WORK,
        content={"task": "fix bug #42", "status": "pending"},
        tags=["bug", "urgent"],
        source="observer-beta",
        created_at=now - timedelta(hours=1),
    ))
    mem.store(MemoryEntry(
        layer=MemoryLayer.LEARNED,
        content={"lesson": "Always validate config before start", "impact": "high"},
        tags=["config", "devops"],
        source="observer-alpha",
        created_at=now - timedelta(hours=3),
    ))
    mem.store(MemoryEntry(
        layer=MemoryLayer.LEARNED,
        content={"lesson": "FTS5 MATCH supports boolean operators", "impact": "medium"},
        tags=["search", "sqlite"],
        source="observer-gamma",
        created_at=now - timedelta(minutes=30),
    ))
    mem.store(MemoryEntry(
        layer=MemoryLayer.KNOWLEDGE,
        content={"title": "OCE Architecture", "body": "Three-layer observer mesh with event fabric."},
        tags=["architecture", "oce"],
        source="observer-alpha",
        created_at=now - timedelta(hours=4),
    ))
    mem.store(MemoryEntry(
        layer=MemoryLayer.KNOWLEDGE,
        content={"title": "SRRA-OPH Phases", "body": "9 phases, 77 tests passing."},
        tags=["srrs", "testing"],
        source="observer-beta",
        created_at=now - timedelta(hours=5),
    ))
    return mem


# ─── MemoryEntry Model ────────────────────────────────────────────────────────

class TestMemoryEntry:
    def test_create_default_id(self):
        entry = MemoryEntry(layer=MemoryLayer.WORK, content={"key": "val"})
        assert entry.entry_id is not None
        assert len(entry.entry_id) > 0

    def test_create_with_explicit_id(self):
        entry = MemoryEntry(entry_id="abc-123", layer=MemoryLayer.LEARNED, content={})
        assert entry.entry_id == "abc-123"

    def test_default_tags_empty(self):
        entry = MemoryEntry(layer=MemoryLayer.WORK, content={})
        assert entry.tags == []

    def test_default_source(self):
        entry = MemoryEntry(layer=MemoryLayer.KNOWLEDGE, content={})
        assert entry.source == "unknown"

    def test_timestamps_auto_set(self):
        entry = MemoryEntry(layer=MemoryLayer.WORK, content={})
        assert entry.created_at is not None
        assert entry.updated_at is not None


# ─── Store ────────────────────────────────────────────────────────────────────

class TestStore:
    def test_store_returns_id(self, mem):
        entry = MemoryEntry(layer=MemoryLayer.WORK, content={"a": 1})
        eid = mem.store(entry)
        assert eid == entry.entry_id

    def test_store_and_retrieve(self, mem):
        entry = MemoryEntry(
            layer=MemoryLayer.LEARNED,
            content={"lesson": "test"},
            tags=["test"],
            source="unit-test",
        )
        eid = mem.store(entry)
        results = mem.search(query="test", limit=10)
        assert len(results) == 1
        assert results[0].entry_id == eid

    def test_store_all_layers(self, mem):
        for layer in MemoryLayer:
            entry = MemoryEntry(layer=layer, content={"layer": layer.value})
            eid = mem.store(entry)
            assert eid is not None

    def test_store_overwrites_on_same_id(self, mem):
        entry = MemoryEntry(
            entry_id="fixedid",
            layer=MemoryLayer.WORK,
            content={"v": 1},
        )
        mem.store(entry)
        entry.content = {"v": 2}
        mem.store(entry)
        # Verify no duplicate by checking stats
        stats = mem.get_stats()
        assert stats.total_entries == 1


# ─── Search ───────────────────────────────────────────────────────────────────

class TestSearch:
    def test_search_by_fts_query(self, populated_mem):
        results = populated_mem.search(query="config", limit=10)
        assert len(results) >= 1
        assert any("config" in str(r.content) for r in results)

    def test_search_filter_by_layer(self, populated_mem):
        results = populated_mem.search(query="", layer=MemoryLayer.WORK, limit=10)
        assert all(r.layer == MemoryLayer.WORK for r in results)
        assert len(results) == 2

    def test_search_filter_by_tags(self, populated_mem):
        results = populated_mem.search(query="", tags=["api"], limit=10)
        assert all("api" in r.tags for r in results)

    def test_search_combined_layer_and_tags(self, populated_mem):
        results = populated_mem.search(
            query="", layer=MemoryLayer.LEARNED, tags=["sqlite"], limit=10
        )
        assert len(results) == 1
        assert results[0].layer == MemoryLayer.LEARNED

    def test_search_limit(self, populated_mem):
        results = populated_mem.search(query="", limit=3)
        assert len(results) <= 3

    def test_search_no_results(self, populated_mem):
        results = populated_mem.search(query="zzzznonexistentxxxx", limit=10)
        assert len(results) == 0


# ─── Timeline ─────────────────────────────────────────────────────────────────

class TestTimeline:
    def test_timeline_returns_chronological(self, populated_mem):
        entries = populated_mem.get_timeline("observer-alpha")
        assert len(entries) >= 2
        timestamps = [e.created_at for e in entries]
        assert timestamps == sorted(timestamps)

    def test_timeline_filters_by_observer(self, populated_mem):
        entries = populated_mem.get_timeline("observer-beta")
        assert all(e.source == "observer-beta" for e in entries)

    def test_timeline_with_time_range(self, populated_mem):
        now = datetime.now(timezone.utc)
        entries = populated_mem.get_timeline(
            "observer-alpha",
            start_time=now - timedelta(hours=3),
            end_time=now - timedelta(hours=1),
        )
        for e in entries:
            assert e.created_at >= now - timedelta(hours=3)
            assert e.created_at <= now - timedelta(hours=1)

    def test_timeline_empty_for_unknown_observer(self, populated_mem):
        entries = populated_mem.get_timeline("nonexistent-observer")
        assert entries == []


# ─── Compress ─────────────────────────────────────────────────────────────────

class TestCompress:
    def test_compress_noop_when_under_limit(self, populated_mem):
        removed = populated_mem.compress(MemoryLayer.WORK, max_entries=100)
        assert removed == 0

    def test_compress_removes_oldest(self, mem):
        now = datetime.now(timezone.utc)
        for i in range(5):
            mem.store(MemoryEntry(
                layer=MemoryLayer.WORK,
                content={"idx": i},
                created_at=now - timedelta(hours=5 - i),
            ))
        removed = mem.compress(MemoryLayer.WORK, max_entries=3)
        assert removed == 2
        stats = mem.get_stats()
        assert stats.work_count == 3

    def test_compress_only_affects_target_layer(self, mem):
        now = datetime.now(timezone.utc)
        for i in range(5):
            mem.store(MemoryEntry(layer=MemoryLayer.WORK, content={"i": i}, created_at=now - timedelta(hours=5 - i)))
            mem.store(MemoryEntry(layer=MemoryLayer.LEARNED, content={"i": i}, created_at=now - timedelta(hours=5 - i)))
        mem.compress(MemoryLayer.WORK, max_entries=2)
        stats = mem.get_stats()
        assert stats.work_count == 2
        assert stats.learned_count == 5


# ─── Export Wiki ──────────────────────────────────────────────────────────────

class TestExportWiki:
    def test_export_returns_markdown(self, populated_mem):
        md = populated_mem.export_wiki()
        assert "# OCE Knowledge Wiki" in md
        assert "OCE Architecture" in md

    def test_export_only_knowledge_layer(self, populated_mem):
        md = populated_mem.export_wiki()
        # WORK/LEARNED entries should not appear
        assert "build API" not in md
        assert "Always validate config" not in md

    def test_export_writes_file(self, populated_mem, tmp_path):
        out = tmp_path / "wiki.md"
        populated_mem.export_wiki(path=out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# OCE Knowledge Wiki" in content

    def test_export_empty_knowledge(self, mem):
        mem.store(MemoryEntry(layer=MemoryLayer.WORK, content={"a": 1}))
        md = mem.export_wiki()
        assert "**0 entries**" in md


# ─── Stats ────────────────────────────────────────────────────────────────────

class TestStats:
    def test_stats_counts(self, populated_mem):
        stats = populated_mem.get_stats()
        assert stats.total_entries == 6
        assert stats.work_count == 2
        assert stats.learned_count == 2
        assert stats.knowledge_count == 2

    def test_stats_oldest_newest(self, populated_mem):
        stats = populated_mem.get_stats()
        assert stats.oldest_entry is not None
        assert stats.newest_entry is not None

    def test_stats_db_size(self, populated_mem):
        stats = populated_mem.get_stats()
        assert stats.db_size_bytes > 0

    def test_stats_empty_db(self, mem):
        stats = mem.get_stats()
        assert stats.total_entries == 0
        assert stats.oldest_entry is None
        assert stats.newest_entry is None
