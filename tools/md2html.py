#!/usr/bin/env python3
"""
md2html.py — Markdown to Beautiful HTML Converter

Uses the md2html template + components to convert markdown files to
self-contained HTML pages with Mermaid diagrams, step cards, callouts, etc.

This is a Python wrapper that applies the md2html template to markdown files.
For the full agent-based analysis, use the /md2html skill in Claude Code.

Usage:
    python tools/md2html.py <file.md>                    # Output next to source
    python tools/md2html.py <file.md> --output x.html    # Custom output
    python tools/md2html.py --all                        # Convert all workspace docs
    python tools/md2html.py --dir skills/                # Convert directory
"""

import argparse
import re
import sys
from pathlib import Path

# Try to import markdown for basic conversion
try:
    import markdown as md_lib
except ImportError:
    md_lib = None

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
HTML_VIEWER = WORKSPACE / "html-viewer"
MD2HTML_DIR = Path(r"C:\Users\wifik\Desktop\projects\md2html")
TEMPLATE_FILE = MD2HTML_DIR / "template.html"


def load_template():
    """Load the md2html template."""
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return None


def basic_md_to_html(md_text):
    """Basic markdown to HTML conversion."""
    if md_lib:
        extensions = ['fenced_code', 'tables', 'toc', 'codehilite', 'md_in_html']
        md = md_lib.Markdown(extensions=extensions)
        return md.convert(md_text)

    # Fallback: very basic conversion
    html = md_text
    # Code blocks
    html = re.sub(r'```(\w+)\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', html, flags=re.DOTALL)
    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    # Paragraphs
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = f'<p>{html}</p>'
    return html


def convert_with_template(md_text, title="Document"):
    """Convert markdown using the md2html template."""
    template = load_template()
    if not template:
        print("[WARN] md2html template not found, using basic conversion")
        content = basic_md_to_html(md_text)
        return f"<!DOCTYPE html><html><head><title>{title}</title></head><body>{content}</body></html>"

    # Convert markdown to HTML content
    content = basic_md_to_html(md_text)

    # Extract title from first h1
    title_match = re.search(r'<h1>(.*?)</h1>', content)
    if title_match:
        title = title_match.group(1)
        content = content.replace(title_match.group(0), '', 1)

    # Replace placeholders in template
    html = template.replace('{{TITLE}}', title)
    html = html.replace('{{CONTENT}}', content)
    html = html.replace('{{PLACEHOLDER}}', content)

    return html


def convert_file(md_path, output_path=None):
    """Convert a single markdown file to HTML."""
    md_path = Path(md_path)
    if not md_path.exists():
        print(f"  [SKIP] Not found: {md_path}")
        return None

    md_text = md_path.read_text(encoding="utf-8", errors="ignore")

    # Determine title
    title_match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    title = title_match.group(1) if title_match else md_path.stem.replace("-", " ").replace("_", " ").title()

    # Convert
    html = convert_with_template(md_text, title)

    # Determine output path
    if output_path:
        out = Path(output_path)
    else:
        out = HTML_VIEWER / f"{md_path.stem}.html"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  [OK] {md_path.name} → {out.name}")
    return out


def scan_and_convert_all():
    """Scan workspace and convert all markdown files."""
    files = []

    # Root files
    for f in WORKSPACE.glob("*.md"):
        files.append(f)

    # Skills
    for f in (WORKSPACE / "skills").rglob("SKILL.md"):
        files.append(f)

    # Progress
    for f in (WORKSPACE / "progress").glob("*.md"):
        files.append(f)

    # Shared
    for f in (WORKSPACE / "shared-conversations").glob("*.md"):
        files.append(f)

    # Mermaid diagrams
    mermaid_dir = WORKSPACE / "all-mermaids"
    if mermaid_dir.exists():
        for f in mermaid_dir.rglob("*.md"):
            files.append(f)

    # Docs
    docs_dir = WORKSPACE / "docs"
    if docs_dir.exists():
        for f in docs_dir.rglob("*.md"):
            files.append(f)

    print(f"Found {len(files)} markdown files\n")

    converted = 0
    for f in sorted(set(files)):
        result = convert_file(f)
        if result:
            converted += 1

    print(f"\n✅ Converted {converted}/{len(files)} files → {HTML_VIEWER}")
    return converted


def main():
    parser = argparse.ArgumentParser(
        description="md2html — Convert Markdown to Beautiful HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", nargs="?", help="Markdown file to convert")
    parser.add_argument("--output", "-o", help="Output HTML file path")
    parser.add_argument("--all", action="store_true", help="Convert all workspace docs")
    parser.add_argument("--dir", help="Convert all .md files in directory")
    parser.add_argument("--title", help="Override document title")

    args = parser.parse_args()

    if args.all:
        scan_and_convert_all()
        return

    if args.file:
        convert_file(args.file, args.output)
        return

    if args.dir:
        d = Path(args.dir)
        for f in sorted(d.rglob("*.md")):
            convert_file(f)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
