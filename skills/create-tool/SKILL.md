---
name: create-tool
description: >
  Automated pipeline to turn any GitHub repository into an agent-native tool + skill.
  Full workflow: clone → analyze → build CLI harness → generate SKILL.md → install → register.
  One command does it all. Use when the user says "turn this repo into a skill",
  "make a tool from this GitHub project", "convert repo to agent tool", "build a skill from <url>",
  or any request to transform an external codebase into a workspace skill + CLI tool.
version: 1.0.0
---

# Create Tool — GitHub Repo → Agent Tool + Skill Pipeline

> **One command turns any GitHub repo into a fully integrated agent tool + skill.**
> Combines CLI-Anything's 7-phase harness methodology with automated skill generation.
> **Wrapper**: `python tools/create_tool.py`

## When to Use

| Trigger | Action |
|---------|--------|
| "Turn this repo into a skill/tool" | `python tools/create_tool.py <url>` |
| "Make a tool from <GitHub URL>" | `python tools/create_tool.py <url>` |
| "Convert this project to an agent tool" | `python tools/create_tool.py <url>` |
| "Build a skill from <repo>" | `python tools/create_tool.py <url>` |
| "Clone and integrate <software>" | `python tools/create_tool.py <url>` |
| Any GitHub URL + "tool" or "skill" intent | Run the pipeline |

## Quick Start

```bash
# Full automated pipeline (one command)
python tools/create_tool.py https://github.com/user/repo

# With options
python tools/create_tool.py https://github.com/user/repo \
  --name my-tool \
  --category creative \
  --focus "specific functionality" \
  --dry-run

# Install only (skip build, just clone + skill)
python tools/create_tool.py https://github.com/user/repo --install-only

# Build from already-cloned repo
python tools/create_tool.py C:\Users\wifik\Desktop\projects\some-repo --local
```

## Automated Pipeline (7 Phases)

```
GitHub URL
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Phase 0: Source Acquisition                         │
│   • Clone repo to C:\Users\wifik\Desktop\projects\  │
│   • Detect language, framework, package manager     │
│   • Identify project name from repo/dir             │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ Phase 1: Codebase Analysis                          │
│   • Scan README, docs, source structure             │
│   • Identify: backend engine, data model, APIs      │
│   • Map GUI actions → API calls (if applicable)     │
│   • Detect existing CLI entry points                │
│   • Classify: library / CLI / GUI / web / API       │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ Phase 2: Tool Architecture Design                   │
│   • Choose pattern: CLI wrapper / Skill only / Both │
│   • Design command groups (if CLI)                  │
│   • Plan state model + output formats               │
│   • Determine install method: pip / npx / direct    │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ Phase 3: Implementation                             │
│   • Create agent-harness/ directory structure       │
│   • Build Click-based CLI (if applicable)           │
│   • Add --json output for agent consumption         │
│   • Add REPL mode for interactive use               │
│   • Create Python wrapper for complex integrations  │
│   • Write setup.py for pip install                  │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ Phase 4: SKILL.md Generation                        │
│   • Auto-generate YAML frontmatter                  │
│   • Write description from repo README              │
│   • Document all commands + examples                │
│   • Add agent-specific guidance                     │
│   • Place in skills/<tool-name>/SKILL.md            │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ Phase 5: Installation + Registration                │
│   • pip install -e . (if Python package)            │
│   • Copy skill to all agent skill directories       │
│   • Register in .agent-tags.json                    │
│   • Update CODEMAP.md                               │
│   • Run smoke tests                                 │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│ Phase 6: Progress Sync + Team Notification          │
│   • Update progress/polymorph-progress.md           │
│   • Post to shared-conversations/team-chat.md       │
│   • Run progress-sync.py                            │
│   • Commit + push to origin/master                  │
└─────────────────────────────────────────────────────┘
```

## Tool Classification (Auto-Detected)

The pipeline auto-classifies repos and chooses the right integration pattern:

| Repo Type | Detection | Integration Pattern |
|-----------|-----------|-------------------|
| **CLI tool** | Has `setup.py`/`pyproject.toml` with `console_scripts` | Wrap existing CLI, add `--json`, generate SKILL.md |
| **Python library** | Has `setup.py`/`pyproject.toml`, no CLI | Build Click CLI wrapper + SKILL.md |
| **Node.js tool** | Has `package.json` with `bin` | Wrap with `npx`, generate SKILL.md |
| **GUI app** | Has GUI framework (Qt, Electron, etc.) | Full CLI-Anything 7-phase harness |
| **Web app/API** | Has web framework (Flask, FastAPI, Express) | Build API client CLI + SKILL.md |
| **Data/ML** | Has models, training scripts, datasets | Build pipeline CLI + SKILL.md |
| **Docs/Config** | Markdown, YAML, templates only | Skill-only (no CLI needed) |

## Output Structure

After running, the workspace will have:

```
larger-lab/
├── skills/<tool-name>/
│   └── SKILL.md              # Agent skill definition
├── tools/<tool-name>.py      # Python wrapper (if applicable)
├── C:\Users\wifik\Desktop\projects/<repo>/  # Cloned repo
│   └── agent-harness/        # Generated CLI harness (if built)
│       ├── cli_anything.<tool>/
│       │   ├── core/         # Core modules
│       │   ├── utils/        # Utilities
│       │   └── tests/        # Test suite
│       ├── setup.py          # pip install
│       └── SKILL.md          # Packaged skill copy
```

## Options

| Flag | Description |
|------|-------------|
| `--name <name>` | Override auto-detected tool name |
| `--category <cat>` | Set category: creative, productivity, ai, dev, science, gaming, network, other |
| `--focus <text>` | Specific functionality focus for gap analysis |
| `--dry-run` | Analyze only, don't build |
| `--install-only` | Clone + generate SKILL.md, skip CLI build |
| `--local` | Build from already-cloned local path |
| `--no-tests` | Skip test generation |
| `--no-sync` | Skip progress sync and team notification |

## Examples

```bash
# Turn beautiful-mermaid into a tool + skill
python tools/create_tool.py https://github.com/lukilabs/beautiful-mermaid

# Turn a quant analysis library into an agent tool
python tools/create_tool.py https://github.com/some/quant-lib --category ai

# Analyze first, then decide
python tools/create_tool.py https://github.com/user/repo --dry-run

# Quick install of a CLI-Anything pre-built skill
python tools/create_tool.py https://github.com/HKUDS/CLI-Anything --install-only

# Build from already-cloned repo with custom name
python tools/create_tool.py C:\Users\wifik\Desktop\projects\my-repo --name my-tool --local
```

## Integration with CLI-Anything

For complex GUI applications, the pipeline delegates to CLI-Anything's full 7-phase harness:

```bash
# This will use CLI-Anything for GUI apps, lightweight wrapper for libraries
python tools/create_tool.py https://github.com/GNOME/gimp
# → Detects GUI app → delegates to CLI-Anything pipeline

python tools/create_tool.py https://github.com/some/python-lib
# → Detects library → builds lightweight Click wrapper + SKILL.md
```

## Agent Skill Distribution

After creation, the skill is automatically copied to all agent skill directories:

- `skills/<tool-name>/` — Main workspace skills
- `.openclaw/skills/<tool-name>/` — OpenClaw agent
- `.hermes/skills/<tool-name>/` — Hermes persistent agent
- `agent-lab/agents/hermes/skills/<tool-name>/` — Hermes workspace agent

## Reference Files
- `tools/create_tool.py` — Main pipeline script
- `skills/cli-anything/SKILL.md` — CLI-Anything methodology
- `skills/agent-harness-sop/SKILL.md` — Agent harness SOP
- `C:\Users\wifik\Desktop\projects\CLI-Anything\cli-anything-plugin\HARNESS.md` — Full CLI-Anything spec
