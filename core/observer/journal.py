"""Execution journaling for observer interactions.

Every Telegram interaction creates:
- execution trace (in-memory + vault note)
- structured failure entry (CAUSE/FIX/RESULT/LINKS)
- continuity update (timestamped, linked)
"""
import os
import datetime
from typing import Dict, Any, List
from core.observer.vault import Vault


class Journal:
    def __init__(self, vault: Vault = None):
        self.vault = vault or Vault()
        self._events: List[Dict[str, Any]] = []

    def record_event(self, event: Dict[str, Any]) -> None:
        e = dict(event)
        e['timestamp'] = datetime.datetime.utcnow().isoformat() + 'Z'
        self._events.append(e)
        title = e.get('type', 'event') + ' ' + e.get('command', e.get('target', ''))
        content = f"Timestamp: {e['timestamp']}\n\nPayload:\n{e}\n"
        self.vault.save_note(title or 'event', content)

    def record_structured_failure(self, entry: Dict[str, Any]) -> str:
        """Write a structured failure note to the vault with CAUSE/FIX/RESULT/LINKS."""
        ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        cause = entry.get('cause', 'unknown')
        fix = entry.get('fix', 'TBD')
        result = entry.get('result', 'TBD')
        links = entry.get('links', [])
        title = f"failure_{ts}_{cause[:40]}"
        lines = [
            f"# Failure: {cause}",
            "",
            f"**Timestamp:** {ts}",
            "",
            "## CAUSE",
            cause,
            "",
            "## FIX",
            fix,
            "",
            "## RESULT",
            result,
            "",
            "## LINKS",
        ]
        if links:
            for l in links:
                lines.append(f"- [[{l}]]")
        else:
            lines.append("- (none)")
        content = "\n".join(lines)
        fp = self.vault.save_note(title, content)
        self._events.append({"type": "failure", "cause": cause, "vault_path": fp, "timestamp": ts})
        return fp

    def recent_events(self, n: int = 20) -> List[Dict[str, Any]]:
        return list(self._events[-n:])[::-1]
