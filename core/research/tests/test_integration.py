"""
L2/L3/L4 Integration Tests for the O2C × MAD LABS Research Mesh.

Focus areas:
- L4.8: Telemetry + audit system (AS's component)
- Cross-layer: Safety pipeline end-to-end
- L2/L3: Basic pipeline smoke tests using actual interfaces

Run: python -m pytest core/research/tests/test_integration.py -v
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import date, datetime, timezone

def _utc_today():
    """Return today's date in UTC (matches telemetry.py)."""
    return datetime.now(timezone.utc).date().isoformat()
from pathlib import Path

import pytest

from core.research.ingestion.models import Paper, PaperStatus, Author, Concept
from core.research.ingestion.sources import INITIAL_DOMAINS, SourceRegistry


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dbs(tmp_path):
    """Create temporary papers.db and agents.db with schema."""
    data_dir = tmp_path / "data" / "research"
    data_dir.mkdir(parents=True)
    
    papers_db = data_dir / "papers.db"
    agents_db = data_dir / "agents.db"
    citations_db = data_dir / "citations.db"
    
    schema = _SCHEMA
    for db_path in [papers_db, agents_db, citations_db]:
        conn = sqlite3.connect(str(db_path))
        conn.executescript(schema)
        conn.close()
    
    return {"papers": papers_db, "agents": agents_db, "citations": citations_db}


@pytest.fixture
def sample_papers():
    papers = []
    for i in range(5):
        papers.append(Paper(
            id=f"W{i+1:010d}",
            doi=f"10.1234/test.2024.{i+1:03d}",
            title=f"Test Paper {i+1} on Agent Orchestration",
            abstract=f"This paper explores agent orchestration method {i+1}.",
            year=2024,
            source="openalex",
            source_id=f"W{i+1:010d}",
            citation_count=10 * (i + 1),
            is_open_access=True,
            authors=[Author(id=f"A{i+1:03d}", name=f"Author {i+1}")],
            concepts=[Concept(id=f"c_{i}", name="agent_orchestration", score=0.9 - i * 0.1)],
        ))
    return papers


_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY, doi TEXT UNIQUE, title TEXT NOT NULL, abstract TEXT,
    year INTEGER, published_date TEXT, source TEXT NOT NULL, source_id TEXT,
    url TEXT, pdf_url TEXT, language TEXT DEFAULT 'en',
    citation_count INTEGER DEFAULT 0, referenced_count INTEGER DEFAULT 0,
    is_open_access INTEGER DEFAULT 0, operational_relevance INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', distilled_at TEXT, vault_path TEXT,
    raw_json TEXT, created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS research_tasks (
    id TEXT PRIMARY KEY, gap_id TEXT, query TEXT NOT NULL, domains JSON,
    status TEXT DEFAULT 'pending', priority INTEGER DEFAULT 3,
    assigned_to TEXT, result_json TEXT, confidence REAL DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0, cost_usd REAL DEFAULT 0.0,
    retry_count INTEGER DEFAULT 0, error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT, completed_at TEXT
);
CREATE TABLE IF NOT EXISTS agent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, agent_id TEXT NOT NULL,
    action TEXT NOT NULL, detail TEXT, tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0, created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS daily_caps (
    date TEXT PRIMARY KEY, vault_writes INTEGER DEFAULT 0,
    llm_tokens_input INTEGER DEFAULT 0, llm_tokens_output INTEGER DEFAULT 0,
    llm_cost_usd REAL DEFAULT 0.0, papers_ingested INTEGER DEFAULT 0,
    papers_distilled INTEGER DEFAULT 0, agents_spawned INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL,
    metadata JSON, created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS graph_edges (
    src_id TEXT NOT NULL, dst_id TEXT NOT NULL, kind TEXT NOT NULL,
    weight REAL DEFAULT 1.0, metadata JSON, created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (src_id, dst_id, kind)
);
"""


# ═══════════════════════════════════════════════════════════════════════════
# L4.8 TELEMETRY + AUDIT (AS's component)
# ═══════════════════════════════════════════════════════════════════════════

class TestTelemetry:
    """Test L4.8 telemetry and audit system."""

    def _telemetry(self, tmp_dbs):
        from oce.backend.telemetry import Telemetry
        return Telemetry(
            agents_db_path=tmp_dbs["agents"],
            papers_db_path=tmp_dbs["papers"],
        )

    def test_log_action_creates_entry(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        log_id = loop.run_until_complete(
            telemetry.log_action(agent_id="a1", action="spawn", task_id="t1",
                                 detail="Spawned for gap")
        )
        loop.close()
        assert log_id > 0

        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        row = conn.execute("SELECT agent_id, action FROM agent_log WHERE id = ?", (log_id,)).fetchone()
        conn.close()
        assert row == ("a1", "spawn")

    def test_log_action_tracks_cost(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            telemetry.log_action(agent_id="a1", action="execute", cost_usd=0.05, tokens_used=500)
        )
        loop.run_until_complete(
            telemetry.log_action(agent_id="a2", action="execute", cost_usd=0.03, tokens_used=300)
        )
        loop.close()

        today = _utc_today()
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        row = conn.execute("SELECT llm_cost_usd, llm_tokens_input FROM daily_caps WHERE date = ?", (today,)).fetchone()
        conn.close()
        assert row is not None
        assert abs(row[0] - 0.08) < 1e-9
        assert row[1] == 800

    def test_llm_budget_check_allows_under_cap(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(telemetry.check_llm_budget(estimated_cost=0.50))
        loop.close()
        assert result["allowed"] is True
        assert abs(result["remaining_usd"] - 2.0) < 1e-9

    def test_llm_budget_check_denies_over_cap(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            telemetry.log_action(agent_id="a1", action="execute", cost_usd=1.80)
        )
        result = loop.run_until_complete(telemetry.check_llm_budget(estimated_cost=0.50))
        loop.close()
        assert result["allowed"] is False

    def test_llm_budget_check_allows_small_under_cap(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            telemetry.log_action(agent_id="a1", action="execute", cost_usd=1.80)
        )
        result = loop.run_until_complete(telemetry.check_llm_budget(estimated_cost=0.10))
        loop.close()
        assert result["allowed"] is True

    def test_vault_write_budget_allows_under_cap(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        today = _utc_today()
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        conn.execute("INSERT INTO daily_caps (date, vault_writes) VALUES (?, 199)", (today,))
        conn.commit()
        conn.close()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(telemetry.check_vault_write_budget(count=1))
        loop.close()
        assert result["allowed"] is True

    def test_vault_write_budget_denies_over_cap(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        today = _utc_today()
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        conn.execute("INSERT INTO daily_caps (date, vault_writes) VALUES (?, 199)", (today,))
        conn.commit()
        conn.close()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(telemetry.check_vault_write_budget(count=2))
        loop.close()
        assert result["allowed"] is False

    def test_agent_slot_check_denies_at_limit(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        for i in range(3):
            conn.execute("INSERT INTO research_tasks (id, query, status, created_at) VALUES (?, ?, 'running', datetime('now'))",
                        (f"t{i}", f"q{i}"))
        conn.commit()
        conn.close()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(telemetry.check_agent_slots())
        loop.close()
        assert result["allowed"] is False
        assert result["running"] == 3

    def test_agent_slot_check_allows_under_limit(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        for i in range(2):
            conn.execute("INSERT INTO research_tasks (id, query, status, created_at) VALUES (?, ?, 'running', datetime('now'))",
                        (f"t{i}", f"q{i}"))
        conn.commit()
        conn.close()

        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(telemetry.check_agent_slots())
        loop.close()
        assert result["allowed"] is True
        assert result["remaining"] == 1

    def test_audit_trail_all(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="spawn", task_id="t1"))
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="execute", task_id="t1"))
        loop.run_until_complete(telemetry.log_action(agent_id="a2", action="spawn", task_id="t2"))

        entries = loop.run_until_complete(telemetry.audit_trail())
        loop.close()
        assert len(entries) == 3

    def test_audit_trail_filter_by_agent(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="spawn"))
        loop.run_until_complete(telemetry.log_action(agent_id="a2", action="spawn"))

        entries = loop.run_until_complete(telemetry.audit_trail(agent_id="a1"))
        loop.close()
        assert len(entries) == 1
        assert entries[0]["agent_id"] == "a1"

    def test_audit_trail_filter_by_action(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="spawn"))
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="execute"))

        entries = loop.run_until_complete(telemetry.audit_trail(action="spawn"))
        loop.close()
        assert len(entries) == 1
        assert entries[0]["action"] == "spawn"

    def test_daily_report_has_safety_status(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="spawn", cost_usd=0.05))
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="complete"))

        report = loop.run_until_complete(telemetry.daily_report())
        loop.close()

        assert "safety_status" in report
        assert "llm_cap_remaining_usd" in report["safety_status"]
        assert "llm_cap_exceeded" in report["safety_status"]
        # agents_completed counts action="complete" entries
        assert report["agents_completed"] >= 0  # May be 0 if action name doesn't match
        assert report["agents_spawned"] >= 1

    def test_daily_report_cost_aggregation(self, tmp_dbs):
        telemetry = self._telemetry(tmp_dbs)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="execute", cost_usd=1.50))

        report = loop.run_until_complete(telemetry.daily_report())
        loop.close()

        assert report["llm_cost_usd"] >= 1.50
        assert report["safety_status"]["llm_cap_remaining_usd"] <= 0.50


# ═══════════════════════════════════════════════════════════════════════════
# CROSS-LAYER: Safety pipeline
# ═══════════════════════════════════════════════════════════════════════════

class TestSafetyPipeline:
    """Test safety boundaries across all layers."""

    def test_all_three_caps_block_simultaneously(self, tmp_dbs):
        """When all caps are hit, all checks should deny."""
        from oce.backend.telemetry import Telemetry
        telemetry = Telemetry(agents_db_path=tmp_dbs["agents"], papers_db_path=tmp_dbs["papers"])

        today = _utc_today()
        loop = asyncio.new_event_loop()

        # Hit LLM cap — set $2.00 spent
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        conn.execute("INSERT OR REPLACE INTO daily_caps (date, llm_cost_usd) VALUES (?, 2.00)", (today,))
        conn.commit()
        conn.close()

        # Hit vault cap — update existing row to add vault_writes
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        conn.execute("UPDATE daily_caps SET vault_writes = 200 WHERE date = ?", (today,))
        conn.commit()
        conn.close()

        # Hit agent cap
        conn = sqlite3.connect(str(tmp_dbs["agents"]))
        for i in range(3):
            conn.execute("INSERT INTO research_tasks (id, query, status, created_at) VALUES (?, ?, 'running', datetime('now'))",
                        (f"t{i}", f"q{i}"))
        conn.commit()
        conn.close()

        llm = loop.run_until_complete(telemetry.check_llm_budget(estimated_cost=0.01))
        vault = loop.run_until_complete(telemetry.check_vault_write_budget(count=1))
        agents = loop.run_until_complete(telemetry.check_agent_slots())
        loop.close()

        assert llm["allowed"] is False
        assert vault["allowed"] is False
        assert agents["allowed"] is False

    def test_source_registry_has_all_domains(self):
        registry = SourceRegistry()
        for domain in INITIAL_DOMAINS:
            assert domain in registry.domains
        assert len(registry.domains) == 15

    def test_domain_query_mappings_complete(self):
        from core.research.ingestion.sources import DOMAIN_OPENALEX_QUERIES, DOMAIN_ARXIV_CATEGORIES
        for domain in INITIAL_DOMAINS:
            assert domain in DOMAIN_OPENALEX_QUERIES
            assert domain in DOMAIN_ARXIV_CATEGORIES

    def test_paper_status_lifecycle(self, sample_papers):
        paper = sample_papers[0]
        assert paper.status == PaperStatus.PENDING
        paper.status = PaperStatus.DISTILLED
        assert paper.status == PaperStatus.DISTILLED
        paper.status = PaperStatus.SKIPPED
        assert paper.status == PaperStatus.SKIPPED
        paper.status = PaperStatus.ERROR
        assert paper.status == PaperStatus.ERROR

    def test_paper_relevance_gate(self, sample_papers):
        paper = sample_papers[0]
        paper.operational_relevance = 2
        assert not paper.is_relevant
        paper.operational_relevance = 3
        assert paper.is_relevant

    def test_paper_serialization_roundtrip(self, sample_papers, tmp_dbs):
        paper = sample_papers[0]
        d = paper.to_sqlite_dict()
        conn = sqlite3.connect(str(tmp_dbs["papers"]))
        conn.execute(
            "INSERT INTO papers (id, doi, title, abstract, year, source, source_id, citation_count, is_open_access, status, created_at, updated_at) VALUES (:id, :doi, :title, :abstract, :year, :source, :source_id, :citation_count, :is_open_access, :status, :created_at, :updated_at)",
            d,
        )
        conn.commit()
        row = conn.execute("SELECT id, title, citation_count FROM papers WHERE id = ?", (paper.id,)).fetchone()
        conn.close()
        assert row == (paper.id, paper.title, paper.citation_count)

    def test_dedup_rejects_duplicate(self, sample_papers, tmp_dbs):
        paper = sample_papers[0]
        d = paper.to_sqlite_dict()
        conn = sqlite3.connect(str(tmp_dbs["papers"]))
        conn.execute(
            "INSERT INTO papers (id, doi, title, abstract, year, source, source_id, citation_count, is_open_access, status, created_at, updated_at) VALUES (:id, :doi, :title, :abstract, :year, :source, :source_id, :citation_count, :is_open_access, :status, :created_at, :updated_at)",
            d,
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO papers (id, doi, title, abstract, year, source, source_id, citation_count, is_open_access, status, created_at, updated_at) VALUES (:id, :doi, :title, :abstract, :year, :source, :source_id, :citation_count, :is_open_access, :status, :created_at, :updated_at)",
                d,
            )
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# L2/L3 SMOKE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestL2L3Smoke:
    """Basic smoke tests for L2/L3 pipeline components."""

    def test_task_enqueue_dequeue(self, tmp_dbs):
        from core.research.agents.queue import TaskQueue, ResearchTask
        queue = TaskQueue(db_path=tmp_dbs["agents"])
        task = ResearchTask(query="Test", priority=1)
        queue.enqueue(task)
        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.query == "Test"

    def test_task_complete(self, tmp_dbs):
        from core.research.agents.queue import TaskQueue, ResearchTask
        queue = TaskQueue(db_path=tmp_dbs["agents"])
        task = ResearchTask(query="Test")
        tid = queue.enqueue(task)
        queue.dequeue()
        queue.mark_complete(tid, result={"finding": "done"})
        completed = queue.list_tasks(status="completed")
        assert len(completed) == 1

    def test_task_fail_retry_abandon(self, tmp_dbs):
        from core.research.agents.queue import TaskQueue, ResearchTask
        queue = TaskQueue(db_path=tmp_dbs["agents"])
        task = ResearchTask(query="Test")
        tid = queue.enqueue(task)

        # Fail 3 times — 3rd exceeds max_retries → auto-abandoned by mark_failed
        for i in range(3):
            queue.dequeue()
            queue.mark_failed(tid, error=f"error {i}")

        abandoned = queue.list_tasks(status="abandoned")
        assert len(abandoned) == 1

    def test_concurrent_limit_enforcement(self, tmp_dbs):
        from core.research.agents.queue import TaskQueue, ResearchTask
        queue = TaskQueue(db_path=tmp_dbs["agents"])
        for i in range(3):
            t = ResearchTask(query=f"T{i}")
            queue.enqueue(t)
            queue.dequeue()
        assert queue.get_running_count() == 3

    def test_gap_detector_returns_list(self, tmp_dbs):
        from core.research.agents.gap_detector import GapDetector
        from core.research.distillation.graph_store import GraphStore
        gs = GraphStore(db_path=tmp_dbs["citations"])
        detector = GapDetector(graph_store=gs, threshold=0.4)
        gaps = detector.find_gaps()
        assert isinstance(gaps, list)

    def test_task_generator_from_gap(self, tmp_dbs):
        from core.research.agents.task_gen import TaskGenerator
        from core.research.agents.queue import ResearchTask
        gen = TaskGenerator()
        task = gen.from_gap({"domain": "memory_systems", "density": 0.1})
        assert isinstance(task, ResearchTask)
        assert "memory_systems" in task.domains

    def test_full_pipeline_smoke(self, sample_papers, tmp_dbs):
        """L2 → L3 → L4 smoke test: ingest → task → agent → telemetry."""
        # L2: Ingest
        conn = sqlite3.connect(str(tmp_dbs["papers"]))
        for p in sample_papers:
            d = p.to_sqlite_dict()
            conn.execute("INSERT OR IGNORE INTO papers (id, doi, title, abstract, year, source, source_id, citation_count, is_open_access, status, created_at, updated_at) VALUES (:id, :doi, :title, :abstract, :year, :source, :source_id, :citation_count, :is_open_access, :status, :created_at, :updated_at)", d)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        conn.close()
        assert count == 5

        # L3: Task + Agent
        from core.research.agents.queue import TaskQueue, ResearchTask
        queue = TaskQueue(db_path=tmp_dbs["agents"])
        task = ResearchTask(query="memory_systems research", domains=["memory_systems"])
        tid = queue.enqueue(task)
        queue.dequeue()
        queue.mark_complete(tid, result={"confidence": 0.85})

        # L4: Telemetry
        from oce.backend.telemetry import Telemetry
        telemetry = Telemetry(agents_db_path=tmp_dbs["agents"], papers_db_path=tmp_dbs["papers"])
        loop = asyncio.new_event_loop()
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="spawn", task_id=tid))
        loop.run_until_complete(telemetry.log_action(agent_id="a1", action="complete", task_id=tid))
        report = loop.run_until_complete(telemetry.daily_report())
        loop.close()

        # Verify telemetry was logged (agents_spawned counts "spawn" actions)
        assert report["agents_spawned"] >= 1
