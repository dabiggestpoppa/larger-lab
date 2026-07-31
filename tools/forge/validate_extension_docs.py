#!/usr/bin/env python3
"""Validate the QUANT LAB INFRA UPGRADE documentation topology."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

DEFAULT_EXTENSION = Path("QUANT-LAB-INFRA-UPGRADE")
EXPECTED_PHASES = {
    "phase-00-reality-lock": 4,
    "phase-01-forge-constitution": 4,
    "phase-02-runtime-foundry": 5,
    "phase-03-data-forge": 5,
    "phase-04-intelligence-forge": 5,
    "phase-05-discovery-forge": 5,
    "phase-06-strategy-forge": 5,
    "phase-07-validation-forge": 5,
    "phase-08-simulation-forge": 5,
    "phase-09-execution-forge": 5,
    "phase-10-portfolio-forge": 5,
    "phase-11-sovereign-operations": 5,
}
REQUIRED_ANCHORS = (
    "README.md",
    "AGENTS.md",
    "CODEX_START_HERE.md",
    "BUILD_STATUS.md",
    "GLX_FORGE_MASTER_BLUEPRINT.md",
    "GLX_FORGE_BUILD_GUIDE.md",
)
MARKDOWN_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def _issue(
    code: str,
    path: Path,
    repo_root: Path,
    detail: str,
) -> dict[str, str]:
    try:
        relative_path = path.relative_to(repo_root).as_posix()
    except ValueError:
        relative_path = str(path)
    return {"code": code, "path": relative_path, "detail": detail}


def _relative_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = target.split("#", 1)[0]
    if not target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or target.startswith("//"):
        return None
    return unquote(target)


def validate_extension_docs(
    repo_root: Path,
    extension_path: Path = DEFAULT_EXTENSION,
) -> dict[str, Any]:
    """Return a deterministic validation report for the extension corpus."""
    root = repo_root.resolve()
    extension = extension_path
    if not extension.is_absolute():
        extension = root / extension
    extension = extension.resolve()
    issues: list[dict[str, str]] = []

    if not extension.is_dir():
        issues.append(
            _issue(
                "extension_missing",
                extension,
                root,
                "The QUANT LAB INFRA UPGRADE directory does not exist",
            )
        )
        return {
            "valid": False,
            "extension": str(extension),
            "counts": {
                "markdown_files": 0,
                "phase_directories": 0,
                "phase_readmes": 0,
                "books": 0,
                "markdown_links": 0,
                "mermaid_blocks": 0,
            },
            "issues": issues,
        }

    for anchor in REQUIRED_ANCHORS:
        anchor_path = extension / anchor
        if not anchor_path.is_file():
            issues.append(
                _issue(
                    "required_anchor_missing",
                    anchor_path,
                    root,
                    f"Required extension anchor is absent: {anchor}",
                )
            )

    phases_root = extension / "phases"
    phase_directories = sorted(
        path for path in phases_root.glob("phase-*") if path.is_dir()
    )
    actual_phase_names = {path.name for path in phase_directories}
    expected_phase_names = set(EXPECTED_PHASES)
    for missing in sorted(expected_phase_names - actual_phase_names):
        issues.append(
            _issue(
                "phase_missing",
                phases_root / missing,
                root,
                f"Expected phase directory is absent: {missing}",
            )
        )
    for unexpected in sorted(actual_phase_names - expected_phase_names):
        issues.append(
            _issue(
                "unexpected_phase",
                phases_root / unexpected,
                root,
                f"Unregistered phase directory exists: {unexpected}",
            )
        )

    phase_readmes: list[Path] = []
    books: list[Path] = []
    for phase_name, expected_book_count in EXPECTED_PHASES.items():
        phase_path = phases_root / phase_name
        readme = phase_path / "README.md"
        phase_books = sorted(phase_path.glob("book-*.md"))
        if readme.is_file():
            phase_readmes.append(readme)
        else:
            issues.append(
                _issue(
                    "phase_readme_missing",
                    readme,
                    root,
                    "Every phase requires a README",
                )
            )
        books.extend(phase_books)
        if len(phase_books) != expected_book_count:
            issues.append(
                _issue(
                    "book_count_mismatch",
                    phase_path,
                    root,
                    f"Expected {expected_book_count} books; found {len(phase_books)}",
                )
            )

    markdown_files = sorted(extension.rglob("*.md"))
    markdown_links = 0
    mermaid_blocks = 0
    phase_plan_paths = set(phase_readmes + books)
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("#"):
            issues.append(
                _issue(
                    "top_heading_missing",
                    path,
                    root,
                    "Markdown files must start with a level-one heading",
                )
            )
        if text.count("```") % 2:
            issues.append(
                _issue(
                    "unbalanced_code_fence",
                    path,
                    root,
                    "The Markdown code-fence count is not balanced",
                )
            )
        path_mermaid_blocks = text.count("```mermaid")
        mermaid_blocks += path_mermaid_blocks
        if path in phase_plan_paths and path_mermaid_blocks == 0:
            issues.append(
                _issue(
                    "phase_plan_mermaid_missing",
                    path,
                    root,
                    "Every phase README and book requires a Mermaid graph",
                )
            )
        if "docs/forge" in text:
            issues.append(
                _issue(
                    "stale_extension_path",
                    path,
                    root,
                    "Replace the retired docs/forge path with QUANT-LAB-INFRA-UPGRADE",
                )
            )

        for raw_target in MARKDOWN_LINK.findall(text):
            relative_target = _relative_link_target(raw_target)
            if relative_target is None:
                continue
            markdown_links += 1
            target_path = (path.parent / relative_target).resolve()
            if not target_path.is_relative_to(root):
                issues.append(
                    _issue(
                        "link_escapes_repository",
                        path,
                        root,
                        f"Relative link escapes the repository: {raw_target}",
                    )
                )
            elif not target_path.exists():
                issues.append(
                    _issue(
                        "broken_relative_link",
                        path,
                        root,
                        f"Relative link target does not exist: {raw_target}",
                    )
                )

    issues.sort(key=lambda item: (item["path"], item["code"], item["detail"]))
    return {
        "valid": not issues,
        "extension": extension.relative_to(root).as_posix()
        if extension.is_relative_to(root)
        else str(extension),
        "counts": {
            "markdown_files": len(markdown_files),
            "phase_directories": len(phase_directories),
            "phase_readmes": len(phase_readmes),
            "books": len(books),
            "markdown_links": markdown_links,
            "mermaid_blocks": mermaid_blocks,
        },
        "issues": issues,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate QUANT LAB INFRA UPGRADE planning topology.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--extension",
        type=Path,
        default=DEFAULT_EXTENSION,
        help="Extension directory, relative to the repository root by default.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_argument_parser().parse_args(list(argv) if argv is not None else None)
    report = validate_extension_docs(args.root, args.extension)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
