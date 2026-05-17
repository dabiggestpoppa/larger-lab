---
name: cli-anything
description: >
  Build agent-native CLI harnesses for ANY software with a codebase.
  7-phase automated pipeline: analyze → design → implement → test → document → publish.
  Also install pre-built CLIs from CLI-Hub (57+ available) via `npx skills add` or `cli-hub install`.
  Use when: building a tool for GUI software, wrapping a GitHub repo as a CLI,
  installing agent-native CLIs, or making any professional software agent-accessible.
version: 2.0.0
---

# CLI-Anything — Make Any Software Agent-Native

> **Source**: [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) (Apache 2.0, 34.9k stars)
> **Core Plugin**: `cli-anything-plugin/` (in `C:\Users\wifik\Desktop\projects\CLI-Anything\`)
> **CLI-Hub**: `pip install cli-anything-hub` → browse/install 57+ pre-built CLIs
> **npx installer**: `npx skills add HKUDS/CLI-Anything --skill <name> -g -y`
> **Python wrapper**: `python tools/cli_anything.py`

---

## 1. What Is CLI-Anything

CLI-Anything is a framework and ecosystem for making **any software agent-native**. It transforms GUI applications, web services, libraries, and internal tools into structured command-line interfaces that AI agents can discover, install, and operate programmatically.

### The Problem It Solves

Most professional software is designed for humans: graphical interfaces, visual workflows, mouse-driven interaction. AI agents can't click buttons. They need structured, text-based, composable interfaces with predictable output. CLI-Anything bridges this gap by wrapping real software backends with clean CLI harnesses that expose the same functionality through commands, subcommands, and JSON output.

### CLI-Hub — The Community Registry

CLI-Hub is a community-built registry of agent-native CLIs. Think of it as npm/pip for agent tools. Anyone can publish a CLI harness; anyone can install and use it. The hub currently hosts 57+ pre-built CLIs spanning creative tools, productivity software, AI/ML platforms, DevOps infrastructure, scientific instruments, and game engines.

```bash
# Browse the entire catalog
cli-hub search "video editing"
cli-hub search "3d modeling"
cli-hub list --category creative
```

### Architecture: HARNESS.md Progressive Disclosure

Every CLI-Anything harness is defined by a `HARNESS.md` file that follows a **progressive disclosure** pattern:

1. **Level 1 — Quick Start**: Install, first command, basic usage (30 seconds to value)
2. **Level 2 — Command Reference**: All commands, flags, and output formats
3. **Level 3 — Architecture**: State model, session management, integration points
4. **Level 4 — Extension**: How to add commands, customize behavior, contribute

This layered approach means an agent can start using a CLI from the first page, then go deeper only when needed. No 200-page manual required before the first command.

### How It Bridges AI Agents and the World's Software

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  AI Agent    │────▶│  CLI Harness  │────▶│  Real Software   │
│  (text I/O)  │◀────│  (structured) │◀────│  (Blender, GIMP, │
│              │     │  commands +   │     │   LibreOffice…)  │
│              │     │  JSON output  │     │                  │
└─────────────┘     └──────────────┘     └──────────────────┘
```

The agent sends structured commands. The CLI harness translates them into real operations on real software. Results come back as JSON the agent can parse and reason about. The agent never needs to know whether it's talking to a local process, a REST API, or a remote service.

### Key Design Principles

- **Authentic integration**: CLIs call the *real* application — no mock backends, no toy replacements
- **Dual-mode operation**: Every CLI supports both REPL (interactive) and subcommand (scriptable) modes
- **Agent-native output**: `--json` flag on every command for structured consumption
- **Session persistence**: REPL sessions maintain state across commands with undo/redo
- **Namespace packaging**: All CLIs under `cli_anything.*` — conflict-free, pip-installable

---

## 2. Using CLI-Anything

### Installation

```bash
# Install the CLI-Hub package manager
pip install cli-anything-hub

# Verify installation
cli-hub --version

# Install the Python wrapper for agent workflows
pip install cli-anything
```

### Browsing Available CLIs

```bash
# List all available CLIs
cli-hub list

# Search by keyword
cli-hub search "image editing"
cli-hub search "3d"
cli-hub search "diagram"

# Filter by category
cli-hub list --category creative
cli-hub list --category productivity
cli-hub list --category devops
cli-hub list --category ai-ml

# Show details about a specific CLI
cli-hub info blender
cli-hub info gimp
cli-hub info drawio
```

### Installing CLIs

```bash
# Install a specific CLI from CLI-Hub
cli-hub install gimp          # Image editing (107 tests)
cli-hub install blender       # 3D modeling (208 tests)
cli-hub install drawio        # Diagramming (138 tests)
cli-hub install mermaid       # Mermaid diagrams (10 tests)
cli-hub install libreoffice   # Office suite (158 tests)
cli-hub install ollama        # Local LLM inference (98 tests)
cli-hub install n8n           # Workflow automation (55+ commands)

# Install via npx (alternative method)
npx skills add HKUDS/CLI-Anything --skill cli-anything-gimp -g -y
npx skills add HKUDS/CLI-Anything --skill cli-anything-blender -g -y

# List all installable skills
npx skills add HKUDS/CLI-Anything --list
```

### Using Installed CLIs

Every installed CLI supports two interaction modes:

**Subcommand mode** (for scripts and pipelines):
```bash
# Create a new diagram and export it
cli-anything-drawio diagram new --name "system-arch" --json
cli-anything-drawio shape add --diagram "system-arch" --type rectangle --label "API"
cli-anything-drawio export --diagram "system-arch" --format svg --output ./arch.svg --json

# Batch image processing
cli-anything-gimp batch --input "*.png" --operation resize --width 1024 --height 768 --json

# 3D rendering
cli-anything-blender render --scene "product-shot" --output ./render.png --samples 256 --json
```

**REPL mode** (for interactive agent sessions):
```bash
$ cli-anything-drawio
drawio> diagram new --name "flowchart"
drawio> shape add --type diamond --label "Decision?"
drawio> shape add --type rectangle --label "Process A"
drawio> connect --from "Decision?" --to "Process A" --label "Yes"
drawio> undo
drawio> redo
drawio> export --format png --output ./flow.png
drawio> exit
```

**JSON output** (for agent consumption):
```bash
$ cli-anything-drawio diagram list --json
{
  "diagrams": [
    {"id": "diag-001", "name": "system-arch", "shapes": 12, "connections": 15},
    {"id": "diag-002", "name": "flowchart", "shapes": 4, "connections": 3}
  ],
  "total": 2
}
```

---

## 3. Creating CLI Harnesses

### HARNESS.md Format and Structure

Every CLI harness is defined by a `HARNESS.md` file. This is the single source of truth for the CLI's interface, behavior, and integration.

```markdown
# HARNESS.md — CLI for {Software Name}

## Quick Start
Installation and first command.

## Commands
### {command-name}
- **Description**: What it does
- **Usage**: `cli-name {command} [options]`
- **Options**:
  - `--flag` (type): Description
- **Output**: JSON schema or description
- **Example**: Concrete example with output

## State Model
Description of session state, persistence, and lifecycle.

## Integration
How this CLI connects to the real software backend.

## Extension
How to add new commands or customize behavior.
```

### Progressive Disclosure Pattern

The HARNESS.md file uses progressive disclosure to serve different audiences:

1. **Lines 1–30**: Quick start — get running in 30 seconds
2. **Lines 31–150**: Command reference — all commands with examples
3. **Lines 151–250**: Architecture — state model, session management, backend integration
4. **Lines 251+**: Extension — adding commands, contributing, advanced configuration

### Command Documentation Format

Every command follows this standard format:

```markdown
### command-name

**Description**: One-line description of what this command does.

**Usage**:
    cli-name command-name [arguments] [options]

**Arguments**:
    NAME       TYPE    DESCRIPTION
    name       str     Name of the resource
    path       str     File path (must exist)

**Options**:
    --format   str     Output format: json, table, raw (default: table)
    --output   str     Output file path (default: stdout)
    --force    bool    Overwrite existing files
    --json     bool    Output as JSON (equivalent to --format json)

**Returns** (JSON mode):
    {
      "status": "success",
      "data": { ... },
      "meta": {
        "command": "command-name",
        "duration_ms": 42
      }
    }

**Examples**:
    # Basic usage
    cli-name command-name my-resource

    # With options
    cli-name command-name my-resource --format json --output result.json

    # Piping to another CLI
    cli-name command-name my-resource --json | cli-other process --stdin
```

### Example: Creating a CLI Harness for a Custom Tool

Let's create a CLI harness for a hypothetical project management tool called "TaskForge":

**Step 1 — Analyze the software:**
```bash
# Understand the backend API
python tools/cli_anything.py analyze C:\tools\taskforge

# Output shows:
# - REST API at localhost:8080
# - Resources: projects, tasks, users, reports
# - Auth: API key header
# - Data format: JSON
```

**Step 2 — Design the CLI structure:**
```
taskforge
├── project
│   ├── list
│   ├── create
│   ├── update
│   └── delete
├── task
│   ├── list
│   ├── create
│   ├── update
│   ├── complete
│   └── assign
├── report
│   ├── burndown
│   ├── velocity
│   └── summary
└── config
    ├── set
    └── show
```

**Step 3 — Implement the harness:**
```python
# taskforge_cli/main.py
import click
import json
import requests
from typing import Optional

API_BASE = "http://localhost:8080/api/v1"

@click.group()
@click.option('--api-key', envvar='TASKFORGE_API_KEY', help='API key')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def cli(ctx, api_key, output_json):
    """TaskForge — Project management for agents."""
    ctx.ensure_object(dict)
    ctx.obj['api_key'] = api_key
    ctx.obj['json'] = output_json

@cli.group()
def project():
    """Manage projects."""
    pass

@project.command('list')
@click.option('--status', type=click.Choice(['active', 'archived', 'all']), default='all')
@click.pass_context
def project_list(ctx, status):
    """List all projects."""
    headers = {'Authorization': f'Bearer {ctx.obj["api_key"]}'}
    params = {'status': status} if status != 'all' else {}
    resp = requests.get(f"{API_BASE}/projects", headers=headers, params=params)
    data = resp.json()
    if ctx.obj['json']:
        click.echo(json.dumps(data, indent=2))
    else:
        for proj in data['projects']:
            click.echo(f"{proj['id']:8}  {proj['name']:30}  {proj['status']}")

@project.command('create')
@click.argument('name')
@click.option('--description', default='', help='Project description')
@click.pass_context
def project_create(ctx, name, description):
    """Create a new project."""
    headers = {'Authorization': f'Bearer {ctx.obj["api_key"]}'}
    payload = {'name': name, 'description': description}
    resp = requests.post(f"{API_BASE}/projects", headers=headers, json=payload)
    data = resp.json()
    if ctx.obj['json']:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Created project: {data['id']} — {data['name']}")

# ... additional commands for task, report, config ...

if __name__ == '__main__':
    cli(obj={})
```

**Step 4 — Write the HARNESS.md:**
```markdown
# HARNESS.md — TaskForge CLI

## Quick Start
    pip install cli-anything-taskforge
    export TASKFORGE_API_KEY="your-key"
    taskforge project list

## Commands
### project list
List all projects.
    taskforge project list [--status active|archived|all] [--json]

### project create
Create a new project.
    taskforge project create <name> [--description text] [--json]

[... additional command docs ...]
```

**Step 5 — Test and publish:**
```bash
# Run the test suite
python tools/cli_anything.py test C:\tools\taskforge\agent-harness

# Validate against HARNESS.md standards
python tools/cli_anything.py validate C:\tools\taskforge\agent-harness

# Publish to CLI-Hub
cli-hub publish C:\tools\taskforge\agent-harness
```

### Testing and Publishing to CLI-Hub

Every harness should have three test files:

```python
# tests/test_core.py — Unit tests for command logic
# tests/test_e2e.py  — End-to-end tests with real backend
# tests/test_cli.py   — CLI interface tests (Click testing)
```

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_core.py -v -k "project"
python -m pytest tests/test_e2e.py -v --timeout=30

# Validate the harness structure
python tools/cli_anything.py validate ./my-harness

# Publish to CLI-Hub (requires account)
cli-hub login
cli-hub publish ./my-harness --name my-tool --version 1.0.0
```

---

## 4. Integration with OCE

The Operator Continuity Engine (OCE) is the continuity architecture at the core of the larger-lab workspace. CLI-Anything integrates with OCE by providing agent-native interfaces to OCE's tools, observers, and memory systems.

### Creating CLI Harnesses for OCE Tools

OCE tools are Python modules in `oce/backend/`. Each can be wrapped as a CLI:

```bash
# Wrap the event fabric as a CLI
python tools/cli_anything.py build oce/backend/event_fabric.py \
    --name oce-events \
    --description "OCE Event Fabric — ingest, query, and manage events"

# Wrap the observer runtime as a CLI
python tools/cli_anything.py build oce/backend/observer_runtime.py \
    --name oce-observers \
    --description "OCE Observer Runtime — manage observer lifecycle"

# Wrap the structural memory as a CLI
python tools/cli_anything.py build oce/backend/structural_memory.py \
    --name oce-memory \
    --description "OCE Structural Memory — store, search, compress memories"
```

### Creating CLI Harnesses for SRRA-OPH Modules

SRRA-OPH modules in `srrs_opc/` can be exposed as CLIs for agent consumption:

```bash
# Wrap the topology router
python tools/cli_anything.py build srrs_opc/topology_routing.py \
    --name srrs-topology \
    --description "SRRA-OPH Topology Router — manage observer mesh connections"

# Wrap the entropy economics module
python tools/cli_anything.py build srrs_opc/entropy_economics.py \
    --name srrs-entropy \
    --description "SRRA-OPH Entropy Economics — compute and allocate cognitive resources"
```

### Creating CLI Harnesses for Operator Tools

Operator tools in `tools/operator/` control the desktop, VS Code, system, and observers:

```bash
# Wrap the desktop control tool
python tools/cli_anything.py build tools/operator/desktop-control.py \
    --name oph-desktop \
    --description "Operator Desktop Control — screen capture, input, window management"

# Wrap the observer debug tool
python tools/cli_anything.py build tools/operator/observer-debug.py \
    --name oph-observers \
    --description "Operator Observer Debug — list, status, health, events, logs"
```

### Auto-Generating CLIs from Python Modules

CLI-Anything can auto-detect Click/Typer decorators and generate HARNESS.md:

```bash
# Auto-generate from a Python module with Click commands
python tools/cli_anything.py auto-generate \
    --source tools/operator/system_operator.py \
    --output skills/cli-anything/system-operator/HARNESS.md \
    --cli-name oph-system

# Auto-generate from a FastAPI app
python tools/cli_anything.py auto-generate \
    --source oce/backend/main.py \
    --type fastapi \
    --output skills/cli-anything/oce-api/HARNESS.md \
    --cli-name oce-api
```

The auto-generator inspects the source code, extracts command signatures, docstrings, and type annotations, then produces a complete HARNESS.md with command reference, examples, and JSON output schemas.

---

## 5. Examples

### Example 1: CLI for OCE Backend Operations

```bash
# Check OCE health
oce-api health --json
# {"status": "healthy", "uptime_s": 3600, "version": "1.0.0"}

# Ingest an event
oce-api events ingest \
    --type "agent.action" \
    --source "OWL" \
    --data '{"action": "file_edit", "path": "AGENTS.md"}' \
    --json

# Query events
oce-api events query \
    --type "agent.action" \
    --since "2026-05-16T00:00:00Z" \
    --limit 50 \
    --json

# Get event statistics
oce-api events stats --json
# {"total_events": 1523, "types": {"agent.action": 890, "system.heartbeat": 633}}

# Compress old events
oce-api events compress --older-than 7d --json
# {"compressed": 234, "freed_bytes": 1048576}
```

### Example 2: CLI for Observer Management

```bash
# List all observers
oph-observers list --json
# {"observers": [{"id": "obs-001", "name": "gateway-monitor", "status": "active"}, ...]}

# Get observer health
oph-observers health obs-001 --json
# {"id": "obs-001", "status": "healthy", "last_heartbeat": "2026-05-16T22:15:00Z"}

# Activate an observer
oph-observers activate obs-002 --json
# {"id": "obs-002", "status": "active", "activated_at": "2026-05-16T22:16:00Z"}

# Suspend an observer
oph-observers suspend obs-003 --reason "maintenance" --json
# {"id": "obs-003", "status": "suspended", "reason": "maintenance"}

# View observer events
oph-observers events obs-001 --limit 20 --json

# View observer logs
oph-observers logs obs-001 --follow --level warn
```

### Example 3: CLI for Memory Operations

```bash
# Store a memory entry
oce-memory store \
    --key "decision/2026-05-16/phase-advance" \
    --value "Phase 4 advanced after 6/6 tests passing" \
    --tags "phase,srrs,success" \
    --json

# Search memories
oce-memory search --query "phase advance" --limit 10 --json
# {"results": [{"key": "decision/2026-05-16/phase-advance", "score": 0.95, ...}]}

# Get memory timeline for an observer
oce-memory timeline obs-001 --json
# {"observer": "obs-001", "entries": [...], "total": 42}

# Compress the memory layer
oce-memory compress --older-than 30d --json
# {"compressed": 156, "retained": 89, "freed_bytes": 524288}

# Export as wiki markdown
oce-memory export --output ./memory-wiki.md --format wiki

# Get memory statistics
oce-memory stats --json
# {"total_entries": 245, "total_size_bytes": 1048576, "layers": {"hot": 89, "warm": 156}}
```

### Example 4: Full Agent Workflow with CLI-Anything

```bash
# An agent performing a system health check using CLI-Anything tools:

# 1. Check OCE health
oce-api health --json
# → {"status": "healthy"}

# 2. Check all observers
oph-observers list --json
# → All 6 observers active

# 3. Check for recent errors
oce-api events query --type "system.error" --since "1h ago" --json
# → {"events": []} — no errors in the last hour

# 4. Check memory stats
oce-memory stats --json
# → {"total_entries": 245} — healthy

# 5. Log the health check result
oce-api events ingest \
    --type "system.health_check" \
    --source "OWL" \
    --data '{"status": "all_clear", "observers": 6, "errors": 0}' \
    --json

# All from a single agent turn, using structured CLI tools.
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Install CLI-Hub | `pip install cli-anything-hub` |
| Browse CLIs | `cli-hub list` or `cli-hub search <query>` |
| Install a CLI | `cli-hub install <name>` |
| Build a harness | `python tools/cli_anything.py build <path>` |
| Refine a harness | `python tools/cli_anything.py refine <path>` |
| Test a harness | `python tools/cli_anything.py test <path>` |
| Validate a harness | `python tools/cli_anything.py validate <path>` |
| Auto-generate CLI | `python tools/cli_anything.py auto-generate --source <file>` |
| Publish to CLI-Hub | `cli-hub publish <path>` |
| npx install | `npx skills add HKUDS/CLI-Anything --skill <name> -g -y` |
