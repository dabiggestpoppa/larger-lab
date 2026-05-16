#!/usr/bin/env python3
"""
cli_anything.py — CLI-Anything Pipeline Wrapper

Wrapper around the CLI-Anything methodology for building agent-native CLI harnesses.
Provides Python interface to the 7-phase pipeline.

Usage:
    python tools/cli_anything.py build <path-or-url>     # Build a new CLI harness
    python tools/cli_anything.py refine <path> [focus]    # Refine existing harness
    python tools/cli_anything.py test <path>              # Run tests
    python tools/cli_anything.py validate <path>          # Validate against HARNESS.md
    python tools/cli_anything.py list                     # List available CLI-Anything skills
    python tools/cli_anything.py install <name>           # Install from CLI-Hub
    python tools/cli_anything.py search <query>           # Search CLI-Hub
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CLI_ANYTHING_REPO = Path(r"C:\Users\wifik\Desktop\projects\CLI-Anything")
HARNESS_MD = CLI_ANYTHING_REPO / "cli-anything-plugin" / "HARNESS.md"


def run_cmd(cmd, cwd=None):
    """Run a shell command."""
    print(f"  [RUN] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[:2000])
    if result.returncode != 0 and result.stderr:
        print(f"  [ERR] {result.stderr[:500]}")
    return result.returncode == 0


def cmd_build(args):
    """Build a new CLI harness."""
    source = args.source
    print(f"[BUILD] Creating CLI harness for: {source}")
    print(f"[INFO] HARNESS.md: {HARNESS_MD}")
    print()
    print("This command is designed to be run inside Claude Code with the CLI-Anything plugin.")
    print("In Claude Code, use:")
    print(f"  /cli-anything {source}")
    print()
    print("For automated pipeline, use create_tool.py instead:")
    print(f"  python tools/create_tool.py {source}")


def cmd_refine(args):
    """Refine an existing CLI harness."""
    path = args.source
    focus = args.focus or ""
    print(f"[REFINE] Refining CLI harness at: {path}")
    if focus:
        print(f"[FOCUS] {focus}")
    print()
    print("In Claude Code, use:")
    print(f"  /cli-anything:refine {path} \"{focus}\"")


def cmd_test(args):
    """Run tests for a CLI harness."""
    path = args.source
    test_dir = Path(path) / "cli_anything"
    
    # Find test directories
    test_dirs = list(test_dir.rglob("tests")) if test_dir.exists() else []
    
    if not test_dirs:
        # Try agent-harness structure
        test_dirs = list(Path(path).rglob("tests"))
    
    if not test_dirs:
        print(f"[WARN] No test directories found in {path}")
        return False
    
    all_passed = True
    for td in test_dirs:
        print(f"\n[TEST] Running tests in: {td}")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(td), "-v", "--tb=short"],
            capture_output=True, text=True
        )
        print(result.stdout[-2000:] if result.stdout else "")
        if result.returncode != 0:
            all_passed = False
            print(f"[FAIL] Tests failed in {td}")
    
    return all_passed


def cmd_validate(args):
    """Validate a CLI harness against HARNESS.md standards."""
    path = Path(args.source)
    print(f"[VALIDATE] Checking {path} against HARNESS.md standards")
    
    issues = []
    
    # Check required files
    required = ["setup.py", "cli_anything"]
    for r in required:
        if not (path / r).exists() and not (path / "agent-harness" / r).exists():
            issues.append(f"Missing: {r}")
    
    # Check for tests
    has_tests = bool(list(path.rglob("test_*.py")) or list(path.rglob("tests/")))
    if not has_tests:
        issues.append("No test files found")
    
    # Check for SKILL.md
    has_skill = (path / "SKILL.md").exists() or bool(list(path.rglob("skills/*/SKILL.md")))
    if not has_skill:
        issues.append("No SKILL.md found")
    
    if issues:
        print("\n[ISSUES]")
        for i in issues:
            print(f"  ⚠ {i}")
    else:
        print("\n[OK] All checks passed")
    
    return len(issues) == 0


def cmd_list(args):
    """List available CLI-Anything skills."""
    skills_dir = CLI_ANYTHING_REPO / "skills"
    if not skills_dir.exists():
        print(f"[ERROR] Skills directory not found: {skills_dir}")
        return
    
    skills = sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])
    print(f"\nAvailable CLI-Anything Skills ({len(skills)}):\n")
    
    # Group by category
    categories = {}
    for s in skills:
        if s.startswith("cli-anything-"):
            cat = "CLI Harness"
        elif s == "cli-hub-meta-skill":
            cat = "Meta"
        else:
            cat = "Other"
        categories.setdefault(cat, []).append(s)
    
    for cat, items in categories.items():
        print(f"  [{cat}]")
        for item in items:
            print(f"    {item}")
        print()
    
    print("Install with: npx skills add HKUDS/CLI-Anything --skill <name> -g -y")


def cmd_install(args):
    """Install a CLI from CLI-Hub."""
    name = args.name
    print(f"[INSTALL] Installing {name} from CLI-Hub")
    
    # Try cli-hub first
    result = subprocess.run(
        ["cli-hub", "install", name],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        # Fallback: npx skills
        print(f"[FALLBACK] Trying npx skills add...")
        result = subprocess.run(
            ["npx", "skills", "add", "HKUDS/CLI-Anything", f"--skill=cli-anything-{name}", "-g", "-y"],
            capture_output=True, text=True
        )
    
    if result.stdout:
        print(result.stdout[:1000])
    if result.returncode == 0:
        print(f"[DONE] {name} installed successfully")
    else:
        print(f"[FAIL] Installation failed: {result.stderr[:500]}")


def cmd_search(args):
    """Search CLI-Hub for CLIs."""
    query = args.query
    print(f"[SEARCH] Searching CLI-Hub for: {query}")
    
    result = subprocess.run(
        ["cli-hub", "search", query],
        capture_output=True, text=True
    )
    
    if result.stdout:
        print(result.stdout)
    else:
        print(f"[INFO] No results or cli-hub not installed")
        print("Install: pip install cli-anything-hub")


def main():
    parser = argparse.ArgumentParser(
        description="CLI-Anything Pipeline Wrapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python tools/cli_anything.py build ./gimp
  python tools/cli_anything.py refine ./gimp "batch processing"
  python tools/cli_anything.py test ./gimp/agent-harness
  python tools/cli_anything.py validate ./gimp/agent-harness
  python tools/cli_anything.py list
  python tools/cli_anything.py install gimp
  python tools/cli_anything.py search "image editing"
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # build
    p_build = subparsers.add_parser("build", help="Build a new CLI harness")
    p_build.add_argument("source", help="Path or URL to software")

    # refine
    p_refine = subparsers.add_parser("refine", help="Refine an existing harness")
    p_refine.add_argument("source", help="Path to existing harness")
    p_refine.add_argument("focus", nargs="?", help="Specific focus area")

    # test
    p_test = subparsers.add_parser("test", help="Run tests for a harness")
    p_test.add_argument("source", help="Path to harness directory")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate against HARNESS.md")
    p_validate.add_argument("source", help="Path to harness directory")

    # list
    subparsers.add_parser("list", help="List available CLI-Anything skills")

    # install
    p_install = subparsers.add_parser("install", help="Install from CLI-Hub")
    p_install.add_argument("name", help="CLI name to install (e.g., gimp, blender)")

    # search
    p_search = subparsers.add_parser("search", help="Search CLI-Hub")
    p_search.add_argument("query", help="Search query")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "build": cmd_build,
        "refine": cmd_refine,
        "test": cmd_test,
        "validate": cmd_validate,
        "list": cmd_list,
        "install": cmd_install,
        "search": cmd_search,
    }

    handler = commands.get(args.command)
    if handler:
        success = handler(args)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
