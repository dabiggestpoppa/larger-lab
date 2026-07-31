"""Report Return System — agent output → Telegram.

Collects agent execution results, compresses them, and formats
for Telegram delivery. Also writes compressed reports into the vault.
"""
import datetime
from typing import Dict, Any, List, Optional
from core.observer.vault import Vault
from core.observer.journal import Journal


class ReportReturnSystem:
    def __init__(self, vault: Vault = None, journal: Journal = None):
        self.vault = vault or Vault()
        self.journal = journal or Journal(self.vault)
        self._reports: List[Dict[str, Any]] = []

    def submit_report(self, agent: str, task: str, output: str, meta: Dict[str, Any] = None) -> str:
        """Submit an agent report. Returns a compressed Telegram-ready summary."""
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        # compress: truncate long outputs
        compressed = output[:500] + ("..." if len(output) > 500 else "")
        report = {
            "timestamp": ts,
            "agent": agent,
            "task": task,
            "output": compressed,
            "full_length": len(output),
            "meta": meta or {}
        }
        self._reports.append(report)

        # persist to vault
        title = f"report_{agent}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        content = (
            f"# Report: {agent} — {task}\n\n"
            f"**Timestamp:** {ts}\n\n"
            f"## Output\n{compressed}\n\n"
            f"## Meta\n{meta or {}}\n"
        )
        self.vault.save_note(title, content)
        self.journal.record_event({"type": "report", "agent": agent, "task": task})

        return self._format_for_telegram(report)

    def _format_for_telegram(self, report: Dict[str, Any]) -> str:
        return (
            f"📋 Report from {report['agent']}\n"
            f"Task: {report['task']}\n"
            f"Time: {report['timestamp']}\n"
            f"---\n"
            f"{report['output']}"
        )

    def recent_reports(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(self._reports[-n:])[::-1]


if __name__ == "__main__":
    rrs = ReportReturnSystem()
    print(rrs.submit_report("AS", "workspace review", "All 7 services online. Vault synced. 71 notes indexed."))
