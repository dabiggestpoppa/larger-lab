---
name: cli-anything
description: >
  Build agent-native CLI harnesses for ANY software with a codebase.
  7-phase automated pipeline: analyze → design → implement → test → document → publish.
  Also install pre-built CLIs from CLI-Hub (57+ available) via `npx skills add` or `cli-hub install`.
  Use when: building a tool for GUI software, wrapping a GitHub repo as a CLI,
  installing agent-native CLIs, or making any professional software agent-accessible.
version: 1.0.0
---

# CLI-Anything — Make Any Software Agent-Native

> **Source**: [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) (Apache 2.0, 34.9k stars)
> **Core Plugin**: `cli-anything-plugin/` (in `C:\Users\wifik\Desktop\projects\CLI-Anything\`)
> **CLI-Hub**: `pip install cli-anything-hub` → browse/install 57+ pre-built CLIs
> **npx installer**: `npx skills add HKUDS/CLI-Anything --skill <name> -g -y`
> **Python wrapper**: `python tools/cli_anything.py`

## What It Does

CLI-Anything transforms any software with a source codebase into a **stateful, agent-native CLI** with:
- **REPL mode** — interactive sessions with persistent project state
- **Subcommand mode** — scriptable commands for pipelines
- **JSON output** — `--json` flag on every command for agent consumption
- **Real backend integration** — calls actual software (Blender, LibreOffice, etc.), NOT toy replacements
- **Undo/redo** — session management with history
- **2,280+ tests** across 18+ production harnesses

## When to Use

| Scenario | Action |
|----------|--------|
| Build a CLI for GUI software | Use `/cli-anything <path-or-repo>` (Claude Code) or `python tools/cli_anything.py build <path>` |
| Install a pre-built CLI | `npx skills add HKUDS/CLI-Anything --skill <name> -g -y` or `cli-hub install <name>` |
| Refine an existing harness | `/cli-anything:refine <path> [focus]` |
| Run tests for a harness | `/cli-anything:test <path>` |
| Validate a harness | `/cli-anything:validate <path>` |
| Browse available CLIs | `cli-hub list` or `npx skills add HKUDS/CLI-Anything --list` |
| Wrap a GitHub repo as a tool | `python tools/cli_anything.py build https://github.com/user/repo` |

## Quick Start

### Option A: Install Pre-built CLIs (Fastest)

```bash
# Install CLI-Hub package manager
pip install cli-anything-hub

# Browse all 57+ available CLIs
cli-hub list

# Install a specific CLI
cli-hub install gimp
cli-hub install blender
cli-hub install drawio
cli-hub install mermaid

# Use the installed CLI
cli-anything-gimp --help
cli-anything-blender  # enters REPL mode
cli-anything-drawio --json diagram new --name my-diagram
```

### Option B: npx Skills Install (Recommended for Agents)

```bash
# List all available skills
npx skills add HKUDS/CLI-Anything --list

# Install a specific skill globally
npx skills add HKUDS/CLI-Anything --skill cli-anything-gimp -g -y

# Install the meta-skill for CLI discovery
npx skills add HKUDS/CLI-Anything --skill cli-hub-meta-skill -g -y

# Install the core build skill
npx skills add HKUDS/CLI-Anything --skill cli-anything -g -y
```

### Option C: Build a New CLI Harness (Python Wrapper)

```bash
# Build from local source
python tools/cli_anything.py build C:\path\to\software

# Build from GitHub repo
python tools/cli_anything.py build https://github.com/user/repo

# Build with specific focus
python tools/cli_anything.py build ./gimp --focus "image batch processing and filters"

# Refine an existing harness
python tools/cli_anything.py refine C:\path\to\software\agent-harness

# Run tests
python tools/cli_anything.py test C:\path\to\software\agent-harness

# Validate against HARNESS.md standards
python tools/cli_anything.py validate C:\path\to\software\agent-harness
```

### Option D: Claude Code Plugin (If Using Claude Code)

```bash
# Add marketplace
/plugin marketplace add HKUDS/CLI-Anything

# Install plugin
/plugin install cli-anything

# Build a CLI in one command
/cli-anything ./gimp

# Refine
/cli-anything:refine ./gimp "batch processing"
```

## 7-Phase Build Pipeline

| Phase | Name | What It Does |
|-------|------|-------------|
| 0 | Source Acquisition | Clone repo if URL, verify local path |
| 1 | Codebase Analysis | Analyze backend, map GUI→API, find data model |
| 2 | CLI Architecture Design | Command groups, state model, output formats |
| 3 | Implementation | Click CLI + REPL + `--json` + undo/redo |
| 4 | Test Planning | Unit + E2E + subprocess test plans |
| 5 | Test Implementation | `test_core.py`, `test_e2e.py`, `test_cli.py` |
| 6 | Documentation | SKILL.md, TEST.md, architecture SOP |
| 7 | Publishing | `setup.py`, PATH install, skill registry |

## Available Pre-built CLIs (57+)

### Creative & Media
- `cli-anything-gimp` — Image editing (107 tests)
- `cli-anything-blender` — 3D modeling & rendering (208 tests)
- `cli-anything-inkscape` — Vector graphics (202 tests)
- `cli-anything-audacity` — Audio production (161 tests)
- `cli-anything-obs-studio` — Live streaming (153 tests)
- `cli-anything-kdenlive` — Video editing (155 tests)
- `cli-anything-shotcut` — Video editing (154 tests)
- `cli-anything-krita` — Digital painting
- `cli-anything-musescore` — Music notation (56 tests)
- `cli-anything-openscreen` — Screen recording editor (101 tests)
- `cli-anything-videocaptioner` — AI video captioning (26 tests)

### Productivity & Office
- `cli-anything-libreoffice` — Office suite (158 tests)
- `cli-anything-drawio` — Diagramming (138 tests)
- `cli-anything-mermaid` — Mermaid diagrams (10 tests)
- `cli-anything-mubu` — Knowledge management (96 tests)
- `cli-anything-obsidian` — Note-taking via REST API
- `cli-anything-zotero` — Reference management
- `cli-anything-notebooklm` — AI research assistant (21 tests)

### AI & ML
- `cli-anything-ollama` — Local LLM inference (98 tests)
- `cli-anything-comfyui` — AI image generation (70 tests)
- `cli-anything-anygen` — AI content generation (50 tests)
- `cli-anything-exa` — AI web search (40 tests)
- `cli-anything-novita` — OpenAI-compatible API
- `cli-anything-dify-workflow` — Dify DSL editing (11 tests)
- `cli-anything-chromadb` — Vector database
- `cli-anything-unimol-tools` — Molecular modeling (67 tests)

### Development & DevOps
- `cli-anything-n8n` — Workflow automation (55+ commands)
- `cli-anything-mailchimp` — Email marketing (303 commands)
- `cli-anything-zoom` — Video conferencing (22 tests)
- `cli-anything-wiremock` — HTTP mock server
- `cli-anything-jenkins` — CI/CD
- `cli-anything-firefly-iii` — Personal finance

### Science & Engineering
- `cli-anything-freecad` — 3D CAD (258 commands)
- `cli-anything-qgis` — Geospatial analysis (22 tests)
- `cli-anything-cloudcompare` — Point cloud processing (88 tests)
- `cli-anything-cloudanalyzer` — Point cloud QA (14 tests)
- `cli-anything-renderdoc` — GPU debugging (59 tests)
- `cli-anything-lldb` — Native debugging (27 tests)
- `cli-anything-nsight-graphics` — GPU profiling (51 tests)
- `cli-anything-unrealinsights` — UE profiling (50 tests)

### Gaming
- `cli-anything-godot` — Game engine (24 tests)
- `cli-anything-sbox` — Source 2 engine (244 tests)
- `cli-anything-slay-the-spire-ii` — Game automation

### Network & Infrastructure
- `cli-anything-adguardhome` — DNS ad blocking (36 tests)
- `cli-anything-rms` — Device management
- `cli-anything-pm2` — Node.js process management
- `cli-anything-eth2-quickstart` — Ethereum staking (18 tests)

### Browser & OS
- `cli-anything-browser` — Browser automation via DOMShell MCP
- `cli-anything-safari` — Safari automation (macOS)
- `cli-anything-iterm2` — iTerm2 control (macOS)
- `cli-anything-quietshrink` — macOS screen recording compression

## Key Architecture Patterns

### Authentic Software Integration
The CLI generates valid project files and delegates to **real applications** for rendering. No Pillow replacements for GIMP, no custom renderers for Blender.

### Dual Interaction Modes
Every CLI supports both **REPL** (interactive agent sessions) and **subcommand** (scripting/pipelines) modes.

### Agent-Native Output
Every command supports `--json` for structured agent consumption, plus human-readable tables for debugging.

### Namespace Packaging
All CLIs organized under `cli_anything.*` namespace — conflict-free, pip-installable.

## Integration with larger-lab

### Python Wrapper
`tools/cli_anything.py` provides a Python interface to the CLI-Anything pipeline:
- Build new harnesses from local paths or GitHub repos
- Refine existing harnesses with gap analysis
- Run tests and validate against HARNESS.md standards
- Install pre-built CLIs from CLI-Hub

### OpenClaw Integration
CLI-Anything skills can be installed into OpenClaw:
```bash
# Copy skill to OpenClaw skills directory
cp skills/cli-anything/SKILL.md ~/.openclaw/skills/cli-anything/SKILL.md
```

### Agent Workflow
1. **CC** identifies need for a new agent tool
2. **PM** uses CLI-Anything to build the harness (or install from CLI-Hub)
3. **AS** tests the generated CLI
4. **PM** debugs any issues
5. **All agents** can now use the new CLI tool

## Reference Files
- `C:\Users\wifik\Desktop\projects\CLI-Anything\cli-anything-plugin\HARNESS.md` — Full methodology SOP
- `C:\Users\wifik\Desktop\projects\CLI-Anything\cli-anything-plugin\commands\cli-anything.md` — Build command spec
- `C:\Users\wifik\Desktop\projects\CLI-Anything\skills\cli-hub-meta-skill\SKILL.md` — CLI-Hub catalog
- `tools/cli_anything.py` — Python wrapper for agent use
