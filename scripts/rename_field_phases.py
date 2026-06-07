#!/usr/bin/env python3
"""Rename phase directories to be valid Python module names.

Maps: 4_instrumentation -> phase4_instrumentation
      5_continuity      -> phase5_continuity
      ... etc

Also updates all import statements inside test files and __init__.py files.
"""
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent / "field"


def rename_dir(old_name: str) -> str:
    """Rename dir from 'N_xxx' to 'phaseN_xxx' and update all files inside."""
    if not old_name[0].isdigit():
        return old_name  # already renamed

    new_name = "phase" + old_name
    old_path = BASE / old_name
    new_path = BASE / new_name

    if not old_path.exists():
        return old_name

    # Rename directory
    old_path.rename(new_path)
    print(f"  [RENAMED] {old_name} -> {new_name}")

    # Update imports in all .py files inside
    pattern_import = re.compile(rf"\bfield\.{re.escape(old_name)}\b")
    pattern_import2 = re.compile(rf"\bfrom\s+{re.escape(old_name)}\b")
    pattern_init = re.compile(rf"\b{re.escape(old_name)}\b")

    files_changed = 0
    for py_file in new_path.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        original = text
        text = pattern_import.sub(f"field.{new_name}", text)
        text = pattern_import2.sub(f"from {new_name}", text)
        if text != original:
            py_file.write_text(text, encoding="utf-8")
            files_changed += 1

    print(f"    -> updated {files_changed} file(s) inside")
    return new_name


def main() -> int:
    """Rename all numeric-prefixed phase directories."""
    if not BASE.exists():
        print(f"ERROR: {BASE} does not exist")
        return 1

    print("Renaming phase directories (digit prefix -> phaseN prefix):")
    renamed = []
    for entry in sorted(BASE.iterdir()):
        if entry.is_dir() and entry.name[0].isdigit():
            new_name = rename_dir(entry.name)
            renamed.append(new_name)

    if not renamed:
        print("  (nothing to rename)")

    print(f"\n✅ Renamed {len(renamed)} directories")
    print("Renamed:")
    for n in renamed:
        print(f"  - field/{n}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
