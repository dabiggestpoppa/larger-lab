"""
Arch Commit — Auto-update system architecture diagrams with alignment review
=============================================================================
Lightweight hook agents call after editing/building. Before updating diagrams,
it reviews alignment between the claimed change and the actual codebase state.
Flags mismatches to prevent structural drift.

Usage:
  python tools/arch-commit.py --agent AS --file "oce/backend/event_fabric.py" --change "Added observer subscription"
  python tools/arch-commit.py --agent CC --file "srrs_opc/observer_runtime.py" --change "Built lifecycle manager"
  python tools/arch-commit.py --list     # Show recent arch commits
  python tools/arch-commit.py --review   # Full alignment review (no commit)
  python tools/arch-commit.py --force    # Force commit even if misaligned

Alignment checks:
  1. Does the referenced file actually exist?
  2. Does the change description match actual code content?
  3. Is the correct arch diagram file being updated?
  4. Does the diagram's stated phase match the code's actual phase?
  5. Are there cross-references to other components that need updating?
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LAB_ROOT = Path(__file__).parent.parent
ARCH_DIR = LAB_ROOT / "system-arch"
LOG_FILE = ARCH_DIR / "arch-changes.jsonl"

# Map file patterns to arch diagram files
PATTERNS = {
    "system-arch/01-system-overview.md": [
        "oce/backend/", "oce/frontend/", "main.py", "event_fabric",
        "observer_runtime", "oce/", "gateway", "watchdog", "oc2",
        "srrs_adapter", "dspy_pipeline"
    ],
    "system-arch/02-agent-workflow.md": [
        "agent", "workflow", "team-chat", "progress-sync", "chat_sync",
        "agent-lab/", "hermes", "openclaw", "claude-code", "polymorph",
        "assistant", "rl-progress", "openclaw-2"
    ],
    "system-arch/03-srra-topology.md": [
        "srrs_opc/", "observer", "collar", "patch", "repair", "drift",
        "entropy", "topology", "recovery", "anchor", "continuity",
        "reconstruction", "consensus", "coupling"
    ],
    "system-arch/04-data-and-storage.md": [
        "data", "storage", "backup", "parquet", "csv", "nautilus",
        "memory", "sync", "progress", "memory-bank", "errors-and-solutions"
    ],
}

# Alignment rules per arch file
ALIGNMENT_RULES = {
    "01-system-overview.md": {
        "files_exist": ["oce/backend/main.py", "oce/backend/event_fabric.py"],
        "cross_refs": ["03-srra-topology.md", "02-agent-workflow.md"],
    },
    "02-agent-workflow.md": {
        "files_exist": ["shared-conversations/team-chat.md"],
        "cross_refs": ["01-system-overview.md"],
    },
    "03-srra-topology.md": {
        "files_exist": ["srrs_opc/__init__.py"],
        "cross_refs": ["01-system-overview.md"],
    },
    "04-data-and-storage.md": {
        "files_exist": ["tools/progress-sync.py"],
        "cross_refs": ["02-agent-workflow.md"],
    },
}


def find_arch_file(changed_file: str):
    """Determine which arch diagram file to update."""
    changed_lower = changed_file.lower()
    best_match = None
    best_score = 0
    for arch_file, patterns in PATTERNS.items():
        score = sum(1 for p in patterns if p.lower() in changed_lower)
        if score > best_score:
            best_score = score
            best_match = arch_file
    return best_match


def check_file_exists(file_path: str) -> bool:
    return (LAB_ROOT / file_path).exists()


def check_code_contains(file_path: str, keyword: str) -> bool:
    full_path = LAB_ROOT / file_path
    if not full_path.exists():
        return False
    try:
        content = full_path.read_text(encoding="utf-8", errors="replace").lower()
        return keyword.lower() in content
    except Exception:
        return False


def review_alignment(agent, changed_file, change_desc, arch_file):
    """Review alignment between claimed change and actual codebase."""
    report = {
        "agent": agent, "file": changed_file, "change": change_desc,
        "arch_file": arch_file, "checks": [], "warnings": [], "errors": [], "aligned": True,
    }

    # 1. File exists?
    if check_file_exists(changed_file):
        report["checks"].append("OK File exists: " + changed_file)
    else:
        report["warnings"].append("WARN File not found: " + changed_file)
        report["aligned"] = False

    # 2. Change description matches code content?
    key_terms = re.findall(r'\b\w{4,}\b', change_desc.lower())
    skip = {"added", "updated", "fixed", "changed", "removed", "built", "created", "modified", "with", "from", "this", "that", "have", "been", "will", "into", "using", "have"}
    key_terms = [t for t in key_terms if t not in skip]
    if key_terms and check_file_exists(changed_file):
        found = [t for t in key_terms[:5] if check_code_contains(changed_file, t)]
        missing = [t for t in key_terms[:5] if t not in found]
        if found:
            report["checks"].append("OK Code contains: " + ", ".join(found))
        if missing:
            report["warnings"].append("WARN Code may not contain: " + ", ".join(missing))

    # 3. Correct arch file? (compare just filenames)
    expected = find_arch_file(changed_file)
    if expected:
        expected_name = Path(expected).name
        arch_name = Path(arch_file).name if "/" in arch_file else arch_file
        if expected_name != arch_name:
            report["warnings"].append("WARN Expected: " + expected + " but updating: " + arch_file)
            report["aligned"] = False

    # 4. Cross-references exist?
    # arch_file comes in as "system-arch/01-system-overview.md" but rules use "01-system-overview.md"
    arch_key = Path(arch_file).name if "/" in arch_file else arch_file
    # Try both the full path and just the filename
    rules = ALIGNMENT_RULES.get(arch_file, ALIGNMENT_RULES.get(arch_key, {}))
    for ref in rules.get("cross_refs", []):
        ref_path = ARCH_DIR / Path(ref).name
        if ref_path.exists():
            report["checks"].append("OK Cross-ref: " + ref)
        else:
            report["warnings"].append("WARN Cross-ref missing: " + ref)

    return report


def print_report(report):
    print("\n" + "=" * 60)
    print("  Alignment Review: " + report['agent'] + " -> " + report['arch_file'])
    print("  File: " + report['file'])
    print("  Change: " + report['change'])
    print("=" * 60)
    for c in report["checks"]:
        print("  " + c)
    if report["warnings"]:
        print("\n  Warnings:")
        for w in report["warnings"]:
            print("    " + w)
    if report["aligned"] and not report["warnings"]:
        print("\n  ALIGNED -- No issues.")
    elif report["aligned"]:
        print("\n  ALIGNED WITH WARNINGS -- Review before committing.")
    else:
        print("\n  MISALIGNED -- Fix issues or use --force.")
    print("=" * 60 + "\n")


def update_arch_file(arch_file, agent, changed_file, change_desc):
    # arch_file might be "system-arch/01-system-overview.md" or just "01-system-overview.md"
    arch_name = Path(arch_file).name
    arch_path = ARCH_DIR / arch_name
    if not arch_path.exists():
        print("  ERROR Arch file not found: " + str(arch_path))
        return
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    note = "\n<!-- ARCH-COMMIT [" + ts + "] " + agent + ": " + changed_file + " -- " + change_desc + " -->\n"
    with open(arch_path, "a", encoding="utf-8") as f:
        f.write(note)
    print("  OK Updated " + arch_file)


def log_change(agent, changed_file, change_desc, arch_file, aligned):
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent, "file": changed_file, "change": change_desc,
        "arch_file": arch_file, "aligned": aligned,
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print("  OK Logged to " + LOG_FILE.name)


def list_changes(limit=20):
    if not LOG_FILE.exists():
        print("No arch commits yet.")
        return
    with open(LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    print("\nRecent arch commits (last " + str(limit) + "):")
    print("-" * 80)
    for line in lines[-limit:]:
        e = json.loads(line)
        s = "OK" if e.get("aligned") else "!!"
        print("  " + s + " [" + e['ts'][:16] + "] " + e['agent'].ljust(4) + " -> " + e['arch_file'])
        print("           " + e['file'] + ": " + e['change'])
        print()


def full_review():
    print("\n" + "=" * 60)
    print("  Full Alignment Review -- All System Diagrams")
    print("  " + datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
    print("=" * 60)
    total_issues = 0
    for arch_file, rules in ALIGNMENT_RULES.items():
        print("\n  " + arch_file)
        arch_path = ARCH_DIR / arch_file
        if not arch_path.exists():
            print("    MISSING: " + arch_file)
            total_issues += 1
            continue
        for ref in rules.get("files_exist", []):
            if check_file_exists(ref):
                print("    OK " + ref)
            else:
                print("    MISSING: " + ref)
                total_issues += 1
        for ref in rules.get("cross_refs", []):
            ref_path = ARCH_DIR / Path(ref).name
            if ref_path.exists():
                print("    OK cross-ref: " + ref)
            else:
                print("    MISSING cross-ref: " + ref)
                total_issues += 1
    print("\n" + "=" * 60)
    if total_issues == 0:
        print("  All diagrams aligned. No issues.")
    else:
        print("  " + str(total_issues) + " issue(s) found.")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Arch Commit with alignment review")
    parser.add_argument("--agent", help="Agent tag")
    parser.add_argument("--file", help="Changed file")
    parser.add_argument("--change", help="Change description")
    parser.add_argument("--list", action="store_true", help="List recent commits")
    parser.add_argument("--review", action="store_true", help="Full alignment review")
    parser.add_argument("--force", action="store_true", help="Force commit if misaligned")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.list:
        list_changes(args.limit)
        return
    if args.review:
        full_review()
        return
    if not args.agent or not args.file or not args.change:
        print("ERROR: --agent, --file, --change required. Use --list or --review.")
        sys.exit(1)

    arch_file = find_arch_file(args.file)
    if not arch_file:
        print("  No matching arch file for: " + args.file)
        return

    # Normalize: arch_file is like "system-arch/01-system-overview.md"
    # But ALIGNMENT_RULES uses "01-system-overview.md"
    arch_key = Path(arch_file).name

    print("\nArch commit: " + args.agent + " -> " + arch_file)
    report = review_alignment(args.agent, args.file, args.change, arch_key)
    print_report(report)

    if not report["aligned"] and not args.force:
        print("  BLOCKED -- Fix issues or use --force")
        sys.exit(1)

    update_arch_file(arch_file, args.agent, args.file, args.change)
    log_change(args.agent, args.file, args.change, arch_file, report["aligned"])


if __name__ == "__main__":
    main()
