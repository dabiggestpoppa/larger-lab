"""
TB-R6.3 — WEEKLY SIGNAL-COMPLETENESS AUDITOR · REPORT
=====================================================

Human-readable + machine-readable artifact writer.

Artifacts (quant-lab/tb_audits/YYYY-Www/):
  TB_WEEKLY_AUDIT.json          full structured result
  TB_WEEKLY_AUDIT.md            end-of-week human report
  TB_EXPECTED_EVENTS.csv        deterministic expected-event ledger
  TB_RUNTIME_MATCH.csv          expected vs runtime detail table
  TB_DATA_PARITY.csv            parity rows
  TB_ACTIVITY_CONTEXT.json      distributions + rolling activity
  TB_WEEKLY_AUDIT_HISTORY.csv   append-only summary (one row per run)

The auditor writes ONLY under the tb_audits directory. It never writes to
the runtime DBs, never sends orders, and never modifies strategy state.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from tb_audit_core import (
    CONTROL_STRATEGY_ID,
    PRIMARY_STRATEGY_ID,
    STRATEGY_IDS,
    MatchRecord,
    OutcomeClass,
)

AUDIT_ROOT_NAME = "tb_audits"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AuditReportWriter:
    def __init__(self, out_dir: Path, run_id: str = ""):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or _now_iso()

    # ── machine artifacts ────────────────────────────────────────────────
    def write_json(self, name: str, data: dict) -> Path:
        p = self.out_dir / name
        p.write_text(json.dumps(data, indent=2, default=str),
                     encoding="utf-8")
        return p

    def write_csv(self, name: str, rows: List[dict]) -> Path:
        p = self.out_dir / name
        if not rows:
            p.write_text("", encoding="utf-8")
            return p
        cols = list(rows[0].keys())
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        return p

    def write_expected(self, events) -> Path:
        return self.write_csv("TB_EXPECTED_EVENTS.csv",
                              [e.to_row() for e in events])

    def write_match(self, records: List[MatchRecord]) -> Path:
        return self.write_csv("TB_RUNTIME_MATCH.csv",
                              [r.to_row() for r in records])

    def write_parity(self, divergences: List[dict]) -> Path:
        return self.write_csv("TB_DATA_PARITY.csv", divergences)

    def write_activity(self, activity: dict) -> Path:
        return self.write_json("TB_ACTIVITY_CONTEXT.json", activity)

    def append_history(self, summary_row: dict) -> Path:
        """Append-only summary ledger; one row per audit run."""
        p = self.out_dir.parent / "TB_WEEKLY_AUDIT_HISTORY.csv"
        new = not p.exists()
        with p.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(summary_row.keys()))
            if new:
                w.writeheader()
            w.writerow(summary_row)
        return p

    # ── human report ─────────────────────────────────────────────────────
    def write_md(self, report: dict) -> Path:
        lines = []
        lines.append("# TB WEEKLY AUDIT")
        lines.append(f"Week: {report['week_start']} -> {report['week_end']}")
        lines.append(f"Audit run: {report['run_id']}")
        lines.append(f"Data source: {report['data_source']}")
        lines.append("")
        if not report["data_valid"]:
            lines.append("## AUDIT_INVALID_DATA")
            lines.append("Data integrity gates failed — the auditor refuses")
            lines.append("to claim missed signals on broken data (fail closed).")
            lines.append("")
            lines.append("Reasons:")
            for r in report["data_reasons"]:
                lines.append(f"- {r}")
            lines.append("")
            lines.append("Engineering completeness: BLOCKED_DATA_DIVERGENCE")
            lines.append("Activity state: INSUFFICIENT_HISTORY")
            p = self.out_dir / "TB_WEEKLY_AUDIT.md"
            p.write_text("\n".join(lines), encoding="utf-8")
            return p

        for s in STRATEGY_IDS:
            summ = report["summaries"][s]
            label = "PRIMARY" if s == PRIMARY_STRATEGY_ID else "CONTROL"
            lines.append(f"## {label} ({s})")
            lines.append(f"Expected signals: {summ['expected_signals']}")
            lines.append(f"Runtime identified: {summ['runtime_signals']}")
            lines.append(f"Taken: {summ['taken']}")
            lines.append(f"Shadow: {summ['shadow']}")
            lines.append(f"Valid blocks: {summ['valid_blocks']}")
            lines.append(f"Missed: {summ['missed']}")
            lines.append(f"Runtime-only: {summ['runtime_only']}")
            lines.append(f"Data divergence: {summ['data_divergence']}")
            lines.append("")
        lines.append(f"Engineering completeness: {report['engineering']}")
        lines.append(f"Data parity: {report['data_parity']}")
        lines.append("")
        lines.append("## Historical cadence")
        for s in STRATEGY_IDS:
            label = "PRIMARY" if s == PRIMARY_STRATEGY_ID else "CONTROL"
            act = report["activity"].get(s, {})
            dist = act.get("weekly_distribution", {})
            lines.append(f"### {label} cadence")
            lines.append(f"current week = {act.get('current_week')}")
            lines.append(f"trailing 4w = {act.get('trailing_4_week')} "
                         f"({act.get('trailing_4_week_class')})")
            lines.append(f"trailing 8w = {act.get('trailing_8_week')} "
                         f"({act.get('trailing_8_week_class')})")
            lines.append(f"trailing 12w = {act.get('trailing_12_week')} "
                         f"({act.get('trailing_12_week_class')})")
            lines.append(f"activity = {act.get('current_week_class')}")
            lines.append(f"weekly dist: mean={dist.get('mean')} "
                         f"median={dist.get('median')} "
                         f"p5={dist.get('p5')} p25={dist.get('p25')} "
                         f"p75={dist.get('p75')} p95={dist.get('p95')} "
                         f"max={dist.get('max')}")
            lines.append(f"weeks with 0/1/2/3/4+ signals: "
                         f"{dist.get('frac_weeks_0')}/"
                         f"{dist.get('frac_weeks_1')}/"
                         f"{dist.get('frac_weeks_2')}/"
                         f"{dist.get('frac_weeks_3')}/"
                         f"{dist.get('frac_weeks_4plus')}")
            lines.append("")
        lines.append("## Detail")
        lines.append("See TB_RUNTIME_MATCH.csv for the per-event detail table")
        lines.append("(timestamp, strategy, z, direction, expected action,")
        lines.append("runtime action, runtime blocker, match status, data")
        lines.append("parity, notes).")
        p = self.out_dir / "TB_WEEKLY_AUDIT.md"
        p.write_text("\n".join(lines), encoding="utf-8")
        return p
