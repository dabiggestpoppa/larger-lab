"""
L4.8 — Telemetry + Audit for the Research Mesh.

Provides:
- Execution journal: logs every agent action to agent_log table
- Daily reporting: papers ingested, distilled, agents run, $ spent
- Audit export: full trace of any research action
- Wired into research_api.py endpoints

Usage:
    from .telemetry import Telemetry
    telemetry = Telemetry()
    await telemetry.log_action(agent_id="agent_1", action="spawn", task_id="task_1")
    report = await telemetry.daily_report()
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Database paths
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "research"
AGENTS_DB = DATA_DIR / "agents.db"
PAPERS_DB = DATA_DIR / "papers.db"
CITATIONS_DB = DATA_DIR / "citations.db"

# Safety limits (mirror research_mesh_principles.md §5)
DAILY_LLM_CAP_USD = 2.0
DAILY_VAULT_WRITE_CAP = 200
MAX_CONCURRENT_AGENTS = 3


class Telemetry:
    """
    Research mesh telemetry + audit system.
    
    Logs every agent action to the execution journal (agent_log table),
    tracks daily caps, and provides audit export.
    """

    def __init__(
        self,
        agents_db_path: Optional[Path] = None,
        papers_db_path: Optional[Path] = None,
    ):
        self.agents_db_path = agents_db_path or AGENTS_DB
        self.papers_db_path = papers_db_path or PAPERS_DB
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Ensure agent_log and daily_caps tables exist."""
        conn = sqlite3.connect(self.agents_db_path)
        try:
            conn.executescript(_TELEMETRY_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _get_agents_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.agents_db_path)

    def _get_papers_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.papers_db_path)

    # ── Execution Journal ──────────────────────────────────────────────────

    async def log_action(
        self,
        agent_id: str,
        action: str,
        task_id: Optional[str] = None,
        detail: str = "",
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> int:
        """
        Log an agent action to the execution journal.
        
        Returns the log entry ID.
        """
        conn = self._get_agents_conn()
        try:
            cursor = conn.execute(
                """INSERT INTO agent_log (task_id, agent_id, action, detail, tokens_used, cost_usd, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (task_id, agent_id, action, detail, tokens_used, cost_usd),
            )
            conn.commit()
            log_id = cursor.lastrowid

            # Update daily caps for cost/tokens
            if cost_usd > 0 or tokens_used > 0:
                self._increment_daily_cost(conn, cost_usd, tokens_used)

            return log_id
        finally:
            conn.close()

    def _increment_daily_cost(
        self, conn: sqlite3.Connection, cost_usd: float, tokens_used: int
    ) -> None:
        """Atomically increment daily cost/token counters."""
        today = datetime.now(timezone.utc).date().isoformat()
        conn.execute(
            """INSERT INTO daily_caps (date, llm_cost_usd, llm_tokens_input, updated_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(date) DO UPDATE SET
                   llm_cost_usd = llm_cost_usd + excluded.llm_cost_usd,
                   llm_tokens_input = llm_tokens_input + excluded.llm_tokens_input,
                   updated_at = datetime('now')""",
            (today, cost_usd, tokens_used),
        )
        conn.commit()

    # ── Daily Report ───────────────────────────────────────────────────────

    async def daily_report(self, day: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a daily report of research mesh activity.
        
        Args:
            day: ISO date string (YYYY-MM-DD). Defaults to today (UTC).
            
        Returns:
            Dict with papers ingested, distilled, agents run, $ spent, etc.
        """
        target_day = day or datetime.now(timezone.utc).date().isoformat()
        report: Dict[str, Any] = {
            "date": target_day,
            "papers_ingested": 0,
            "papers_distilled": 0,
            "papers_skipped": 0,
            "papers_error": 0,
            "agents_spawned": 0,
            "agents_completed": 0,
            "agents_failed": 0,
            "agents_abandoned": 0,
            "llm_cost_usd": 0.0,
            "llm_tokens_input": 0,
            "llm_tokens_output": 0,
            "vault_writes": 0,
            "graph_nodes_added": 0,
            "graph_edges_added": 0,
            "top_actions": [],
            "errors": [],
        }

        # Papers stats from papers.db
        try:
            papers_conn = self._get_papers_conn()
            # Ingested today
            row = papers_conn.execute(
                "SELECT COUNT(*) FROM papers WHERE date(created_at) = ?",
                (target_day,),
            ).fetchone()
            report["papers_ingested"] = row[0] if row else 0

            # Distilled today
            row = papers_conn.execute(
                "SELECT COUNT(*) FROM papers WHERE status = 'distilled' AND date(distilled_at) = ?",
                (target_day,),
            ).fetchone()
            report["papers_distilled"] = row[0] if row else 0

            # Skipped today
            row = papers_conn.execute(
                "SELECT COUNT(*) FROM papers WHERE status = 'skipped' AND date(updated_at) = ?",
                (target_day,),
            ).fetchone()
            report["papers_skipped"] = row[0] if row else 0

            # Errors today
            row = papers_conn.execute(
                "SELECT COUNT(*) FROM papers WHERE status = 'error' AND date(updated_at) = ?",
                (target_day,),
            ).fetchone()
            report["papers_error"] = row[0] if row else 0

            papers_conn.close()
        except Exception as e:
            logger.warning(f"Failed to query papers.db for daily report: {e}")

        # Agent stats from agents.db
        try:
            agents_conn = self._get_agents_conn()

            # Agent actions today
            rows = agents_conn.execute(
                """SELECT action, COUNT(*) as cnt
                   FROM agent_log
                   WHERE date(created_at) = ?
                   GROUP BY action
                   ORDER BY cnt DESC""",
                (target_day,),
            ).fetchall()
            action_counts = {row[0]: row[1] for row in rows}
            report["agents_spawned"] = action_counts.get("spawn", 0)
            report["agents_completed"] = action_counts.get("complete", 0)
            report["agents_failed"] = action_counts.get("fail", 0)
            report["agents_abandoned"] = action_counts.get("abandon", 0)
            report["top_actions"] = [
                {"action": a, "count": c} for a, c in rows[:10]
            ]

            # Errors today
            error_rows = agents_conn.execute(
                """SELECT agent_id, task_id, detail, created_at
                   FROM agent_log
                   WHERE action = 'error' AND date(created_at) = ?
                   ORDER BY created_at DESC
                   LIMIT 20""",
                (target_day,),
            ).fetchall()
            report["errors"] = [
                {
                    "agent_id": row[0],
                    "task_id": row[1],
                    "detail": row[2],
                    "time": row[3],
                }
                for row in error_rows
            ]

            # Daily caps
            cap_row = agents_conn.execute(
                """SELECT vault_writes, llm_tokens_input, llm_tokens_output, llm_cost_usd,
                          papers_ingested, papers_distilled, agents_spawned
                   FROM daily_caps WHERE date = ?""",
                (target_day,),
            ).fetchone()
            if cap_row:
                report["vault_writes"] = cap_row[0]
                report["llm_tokens_input"] = cap_row[1]
                report["llm_tokens_output"] = cap_row[2]
                report["llm_cost_usd"] = cap_row[3]

            agents_conn.close()
        except Exception as e:
            logger.warning(f"Failed to query agents.db for daily report: {e}")

        # Safety status
        report["safety_status"] = {
            "llm_cap_remaining_usd": max(0, DAILY_LLM_CAP_USD - report["llm_cost_usd"]),
            "llm_cap_exceeded": report["llm_cost_usd"] >= DAILY_LLM_CAP_USD,
            "vault_write_cap_remaining": max(0, DAILY_VAULT_WRITE_CAP - report["vault_writes"]),
            "vault_write_cap_exceeded": report["vault_writes"] >= DAILY_VAULT_WRITE_CAP,
        }

        return report

    # ── Audit Export ───────────────────────────────────────────────────────

    async def audit_trail(
        self,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        action: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Export audit trail with optional filters.
        
        Args:
            agent_id: Filter by agent
            task_id: Filter by task
            action: Filter by action type
            since: ISO timestamp — only return entries after this time
            limit: Max entries to return
            
        Returns:
            List of audit entries
        """
        conn = self._get_agents_conn()
        try:
            sql = "SELECT id, task_id, agent_id, action, detail, tokens_used, cost_usd, created_at FROM agent_log"
            conditions: List[str] = []
            params: List[Any] = []

            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)
            if task_id:
                conditions.append("task_id = ?")
                params.append(task_id)
            if action:
                conditions.append("action = ?")
                params.append(action)
            if since:
                conditions.append("created_at >= ?")
                params.append(since)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            return [
                {
                    "id": row[0],
                    "task_id": row[1],
                    "agent_id": row[2],
                    "action": row[3],
                    "detail": row[4],
                    "tokens_used": row[5],
                    "cost_usd": row[6],
                    "created_at": row[7],
                }
                for row in rows
            ]
        finally:
            conn.close()

    # ── Safety Checks ──────────────────────────────────────────────────────

    async def check_llm_budget(self, estimated_cost: float = 0.0) -> Dict[str, Any]:
        """
        Check if LLM budget allows a spend operation.
        
        Returns dict with 'allowed' boolean and remaining budget.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        conn = self._get_agents_conn()
        try:
            row = conn.execute(
                "SELECT llm_cost_usd FROM daily_caps WHERE date = ?", (today,)
            ).fetchone()
            current_cost = row[0] if row else 0.0
            remaining = max(0, DAILY_LLM_CAP_USD - current_cost)
            allowed = (current_cost + estimated_cost) <= DAILY_LLM_CAP_USD
            return {
                "allowed": allowed,
                "current_cost_usd": current_cost,
                "remaining_usd": remaining,
                "estimated_cost_usd": estimated_cost,
                "cap_usd": DAILY_LLM_CAP_USD,
            }
        finally:
            conn.close()

    async def check_vault_write_budget(self, count: int = 1) -> Dict[str, Any]:
        """
        Check if vault write budget allows writing.
        
        Returns dict with 'allowed' boolean and remaining budget.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        conn = self._get_agents_conn()
        try:
            row = conn.execute(
                "SELECT vault_writes FROM daily_caps WHERE date = ?", (today,)
            ).fetchone()
            current_writes = row[0] if row else 0
            remaining = max(0, DAILY_VAULT_WRITE_CAP - current_writes)
            allowed = (current_writes + count) <= DAILY_VAULT_WRITE_CAP
            return {
                "allowed": allowed,
                "current_writes": current_writes,
                "remaining": remaining,
                "requested": count,
                "cap": DAILY_VAULT_WRITE_CAP,
            }
        finally:
            conn.close()

    async def check_agent_slots(self) -> Dict[str, Any]:
        """
        Check if a new agent can be spawned (max 3 concurrent).
        
        Returns dict with 'allowed' boolean and current slot usage.
        """
        conn = self._get_agents_conn()
        try:
            row = conn.execute(
                "SELECT COUNT(*) FROM research_tasks WHERE status = 'running'"
            ).fetchone()
            running = row[0] if row else 0
            remaining = max(0, MAX_CONCURRENT_AGENTS - running)
            return {
                "allowed": running < MAX_CONCURRENT_AGENTS,
                "running": running,
                "remaining": remaining,
                "max": MAX_CONCURRENT_AGENTS,
            }
        finally:
            conn.close()


# ── Schema ────────────────────────────────────────────────────────────────

_TELEMETRY_SCHEMA = """
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

CREATE INDEX IF NOT EXISTS idx_agent_log_task ON agent_log(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_agent ON agent_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_log_action ON agent_log(action);
CREATE INDEX IF NOT EXISTS idx_agent_log_created ON agent_log(created_at);

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
"""
