# Spec Kit - Spec-Driven Development Toolkit

GitHub's open-source toolkit for spec-driven development. Build high-quality software faster by making specifications executable.

**Use Spec Kit when:**
- Starting a new project or feature
- You want structured AI-assisted development (constitution -> spec -> plan -> tasks -> implement)
- Working with CC (Claude Code) or other AI coding agents
- You want reproducible, auditable development workflows

**Requires:** `specify` CLI (installed via `uv tool install`)

## Quick Start

```bash
# 1. Initialize a new project
specify init my-project --integration copilot
cd my-project

# 2. Initialize in current directory
specify init . --integration copilot

# 3. Force init (overwrite existing)
specify init . --force --integration copilot
```

## The Spec-Driven Workflow

### Step 1: Constitution
Establish project governing principles and development guidelines.

```
/speckit.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements
```

### Step 2: Specify
Define what you want to build. Focus on the **what** and **why**, not the tech stack.

```
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping.
```

### Step 3: Plan
Create technical implementation plan with your chosen tech stack.

```
/speckit.plan The application uses Vite with minimal libraries. Use vanilla HTML, CSS, JavaScript. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### Step 4: Tasks
Generate actionable task list from the implementation plan.

```
/speckit.tasks
```

### Step 5: Implement
Execute all tasks and build the feature.

```
/speckit.implement
```

## Available Slash Commands

| Command | Description |
|---------|-------------|
| `/speckit.constitution` | Create/update project governing principles |
| `/speckit.specify` | Define what to build (requirements + user stories) |
| `/speckit.plan` | Create technical implementation plan |
| `/speckit.tasks` | Generate actionable task list |
| `/speckit.taskstoissues` | Convert tasks to GitHub issues |
| `/speckit.implement` | Execute all tasks |
| `/speckit.clarify` | Clarify underspecified areas (before plan) |
| `/speckit.analyze` | Cross-artifact consistency & coverage analysis |
| `/speckit.checklist` | Generate custom quality checklists |

## Supported AI Agents (30+)

Works with Claude Code, Codex CLI, Gemini CLI, Cursor, Qwen CLI, opencode, Qoder CLI, Tabnine CLI, Kiro CLI, Pi, Forge, Goose, Mistral Vibe, and more.

## CLI Reference

```bash
# List available integrations
specify integration list

# Initialize with specific integration
specify init my-project --integration codex
specify init my-project --integration gemini

# Initialize with skills mode
specify init my-project --integration codex --integration-options="--skills"

# Ignore agent tool detection
specify init my-project --integration copilot --ignore-agent-tools
```

## Extensions & Presets

- **Extensions** — Add new commands, hooks, and capabilities
- **Presets** — Customize templates, commands, and terminology
- **Project-local overrides** — `.specify/templates/overrides/`

Priority order: Project overrides > Presets > Extensions > Core

## Links

- **GitHub:** https://github.com/github/spec-kit
- **Docs:** https://github.github.io/spec-kit/
- **License:** MIT
