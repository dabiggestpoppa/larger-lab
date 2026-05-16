#!/usr/bin/env python3
"""
md_to_html.py — Markdown to HTML Converter for Agent Memory

Converts all .md files in the workspace to styled HTML for better agent readability.
Based on ByteRover's findings: HTML is 5.9% more accurate, 42.4% cheaper, 39.2% faster
for agent memory retrieval compared to Markdown.

Usage:
    python tools/md_to_html.py                          # Convert all MD files
    python tools/md_to_html.py --file AGENTS.md         # Convert single file
    python tools/md_to_html.py --dir skills/            # Convert directory
    python tools/md_to_html.py --mermaid-only           # Only convert mermaid diagrams
    python tools/md_to_html.py --index                  # Generate index.html
    python tools/md_to_html.py --all                    # Convert everything + index
"""

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

try:
    import markdown
    from markdown.extensions import codehilite, fenced_code, tables, toc
except ImportError:
    print("ERROR: Install markdown package first: uv add markdown")
    sys.exit(1)

# ─── Constants ───────────────────────────────────────────────────────────────

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
HTML_OUTPUT = WORKSPACE / "html-viewer"
MERMAID_DIR = WORKSPACE / "all-mermaids"

# ─── HTML Template ───────────────────────────────────────────────────────────

HTML_TEMPLATE = textwrap.dedent("""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} — larger-lab</title>
        <style>
            :root {{
                --bg-primary: #0d1117;
                --bg-secondary: #161b22;
                --bg-tertiary: #21262d;
                --text-primary: #e6edf3;
                --text-secondary: #8b949e;
                --text-muted: #6e7681;
                --accent-blue: #58a6ff;
                --accent-green: #3fb950;
                --accent-orange: #d29922;
                --accent-red: #f85149;
                --accent-purple: #bc8cff;
                --accent-cyan: #39d2c0;
                --border-color: #30363d;
                --code-bg: #161b22;
                --link-color: #58a6ff;
                --success-bg: #1a3a2a;
                --warning-bg: #3a2a1a;
                --error-bg: #3a1a1a;
                --info-bg: #1a2a3a;
            }}

            * {{ margin: 0; padding: 0; box-sizing: border-box; }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
                background: var(--bg-primary);
                color: var(--text-primary);
                line-height: 1.6;
                display: flex;
                min-height: 100vh;
            }}

            /* Sidebar */
            .sidebar {{
                width: 280px;
                min-width: 280px;
                background: var(--bg-secondary);
                border-right: 1px solid var(--border-color);
                padding: 20px 0;
                position: fixed;
                height: 100vh;
                overflow-y: auto;
                z-index: 100;
            }}

            .sidebar-header {{
                padding: 0 20px 16px;
                border-bottom: 1px solid var(--border-color);
                margin-bottom: 12px;
            }}

            .sidebar-header h1 {{
                font-size: 16px;
                font-weight: 600;
                color: var(--accent-blue);
            }}

            .sidebar-header p {{
                font-size: 12px;
                color: var(--text-muted);
                margin-top: 4px;
            }}

            .sidebar-nav {{
                list-style: none;
            }}

            .nav-section {{
                padding: 8px 20px 4px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                color: var(--text-muted);
                letter-spacing: 0.5px;
            }}

            .nav-item a {{
                display: block;
                padding: 6px 20px 6px 28px;
                color: var(--text-secondary);
                text-decoration: none;
                font-size: 13px;
                transition: all 0.15s;
                border-left: 3px solid transparent;
            }}

            .nav-item a:hover {{
                color: var(--text-primary);
                background: var(--bg-tertiary);
                border-left-color: var(--accent-blue);
            }}

            .nav-item a.active {{
                color: var(--accent-blue);
                background: var(--bg-tertiary);
                border-left-color: var(--accent-blue);
            }}

            /* Main Content */
            .main {{
                margin-left: 280px;
                flex: 1;
                padding: 32px 48px;
                max-width: 960px;
            }}

            /* Typography */
            h1 {{
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 16px;
                padding-bottom: 8px;
                border-bottom: 1px solid var(--border-color);
                color: var(--text-primary);
            }}

            h2 {{
                font-size: 22px;
                font-weight: 600;
                margin: 28px 0 12px;
                padding-bottom: 6px;
                border-bottom: 1px solid var(--border-color);
                color: var(--accent-blue);
            }}

            h3 {{
                font-size: 18px;
                font-weight: 600;
                margin: 24px 0 10px;
                color: var(--accent-green);
            }}

            h4 {{
                font-size: 15px;
                font-weight: 600;
                margin: 20px 0 8px;
                color: var(--accent-orange);
            }}

            p {{ margin: 12px 0; color: var(--text-primary); }}

            a {{ color: var(--link-color); text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}

            /* Code */
            code {{
                background: var(--code-bg);
                color: var(--accent-orange);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace;
                font-size: 13px;
            }}

            pre {{
                background: var(--code-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 16px;
                overflow-x: auto;
                margin: 16px 0;
            }}

            pre code {{
                background: none;
                padding: 0;
                color: var(--text-primary);
                font-size: 13px;
                line-height: 1.5;
            }}

            /* Tables */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 16px 0;
                font-size: 14px;
            }}

            th {{
                background: var(--bg-tertiary);
                color: var(--accent-blue);
                font-weight: 600;
                text-align: left;
                padding: 10px 14px;
                border: 1px solid var(--border-color);
            }}

            td {{
                padding: 8px 14px;
                border: 1px solid var(--border-color);
                color: var(--text-primary);
            }}

            tr:nth-child(even) {{ background: var(--bg-secondary); }}

            /* Lists */
            ul, ol {{
                margin: 12px 0;
                padding-left: 24px;
            }}

            li {{
                margin: 4px 0;
                color: var(--text-primary);
            }}

            /* Blockquotes */
            blockquote {{
                border-left: 4px solid var(--accent-blue);
                background: var(--info-bg);
                padding: 12px 16px;
                margin: 16px 0;
                border-radius: 0 8px 8px 0;
            }}

            blockquote p {{
                color: var(--text-secondary);
                margin: 4px 0;
            }}

            /* Status badges */
            .badge {{
                display: inline-block;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                margin: 2px;
            }}

            .badge-success {{ background: var(--success-bg); color: var(--accent-green); }}
            .badge-warning {{ background: var(--warning-bg); color: var(--accent-orange); }}
            .badge-error {{ background: var(--error-bg); color: var(--accent-red); }}
            .badge-info {{ background: var(--info-bg); color: var(--accent-blue); }}
            .badge-purple {{ background: #2a1a3a; color: var(--accent-purple); }}

            /* Mermaid diagrams */
            .mermaid {{
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 20px;
                margin: 16px 0;
                text-align: center;
                overflow-x: auto;
            }}

            /* Horizontal rule */
            hr {{
                border: none;
                border-top: 1px solid var(--border-color);
                margin: 24px 0;
            }}

            /* File metadata */
            .file-meta {{
                font-size: 12px;
                color: var(--text-muted);
                margin-bottom: 20px;
                padding: 8px 12px;
                background: var(--bg-secondary);
                border-radius: 6px;
                border: 1px solid var(--border-color);
            }}

            /* Agent tag colors */
            .agent-cc {{ color: #58a6ff; }}
            .agent-oc {{ color: #bc8cff; }}
            .agent-oc2 {{ color: #d29922; }}
            .agent-as {{ color: #39d2c0; }}
            .agent-pm {{ color: #f85149; }}
            .agent-rl {{ color: #3fb950; }}

            /* Responsive */
            @media (max-width: 768px) {{
                .sidebar {{ display: none; }}
                .main {{ margin-left: 0; padding: 16px; }}
            }}
        </style>
        {mermaid_script}
    </head>
    <body>
        {sidebar}
        <div class="main">
            {content}
        </div>
        {mermaid_init}
    </body>
    </html>
    """)

SIDEBAR_TEMPLATE = textwrap.dedent("""\
    <nav class="sidebar">
        <div class="sidebar-header">
            <h1>🦅 larger-lab</h1>
            <p>Agent Workspace — HTML View</p>
        </div>
        <ul class="sidebar-nav">
            {nav_items}
        </ul>
    </nav>
    """)


def build_sidebar(active_file="", files_index=None):
    """Build sidebar navigation from file index."""
    if not files_index:
        return ""

    sections = {}
    for f in files_index:
        section = f.get("section", "Other")
        sections.setdefault(section, []).append(f)

    nav_html = ""
    order = ["Core", "Agents", "Skills", "Progress", "Shared", "Docs", "Other"]
    for section in order:
        if section not in sections:
            continue
        nav_html += f'<li class="nav-section">{section}</li>\n'
        for f in sections[section]:
            active_class = ' class="active"' if f["html"] == active_file else ""
            nav_html += f'<li class="nav-item"><a href="{f["html"]}"{active_class}>{f["label"]}</a></li>\n'

    # Any remaining sections
    for section, items in sections.items():
        if section in order:
            continue
        nav_html += f'<li class="nav-section">{section}</li>\n'
        for f in items:
            active_class = ' class="active"' if f["html"] == active_file else ""
            nav_html += f'<li class="nav-item"><a href="{f["html"]}"{active_class}>{f["label"]}</a></li>\n'

    return SIDEBAR_TEMPLATE.format(nav_items=nav_html)


def md_to_html_content(md_text, file_path=""):
    """Convert markdown text to HTML content (without wrapper)."""
    extensions = [
        'fenced_code',
        'tables',
        'toc',
        'codehilite',
        'md_in_html',
    ]

    md = markdown.Markdown(extensions=extensions)
    html = md.convert(md_text)

    # Convert mermaid code blocks to mermaid divs
    html = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        r'<div class="mermaid">\1</div>',
        html,
        flags=re.DOTALL
    )

    # Also handle plain mermaid blocks
    html = re.sub(
        r'<pre><code>mermaid\n(.*?)</code></pre>',
        r'<div class="mermaid">\1</div>',
        html,
        flags=re.DOTALL
    )

    # Add status badge classes
    html = html.replace('✅', '<span class="badge badge-success">✅</span>')
    html = html.replace('⏳', '<span class="badge badge-warning">⏳</span>')
    html = html.replace('❌', '<span class="badge badge-error">❌</span>')
    html = html.replace('📋', '<span class="badge badge-info">📋</span>')
    html = html.replace('🔄', '<span class="badge badge-purple">🔄</span>')

    # Color agent tags
    agent_colors = {
        '🔵 CC': '<span class="agent-cc">🔵 CC</span>',
        '🟣 OC': '<span class="agent-oc">🟣 OC</span>',
        '🟠 OC2': '<span class="agent-oc2">🟠 OC2</span>',
        '🟡 AS': '<span class="agent-as">🟡 AS</span>',
        '🔴 PM': '<span class="agent-pm">🔴 PM</span>',
        '🟢 RL': '<span class="agent-rl">🟢 RL</span>',
    }
    for tag, colored in agent_colors.items():
        html = html.replace(tag, colored)

    return html


def convert_file(md_path, output_dir, files_index=None):
    """Convert a single MD file to HTML."""
    md_path = Path(md_path)
    if not md_path.exists():
        print(f"  [SKIP] Not found: {md_path}")
        return None

    md_text = md_path.read_text(encoding="utf-8", errors="ignore")
    html_content = md_to_html_content(md_text, str(md_path))

    # Determine output path — use parent dir name to avoid collisions
    rel_path = md_path.relative_to(WORKSPACE) if str(md_path).startswith(str(WORKSPACE)) else md_path.name
    # For files like skills/*/SKILL.md, use parent dir name instead of "SKILL.html"
    if md_path.stem.upper() == "SKILL" and md_path.parent.name:
        html_name = f"skill-{md_path.parent.name}.html"
    elif md_path.stem.upper() == "README" and md_path.parent != WORKSPACE:
        html_name = f"readme-{md_path.parent.name}.html"
    else:
        html_name = md_path.stem + ".html"
    html_path = output_dir / html_name

    # Check if this file has mermaid diagrams
    has_mermaid = "```mermaid" in md_text or "mermaid" in md_text.lower()
    mermaid_script = ""
    mermaid_init = ""
    if has_mermaid:
        mermaid_script = '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'
        mermaid_init = '<script>mermaid.initialize({startOnLoad:true, theme:"dark"});</script>'

    # Build sidebar
    sidebar = build_sidebar(html_name, files_index) if files_index else ""

    # Determine title
    title = md_path.stem.replace("-", " ").replace("_", " ").title()

    # File metadata
    stat = md_path.stat()
    meta = f'<div class="file-meta">📄 {rel_path} · {stat.st_size:,} bytes · Modified: {datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")}</div>'

    # Full HTML
    full_html = HTML_TEMPLATE.format(
        title=title,
        sidebar=sidebar,
        content=meta + html_content,
        mermaid_script=mermaid_script,
        mermaid_init=mermaid_init,
    )

    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(full_html, encoding="utf-8")
    print(f"  [OK] {rel_path} → {html_path.name}")
    return html_path


def scan_workspace():
    """Scan workspace for all MD files and build index."""
    files = []

    # Root files
    root_files = [
        ("AGENTS.md", "AGENTS.md", "Agent Roster"),
        ("CLAUDE.md", "CLAUDE.md", "12-Rule Contract"),
        ("CODEMAP.md", "CODEMAP.md", "Code Map"),
        ("MEMORY.md", "MEMORY.md", "Memory"),
        ("SOUL.md", "SOUL.md", "Soul"),
        ("IDENTITY.md", "IDENTITY.md", "Identity"),
        ("SYSTEM_ARCHITECTURE.md", "SYSTEM_ARCHITECTURE.md", "Architecture"),
        ("WORKFLOW_PROTOCOL.md", "WORKFLOW_PROTOCOL.md", "Workflow"),
        ("TEAMS.md", "TEAMS.md", "Teams"),
        ("TOOLS.md", "TOOLS.md", "Tools"),
        ("USER.md", "USER.md", "User"),
        ("README.md", "README.md", "README"),
        ("HEARTBEAT.md", "HEARTBEAT.md", "Heartbeat"),
        ("ERROR_CLASSIFICATION.md", "ERROR_CLASSIFICATION.md", "Error Classification"),
        ("PROJECT_PROGRESS_CLEAN.md", "PROJECT_PROGRESS_CLEAN.md", "Progress"),
    ]

    for fname, html_name, label in root_files:
        fpath = WORKSPACE / fname
        if fpath.exists():
            files.append({
                "md": str(fpath),
                "html": html_name,
                "label": label,
                "section": "Core",
            })

    # Skills
    skills_dir = WORKSPACE / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    files.append({
                        "md": str(skill_md),
                        "html": f"skill-{skill_dir.name}.html",
                        "label": f"Skill: {skill_dir.name}",
                        "section": "Skills",
                    })

    # Progress files
    progress_dir = WORKSPACE / "progress"
    if progress_dir.exists():
        for pf in sorted(progress_dir.glob("*.md")):
            files.append({
                "md": str(pf),
                "html": f"progress-{pf.stem}.html",
                "label": f"Progress: {pf.stem}",
                "section": "Progress",
            })

    # Shared conversations
    shared_dir = WORKSPACE / "shared-conversations"
    if shared_dir.exists():
        for sf in sorted(shared_dir.glob("*.md")):
            files.append({
                "md": str(sf),
                "html": f"shared-{sf.stem}.html",
                "label": f"Chat: {sf.stem}",
                "section": "Shared",
            })

    # Mermaid diagrams
    if MERMAID_DIR.exists():
        for mmd in sorted(MERMAID_DIR.rglob("*.md")):
            rel = mmd.relative_to(MERMAID_DIR)
            files.append({
                "md": str(mmd),
                "html": f"mermaid-{mmd.stem}.html",
                "label": f"📊 {rel}",
                "section": "Diagrams",
            })

    # Docs
    docs_dir = WORKSPACE / "docs"
    if docs_dir.exists():
        for df in sorted(docs_dir.rglob("*.md")):
            rel = df.relative_to(docs_dir)
            files.append({
                "md": str(df),
                "html": f"doc-{df.stem}.html",
                "label": f"Doc: {rel}",
                "section": "Docs",
            })

    return files


def generate_index(files, output_dir):
    """Generate index.html with links to all converted files."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    sections = {}
    for f in files:
        sections.setdefault(f["section"], []).append(f)

    content_parts = [f'<p class="file-meta">Generated: {now} · {len(files)} files · larger-lab workspace</p>']

    order = ["Core", "Agents", "Skills", "Progress", "Shared", "Docs", "Diagrams", "Other"]
    for section in order:
        if section not in sections:
            continue
        items = sections[section]
        content_parts.append(f'<h2>{section} ({len(items)})</h2>')
        content_parts.append('<ul>')
        for f in items:
            content_parts.append(f'<li><a href="{f["html"]}">{f["label"]}</a></li>')
        content_parts.append('</ul>')

    sidebar = build_sidebar("index.html", files)
    mermaid_script = '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'
    mermaid_init = '<script>mermaid.initialize({startOnLoad:true, theme:"dark"});</script>'

    html = HTML_TEMPLATE.format(
        title="Index",
        sidebar=sidebar,
        content="\n".join(content_parts),
        mermaid_script=mermaid_script,
        mermaid_init=mermaid_init,
    )

    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"\n  [INDEX] → {index_path}")
    return index_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert Markdown to HTML for agent memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Convert single file")
    parser.add_argument("--dir", help="Convert directory")
    parser.add_argument("--mermaid-only", action="store_true", help="Only mermaid diagrams")
    parser.add_argument("--index", action="store_true", help="Generate index.html only")
    parser.add_argument("--all", action="store_true", help="Convert everything + index")
    parser.add_argument("--output", default=str(HTML_OUTPUT), help="Output directory")

    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.index:
        files = scan_workspace()
        generate_index(files, output_dir)
        return

    if args.file:
        convert_file(args.file, output_dir)
        return

    if args.dir:
        d = Path(args.dir)
        for md_file in sorted(d.rglob("*.md")):
            convert_file(md_file, output_dir)
        return

    # Default: scan and convert everything
    print("Scanning workspace...")
    files = scan_workspace()
    print(f"Found {len(files)} markdown files\n")

    if args.mermaid_only:
        files = [f for f in files if f["section"] == "Diagrams"]

    # Convert all files
    converted = 0
    for f in files:
        result = convert_file(f["md"], output_dir, files)
        if result:
            converted += 1

    # Generate index
    generate_index(files, output_dir)

    print(f"\n✅ Converted {converted}/{len(files)} files → {output_dir}")
    print(f"   Open: {output_dir / 'index.html'}")


if __name__ == "__main__":
    main()
