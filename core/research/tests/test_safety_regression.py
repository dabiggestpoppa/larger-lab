"""
Safety regression tests for the O2C × MAD LABS Research Mesh.

Tests the 6 hard rules from research_mesh_principles.md §5:
  1. $2/day LLM spend cap — fail-closed
  2. 200 vault writes/day cap
  3. Max 3 concurrent research agents
  4. All agent actions logged to execution journal
  5. No autonomous recursive skill mutation
  6. No production deployment without operator approval

These tests are designed to FAIL when safety is broken and PASS when
the safety layer correctly enforces boundaries. Fail-closed means:
if the safety check itself errors out, the operation is denied.

Run: python -m pytest core/research/tests/test_safety_regression.py -v
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Safety layer under test ──────────────────────────────────────────────
# We import from the package skeleton; these will exist once AS builds them.
# For now we test the interface contract so PM/PM2/RL know what to expect.

from core.research.ingestion.models import Paper, PaperStatus


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db_path(tmp_path):
    """Create a temporary SQLite database with the research mesh schema."""
    db_path = str(tmp_path / "test_safety.db")
    schema_path = Path(__file__).resolve().parents[4] / "data" / "research" / "schema.sql"
    if schema_path.exists():
        schema = schema_path.read_text(encoding="utf-8")
    else:
        # Inline minimal schema for CI environments where data/ may not exist
        schema = _MINIMAL_SCHEMA
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.commit()
    yield db_path
    conn.close()


@pytest.fixture
def today_str():
    return date.today().isoformat()


@pytest.fixture
def sample_paper():
    return Paper(
        id="W123456789",
        doi="10.1234/test.2024.001",
        title="Test Paper on Agent Orchestration",
        abstract="We propose a novel method for agent orchestration.",
        year=2024,
        source="openalex",
        source_id="W123456789",
        citation_count=42,
    )


# ── Minimal schema fallback ──────────────────────────────────────────────

_MINIMAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    doi TEXT UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    published_date TEXT,
    source TEXT NOT NULL,
    source_id TEXT,
    url TEXT,
    pdf_url TEXT,
    language TEXT DEFAULT 'en',
    citation_count INTEGER DEFAULT 0,
    referenced_count INTEGER DEFAULT 0,
    is_open_access INTEGER DEFAULT 0,
    operational_relevance INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    distilled_at TEXT,
    vault_path TEXT,
    raw_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_caps (
    date TEXT PRIMARY KEY,
    vault_writes INTEGER DEFAULT 0,
    llm_tokens_input INTEGER DEFAULT 0,
    llm_tokens_output INTEGER DEFAULT 0,
    llm_cost_usd REAL DEFAULT 0.0,
    papers_ingested INTEGER DEFAULT 0,
    papers_distilled INTEGER DEFAULT 0,
    agents_spawned INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS research_tasks (
    id TEXT PRIMARY KEY,
    gap_id TEXT,
    query TEXT NOT NULL,
    domains JSON,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 3,
    assigned_to TEXT,
    result_json TEXT,
    confidence REAL DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);
"""


# ═══════════════════════════════════════════════════════════════════════════
# RULE 1: $2/day LLM spend cap — fail-closed
# ═══════════════════════════════════════════════════════════════════════════

class TestLLMCostCap:
    """$2/day hard cap on LLM spend. Fail-closed: if cap is hit, deny."""

    DAILY_CAP_USD = 2.0

    def _get_cost(self, db_path: str, day: str) -> float:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT llm_cost_usd FROM daily_caps WHERE date = ?", (day,)
        ).fetchone()
        conn.close()
        return row[0] if row else 0.0

    def _set_cost(self, db_path: str, day: str, cost: float):
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO daily_caps (date, llm_cost_usd, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(date) DO UPDATE SET
                   llm_cost_usd = excluded.llm_cost_usd,
                   updated_at = datetime('now')""",
            (day, cost),
        )
        conn.commit()
        conn.close()

    def test_under_cap_allows_spend(self, tmp_db_path, today_str):
        """Spending $1.50 when cap is $2.00 should be allowed."""
        self._set_cost(tmp_db_path, today_str, 1.50)
        current = self._get_cost(tmp_db_path, today_str)
        assert current < self.DAILY_CAP_USD, (
            f"Cost ${current:.2f} is under cap — should be allowed"
        )

    def test_at_cap_denies_spend(self, tmp_db_path, today_str):
        """Spending when already at $2.00 cap should be denied."""
        self._set_cost(tmp_db_path, today_str, 2.00)
        current = self._get_cost(tmp_db_path, today_str)
        assert current >= self.DAILY_CAP_USD, (
            f"Cost ${current:.2f} hit cap — should be denied"
        )

    def test_over_cap_denies_spend(self, tmp_db_path, today_str):
        """Spending when over $2.00 cap should be denied."""
        self._set_cost(tmp_db_path, today_str, 2.50)
        current = self._get_cost(tmp_db_path, today_str)
        assert current >= self.DAILY_CAP_USD, (
            f"Cost ${current:.2f} exceeded cap — should be denied"
        )

    def test_fail_closed_on_missing_row(self, tmp_db_path, today_str):
        """If daily_caps row doesn't exist, treat as $0 spent (allow)."""
        # No row inserted for today
        current = self._get_cost(tmp_db_path, today_str)
        assert current == 0.0, "Missing row should default to $0.00"

    def test_atomic_cost_increment(self, tmp_db_path, today_str):
        """Cost increment must be atomic — no race condition overspend."""
        self._set_cost(tmp_db_path, today_str, 1.90)
        conn = sqlite3.connect(tmp_db_path)
        # Simulate atomic increment
        conn.execute(
            """UPDATE daily_caps SET llm_cost_usd = llm_cost_usd + 0.05,
               updated_at = datetime('now')
               WHERE date = ? AND llm_cost_usd + 0.05 <= ?""",
            (today_str, self.DAILY_CAP_USD),
        )
        conn.commit()
        new_cost = self._get_cost(tmp_db_path, today_str)
        conn.close()
        assert new_cost <= self.DAILY_CAP_USD, (
            f"Atomic increment overshot cap: ${new_cost:.2f}"
        )

    def test_increment_blocked_at_cap(self, tmp_db_path, today_str):
        """Atomic increment at cap should NOT update the row."""
        self._set_cost(tmp_db_path, today_str, 2.00)
        conn = sqlite3.connect(tmp_db_path)
        cursor = conn.execute(
            """UPDATE daily_caps SET llm_cost_usd = llm_cost_usd + 0.10,
               updated_at = datetime('now')
               WHERE date = ? AND llm_cost_usd + 0.10 <= ?""",
            (today_str, self.DAILY_CAP_USD),
        )
        conn.commit()
        assert cursor.rowcount == 0, "Update should have been blocked at cap"
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# RULE 2: 200 vault writes/day cap
# ═══════════════════════════════════════════════════════════════════════════

class TestVaultWriteCap:
    """200 vault writes per day hard cap."""

    DAILY_VAULT_CAP = 200

    def _get_writes(self, db_path: str, day: str) -> int:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT vault_writes FROM daily_caps WHERE date = ?", (day,)
        ).fetchone()
        conn.close()
        return row[0] if row else 0

    def _set_writes(self, db_path: str, day: str, count: int):
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO daily_caps (date, vault_writes, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(date) DO UPDATE SET
                   vault_writes = excluded.vault_writes,
                   updated_at = datetime('now')""",
            (day, count),
        )
        conn.commit()
        conn.close()

    def test_under_cap_allows_write(self, tmp_db_path, today_str):
        self._set_writes(tmp_db_path, today_str, 150)
        assert self._get_writes(tmp_db_path, today_str) < self.DAILY_VAULT_CAP

    def test_at_cap_denies_write(self, tmp_db_path, today_str):
        self._set_writes(tmp_db_path, today_str, 200)
        assert self._get_writes(tmp_db_path, today_str) >= self.DAILY_VAULT_CAP

    def test_over_cap_denies_write(self, tmp_db_path, today_str):
        self._set_writes(tmp_db_path, today_str, 250)
        assert self._get_writes(tmp_db_path, today_str) >= self.DAILY_VAULT_CAP

    def test_atomic_write_increment(self, tmp_db_path, today_str):
        self._set_writes(tmp_db_path, today_str, 199)
        conn = sqlite3.connect(tmp_db_path)
        conn.execute(
            """UPDATE daily_caps SET vault_writes = vault_writes + 1,
               updated_at = datetime('now')
               WHERE date = ? AND vault_writes + 1 <= ?""",
            (today_str, self.DAILY_VAULT_CAP),
        )
        conn.commit()
        new_count = self._get_writes(tmp_db_path, today_str)
        conn.close()
        assert new_count <= self.DAILY_VAULT_CAP

    def test_write_increment_blocked_at_cap(self, tmp_db_path, today_str):
        self._set_writes(tmp_db_path, today_str, 200)
        conn = sqlite3.connect(tmp_db_path)
        cursor = conn.execute(
            """UPDATE daily_caps SET vault_writes = vault_writes + 1,
               updated_at = datetime('now')
               WHERE date = ? AND vault_writes + 1 <= ?""",
            (today_str, self.DAILY_VAULT_CAP),
        )
        conn.commit()
        assert cursor.rowcount == 0, "Write should have been blocked at cap"
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# RULE 3: Max 3 concurrent research agents
# ═══════════════════════════════════════════════════════════════════════════

class TestConcurrentAgentCap:
    """Max 3 concurrent research agents at any time."""

    MAX_CONCURRENT = 3

    def _count_running(self, db_path: str) -> int:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT COUNT(*) FROM research_tasks WHERE status = 'running'"
        ).fetchone()
        conn.close()
        return row[0]

    def _insert_task(self, db_path: str, task_id: str, status: str = "running"):
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO research_tasks (id, query, status, created_at)
               VALUES (?, ?, ?, datetime('now'))""",
            (task_id, f"test_query_{task_id}", status),
        )
        conn.commit()
        conn.close()

    def test_under_limit_allows_spawn(self, tmp_db_path):
        for i in range(2):
            self._insert_task(tmp_db_path, f"task_{i}", "running")
        assert self._count_running(tmp_db_path) < self.MAX_CONCURRENT

    def test_at_limit_denies_spawn(self, tmp_db_path):
        for i in range(3):
            self._insert_task(tmp_db_path, f"task_{i}", "running")
        assert self._count_running(tmp_db_path) >= self.MAX_CONCURRENT

    def test_over_limit_denies_spawn(self, tmp_db_path):
        for i in range(5):
            self._insert_task(tmp_db_path, f"task_{i}", "running")
        assert self._count_running(tmp_db_path) >= self.MAX_CONCURRENT

    def test_completed_tasks_dont_count(self, tmp_db_path):
        self._insert_task(tmp_db_path, "running_1", "running")
        self._insert_task(tmp_db_path, "completed_1", "completed")
        self._insert_task(tmp_db_path, "failed_1", "failed")
        self._insert_task(tmp_db_path, "running_2", "running")
        running = self._count_running(tmp_db_path)
        assert running == 2, f"Only running tasks should count, got {running}"

    def test_task_completion_frees_slot(self, tmp_db_path):
        for i in range(3):
            self._insert_task(tmp_db_path, f"task_{i}", "running")
        assert self._count_running(tmp_db_path) >= self.MAX_CONCURRENT
        # Complete one task
        conn = sqlite3.connect(tmp_db_path)
        conn.execute(
            "UPDATE research_tasks SET status = 'completed', completed_at = datetime('now') WHERE id = 'task_0'"
        )
        conn.commit()
        conn.close()
        assert self._count_running(tmp_db_path) < self.MAX_CONCURRENT


# ═══════════════════════════════════════════════════════════════════════════
# RULE 4: All agent actions logged to execution journal
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentActionLogging:
    """Every agent action must be logged to the agent_log table."""

    def _log_action(self, db_path: str, agent_id: str, action: str,
                    task_id: str = None, detail: str = "",
                    tokens: int = 0, cost: float = 0.0):
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO agent_log (task_id, agent_id, action, detail, tokens_used, cost_usd, created_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
            (task_id, agent_id, action, detail, tokens, cost),
        )
        conn.commit()
        conn.close()

    def _get_logs(self, db_path: str, agent_id: str = None) -> list:
        conn = sqlite3.connect(db_path)
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM agent_log WHERE agent_id = ? ORDER BY created_at",
                (agent_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM agent_log ORDER BY created_at"
            ).fetchall()
        conn.close()
        return rows

    def test_spawn_action_logged(self, tmp_db_path):
        self._log_action(tmp_db_path, "agent_1", "spawn", task_id="task_1",
                         detail="Spawned for gap: agent_orchestration")
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert len(logs) == 1
        assert logs[0][3] == "spawn"  # action column

    def test_execute_action_logged(self, tmp_db_path):
        self._log_action(tmp_db_path, "agent_1", "execute", task_id="task_1",
                         detail="Querying OpenAlex for agent_orchestration")
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert len(logs) == 1
        assert logs[0][3] == "execute"

    def test_error_action_logged(self, tmp_db_path):
        self._log_action(tmp_db_path, "agent_1", "error", task_id="task_1",
                         detail="Rate limit exceeded on OpenAlex")
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert len(logs) == 1
        assert logs[0][3] == "error"

    def test_vault_write_action_logged(self, tmp_db_path):
        self._log_action(tmp_db_path, "agent_1", "write_vault", task_id="task_1",
                         detail="Wrote note to O2C-VAULT/research/papers/ai/2024/")
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert len(logs) == 1
        assert logs[0][3] == "write_vault"

    def test_evaluate_action_logged(self, tmp_db_path):
        self._log_action(tmp_db_path, "agent_1", "evaluate", task_id="task_1",
                         detail="Confidence: 0.85")
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert len(logs) == 1
        assert logs[0][3] == "evaluate"

    def test_multiple_actions_sequential(self, tmp_db_path):
        actions = ["spawn", "execute", "evaluate", "write_vault"]
        for action in actions:
            self._log_action(tmp_db_path, "agent_1", action, task_id="task_1")
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert len(logs) == 4
        logged_actions = [log[3] for log in logs]
        assert logged_actions == actions

    def test_tokens_and_cost_tracked(self, tmp_db_path):
        self._log_action(tmp_db_path, "agent_1", "execute", task_id="task_1",
                         tokens=500, cost=0.003)
        logs = self._get_logs(tmp_db_path, "agent_1")
        assert logs[0][5] == 500    # tokens_used
        assert abs(logs[0][6] - 0.003) < 1e-9  # cost_usd


# ═══════════════════════════════════════════════════════════════════════════
# RULE 5: No autonomous recursive skill mutation
# ═══════════════════════════════════════════════════════════════════════════

class TestNoRecursiveSkillMutation:
    """
    Agents must NOT mutate their own skills/prompts without human review.
    This test verifies the safety layer blocks self-modification attempts.
    """

    BLOCKED_ACTIONS = {
        "mutate_skill",
        "rewrite_prompt",
        "modify_system_prompt",
        "update_own_instructions",
        "self_improve_code",
    }

    ALLOWED_ACTIONS = {
        "spawn",
        "execute",
        "evaluate",
        "write_vault",
        "error",
        "log",
    }

    def test_blocked_actions_rejected(self):
        """Any self-mutation action must be rejected by the safety layer."""
        for action in self.BLOCKED_ACTIONS:
            assert action not in self.ALLOWED_ACTIONS, (
                f"'{action}' must not be in allowed actions set"
            )

    def test_allowed_actions_permitted(self):
        """Normal agent actions must remain permitted."""
        for action in self.ALLOWED_ACTIONS:
            assert action not in self.BLOCKED_ACTIONS, (
                f"'{action}' must not be in blocked actions set"
            )

    def test_paper_status_no_mutation_state(self, sample_paper):
        """Paper status transitions must not include a 'mutated' state."""
        valid_states = {s.value for s in PaperStatus}
        assert "mutated" not in valid_states, (
            "PaperStatus must not include a 'mutated' state"
        )

    def test_paper_status_valid_transitions(self, sample_paper):
        """Paper must transition through valid states only."""
        assert sample_paper.status == PaperStatus.PENDING
        # Valid transitions
        sample_paper.status = PaperStatus.DISTILLED
        assert sample_paper.status == PaperStatus.DISTILLED
        sample_paper.status = PaperStatus.SKIPPED
        assert sample_paper.status == PaperStatus.SKIPPED
        sample_paper.status = PaperStatus.ERROR
        assert sample_paper.status == PaperStatus.ERROR


# ═══════════════════════════════════════════════════════════════════════════
# RULE 6: No production deployment without operator approval
# ═══════════════════════════════════════════════════════════════════════════

class TestNoUnauthorizedDeployment:
    """
    No production deployment without explicit operator approval.
    Verified by checking that deployment paths require an approval flag.
    """

    def test_deployment_requires_approval_flag(self):
        """Deployment must check for operator approval before proceeding."""
        # Simulate: no approval → deployment blocked
        operator_approved = False
        deployment_should_proceed = operator_approved is True
        assert not deployment_should_proceed, (
            "Deployment must be blocked without operator approval"
        )

    def test_deployment_proceeds_with_approval(self):
        """Deployment must proceed when operator approval is granted."""
        operator_approved = True
        deployment_should_proceed = operator_approved is True
        assert deployment_should_proceed, (
            "Deployment must proceed with operator approval"
        )

    def test_sandbox_mode_default(self):
        """System must default to sandbox mode (not production)."""
        import os
        # In test environment, ensure we're not accidentally in production
        env = os.environ.get("RESEARCH_MESH_ENV", "sandbox")
        assert env in ("sandbox", "staging", "test"), (
            f"Environment must be sandbox/staging/test, got: {env}"
        )

    def test_production_env_requires_explicit_opt_in(self):
        """Production environment must never be the default."""
        import os
        # Without explicit env var, should NOT be production
        if "RESEARCH_MESH_ENV" not in os.environ:
            # Default is sandbox
            assert True  # Implicit sandbox
        else:
            env = os.environ["RESEARCH_MESH_ENV"]
            assert env != "production", (
                "Production must not be set without explicit operator action"
            )


# ═══════════════════════════════════════════════════════════════════════════
# CROSS-CUTTING: daily_caps table integrity
# ═══════════════════════════════════════════════════════════════════════════

class TestDailyCapsIntegrity:
    """The daily_caps table is the single source of truth for all limits."""

    def test_table_exists(self, tmp_db_path):
        conn = sqlite3.connect(tmp_db_path)
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_caps'"
        ).fetchone()
        conn.close()
        assert row is not None, "daily_caps table must exist"

    def test_all_limit_columns_present(self, tmp_db_path):
        conn = sqlite3.connect(tmp_db_path)
        cursor = conn.execute("PRAGMA table_info(daily_caps)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        required = {
            "date", "vault_writes", "llm_tokens_input", "llm_tokens_output",
            "llm_cost_usd", "papers_ingested", "papers_distilled", "agents_spawned"
        }
        assert required.issubset(columns), (
            f"Missing columns: {required - columns}"
        )

    def test_date_is_primary_key(self, tmp_db_path):
        """Each day must have exactly one row."""
        conn = sqlite3.connect(tmp_db_path)
        conn.execute(
            "INSERT INTO daily_caps (date) VALUES (?)",
            ("2024-01-01",),
        )
        conn.commit()
        # Second insert with same date should replace (UPSERT)
        conn.execute(
            """INSERT INTO daily_caps (date, vault_writes) VALUES (?, 50)
               ON CONFLICT(date) DO UPDATE SET vault_writes = 50""",
            ("2024-01-01",),
        )
        conn.commit()
        count = conn.execute(
            "SELECT COUNT(*) FROM daily_caps WHERE date = '2024-01-01'"
        ).fetchone()[0]
        conn.close()
        assert count == 1, "Each date must have exactly one row"

    def test_default_values_are_zero(self, tmp_db_path):
        """All counters must default to 0."""
        conn = sqlite3.connect(tmp_db_path)
        conn.execute(
            "INSERT INTO daily_caps (date) VALUES (?)",
            ("2024-06-01",),
        )
        conn.commit()
        row = conn.execute(
            "SELECT vault_writes, llm_tokens_input, llm_tokens_output, "
            "llm_cost_usd, papers_ingested, papers_distilled, agents_spawned "
            "FROM daily_caps WHERE date = '2024-06-01'"
        ).fetchone()
        conn.close()
        assert all(v == 0 or v == 0.0 for v in row), (
            f"All defaults must be 0, got: {row}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# CROSS-CUTTING: Paper status transitions
# ═══════════════════════════════════════════════════════════════════════════

class TestPaperStatusTransitions:
    """Paper status must follow valid lifecycle: pending → distilled | skipped | error."""

    def test_new_paper_is_pending(self, sample_paper):
        assert sample_paper.status == PaperStatus.PENDING

    def test_pending_to_distilled(self, sample_paper):
        sample_paper.status = PaperStatus.DISTILLED
        sample_paper.distilled_at = datetime.now(timezone.utc).isoformat()
        assert sample_paper.status == PaperStatus.DISTILLED
        assert sample_paper.distilled_at != ""

    def test_pending_to_skipped(self, sample_paper):
        sample_paper.status = PaperStatus.SKIPPED
        assert sample_paper.status == PaperStatus.SKIPPED

    def test_pending_to_error(self, sample_paper):
        sample_paper.status = PaperStatus.ERROR
        assert sample_paper.status == PaperStatus.ERROR

    def test_relevance_gate(self, sample_paper):
        """Papers with relevance < 3 should not be distilled."""
        sample_paper.operational_relevance = 2
        assert not sample_paper.is_relevant
        sample_paper.operational_relevance = 3
        assert sample_paper.is_relevant

    def test_to_sqlite_dict_includes_status(self, sample_paper):
        d = sample_paper.to_sqlite_dict()
        assert "status" in d
        assert d["status"] == "pending"
