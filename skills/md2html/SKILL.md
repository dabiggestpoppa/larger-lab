---
name: md2html
description: >
  Convert long-form Markdown (plans, specs, system designs, RFCs, runbooks, postmortems,
  brainstorms, notes) into a single self-contained HTML page with Mermaid diagrams,
  step timelines, callouts, pros-cons tables, comparison cards, sidebar TOC, and a
  light/dark theme. Zero install — works with any AI agent that can read/write files.
  Use when asked to "convert md to html", "make a doc readable", "render this as HTML",
  "create a visual doc", or "turn this markdown into a page".
version: 1.0.0
source: https://github.com/haidang1810/md2html
---

# md2html — Markdown to Beautiful HTML

> **Source**: [haidang1810/md2html](https://github.com/haidang1810/md2html) (MIT)
> **Purpose**: Turn long-form Markdown into self-contained HTML pages people actually want to read.
> **Not a converter — it's an analyzer.** The agent decides which sections become diagrams,
> step cards, pros-cons tables, callouts, and collapsible panels.

## When to Use

| Trigger | Action |
|---------|--------|
| "Convert this md to html" | Run md2html on the file |
| "Make this doc readable/render it" | Run md2html |
| "Create a visual/spec page" | Run md2html |
| Any long-form .md that needs to be shared | Run md2html |
| Agent produces a plan/spec/design doc | Auto-convert with md2html |

## Quick Start

### Option A: Claude Code Skill
```bash
/md2html AGENTS.md              # → AGENTS.html next to source
/md2html CODEMAP.md --out html-viewer/CODEMAP.html
```

### Option B: Python Wrapper
```bash
# Convert a single file
python tools/md2html.py AGENTS.md

# Convert with custom output
python tools/md2html.py CODEMAP.md --output html-viewer/CODEMAP.html

# Convert all workspace docs
python tools/md2html.py --all

# Convert specific directory
python tools/md2html.py --dir skills/
```

### Option C: Direct Agent Use
1. Read `C:\Users\wifik\Desktop\projects\md2html\SKILL.md`
2. Read `template.html` and `components.md` from the same directory
3. Analyze the source markdown
4. Write the HTML output next to the source file

## What It Produces

- **Sidebar TOC** with scroll-spy and anchor links
- **Mermaid diagrams** for flows, sequences, architectures
- **Step cards** with timeline rails for numbered action lists
- **Pros-cons tables** for trade-off discussions
- **Comparison cards** for option analysis (A vs B vs C)
- **Callout panels** (info, warning, success, danger)
- **Collapsible deep-dive** sections for appendices
- **Light/dark theme** toggle (Claude orange theme)
- **Self-contained** — single HTML file, no build step, no server
- **Multi-language** — auto-detects source language, translates UI labels
- **WCAG AA** contrast, ≥40px touch targets, reduced-motion support

## Component Mapping

| Markdown Pattern | HTML Component |
|-----------------|----------------|
| Numbered list of actions | Step cards with timeline rail |
| "A calls B, B writes to DB" prose | Mermaid flowchart |
| "Pros/Cons", "Trade-offs" | Two-column pros-cons box |
| "Option A vs B vs C" | Comparison cards (with ★ Recommended) |
| "Don't do X" / "Must do Y" | Danger/decision callout |
| Long appendix or code dump | Collapsible deep-dive panel |
| Key conclusion | Accent-bordered highlight box |

## Integration with larger-lab

### HTML Standard
The workspace is switching to HTML as the primary documentation format for agents.
All `.md` files are being converted to `.html` in the `html-viewer/` directory.
The HTML viewer is served at `http://127.0.0.1:8080/` via `tools/html_viewer.py`.

### Workflow
1. Agent produces or updates a `.md` file
2. `md2html` converts it to a beautiful `.html` page
3. HTML is placed in `html-viewer/` for browsing
4. All agents can read the HTML version for better comprehension

### Key Files
- `C:\Users\wifik\Desktop\projects\md2html\SKILL.md` — Agent instructions
- `C:\Users\wifik\Desktop\projects\md2html\template.html` — HTML skeleton
- `C:\Users\wifik\Desktop\projects\md2html\components.md` — Component catalog
- `tools/md2html.py` — Python wrapper
- `html-viewer/` — Output directory for all converted HTML files
