"""
OWL Continuous Memory Pipeline
==============================
Auto-captures session context, extracts concepts, updates the Obsidian vault.

This runs on heartbeat or on-demand. It:
1. Reads recent session activity
2. Extracts new concepts, decisions, errors, people
3. Creates/updates vault files with bidirectional links
4. Compresses old daily notes into archive summaries
5. Updates the MOC (Map of Content)

Usage:
    python tools/memory_pipeline.py [--full] [--compress] [--report]
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone, timedelta

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
VAULT = os.path.join(WORKSPACE, "owl-brain")
DAILY_DIR = os.path.join(VAULT, "daily")
CONCEPTS_DIR = os.path.join(VAULT, "concepts")
SYSTEMS_DIR = os.path.join(VAULT, "systems")
PEOPLE_DIR = os.path.join(VAULT, "people")
PROJECTS_DIR = os.path.join(VAULT, "projects")
ARCHIVE_DIR = os.path.join(VAULT, "archive")
INDEX_DIR = os.path.join(VAULT, "index")
DB_PATH = os.path.join(WORKSPACE, "db", "owl_health.db")

# Ensure dirs exist
for d in [DAILY_DIR, CONCEPTS_DIR, SYSTEMS_DIR, PEOPLE_DIR, PROJECTS_DIR, ARCHIVE_DIR, INDEX_DIR]:
    os.makedirs(d, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def daily_path(date_str=None):
    ds = date_str or today_str()
    return os.path.join(DAILY_DIR, f"{ds}.md")


def read_daily(date_str=None):
    p = daily_path(date_str)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def write_daily(content, date_str=None):
    p = daily_path(date_str)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)


def append_daily(section, content, date_str=None):
    """Append a section to today's daily note."""
    existing = read_daily(date_str)
    ts = datetime.now().strftime("%H:%M")
    entry = f"\n### {section} ({ts})\n{content}\n"
    if existing:
        # Check if section already exists
        if f"### {section}" in existing:
            # Append under existing section
            lines = existing.split("\n")
            new_lines = []
            inserted = False
            for i, line in enumerate(lines):
                new_lines.append(line)
                if not inserted and line.strip() == f"### {section}":
                    # Find the next ### or end of file
                    new_lines.append(content)
                    inserted = True
            existing = "\n".join(new_lines)
        else:
            existing += entry
    else:
        existing = f"# {date_str or today_str()}\n" + entry
    write_daily(existing, date_str)


def extract_wikilinks(text):
    """Extract [[wiki-links]] from text."""
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def create_concept_file(name, content):
    """Create or update a concept file."""
    safe_name = re.sub(r"[^a-zA-Z0-9\- ]", "", name).strip()
    filepath = os.path.join(CONCEPTS_DIR, f"{safe_name}.md")
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{content}\n")
        return True
    return False


def create_system_file(name, content):
    """Create or update a system file."""
    safe_name = re.sub(r"[^a-zA-Z0-9\- ]", "", name).strip()
    filepath = os.path.join(SYSTEMS_DIR, f"{safe_name}.md")
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{content}\n")
        return True
    return False


def create_project_file(name, content):
    """Create or update a project file."""
    safe_name = re.sub(r"[^a-zA-Z0-9\- ]", "", name).strip()
    filepath = os.path.join(PROJECTS_DIR, f"{safe_name}.md")
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{content}\n")
        return True
    return False


def update_moc():
    """Regenerate the Map of Content from vault files."""
    moc = "# 🦉 OWL Brain — Map of Content\n\n"
    moc += "> Auto-generated. OWL's continuous memory vault.\n\n"

    # Daily notes
    moc += "## Daily Notes\n"
    for f in sorted(os.listdir(DAILY_DIR), reverse=True):
        if f.endswith(".md"):
            name = f.replace(".md", "")
            moc += f"- [[{name}]]\n"

    # Concepts
    moc += "\n## Core Concepts\n"
    for f in sorted(os.listdir(CONCEPTS_DIR)):
        if f.endswith(".md"):
            name = f.replace(".md", "").replace("-", " ").title()
            moc += f"- [[{name}]]\n"

    # Systems
    moc += "\n## Systems\n"
    for f in sorted(os.listdir(SYSTEMS_DIR)):
        if f.endswith(".md"):
            name = f.replace(".md", "").replace("-", " ").title()
            moc += f"- [[{name}]]\n"

    # People
    moc += "\n## People\n"
    for f in sorted(os.listdir(PEOPLE_DIR)):
        if f.endswith(".md"):
            name = f.replace(".md", "")
            moc += f"- [[{name}]]\n"

    # Projects
    moc += "\n## Projects\n"
    for f in sorted(os.listdir(PROJECTS_DIR)):
        if f.endswith(".md"):
            name = f.replace(".md", "").replace("-", " ").title()
            moc += f"- [[{name}]]\n"

    moc += "\n## Active Tags\n"
    moc += "- `#status/active` — Currently being worked on\n"
    moc += "- `#status/pending` — Waiting for input or next step\n"
    moc += "- `#status/complete` — Done\n"
    moc += "- `#priority/critical` — Must address now\n"
    moc += "- `#type/bug` — Error or issue\n"
    moc += "- `#type/insight` — Learned understanding\n"
    moc += "- `#type/decision` — Made a choice\n"

    moc_path = os.path.join(INDEX_DIR, "MOC.md")
    with open(moc_path, "w", encoding="utf-8") as f:
        f.write(moc)


def capture_session_summary(summary_text):
    """Capture a session summary into today's daily note."""
    append_daily("Session Update", summary_text)
    update_moc()


def log_error_to_vault(error_dict):
    """Log an error from the self-heal scan into the vault."""
    content = f"""- **Severity:** {error_dict.get('severity', 'unknown')}
- **Category:** {error_dict.get('category', 'unknown')}
- **Occurrences:** {error_dict.get('count', 1)}
- **Status:** {'auto-resolved' if error_dict.get('resolved') else 'open'}
"""
    append_daily("Error Detected", content)


def compress_old_notes(days_old=7):
    """Compress daily notes older than N days into archive summaries."""
    cutoff = datetime.now() - timedelta(days=days_old)
    archived = 0
    for f in os.listdir(DAILY_DIR):
        if not f.endswith(".md"):
            continue
        try:
            date_str = f.replace(".md", "")
            note_date = datetime.strptime(date_str, "%Y-%m-%d")
            if note_date < cutoff:
                src = os.path.join(DAILY_DIR, f)
                # Read and extract key insights
                with open(src, "r", encoding="utf-8") as fh:
                    content = fh.read()
                # Create archive summary
                archive_name = f"{date_str}-summary.md"
                archive_path = os.path.join(ARCHIVE_DIR, archive_name)
                # Extract sections (lines starting with # or ##)
                sections = []
                for line in content.split("\n"):
                    if line.startswith("#") and not line.startswith("# "):
                        sections.append(line)
                summary = f"# {date_str} — Archive Summary\n\n"
                summary += f"Original: {len(content)} chars\n\n"
                if sections:
                    summary += "## Key Sections\n"
                    for s in sections:
                        summary += f"- {s.lstrip('#').strip()}\n"
                summary += f"\n[Full notes](daily/{f})\n"
                with open(archive_path, "w", encoding="utf-8") as fh:
                    fh.write(summary)
                archived += 1
        except (ValueError, OSError):
            continue
    return archived


def generate_vault_report():
    """Print vault statistics."""
    stats = {
        "daily_notes": len([f for f in os.listdir(DAILY_DIR) if f.endswith(".md")]),
        "concepts": len([f for f in os.listdir(CONCEPTS_DIR) if f.endswith(".md")]),
        "systems": len([f for f in os.listdir(SYSTEMS_DIR) if f.endswith(".md")]),
        "people": len([f for f in os.listdir(PEOPLE_DIR) if f.endswith(".md")]),
        "projects": len([f for f in os.listdir(PROJECTS_DIR) if f.endswith(".md")]),
        "archived": len([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".md")]),
    }
    print("\n" + "=" * 50)
    print("🦉 OWL BRAIN — Vault Report")
    print("=" * 50)
    for k, v in stats.items():
        print(f"  {k}: {v}")
    # Count total wikilinks
    total_links = 0
    for dir_path in [DAILY_DIR, CONCEPTS_DIR, SYSTEMS_DIR, PEOPLE_DIR, PROJECTS_DIR]:
        for f in os.listdir(dir_path):
            if f.endswith(".md"):
                with open(os.path.join(dir_path, f), "r", encoding="utf-8") as fh:
                    total_links += len(extract_wikilinks(fh.read()))
    print(f"  wikilinks: {total_links}")
    print("=" * 50)
    return stats


def run_full_pipeline():
    """Run the complete memory pipeline."""
    print("🧠 Running OWL Memory Pipeline...")
    # Ensure DB exists
    if WORKSPACE not in sys.path:
        sys.path.insert(0, WORKSPACE)
    from db.schema import init_db
    init_db()

    # Update MOC
    update_moc()
    print("  ✅ MOC updated")

    # Compress old notes
    archived = compress_old_notes(days_old=7)
    if archived:
        print(f"  ✅ Archived {archived} old note(s)")

    # Report
    generate_vault_report()


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--full" in args:
        run_full_pipeline()
    elif "--report" in args:
        generate_vault_report()
    elif "--compress" in args:
        n = compress_old_notes()
        print(f"Archived {n} note(s)")
    elif "--capture" in args and len(args) > 1:
        summary = " ".join(args[1:])
        capture_session_summary(summary)
        print(f"Captured: {summary[:80]}...")
    else:
        print("Usage: python tools/memory_pipeline.py [--full] [--report] [--compress] [--capture <text>]")
