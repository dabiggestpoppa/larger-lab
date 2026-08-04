#!/usr/bin/env python3
"""Phase 0 Book 1 repository fingerprint and core component inventory.

This module intentionally uses only the Python standard library. It observes
repository state and writes sanitized metadata; it does not import or execute
legacy trading, broker, agent, or runtime components.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA_VERSION = "0.1.0"
PART_ID = "PHASE-00-BOOK-01-PART-01"
DEFAULT_OUTPUT = Path("artifacts/forge/phase-00/book-01-part-01")
MAX_COMPONENT_FILES = 5_000
MAX_ENTRYPOINT_READ_BYTES = 512 * 1024
MAX_WORKTREE_HASH_BYTES = 50 * 1024 * 1024
LARGE_TRACKED_FILE_BYTES = 10 * 1024 * 1024

REQUIRED_COMPONENTS: dict[str, dict[str, str]] = {
    "oce": {
        "component_id": "OCE",
        "declared_purpose": "Operator control and lifecycle plane",
    },
    "srrs_opc": {
        "component_id": "SRRA-OPH",
        "declared_purpose": "Continuity, topology, reconstruction, and entropy substrate",
    },
    "projects/trading/backtests": {
        "component_id": "TRADING-BACKTESTS",
        "declared_purpose": "Backtest and research runners pending classification",
    },
    "projects/trading/mt5-mcp": {
        "component_id": "TRADING-MT5-MCP",
        "declared_purpose": "MT5 MCP project; not presumed to be the production FX path",
    },
    "projects/trading/nautilus": {
        "component_id": "TRADING-NAUTILUS-LAB",
        "declared_purpose": "Nautilus-related strategies, runners, and experiments pending classification",
    },
    "projects/trading/nautilus_trader": {
        "component_id": "VENDORED-NAUTILUS-TRADER",
        "declared_purpose": "NautilusTrader source tree pending long-term role classification",
    },
    "projects/trading/strategies": {
        "component_id": "TRADING-STRATEGIES",
        "declared_purpose": "Trading strategy sources pending classification",
    },
    "agent-lab": {
        "component_id": "AGENT-LAB",
        "declared_purpose": "Agent experiments and tooling pending classification",
    },
    "skills": {
        "component_id": "SKILLS",
        "declared_purpose": "Workspace skills and procedural tools",
    },
    "tools": {
        "component_id": "TOOLS",
        "declared_purpose": "Workspace operational and developer tools",
    },
    "system-arch": {
        "component_id": "SYSTEM-ARCH",
        "declared_purpose": "Architecture diagrams and change evidence",
    },
    "memory": {
        "component_id": "MEMORY",
        "declared_purpose": "Workspace memory artifacts",
    },
    "progress": {
        "component_id": "PROGRESS",
        "declared_purpose": "Agent activity and progress evidence",
    },
    "shared-conversations": {
        "component_id": "SHARED-CONVERSATIONS",
        "declared_purpose": "Agent coordination history",
    },
    "QUANT-LAB-INFRA-UPGRADE": {
        "component_id": "QUANT-LAB-INFRA-UPGRADE",
        "declared_purpose": "Canonical GLX FORGE blueprint, phase books, and build anchors",
    },
}

EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}

LANGUAGE_BY_SUFFIX = {
    ".bat": "batch",
    ".c": "c",
    ".cc": "cpp",
    ".cmd": "batch",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".pine": "pine",
    ".ps1": "powershell",
    ".py": "python",
    ".pyx": "cython",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".yaml": "yaml",
    ".yml": "yaml",
}

CONFIG_FILE_NAMES = {
    ".dockerignore",
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "cargo.toml",
    "dockerfile",
    "makefile",
    "package.json",
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "uv.lock",
}

SENSITIVE_QUERY_MARKERS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credential",
    "key",
    "password",
    "pat",
    "secret",
    "signature",
    "token",
}


class InventoryError(RuntimeError):
    """Raised when inventory evidence cannot be collected safely."""


def utc_now() -> str:
    """Return an RFC3339 UTC timestamp."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def canonical_hash(value: Any) -> str:
    """Hash a JSON-serializable value using deterministic encoding."""
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sanitize_remote_url(remote_url: str) -> str:
    """Remove credentials and sensitive query values from a Git remote URL."""
    value = remote_url.strip()
    if not value:
        return value

    if "://" not in value:
        # SCP-style SSH remotes such as git@github.com:owner/repo.git do not
        # carry a password field. Remove only an impossible user:secret@ form.
        return re.sub(r"^[^/@:]+:[^/@]+@", "", value)

    try:
        parsed = urlsplit(value)
    except ValueError:
        return re.sub(r"(?<=://)[^/@]+@", "", value).split("#", 1)[0]

    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    try:
        port = parsed.port
    except ValueError:
        # A malformed port must not force us to return the original,
        # credential-bearing URL. Drop the invalid port and keep sanitizing.
        port = None
    if port is not None:
        hostname = f"{hostname}:{port}"

    if parsed.scheme.lower() in {"http", "https"}:
        netloc = hostname
    else:
        username = parsed.username or ""
        netloc = f"{username}@{hostname}" if username else hostname

    safe_query = []
    for key, query_value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_MARKERS:
            continue
        safe_query.append((key, query_value))

    return urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            urlencode(safe_query),
            "",
        )
    )


def _run(
    command: list[str],
    *,
    cwd: Path,
    required: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        if required:
            raise InventoryError(f"Required executable is unavailable: {command[0]}") from exc
        return subprocess.CompletedProcess(command, 127, "", "")

    if required and completed.returncode != 0:
        safe_command = " ".join(command[:3])
        raise InventoryError(f"Inventory command failed: {safe_command}")
    return completed


def _git(
    repo_root: Path,
    *args: str,
    required: bool = True,
) -> str:
    output = _run(
        ["git", *args],
        cwd=repo_root,
        required=required,
    ).stdout
    # Preserve leading porcelain status columns and NUL record separators.
    # Git's normal human-readable commands only need newline trimming.
    return output.rstrip("\r\n")


def _command_version(executable: str) -> dict[str, Any]:
    path = shutil.which(executable)
    if path is None:
        return {"available": False, "version": None}

    completed = _run([executable, "--version"], cwd=Path.cwd(), required=False)
    first_line = completed.stdout.splitlines()[0].strip() if completed.stdout else None
    return {
        "available": completed.returncode == 0,
        "version": first_line,
    }


def _parse_null_records(raw: str) -> list[str]:
    return [record for record in raw.split("\0") if record]


def _normalize_excluded_worktree_paths(
    repo_root: Path,
    excluded_worktree_paths: Iterable[Path | str],
) -> tuple[str, ...]:
    """Return validated, repository-relative POSIX exclusion prefixes."""
    root = repo_root.resolve()
    normalized = set()
    for supplied_path in excluded_worktree_paths:
        candidate = Path(supplied_path)
        if not candidate.is_absolute():
            candidate = root / candidate
        candidate = candidate.resolve()
        if candidate == root:
            raise InventoryError("The repository root cannot be a worktree exclusion")
        try:
            relative = candidate.relative_to(root)
        except ValueError as exc:
            raise InventoryError(
                "Worktree exclusions must remain inside the repository root"
            ) from exc
        normalized.add(relative.as_posix().rstrip("/"))
    return tuple(sorted(normalized))


def _path_matches_prefix(relative_path: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        relative_path == prefix or relative_path.startswith(f"{prefix}/")
        for prefix in prefixes
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _content_identity(
    repo_root: Path,
    relative_path: str,
    excluded_prefixes: tuple[str, ...],
) -> dict[str, Any]:
    """Identify worktree content without recording file contents or following links."""
    if _path_matches_prefix(relative_path, excluded_prefixes):
        return {"status": "excluded_self_output"}

    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        return {"status": "invalid_repository_path"}

    path = repo_root / relative
    try:
        parent = path.parent.resolve()
        parent.relative_to(repo_root)
    except (OSError, ValueError):
        return {"status": "outside_repository"}

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {"status": "missing"}
    except OSError:
        return {"status": "unreadable"}

    size = metadata.st_size
    if stat.S_ISLNK(metadata.st_mode):
        try:
            target = os.readlink(path).encode("utf-8", errors="surrogateescape")
        except OSError:
            return {"status": "unreadable_symlink", "size_bytes": size}
        return {
            "status": "hashed_symlink",
            "size_bytes": size,
            "sha256": hashlib.sha256(target).hexdigest(),
        }

    if not stat.S_ISREG(metadata.st_mode):
        return {"status": "unsupported_file_type", "size_bytes": size}
    if size > MAX_WORKTREE_HASH_BYTES:
        return {
            "status": "skipped_over_limit",
            "size_bytes": size,
            "sha256": None,
        }

    try:
        digest = _sha256_file(path)
    except OSError:
        return {"status": "unreadable", "size_bytes": size}
    return {
        "status": "hashed",
        "size_bytes": size,
        "sha256": digest,
    }


def _collect_status(
    repo_root: Path,
    excluded_worktree_paths: Iterable[Path | str] = (),
) -> dict[str, Any]:
    excluded_prefixes = _normalize_excluded_worktree_paths(
        repo_root,
        excluded_worktree_paths,
    )
    raw = _git(
        repo_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    tokens = _parse_null_records(raw)
    entries: list[dict[str, Any]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if len(token) < 3:
            index += 1
            continue
        status = token[:2]
        path = token[3:]
        entry = {
            "status": status,
            "path": path,
            "content_identity": _content_identity(
                repo_root,
                path,
                excluded_prefixes,
            ),
        }
        if ("R" in status or "C" in status) and index + 1 < len(tokens):
            entry["source_path"] = tokens[index + 1]
            index += 1
        entries.append(entry)
        index += 1

    entries.sort(key=lambda item: (item["path"], item["status"]))
    return {
        "dirty": bool(entries),
        "entry_count": len(entries),
        "tracked_change_count": sum(item["status"] != "??" for item in entries),
        "untracked_count": sum(item["status"] == "??" for item in entries),
        "content_hash_limit_bytes": MAX_WORKTREE_HASH_BYTES,
        "excluded_worktree_paths": list(excluded_prefixes),
        "entries": entries,
    }


def _collect_remotes(repo_root: Path) -> list[dict[str, Any]]:
    remotes = []
    for name in sorted(_git(repo_root, "remote", required=False).splitlines()):
        if not name:
            continue
        urls = _git(
            repo_root,
            "remote",
            "get-url",
            "--all",
            name,
            required=False,
        ).splitlines()
        remotes.append(
            {
                "name": name,
                "urls": sorted(
                    {
                        sanitize_remote_url(url)
                        for url in urls
                        if url.strip()
                    }
                ),
            }
        )
    return remotes


def _collect_branches(repo_root: Path) -> list[dict[str, Any]]:
    output = _git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)%00%(objectname)%00%(upstream:short)",
        "refs/heads",
    )
    branches = []
    for line in output.splitlines():
        parts = line.split("\0")
        if len(parts) < 3:
            continue
        branches.append(
            {
                "name": parts[0],
                "head_sha": parts[1],
                "upstream": parts[2] or None,
            }
        )
    return sorted(branches, key=lambda item: item["name"])


def _collect_tags(repo_root: Path) -> list[dict[str, str]]:
    output = _git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)%00%(objectname)",
        "refs/tags",
    )
    tags = []
    for line in output.splitlines():
        parts = line.split("\0")
        if len(parts) == 2:
            tags.append({"name": parts[0], "object_sha": parts[1]})
    return sorted(tags, key=lambda item: item["name"])


def _collect_submodules(repo_root: Path) -> list[dict[str, str]]:
    gitmodules = repo_root / ".gitmodules"
    if not gitmodules.is_file():
        return []
    output = _git(
        repo_root,
        "config",
        "--file",
        ".gitmodules",
        "--get-regexp",
        r"^submodule\..*\.path$",
        required=False,
    )
    records = []
    for line in output.splitlines():
        key, _, path = line.partition(" ")
        if key and path:
            records.append({"name": key.removesuffix(".path"), "path": path})
    return sorted(records, key=lambda item: item["path"])


def _tracked_file_inventory(repo_root: Path) -> dict[str, Any]:
    paths = sorted(_parse_null_records(_git(repo_root, "ls-files", "-z")))
    aggregate_size = 0
    unreadable = []
    large_files = []
    for relative in paths:
        path = repo_root / relative
        try:
            size = path.lstat().st_size
        except OSError:
            unreadable.append(relative)
            continue
        aggregate_size += size
        if size >= LARGE_TRACKED_FILE_BYTES:
            large_files.append({"path": relative, "size_bytes": size})
    return {
        "count": len(paths),
        "aggregate_size_bytes": aggregate_size,
        "large_file_threshold_bytes": LARGE_TRACKED_FILE_BYTES,
        "large_files": large_files,
        "unreadable_paths": unreadable,
    }


def _default_branch(repo_root: Path) -> dict[str, str | None]:
    remote_head = _git(
        repo_root,
        "symbolic-ref",
        "--quiet",
        "--short",
        "refs/remotes/origin/HEAD",
        required=False,
    )
    if remote_head.startswith("origin/"):
        return {
            "name": remote_head.removeprefix("origin/"),
            "evidence": "refs/remotes/origin/HEAD",
        }
    return {"name": None, "evidence": "not_configured_locally"}


def _ignore_patterns(repo_root: Path) -> list[str]:
    path = repo_root / ".gitignore"
    if not path.is_file():
        return []
    patterns = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.append(stripped)
    return patterns


def _lfs_state(repo_root: Path) -> dict[str, Any]:
    attributes = repo_root / ".gitattributes"
    uses_lfs = False
    if attributes.is_file():
        content = attributes.read_text(encoding="utf-8", errors="replace")
        uses_lfs = "filter=lfs" in content
    return {
        "declared_in_gitattributes": uses_lfs,
        "command_available": shutil.which("git-lfs") is not None,
    }


def collect_repository_fingerprint(
    repo_root: Path,
    excluded_worktree_paths: Iterable[Path | str] = (),
) -> dict[str, Any]:
    """Collect a sanitized, reproducible repository fingerprint."""
    root = repo_root.resolve()
    excluded_prefixes = _normalize_excluded_worktree_paths(
        root,
        excluded_worktree_paths,
    )
    if not (root / ".git").exists() and not _git(
        root,
        "rev-parse",
        "--git-dir",
        required=False,
    ):
        raise InventoryError("The inventory root is not a Git repository")

    head_sha = _git(root, "rev-parse", "HEAD")
    current_branch = _git(
        root,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        required=False,
    ) or None

    stable = {
        "repository": {
            "name": root.name,
            "head_sha": head_sha,
            "current_branch": current_branch,
            "default_branch": _default_branch(root),
            "remotes": _collect_remotes(root),
            "branches": _collect_branches(root),
            "tags": _collect_tags(root),
            "submodules": _collect_submodules(root),
            "status": _collect_status(root, excluded_prefixes),
            "tracked_files": _tracked_file_inventory(root),
            "git_lfs": _lfs_state(root),
            "ignore_patterns": _ignore_patterns(root),
        },
        "environment": {
            "operating_system": platform.system(),
            "operating_system_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "git": _command_version("git"),
            "docker": _command_version("docker"),
            "podman": _command_version("podman"),
        },
        "collection_policy": {
            "schema_version": SCHEMA_VERSION,
            "remote_urls_sanitized": True,
            "secret_values_collected": False,
            "large_tracked_file_threshold_bytes": LARGE_TRACKED_FILE_BYTES,
            "worktree_content_hash_limit_bytes": MAX_WORKTREE_HASH_BYTES,
            "excluded_worktree_paths": list(excluded_prefixes),
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "RepositoryFingerprint",
        "generated_at": utc_now(),
        "stable_fingerprint": canonical_hash(stable),
        "stable": stable,
    }


def _iter_component_files(component_root: Path) -> tuple[list[Path], bool]:
    discovered: list[Path] = []
    truncated = False
    for current_root, directory_names, file_names in os.walk(component_root):
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in EXCLUDED_DIRECTORY_NAMES
        )
        for file_name in sorted(file_names):
            discovered.append(Path(current_root) / file_name)
            if len(discovered) >= MAX_COMPONENT_FILES:
                truncated = True
                return discovered, truncated
    return discovered, truncated


def _is_test_path(relative_path: Path) -> bool:
    lowered_parts = {part.lower() for part in relative_path.parts}
    name = relative_path.name.lower()
    return (
        "test" in lowered_parts
        or "tests" in lowered_parts
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def _is_config_path(relative_path: Path) -> bool:
    lowered = relative_path.name.lower()
    return (
        lowered in CONFIG_FILE_NAMES
        or lowered.startswith("requirements")
        or relative_path.suffix.lower() in {".ini", ".toml", ".yaml", ".yml"}
        or lowered.startswith("dockerfile")
        or lowered.startswith("compose")
        or lowered.startswith("docker-compose")
    )


def _entrypoint_kind(path: Path) -> str | None:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix in {".bat", ".cmd", ".ps1", ".sh"}:
        return "script"
    if suffix not in {".js", ".jsx", ".py", ".ts", ".tsx"}:
        return None

    conventional_name = (
        name in {"app.py", "cli.py", "main.py", "server.py"}
        or name.startswith(("run_", "start_", "launch_"))
        or name.endswith(("_cli.py", "_server.py"))
    )
    try:
        if path.stat().st_size > MAX_ENTRYPOINT_READ_BYTES:
            return "conventional_name" if conventional_name else None
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "conventional_name" if conventional_name else None

    if suffix == ".py":
        if re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", content):
            return "python_main_guard"
        if content.startswith("#!") and "python" in content.splitlines()[0].lower():
            return "python_shebang"
    else:
        if "require.main === module" in content or "import.meta.main" in content:
            return "javascript_main_guard"
        if content.startswith("#!"):
            return "javascript_shebang"
    return "conventional_name" if conventional_name else None


def _component_record(
    repo_root: Path,
    component_path: str,
    definition: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    absolute = repo_root / component_path
    if not absolute.is_dir():
        return (
            {
                "component_id": definition["component_id"],
                "path": component_path,
                "present": False,
                "presence": "absent",
                "declared_purpose": definition["declared_purpose"],
                "observed_purpose": "unknown",
                "primary_languages": [],
                "entrypoints": [],
                "tests": [],
                "configuration_files": [],
                "external_services": [],
                "data_paths": [],
                "known_agent_owner": "unknown",
                "documentation_references": [],
                "evidence": [f"filesystem:{component_path}:absent"],
                "evidence_level": "verified",
                "scan": {
                    "files_considered": 0,
                    "truncated": False,
                    "maximum_files": MAX_COMPONENT_FILES,
                },
            },
            [],
        )

    files, truncated = _iter_component_files(absolute)
    language_counts: Counter[str] = Counter()
    tests = []
    configs = []
    docs = []
    data_paths: set[str] = set()
    entrypoints = []

    for file_path in files:
        relative_to_repo = file_path.relative_to(repo_root)
        relative_to_component = file_path.relative_to(absolute)
        language = LANGUAGE_BY_SUFFIX.get(file_path.suffix.lower())
        if language:
            language_counts[language] += 1
        if _is_test_path(relative_to_component):
            tests.append(relative_to_repo.as_posix())
        if _is_config_path(relative_to_component):
            configs.append(relative_to_repo.as_posix())
        if (
            file_path.name.lower().startswith("readme")
            or file_path.suffix.lower() == ".md"
        ):
            docs.append(relative_to_repo.as_posix())
        if any(
            part.lower() in {"artifact", "artifacts", "data", "dataset", "datasets", "output", "outputs", "result", "results"}
            for part in relative_to_component.parts[:-1]
        ):
            data_paths.add(relative_to_repo.parent.as_posix())

        kind = _entrypoint_kind(file_path)
        if kind:
            entrypoints.append(
                {
                    "component_id": definition["component_id"],
                    "path": relative_to_repo.as_posix(),
                    "evidence_kind": kind,
                }
            )

    language_rank = [
        {"language": language, "file_count": count}
        for language, count in sorted(
            language_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    entrypoints.sort(key=lambda item: item["path"])
    record = {
        "component_id": definition["component_id"],
        "path": component_path,
        "present": True,
        "presence": "present",
        "declared_purpose": definition["declared_purpose"],
        "observed_purpose": "unclassified",
        "primary_languages": language_rank,
        "entrypoints": [item["path"] for item in entrypoints],
        "tests": sorted(set(tests)),
        "configuration_files": sorted(set(configs)),
        "external_services": [],
        "data_paths": sorted(data_paths),
        "known_agent_owner": "unknown",
        "documentation_references": sorted(set(docs)),
        "evidence": [f"filesystem:{component_path}:present"],
        "evidence_level": "verified",
        "scan": {
            "files_considered": len(files),
            "truncated": truncated,
            "maximum_files": MAX_COMPONENT_FILES,
        },
    }
    return record, entrypoints


def build_core_inventory(repo_root: Path) -> dict[str, Any]:
    """Build required-path coverage and mapped entrypoint evidence."""
    root = repo_root.resolve()
    head_sha = _git(root, "rev-parse", "HEAD")
    components = []
    entrypoints = []
    for component_path, definition in REQUIRED_COMPONENTS.items():
        component, component_entrypoints = _component_record(
            root,
            component_path,
            definition,
        )
        components.append(component)
        entrypoints.extend(component_entrypoints)

    entrypoint_paths = [item["path"] for item in entrypoints]
    if len(entrypoint_paths) != len(set(entrypoint_paths)):
        raise InventoryError("An entrypoint was mapped to more than one required component")

    stable = {
        "source_head_sha": head_sha,
        "scan_policy": {
            "maximum_files_per_component": MAX_COMPONENT_FILES,
            "maximum_entrypoint_read_bytes": MAX_ENTRYPOINT_READ_BYTES,
            "excluded_directory_names": sorted(EXCLUDED_DIRECTORY_NAMES),
            "operational_classification_performed": False,
        },
        "coverage": {
            "required_path_count": len(REQUIRED_COMPONENTS),
            "present_path_count": sum(item["present"] for item in components),
            "absent_path_count": sum(not item["present"] for item in components),
            "required_paths": list(REQUIRED_COMPONENTS),
        },
        "components": components,
        "entrypoints": sorted(entrypoints, key=lambda item: item["path"]),
        "contradictions": [],
        "unknowns": [
            "Operational component classifications are deferred to Phase 0 Book 3.",
            "External services and agent owners require evidence from later Book 1 parts.",
        ],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "CoreComponentInventory",
        "part_id": PART_ID,
        "status": "implemented_unverified",
        "generated_at": utc_now(),
        "stable_fingerprint": canonical_hash(stable),
        **stable,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_part1_artifacts(
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Path]:
    """Collect and atomically write the three Part 1 evidence artifacts."""
    root = repo_root.resolve()
    destination = output_dir.resolve()
    excluded_worktree_paths: tuple[Path, ...] = ()
    if destination.is_relative_to(root):
        if destination == root:
            raise InventoryError("The artifact output directory cannot be the repository root")
        excluded_worktree_paths = (destination,)
    repository_fingerprint = collect_repository_fingerprint(
        root,
        excluded_worktree_paths=excluded_worktree_paths,
    )
    core_inventory = build_core_inventory(root)
    replayed_repository_fingerprint = collect_repository_fingerprint(
        root,
        excluded_worktree_paths=excluded_worktree_paths,
    )
    if (
        replayed_repository_fingerprint["stable_fingerprint"]
        != repository_fingerprint["stable_fingerprint"]
    ):
        raise InventoryError("Repository state changed during Part 1 collection")
    repository_fingerprint = replayed_repository_fingerprint

    source_head = repository_fingerprint["stable"]["repository"]["head_sha"]
    if core_inventory["source_head_sha"] != source_head:
        raise InventoryError("Repository HEAD changed during Part 1 collection")
    if _git(root, "rev-parse", "HEAD") != source_head:
        raise InventoryError("Repository HEAD changed before Part 1 artifacts were written")

    paths = {
        "repository_fingerprint": destination / "repository-fingerprint.json",
        "core_component_inventory": destination / "core-component-inventory.json",
        "part_evidence": destination / "part-01-evidence.json",
    }
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": "BuildPartEvidence",
        "part_id": PART_ID,
        "generated_at": utc_now(),
        "source_head_sha": source_head,
        "repository_fingerprint": repository_fingerprint["stable_fingerprint"],
        "core_inventory_fingerprint": core_inventory["stable_fingerprint"],
        "artifact_files": {
            "repository_fingerprint": paths["repository_fingerprint"].name,
            "core_component_inventory": paths["core_component_inventory"].name,
        },
        "test_obligations": {
            "P0-REP-001": "not_run_by_collector",
            "P0-COV-001": "not_run_by_collector",
            "P0-COV-002": "not_run_by_collector",
            "P0-SEC-002": "not_run_by_collector",
        },
        "authority_and_capital_effect": "none",
        "operational_classification_performed": False,
        "disposition": "implemented_unverified",
    }

    _write_json(paths["repository_fingerprint"], repository_fingerprint)
    _write_json(paths["core_component_inventory"], core_inventory)
    _write_json(paths["part_evidence"], evidence)
    return paths


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect Phase 0 Book 1 Part 1 repository evidence.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Git repository root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for sanitized Part 1 JSON artifacts.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_argument_parser().parse_args(list(argv) if argv is not None else None)
    root = args.root.resolve()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    try:
        paths = write_part1_artifacts(root, output_dir)
    except InventoryError as exc:
        print(f"inventory failed: {exc}", file=sys.stderr)
        return 1

    result = {
        "part_id": PART_ID,
        "status": "implemented_unverified",
        "artifacts": {
            key: str(path.relative_to(root))
            if path.is_relative_to(root)
            else str(path)
            for key, path in paths.items()
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
