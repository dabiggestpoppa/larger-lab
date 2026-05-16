# Workspace Tools & Skills Discovery Guide

> **Purpose:** Quick reference for agents to discover available tools and skills when starting a task or getting stuck on a problem.

---

## 🚀 Quick Start: How to Discover Tools & Skills

### 1. **Check Available Skills**
```bash
# List all skills in workspace
ls .agents/skills/
ls .github/skills/
```

### 2. **Check Available Tools**
```bash
# List all Python tools
ls tools/*.py
```

### 3. **Use the Right Skill**
When you encounter a problem, check if a skill exists:
- **Web/API work** → `web-coder`, `fastapi-python`, `nodejs-backend-patterns`
- **Data analysis** → `pandas-pro`, `senior-data-scientist`, `quantitative-research`
- **PDF/Docs** → `pdf`, `docx`, `pptx`, `md2html`
- **Trading** → `vectorbt-expert`, `mt5-strategy-tester`, `tradingview-quantitative`
- **AI/ML** → `scikit-learn`, `dspy`, `agentic-eval`
- **Frontend** → `frontend-design`, `next-best-practices`, `vercel-react-best-practices`
- **Pine Script** → `pine-developer`, `pine-debugger`, `pine-manager`
- **MCP** → `mcp-builder`, `mcp-cli`

---

## 🛠️ Available Tools (tools/)

### Core Workflow Tools
| Tool | Purpose | Usage |
|------|---------|-------|
| `phase-gate.py` | Phase transitions | `uv run python tools/phase-gate.py --status` |
| `progress-sync.py` | Sync agent progress | `uv run python tools/progress-sync.py --force` |
| `cc-workflow.py` | CC continuous workflow | `uv run python tools/cc-workflow.py` |
| `task-runner.py` | Run tasks | `uv run python tools/task-runner.py` |
| `workflow-runner.py` | Run workflows | `uv run python tools/workflow-runner.py` |

### Development Tools
| Tool | Purpose | Usage |
|------|---------|-------|
| `create_tool.py` | GitHub repo → agent tool pipeline | `uv run python tools/create_tool.py` |
| `md2html.py` | Convert Markdown to beautiful HTML | `uv run python tools/md2html.py <file.md>` |
| `md_to_html.py` | Batch convert all .md files | `uv run python tools/md_to_html.py` |
| `html_viewer.py` | Local HTTP server for HTML docs | `uv run python tools/html_viewer.py` |
| `cli_anything.py` | CLI-Anything wrapper | `uv run python tools/cli_anything.py` |
| `beautiful_mermaid.py` | npx wrapper for beautiful-mermaid | `uv run python tools/beautiful_mermaid.py` |

### Agent Management Tools
| Tool | Purpose | Usage |
|------|---------|-------|
| `agent-onboarding-tool.py` | Onboard new agents | `uv run python tools/agent-onboarding-tool.py` |
| `subagent_manager.py` | Manage subagents | `uv run python tools/subagent_manager.py` |
| `import_agency_agents.py` | Import 93 agency agents | `uv run python tools/import_agency_agents.py` |
| `codemap-updater.py` | Update CODEMAP.md | `uv run python tools/codemap-updater.py` |

### Gateway & Hermes Tools
| Tool | Purpose | Usage |
|------|---------|-------|
| `claude_hermes_mcp.py` | Hermes MCP bridge CLI | `uv run python tools/claude_hermes_mcp.py doctor` |
| `hermes_workflows.py` | Hermes workflow automation | `uv run python tools/hermes_workflows.py` |
| `gateway-status.cmd` | Check OC2 gateway status | `tools\gateway-status.cmd` |

---

## 📚 Available Skills (.agents/skills/)

### Core Development
- `fastapi-python` — FastAPI development
- `fastapi-templates` — FastAPI project scaffolding
- `nodejs-backend-patterns` — Node.js backend patterns
- `python-patterns` — Pythonic idioms & best practices
- `python-testing-patterns` — pytest, fixtures, mocking
- `next-best-practices` — Next.js best practices
- `next-cache-components` — Next.js 16 Cache Components

### Data & Analytics
- `pandas-pro` — DataFrame operations
- `senior-data-scientist` — Statistical modeling & analytics
- `quant-analyst` — Financial modeling & backtesting
- `quantitative-research` — Systematic trading research
- `scikit-learn` — Machine learning
- `statistical-analysis` — Statistical methods
- `vectorbt-expert` — VectorBT backtesting

### Web & Frontend
- `frontend-design` — Production-grade UI design
- `web-coder` — Web development expert
- `vercel-react-best-practices` — React performance
- `vercel-composition-patterns` — React composition
- `threejs-*` — Three.js (animation, geometry, materials, etc.)
- `seo` — Search engine optimization
- `web-design-guidelines` — UI/UX compliance

### Document Processing
- `pdf` — PDF manipulation (extract, merge, OCR, etc.)
- `docx` — Word document creation/editing
- `pptx` — PowerPoint creation/editing
- `xlsx` — Spreadsheet operations
- `md2html` — Markdown to HTML conversion

### Trading & Finance
- `mt5-strategy-tester` — MT5 Strategy Tester
- `pine-developer` — Pine Script v6 development
- `pine-debugger` — Pine Script debugging
- `pine-manager` — Trading system orchestration
- `pine-publisher` — TradingView publication
- `pine-visualizer` — Trading concept breakdown
- `tradingview-quantitative` — Quantitative analysis

### AI & Agents
- `agent-onboarding` — New agent setup
- `agent-owasp-compliance` — Security compliance
- `agent-supply-chain` — Plugin integrity
- `agentic-eval` — AI output evaluation
- `ai-ready` — AI-ready repo setup
- `mcp-builder` — MCP server creation
- `mcp-cli` — MCP server interaction
- `skill-creator` — Create/modify skills

### Specialized
- `accessibility` — WCAG 2.2 compliance
- `algorithmic-art` — p5.js generative art
- `canvas-design` — Visual design creation
- `image-manipulation-image-magick` — Image processing
- `slack-gif-creator` — Animated GIFs for Slack
- `theme-factory` — Design theme application
- `threat-model-analyst` — Security threat modeling
- `vscode-ext-localization` — VS Code extension i18n

---

## 📦 Available Skills (.github/skills/)

### GitHub & CI/CD
- `acreadiness-assess` — AI readiness assessment
- `acreadiness-generate-instructions` — Generate AI instructions
- `create-github-action-workflow-specification` — Workflow specs
- `create-github-issue-feature-from-specification` — Create issues
- `create-github-pull-request-from-specification` — Create PRs
- `create-implementation-plan` — Implementation planning
- `create-specification` — Solution specifications
- `create-technical-spike` — Technical research spikes

### Microsoft Ecosystem
- `microsoft-code-reference` — Microsoft SDK reference
- `microsoft-skill-creator` — Microsoft skill creation
- `dataverse-python-advanced-patterns` — Dataverse SDK
- `dataverse-python-quickstart` — Dataverse setup
- `typespec-api-operations` — TypeSpec API operations
- `typespec-create-api-plugin` — TypeSpec plugins

### Project Management
- `doc-coauthoring` — Documentation workflow
- `internal-comms` — Internal communications
- `tldr-prompt` — Prompt summarization
- `update-implementation-plan` — Update plans
- `update-llms` — Update llms.txt

---

## 🔍 Problem-Solving Flow

### When Starting a Task:
1. **Check if a skill exists** for your domain
2. **Read the skill file** for detailed guidance
3. **Use the appropriate tool** if available
4. **Update progress** in your agent file

### When Stuck on a Problem:
1. **List relevant skills**: `ls .agents/skills/ | grep <keyword>`
2. **Check tools**: `ls tools/*.py | grep <keyword>`
3. **Read the skill documentation** for patterns
4. **Ask the team** in `shared-conversations/team-chat.md`

---

## 📍 Key File Locations

| Purpose | Path |
|---------|------|
| Skills (workspace) | `.agents/skills/` |
| Skills (GitHub) | `.github/skills/` |
| Tools | `tools/*.py` |
| Team chat | `shared-conversations/team-chat.md` |
| Phase state | `.phase-state.json` |
| Progress sync | `tools/progress-sync.py` |
| Agent roster | `.agent-tags.json` |

---

## 🆘 Quick Reference Commands

```bash
# Check current phase
uv run python tools/phase-gate.py --status

# Sync progress
uv run python tools/progress-sync.py --force

# List all skills
ls .agents/skills/

# Find skill by keyword
ls .agents/skills/ | grep <keyword>

# Run a tool
uv run python tools/<tool-name>.py

# Check gateway status
tools\gateway-status.cmd
```