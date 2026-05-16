#!/usr/bin/env python3
"""
import_agency_agents.py — Import agency-agents into larger-lab

Converts msitarzewski/agency-agents into:
  1. Workspace skills in skills/agency-<name>/
  2. HTML versions in html-viewer/
  3. Registers in .agent-tags.json

Usage:
    python tools/import_agency_agents.py                    # Import all agents
    python tools/import_agency_agents.py --division engineering  # Import one division
    python tools/import_agency_agents.py --agent engineering-frontend-developer  # Import one agent
    python tools/import_agency_agents.py --list              # List all available agents
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

AGENCY_REPO = Path(r"C:\Users\wifik\Desktop\projects\agency-agents")
WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
SKILLS_DIR = WORKSPACE / "skills"
HTML_DIR = WORKSPACE / "html-viewer"
AGENT_TAGS = WORKSPACE / ".agent-tags.json"

# Divisions to import (skip examples, .github, integrations, scripts)
DIVISIONS = [
    "academic", "design", "engineering", "finance", "game-development",
    "marketing", "paid-media", "product", "project-management", "sales",
    "spatial-computing", "specialized", "strategy", "support", "testing",
]


def parse_agent_file(md_path):
    """Parse an agent .md file and extract metadata."""
    content = md_path.read_text(encoding="utf-8", errors="ignore")

    # Extract frontmatter
    name = ""
    description = ""
    color = ""
    emoji = ""
    vibe = ""

    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for line in fm.split('\n'):
            if line.startswith('name:'):
                name = line.split(':', 1)[1].strip()
            elif line.startswith('description:'):
                description = line.split(':', 1)[1].strip()
            elif line.startswith('color:'):
                color = line.split(':', 1)[1].strip()
            elif line.startswith('emoji:'):
                emoji = line.split(':', 1)[1].strip().strip('"')
            elif line.startswith('vibe:'):
                vibe = line.split(':', 1)[1].strip().strip('"')

    # Extract identity section
    identity = ""
    id_match = re.search(r'## .*?Identity.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if id_match:
        identity = id_match.group(1).strip()[:500]

    # Extract core mission
    mission = ""
    m_match = re.search(r'## .*?Core Mission.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if m_match:
        mission = m_match.group(1).strip()[:500]

    # Create slug
    slug = md_path.stem

    return {
        "name": name or slug.replace("-", " ").title(),
        "slug": slug,
        "description": description or f"Agency agent: {name}",
        "color": color,
        "emoji": emoji,
        "vibe": vibe,
        "identity": identity,
        "mission": mission,
        "source": str(md_path),
        "division": md_path.parent.name,
        "full_content": content,
    }


def list_agents():
    """List all available agents."""
    agents = []
    for division in DIVISIONS:
        div_dir = AGENCY_REPO / division
        if not div_dir.exists():
            continue
        for md_file in sorted(div_dir.glob("*.md")):
            agent = parse_agent_file(md_file)
            agents.append(agent)
            print(f"  {agent['emoji'] or '  '} {agent['slug']:50s} [{division}] {agent['name']}")
    print(f"\nTotal: {len(agents)} agents across {len(DIVISIONS)} divisions")
    return agents


def convert_to_skill(agent):
    """Convert an agent to a workspace skill."""
    slug = agent["slug"]
    skill_dir = SKILLS_DIR / f"agency-{slug}"
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create SKILL.md from the agent content
    skill_content = f"""---
name: agency-{slug}
description: >
  {agent['description']}
  Division: {agent['division']}. Agency agent from msitarzewski/agency-agents.
version: 1.0.0
source: https://github.com/msitarzewski/agency-agents
---

{agent['full_content']}
"""

    (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
    return skill_dir


def convert_to_html(agent):
    """Convert an agent to HTML."""
    slug = agent["slug"]
    html_path = HTML_DIR / f"agency-{slug}.html"

    # Basic markdown to HTML
    content = agent["full_content"]

    # Remove frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Convert headers
    content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)

    # Convert bold/italic
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)

    # Convert code blocks
    content = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', content, flags=re.DOTALL)

    # Convert inline code
    content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)

    # Convert lists
    content = re.sub(r'^- (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)
    content = re.sub(r'(<li>.*</li>\n)+', r'<ul>\g<0></ul>', content)

    # Convert numbered lists
    content = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', content, flags=re.MULTILINE)

    # Wrap paragraphs
    content = re.sub(r'\n\n+', '</p><p>', content)
    content = f'<p>{content}</p>'

    # Clean up
    content = content.replace('<p><h', '<h').replace('</h></p>', '</h>')
    content = content.replace('<p><pre', '<pre').replace('</pre></p>', '</pre>')
    content = content.replace('<p><ul', '<ul').replace('</ul></p>', '</ul>')

    emoji = agent.get("emoji", "🎭")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{emoji} {agent['name']} — Agency Agent</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; max-width: 800px; margin: 0 auto; padding: 32px; line-height: 1.6; }}
        h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 8px; }}
        h2 {{ color: #3fb950; border-bottom: 1px solid #30363d; padding-bottom: 6px; margin-top: 28px; }}
        h3 {{ color: #d29922; }}
        code {{ background: #161b22; color: #d29922; padding: 2px 6px; border-radius: 4px; font-size: 14px; }}
        pre {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        a {{ color: #58a6ff; }}
        .meta {{ font-size: 13px; color: #6e7681; margin-bottom: 20px; padding: 8px 12px; background: #161b22; border-radius: 6px; }}
    </style>
</head>
<body>
    <div class="meta">🎭 Agency Agent · {agent['division']} division · <a href="https://github.com/msitarzewski/agency-agents">Source</a></div>
    {content}
</body>
</html>"""

    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    return html_path


def register_agent(agent):
    """Register agent in .agent-tags.json."""
    if not AGENT_TAGS.exists():
        return

    try:
        tags = json.loads(AGENT_TAGS.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        tags = {"agents": {}, "tools": []}

    agents_obj = tags.get("agents", {})

    # Use slug as key
    slug = f"agency-{agent['slug']}"
    if slug not in agents_obj:
        agents_obj[slug] = {
            "name": agent["slug"],
            "display_name": agent["name"],
            "division": agent["division"],
            "emoji": agent.get("emoji", ""),
            "skill": f"skills/agency-{agent['slug']}/SKILL.md",
            "html": f"html-viewer/agency-{agent['slug']}.html",
            "source": "msitarzewski/agency-agents",
            "added": datetime.now(timezone.utc).isoformat(),
        }
        tags["agents"] = agents_obj
        AGENT_TAGS.write_text(json.dumps(tags, indent=2))
        return True
    return False


def import_agents(division_filter=None, agent_filter=None):
    """Import agents from the agency-agents repo."""
    imported = 0
    skipped = 0

    for division in DIVISIONS:
        if division_filter and division != division_filter:
            continue

        div_dir = AGENCY_REPO / division
        if not div_dir.exists():
            continue

        for md_file in sorted(div_dir.glob("*.md")):
            if agent_filter and md_file.stem != agent_filter:
                continue

            agent = parse_agent_file(md_file)

            # Convert to skill
            skill_dir = convert_to_skill(agent)

            # Convert to HTML
            convert_to_html(agent)

            # Register
            if register_agent(agent):
                imported += 1
                print(f"  [OK] {agent['emoji'] or '  '} {agent['slug']}")
            else:
                skipped += 1

    print(f"\n✅ Imported {imported} agents ({skipped} already existed)")
    print(f"   Skills: {SKILLS_DIR}/agency-*/")
    print(f"   HTML:   {HTML_DIR}/agency-*.html")
    return imported


def main():
    parser = argparse.ArgumentParser(description="Import agency-agents into larger-lab")
    parser.add_argument("--division", help="Import only one division")
    parser.add_argument("--agent", help="Import only one agent (by slug)")
    parser.add_argument("--list", action="store_true", help="List all available agents")

    args = parser.parse_args()

    if args.list:
        list_agents()
        return

    import_agents(division_filter=args.division, agent_filter=args.agent)


if __name__ == "__main__":
    main()
