"""
PO Workspace Scanner — scans the repo for relevant files and context.

Provides the OCE cognitive pipeline with a real-time view of:
- Python files changed recently
- Config files and their structure
- Test coverage state
- Any patterns matching registered interest profiles
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ScanResult:
    """Result of a workspace scan."""

    timestamp: float
    repo_root: str
    files_scanned: int = 0
    files_fresh: int = 0  # changed within the last scan window
    python_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    patterns_found: Dict[str, List[str]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def summary(self) -> Dict[str, Any]:
        return {
            "files_scanned": self.files_scanned,
            "fresh": self.files_fresh,
            "python_files": len(self.python_files),
            "config_files": len(self.config_files),
            "test_files": len(self.test_files),
            "changed_files": len(self.changed_files),
            "patterns_found": {k: len(v) for k, v in self.patterns_found.items()},
            "errors": len(self.errors),
            "duration_ms": round(self.duration_ms, 1),
        }


class WorkspaceScanner:
    """Scans the workspace for context relevant to PO's current task."""

    # File patterns of interest
    PYTHON_GLOB = "**/*.py"
    CONFIG_GLOB = "**/{pyproject.toml,requirements.txt,*.yaml,*.yml,*.json,*.toml}"
    TEST_GLOB = "**/test_*.py"

    # Freshness window in seconds (default: 5 minutes)
    DEFAULT_FRESH_WINDOW = 300

    # Regex patterns to flag in scan results
    INTEREST_PATTERNS = {
        "todo": re.compile(r"#\s*TODO|#\s*FIXME|#\s*HACK", re.IGNORECASE),
        "import_error": re.compile(r"ImportError|ModuleNotFoundError", re.IGNORECASE),
        "test_fail": re.compile(r"FAILED|ERROR|assert", re.IGNORECASE),
        "po_reference": re.compile(r"\bpo\b|\bPO\b|\bcognitive\b|\bfield\b", re.IGNORECASE),
    }

    def __init__(self, repo_root: str | None = None, fresh_window: int | None = None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
        self.fresh_window = fresh_window or self.DEFAULT_FRESH_WINDOW
        self._last_scan: float = 0.0

    def scan(self) -> ScanResult:
        """Execute a full workspace scan."""
        start = time.monotonic()
        result = ScanResult(
            timestamp=time.time(),
            repo_root=str(self.repo_root),
        )

        try:
            result.python_files = self._glob_files(self.PYTHON_GLOB)
            result.config_files = self._glob_files(self.CONFIG_GLOB)
            result.test_files = self._glob_files(self.TEST_GLOB)
            result.files_scanned = len(result.python_files) + len(result.config_files)

            result.changed_files = self._find_fresh_files()
            result.files_fresh = len(result.changed_files)

            result.patterns_found = self._scan_patterns(result.python_files)

        except Exception as e:
            result.errors.append(f"Scan error: {e}")

        result.duration_ms = (time.monotonic() - start) * 1000
        self._last_scan = result.timestamp
        return result

    def _glob_files(self, pattern: str) -> List[str]:
        """Glob files relative to repo root."""
        try:
            matches = list(self.repo_root.glob(pattern))
            return [str(p.relative_to(self.repo_root)) for p in matches if p.is_file()]
        except Exception:
            return []

    def _find_fresh_files(self) -> List[str]:
        """Find files changed within the freshness window."""
        fresh = []
        cutoff = time.time() - self.fresh_window
        try:
            import git
            repo = git.Repo(str(self.repo_root))
            for item in repo.index.diff(None):
                if item.change_type in ("M", "A", "D"):
                    try:
                        stat = (self.repo_root / item.a_path).stat()
                        if stat.st_mtime > cutoff:
                            fresh.append(item.a_path)
                    except (OSError, ValueError):
                        pass
        except Exception:
            # Fallback: check mtime on all python files
            for f in self.repo_root.glob(self.PYTHON_GLOB):
                try:
                    if f.stat().st_mtime > cutoff:
                        fresh.append(str(f.relative_to(self.repo_root)))
                except OSError:
                    pass
        return fresh

    def _scan_patterns(self, files: List[str]) -> Dict[str, List[str]]:
        """Scan files for interest patterns."""
        hits: Dict[str, List[str]] = {}
        for pattern_name, regex in self.INTEREST_PATTERNS.items():
            pattern_hits = []
            for fpath in files:
                try:
                    full_path = self.repo_root / fpath
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                    if regex.search(content):
                        pattern_hits.append(fpath)
                except (OSError, UnicodeDecodeError):
                    pass
            if pattern_hits:
                hits[pattern_name] = pattern_hits[:20]  # Cap at 20 per pattern
        return hits

    def scan_delta(self, since: float) -> Dict[str, Any]:
        """Return only what changed since a given timestamp."""
        result = self.scan()
        return {
            "files_fresh": result.files_fresh,
            "changed_files": result.changed_files,
            "patterns_found": result.patterns_found,
            "elapsed_ms": result.duration_ms,
        }