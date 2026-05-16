# Beautiful Mermaid — Diagram Rendering Skill

> **Source**: [lukilabs/beautiful-mermaid](https://github.com/lukilabs/beautiful-mermaid) (MIT, 9k stars)
> **Purpose**: Render Mermaid diagrams as beautiful SVGs or ASCII art — fast, themeable, zero DOM deps.
> **Runtime**: Uses `npx beautiful-mermaid` (no install needed) or the Python wrapper at `tools/beautiful_mermaid.py`.

## When to Use

- User asks to create, render, or visualize a diagram (flowchart, sequence, state, class, ER, XY chart)
- User asks to generate architecture diagrams, data flows, state machines, or system diagrams
- User asks to convert Mermaid text to SVG/ASCII/image
- Any request like "draw a diagram", "visualize this flow", "render this mermaid", "create a chart"
- Agent needs to produce diagrams for documentation, reports, or team communication

## Quick Start

### Option A: Python Wrapper (Recommended for Agents)

```bash
# Render Mermaid diagram to SVG
python tools/beautiful_mermaid.py render "graph TD\nA-->B\nB-->C" --output diagram.svg

# Render with a theme
python tools/beautiful_mermaid.py render "graph LR; A-->B" --theme tokyo-night --output diagram.svg

# Render to ASCII (terminal-friendly)
python tools/beautiful_mermaid.py render "graph LR; A-->B" --format ascii

# Render to HTML (interactive, self-contained)
python tools/beautiful_mermaid.py render "graph TD\nA-->B" --output diagram.html

# List all 15 built-in themes
python tools/beautiful_mermaid.py themes

# Validate Mermaid syntax without rendering
python tools/beautiful_mermaid.py validate "graph TD\nA-->B"
```

### Option B: Direct npx (Node.js)

```bash
# Install on first use (cached after)
npx beautiful-mermaid --help
```

## Supported Diagram Types

| Type | Mermaid Prefix | Example |
|------|---------------|---------|
| Flowchart | `graph TD/LR/BT/RL` | `graph TD\nA-->B` |
| State Diagram | `stateDiagram-v2` | `stateDiagram-v2\n[*]-->Idle` |
| Sequence Diagram | `sequenceDiagram` | `sequenceDiagram\nA->>B: Hi` |
| Class Diagram | `classDiagram` | `classDiagram\nAnimal <|-- Duck` |
| ER Diagram | `erDiagram` | `erDiagram\nUSER \|\|--o{ ORDER` |
| XY Chart | `xychart-beta` | `xychart-beta\nbar [10,20,30]` |

## 15 Built-in Themes

| Theme | Type | Best For |
|-------|------|----------|
| `zinc-light` | Light | General docs, GitHub |
| `zinc-dark` | Dark | Dark mode UIs |
| `tokyo-night` | Dark | Terminal, code editors |
| `tokyo-night-storm` | Dark | Softer dark backgrounds |
| `tokyo-night-light` | Light | Light editor themes |
| `catppuccin-mocha` | Dark | Popular dark theme |
| `catppuccin-latte` | Light | Popular light theme |
| `nord` | Dark | Cool-toned dark |
| `nord-light` | Light | Cool-toned light |
| `dracula` | Dark | Vibrant dark |
| `github-light` | Light | GitHub-style |
| `github-dark` | Dark | GitHub dark mode |
| `solarized-light` | Light | Low contrast light |
| `solarized-dark` | Dark | Low contrast dark |
| `one-dark` | Dark | Atom-style dark |

## Theming

### Mono Mode (Default)
Just provide `bg` and `fg` — the entire diagram is derived via `color-mix()`:

```bash
python tools/beautiful_mermaid.py render "graph TD\nA-->B" \
  --bg "#1a1b26" --fg "#a9b1d6"
```

### Enriched Mode
Add optional enrichment colors for richer diagrams:

```bash
python tools/beautiful_mermaid.py render "graph TD\nA-->B" \
  --bg "#1a1b26" --fg "#a9b1d6" \
  --accent "#7aa2f7" --muted "#565f89" --border "#3d59a1"
```

### Color Derivation Table (Mono Mode)
| Element | Derivation |
|---------|-----------|
| Text | `--fg` at 100% |
| Secondary text | `--fg` at 60% into `--bg` |
| Connectors | `--fg` at 50% into `--bg` |
| Arrow heads | `--fg` at 85% into `--bg` |
| Node fill | `--fg` at 3% into `--bg` |
| Node stroke | `--fg` at 20% into `--bg` |

## Output Formats

| Format | Flag | Use Case |
|--------|------|----------|
| SVG | `--format svg` (default) | Web, docs, embedding |
| ASCII | `--format ascii` | Terminal, CLI, plain text |
| Unicode | `--format unicode` | Terminal with box-drawing chars |
| HTML | `--format html` | Self-contained interactive page |

## XY Charts

Bar charts, line charts, and combined:

```bash
# Bar chart
python tools/beautiful_mermaid.py render \
  "xychart-beta\ntitle \"Sales\"\nx-axis [Q1,Q2,Q3,Q4]\nbar [100,200,150,300]" \
  --theme catppuccin-mocha --output chart.svg

# Line chart
python tools/beautiful_mermaid.py render \
  "xychart-beta\ntitle \"Growth\"\nx-axis [Jan,Feb,Mar]\nline [10,25,40]" \
  --theme tokyo-night --output chart.svg

# Combined bar + line
python tools/beautiful_mermaid.py render \
  "xychart-beta\ntitle \"Revenue vs Target\"\nx-axis [Q1,Q2,Q3,Q4]\nbar [100,200,150,300]\nline [120,180,160,280]" \
  --theme nord --output chart.svg
```

## Architecture

```
skills/beautiful-mermaid/
  SKILL.md              ← You are this file
  examples/             ← Example diagrams by type
    flowchart.md
    sequence.md
    state.md
    class.md
    er.md
    xychart.md

tools/
  beautiful_mermaid.py  ← Python CLI wrapper (npx-based)
```

## Integration with Agent Workflow

1. **CC/OC/OC2**: Use for architecture diagrams in docs and team-chat
2. **AS**: Use for visual test reports and quality dashboards
3. **PM**: Use for debugging flowcharts and system topology diagrams
4. **RL (OWL)**: Use for research pipeline diagrams and data flow visualization

## Tips

- All colors are CSS custom properties on the SVG — theme switching is instant without re-rendering
- Pass CSS variable references (`var(--background)`) instead of hex for live theme switching
- SVG output is synchronous and works with React `useMemo()` — no flash
- ASCII mode works in any terminal — no dependencies needed
- For agent-to-agent communication, ASCII diagrams are ideal (copy-paste friendly)
- For documentation and reports, SVG output is best (high quality, scalable)
