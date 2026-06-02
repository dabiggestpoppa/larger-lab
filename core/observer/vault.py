"""Vault context helpers: simple file-based search and note writing."""
import os
import re
import datetime
from typing import List, Dict, Any, Optional


class Vault:
    def __init__(self, path: Optional[str] = None):
        if path:
            self.path = path
        else:
            self.path = os.path.join(os.getcwd(), "memory", "obsidian-vault")
        os.makedirs(self.path, exist_ok=True)

    def _read_file(self, fp: str) -> str:
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    def search_notes(self, keywords: List[str], max_results: int = 20) -> List[Dict[str, Any]]:
        """Return list of dicts with path and snippet for matching markdown files."""
        found = []
        kw = [k.lower() for k in keywords]
        for root, _, files in os.walk(self.path):
            for fn in files:
                if not fn.lower().endswith('.md'):
                    continue
                fp = os.path.join(root, fn)
                text = self._read_file(fp).lower()
                score = 0
                for k in kw:
                    if k in text:
                        score += 1
                if score > 0:
                    # produce a short snippet
                    orig = self._read_file(fp)
                    snippet = next((line.strip() for line in orig.splitlines() if any(k in line.lower() for k in kw)), '')
                    found.append({"path": os.path.relpath(fp, self.path), "snippet": snippet[:140]})
                    if len(found) >= max_results:
                        return found
        return found

    def save_note(self, title: str, content: str) -> str:
        ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        safe = re.sub(r'[^A-Za-z0-9_\-]', '_', title)[:50]
        fname = f"journal_{ts}_{safe}.md"
        fp = os.path.join(self.path, fname)
        try:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(content)
            return fp
        except Exception:
            return ""
