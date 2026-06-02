"""Observer conversation runtime: session + vault context injection.

Before every response:
  message → semantic search → graph traversal → memory extraction → context injection

This runtime provides `process_message` which:
1. Extracts keywords from the message
2. Searches the vault for relevant notes (context injection)
3. Builds a compressed operational response
4. Records the interaction in the execution journal
"""
import os
import re
import datetime
from typing import Dict, Any, List, Optional
from core.observer.vault import Vault
from core.observer.journal import Journal


class ObserverConversationRuntime:
    def __init__(self, vault_path: str = None, vault: Vault = None, journal: Journal = None):
        if vault:
            self.vault = vault
            self.vault_path = vault.path
        elif vault_path:
            self.vault_path = vault_path
            self.vault = Vault(path=vault_path)
        else:
            self.vault_path = os.path.join(os.getcwd(), "memory")
            self.vault = Vault(path=self.vault_path)
        self.journal = journal or Journal(self.vault)
        self._session: List[Dict[str, Any]] = []

    def _extract_keywords(self, message: str) -> List[str]:
        words = re.findall(r"\w+", message)
        stop = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are", "it", "i", "you", "me", "my"}
        return [w for w in words if w.lower() not in stop][:8]

    def _inject_context(self, keywords: List[str]) -> str:
        """Search vault and build a context block for the response."""
        if not keywords:
            return ""
        hits = self.vault.search_notes(keywords, max_results=5)
        if not hits:
            return ""
        lines = ["[Context from vault]"]
        for h in hits:
            lines.append(f"  • {h['path']}: {h['snippet'][:100]}")
        return "\n".join(lines)

    def process_message(self, message: str, meta: Dict[str, Any] = None) -> str:
        """Process an incoming message and return a text reply with vault context injected."""
        if not message:
            return "I received an empty message."

        keywords = self._extract_keywords(message)
        context_block = self._inject_context(keywords)

        # Build response
        if context_block:
            reply = f"{context_block}\n\n---\nResponse: Understood — '{message[:80]}'"
        else:
            reply = f"Echo: {message}\n\n(No matching notes found. Try /memory <keywords> or /search <term>.)"

        # Record in session + journal
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "message": message,
            "keywords": keywords,
            "context_hits": context_block.count("•") if context_block else 0,
            "meta": meta or {}
        }
        self._session.append(entry)
        self.journal.record_event({"type": "conversation", "message": message[:200], "keywords": keywords})

        return reply

    def get_session_summary(self) -> str:
        return f"Session: {len(self._session)} messages processed."
