# Knowledge Importer

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Phase 2: Knowledge Import Engine.
Imports ALL Larger-Lab knowledge into the Obsidian vault.
Writes notes directly to filesystem (bypasses VaultWriter._format_note dict requirement).
"""

import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from core.obsidian.vault_writer import VaultWriter, VALID_CATEGORIES, VAULT_DIRECTORIES


SKIP_PATTERNS = [
    "__pycache__", ".pyc", ".pyo", ".git", ".obsidian",
    "node_modules", ".venv", "uv.lock", ".env",
    "test_sample.csv", ".sync_state.json",
]


def _should_skip(name: str) -> bool:
    return any(p in name for p in SKIP_PATTERNS)


def _infer_category(rel_path: str) -> tuple:
    p = rel_path.replace("\\", "/")
    root_map = {
        "AGENTS.md": ("doctrine", "agents"),
        "SOUL.md": ("doctrine", "soul"),
        "IDENTITY.md": ("doctrine", "identity"),
        "MEMORY.md": ("doctrine", "memory"),
        "HEARTBEAT.md": ("doctrine", "heartbeat"),
        "TOOLS.md": ("doctrine", "tools"),
        "USER.md": ("doctrine", "user"),
        "README.md": ("doctrine", "readme"),
    }
    if p in root_map:
        return root_map[p]
    if p.startswith("docs/architecture"):
        return ("architecture", None)
    if p.startswith("docs/"):
        return ("doctrine", None)
    if p.startswith("memory/"):
        return ("memory", None)
    if p.startswith("core/observer"):
        return ("ontology", "observer")
    if p.startswith("core/obsidian"):
        return ("ontology", "obsidian")
    if p.startswith("core/semantic"):
        return ("ontology", "semantic")
    if p.startswith("core/telegram"):
        return ("ontology", "telegram")
    if p.startswith("core/"):
        return ("ontology", "core")
    if p.startswith("quant-lab/strategies"):
        return ("doctrine", "strategies")
    if p.startswith("quant-lab/configs"):
        return ("doctrine", "configs")
    if p.startswith("quant-lab/engines"):
        return ("doctrine", "engines")
    if p.startswith("skills/"):
        return ("skills", None)
    if p.startswith("shared-conversations/"):
        return ("journals", "conversations")
    parts = p.split("/")
    if len(parts) >= 2 and parts[0] in VALID_CATEGORIES:
        return (parts[0], None)
    return ("doctrine", None)


def _sanitize_filename(title: str) -> str:
    safe = re.sub(r'[^\w\s\-]', '', title)
    return re.sub(r'\s+', '_', safe.strip())[:80]


def _sanitize_title(source_path: str) -> str:
    stem = Path(source_path).stem
    return stem.replace("_", " ").replace("-", " ").title()


def _format_note(title: str, body: str, category: str, tags: list = None) -> str:
    """Format a markdown note with header."""
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        f"# {title}",
        "",
        f"> Category: {category} | Imported: {ts}",
        "",
    ]
    if tags:
        lines.append("Tags: " + " ".join(f"#{t}" for t in tags))
        lines.append("")
    lines.append(body)
    return "\n".join(lines)


class KnowledgeImporter:
    def __init__(self, vault_path=None, workspace_root=None):
        self.vault = VaultWriter(vault_path=vault_path)
        self.workspace_root = Path(workspace_root) if workspace_root else Path(__file__).resolve().parents[2]
        self._imported = 0
        self._skipped = 0
        self._errors = []

    def _write_note(self, category: str, subcategory: Optional[str], title: str, body: str, tags: list = None):
        """Write a note directly to the vault filesystem."""
        cat = category if category in VALID_CATEGORIES else "doctrine"
        dir_p = self.vault.vault_path / cat / (subcategory or "")
        dir_p.mkdir(parents=True, exist_ok=True)
        fn = _sanitize_filename(title) + ".md"
        fp = dir_p / fn
        content = _format_note(title, body, cat, tags)
        fp.write_text(content, encoding="utf-8")
        self._imported += 1

    def import_all(self):
        self._imported = 0
        self._skipped = 0
        self._errors = []
        print(f"[Importer] Workspace: {self.workspace_root}")
        print(f"[Importer] Vault: {self.vault.vault_path}")
        self._import_root_files()
        self._import_directory("docs")
        self._import_directory("memory")
        self._import_python_directory("core")
        self._import_python_directory("quant-lab/strategies")
        self._import_python_directory("quant-lab/configs")
        self._import_python_directory("quant-lab/engines")
        self._import_directory("skills")
        self._import_directory("shared-conversations")
        result = {"imported": self._imported, "skipped": self._skipped, "errors": self._errors}
        print(f"[Importer] Done. Imported: {self._imported}, Skipped: {self._skipped}, Errors: {len(self._errors)}")
        return result

    def _import_root_files(self):
        for fn in ["AGENTS.md", "SOUL.md", "IDENTITY.md", "MEMORY.md", "HEARTBEAT.md", "TOOLS.md", "USER.md", "README.md"]:
            fp = self.workspace_root / fn
            if not fp.exists():
                continue
            try:
                content = fp.read_text(encoding="utf-8")
                cat, subcat = _infer_category(fn)
                title = _sanitize_title(fn)
                tags = [cat] + ([subcat] if subcat else [])
                self._write_note(cat, subcat, title, content, tags)
            except Exception as e:
                self._errors.append(f"{fn}: {e}")

    def _import_directory(self, dir_name):
        dir_path = self.workspace_root / dir_name
        if not dir_path.exists():
            return
        for root, dirs, files in os.walk(str(dir_path)):
            dirs[:] = [d for d in dirs if not _should_skip(d)]
            for fn in sorted(files):
                if _should_skip(fn) or not fn.endswith(".md"):
                    self._skipped += 1
                    continue
                fp = Path(root) / fn
                rel_path = str(fp.relative_to(self.workspace_root))
                try:
                    content = fp.read_text(encoding="utf-8")
                    if not content.strip():
                        self._skipped += 1
                        continue
                    cat, subcat = _infer_category(rel_path)
                    title = _sanitize_title(rel_path)
                    tags = [cat] + ([subcat] if subcat else [])
                    self._write_note(cat, subcat, title, content, tags)
                except Exception as e:
                    self._errors.append(f"{rel_path}: {e}")

    def _import_python_directory(self, dir_name):
        dir_path = self.workspace_root / dir_name
        if not dir_path.exists():
            return
        for root, dirs, files in os.walk(str(dir_path)):
            dirs[:] = [d for d in dirs if not _should_skip(d)]
            for fn in sorted(files):
                if _should_skip(fn) or not fn.endswith(".py") or fn == "__init__.py":
                    self._skipped += 1
                    continue
                fp = Path(root) / fn
                rel_path = str(fp.relative_to(self.workspace_root))
                try:
                    content = fp.read_text(encoding="utf-8")
                    if not content.strip():
                        self._skipped += 1
                        continue
                    cat, subcat = _infer_category(rel_path)
                    title = _sanitize_title(rel_path)
                    tags = [cat, "python"] + ([subcat] if subcat else [])
                    body = f"```python\n{content}\n```"
                    self._write_note(cat, subcat, title, body, tags)
                except Exception as e:
                    self._errors.append(f"{rel_path}: {e}")


if __name__ == "__main__":
    import json
    importer = KnowledgeImporter()
    result = importer.import_all()
    print(json.dumps({"imported": result["imported"], "skipped": result["skipped"], "error_count": len(result["errors"])}, indent=2))

```

LINKS:
[[Architecture]]
[[Agents]]
[[Heartbeat]]
[[Identity]]
[[Readme]]
[[Soul]]
[[Tools]]
[[User]]
[[Hermes Obsidian Test   Vault Working]]
[[Obsidian Vault Connection Info]]
[[Ontology Core Summary]]
[[Sage Audit Environment Utilization]]
[[Citation Workflow]]
[[Modules]]
[[Patterns]]
[[Server]]
[[Skill]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
