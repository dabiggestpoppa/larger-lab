"""
Vault Writer — Phase 0A
Write structured markdown into the O2C Obsidian vault.

Core principle: Every agent execution leaves behind operational intelligence
in markdown format. The filesystem becomes smarter, not the model.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


DEFAULT_VAULT_PATH = Path(__file__).resolve().parent.parent.parent / "O2C-VAULT"

VAULT_DIRECTORIES = [
    "agents/quant", "agents/research", "agents/coding", "agents/observer",
    "memory/successful_patterns", "memory/error_corrections", "memory/spawn_history",
    "memory/consensus_failures", "ontology/cerebus", "ontology/observer_core",
    "ontology/state_machines", "ontology/routing_logic", "graphs/agent_relationships",
    "graphs/execution_flow", "graphs/knowledge_clusters", "journals/daily_runtime",
    "journals/backtest_logs", "journals/forward_test_logs",
    "doctrine", "failures", "execution", "skills", "heuristics", "routing", "architecture",
]

VALID_CATEGORIES = sorted(set(d.split("/")[0] for d in VAULT_DIRECTORIES))


class VaultWriter:
    def __init__(self, vault_path=None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        for d in VAULT_DIRECTORIES:
            (self.vault_path / d).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename(title):
        safe = re.sub(r'[^\w\s\-]', '', title)
        return re.sub(r'\s+', '_', safe.strip())[:100]

    @staticmethod
    def _format_note(title, content, category, tags=None):
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        lines = [f"# {title}", "", f"> Category: {category} | Created: {ts}", ""]
        if tags:
            lines += ["Tags: " + " ".join(f"#{t}" for t in tags), ""]
        for key in ("cause", "fix", "result"):
            if content.get(key):
                lines += [f"{key.upper()}:", str(content[key]), ""]
        if content.get("links"):
            lines.append("LINKS:")
            for link in content["links"]:
                lines.append(f"[[{link}]]")
            lines.append("")
        return "\n".join(lines)

    def write_note(self, category, title, content, tags=None, subcategory=None):
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{category}'")
        dir_p = self.vault_path / category / (subcategory or "")
        dir_p.mkdir(parents=True, exist_ok=True)
        fn = self._sanitize_filename(title) + ".md"
        fp = dir_p / fn
        fp.write_text(self._format_note(title, content, category, tags), encoding="utf-8")
        rel = str(fp.relative_to(self.vault_path))
        return {"id": rel, "title": title, "path": rel, "category": category,
                "tags": tags or [], "modified": datetime.now(timezone.utc).isoformat()}

    def get_note(self, category, title, subcategory=None):
        fn = self._sanitize_filename(title) + ".md"
        fp = self.vault_path / category / (subcategory or "") / fn
        if not fp.exists():
            return None
        content = fp.read_text(encoding="utf-8")
        return {"id": str(fp.relative_to(self.vault_path)), "title": title,
                "path": str(fp.relative_to(self.vault_path)), "category": category,
                "content": content, "tags": re.findall(r"#(\w+)", content),
                "links": re.findall(r"\[\[(.+?)\]\]", content),
                "modified": datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc).isoformat()}

    def list_notes(self, category=None, subcategory=None):
        if category:
            dp = self.vault_path / category / (subcategory or "")
        else:
            dp = self.vault_path
        notes = []
        for p in sorted(dp.rglob("*.md")):
            c = p.read_text(encoding="utf-8")
            rp = str(p.relative_to(self.vault_path))
            notes.append({"id": rp, "title": p.stem.replace("_", " "), "path": rp,
                          "category": rp.split("/")[0], "tags": re.findall(r"#(\w+)", c),
                          "links": re.findall(r"\[\[(.+?)\]\]", c),
                          "modified": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()})
        return notes

    def search_notes(self, query="", category="", limit=50):
        results = []
        for n in self.list_notes(category=category or None):
            fp = self.vault_path / n["path"]
            c = fp.read_text(encoding="utf-8") if fp.exists() else ""
            if query.lower() in n["title"].lower() or query.lower() in c.lower():
                n["content"] = c[:500]
                results.append(n)
            if len(results) >= limit:
                break
        return results

    def list_categories(self):
        return sorted(VALID_CATEGORIES)

    def update_note(self, category, title, content, tags=None, subcategory=None):
        return self.write_note(category, title, content, tags, subcategory)

    def delete_note(self, category, title, subcategory=None):
        fn = self._sanitize_filename(title) + ".md"
        fp = self.vault_path / category / (subcategory or "") / fn
        if fp.exists():
            fp.unlink()
            return True
        return False


_default_writer = None

def get_writer(vault_path=None):
    global _default_writer
    if _default_writer is None:
        _default_writer = VaultWriter(vault_path)
    return _default_writer

def write_note(category, title, content, tags=None):
    return get_writer().write_note(category, title, content, tags)

def get_note(category, title):
    return get_writer().get_note(category, title)

def list_notes(category=None):
    return get_writer().list_notes(category)
