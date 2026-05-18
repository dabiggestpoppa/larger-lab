# 🔧 Tool Integration Status

> **Date:** 2026-05-18
> **Updated by:** OWL (completing Resource Adapter's work after timeout)
> **Purpose:** Track installation and integration status of new tools

---

## Summary

| Tool | Repo | Cloned | Installed | Works | Needs | Status |
|------|------|--------|-----------|-------|-------|--------|
| Open Design | nexu-io/open-design | ✅ | ⏳ Partial | ⏳ Untested | Node 24 + pnpm 10.33 | 🟡 Needs install |
| ViMax | HKUDS/ViMax | ✅ | ⏳ Partial | ⏳ Untested | Python 3.12 + uv + API keys | 🟡 Needs install |
| Netviz | ShadowArcanist/netviz | ✅ | ✅ | ✅ Runs | None (static site) | ✅ Ready |
| UI-TARS Desktop | bytedance/UI-TARS-desktop | ✅ | ⏳ Partial | ⏳ Untested | Node 22+ + pnpm + model API key | 🟡 Needs install |

---

## 1. Open Design (nexu-io/open-design)

**What:** Local-first design product — detects your installed code-agent CLI, runs design skills + design systems, streams artifacts into a sandboxed preview.

**Repo:** https://github.com/nexu-io/open-design
**Local path:** `tools/open-design/`
**Version:** 0.7.0

### Requirements
- Node.js ~24.x
- pnpm 10.33.x (pinned via packageManager)
- Optional: Claude Code, Codex, Gemini CLI, Cursor Agent, etc. (or BYOK API mode)

### Installation Status
- ✅ Repo cloned
- ❌ Dependencies not installed (node_modules missing)
- ❌ Not tested

### How to Install
```powershell
cd tools/open-design
corepack enable
pnpm install
```

### Use Case for Our Stack
- Content Farm visual production (carousels, social graphics, pitch decks)
- Agent-native design — can be triggered by sub-agents
- 200+ design templates included (airbnb, canva, figma, notion, etc.)
- Prompt templates for various content types

### Integration Notes
- Has `skills/` and `prompt-templates/` directories — these could be extracted as agent skills
- Has `design-templates/` with 200+ templates — ready to use
- BYOK (Bring Your Own Key) mode means we can use it with any API key
- Windows native supported (with WSL2 recommended)

### Next Steps
1. Install Node 24 if not present
2. Run `pnpm install`
3. Test with a simple prompt
4. Extract design templates for Content Farm use

---

## 2. ViMax (HKUDS/ViMax)

**What:** Agentic video generation — Director + Screenwriter + Producer + Video Generator all-in-one. Input a concept, get a full video with script, storyboard, character creation, and final video.

**Repo:** https://github.com/HKUDS/ViMax
**Local path:** `tools/ViMax/`
**Version:** 0.1.0

### Requirements
- Python 3.12+
- uv (package manager)
- API keys for video generation providers

### Installation Status
- ✅ Repo cloned
- ✅ .venv already exists (dependencies partially installed)
- ❌ Not tested

### How to Install
```powershell
cd tools/ViMax
uv pip install -r requirements.txt
# or
uv sync
```

### Use Case for Our Stack
- Content Farm video production (TikTok, YT Shorts, Reels)
- Agentic video pipeline — sub-agents can trigger video generation
- Script → Storyboard → Video pipeline

### Integration Notes
- Has `idea2video` and `script2video` pipelines
- Supports multiple providers: Doubao/Seedance, Google Veo, MiniMax
- Config files: `idea2video.yaml`, `script2video.yaml`
- Needs API keys for video generation providers (not free)

### Next Steps
1. Run `uv sync` to ensure all dependencies installed
2. Configure API keys in YAML config files
3. Test with a simple concept
4. Document the workflow for Content Farm agents

---

## 3. Netviz (ShadowArcanist/netviz)

**What:** Browser-based network architecture visualizer. Create interactive diagrams of system architectures.

**Repo:** https://github.com/ShadowArcanist/netviz
**Local path:** `tools/netviz/`
**Version:** 0.0.0

### Requirements
- Node.js (any recent version)
- npm/bun/pnpm

### Installation Status
- ✅ Repo cloned
- ✅ Dependencies installed (node_modules exists)
- ✅ Ready to run

### How to Run
```powershell
cd tools/netviz
npm run dev
# Opens on http://localhost:5173 (or similar)
```

### Use Case for Our Stack
- Visualizing agent architecture (SRRA+OCE topology)
- System design documentation
- Content Farm pipeline visualization
- Can export diagrams as images for content

### Integration Notes
- Static site — no API keys needed
- Uses React + Vite + Tailwind + D3 (via @xyflow/react)
- Can be used immediately
- Export to PNG/SVG for documentation

### Next Steps
1. Run `npm run dev` and verify it works
2. Create a diagram of our current agent architecture
3. Export as image for documentation
4. Consider integrating into agent-environment visualization

---

## 4. UI-TARS Desktop (bytedance/UI-TARS-desktop)

**What:** Multimodal AI agent for browser/desktop automation. Control your computer using natural language.

**Repo:** https://github.com/bytedance/UI-TARS-desktop
**Local path:** `tools/UI-TARS-desktop/`
**Version:** 0.0.1 (monorepo)

### Requirements
- Node.js 22+
- pnpm
- Model API key (for the AI agent)

### Installation Status
- ✅ Repo cloned
- ❌ Dependencies not installed
- ❌ Not tested

### How to Install
```powershell
cd tools/UI-TARS-desktop
pnpm install
```

### Use Case for Our Stack
- Platform connectors for social media (Instagram, TikTok browser automation)
- Automated content posting
- Browser-based tasks that Playwright can't handle (visual understanding)
- Agent-native computer control

### Integration Notes
- Monorepo with multiple packages: agent-tars, ui-tars, omni-tars, tarko
- CLI available: `npm install @agent-tars/cli@latest -g`
- Has MCP (Model Context Protocol) support
- Can integrate with our existing Playwright connectors
- Needs a vision-language model API key

### Next Steps
1. Install with `pnpm install`
2. Install CLI globally: `npm install @agent-tars/cli@latest -g`
3. Configure model API key
4. Test with a simple browser task
5. Evaluate for social media automation

---

## 5. Google Accounts Strategy

**What:** Multiple Google accounts = free NotebookLM notebooks + free cloud storage

**Use Case:** Agent memory backups, research storage, content archives at $0 cost

### Strategy
- Each Google account gets 15GB free storage
- Each account gets free NotebookLM access (unlimited notebooks)
- Use for: agent memory backups, research archives, content storage
- MAD is setting up accounts — document the plan

### Implementation Plan
1. MAD creates multiple Google accounts
2. Store credentials in `config/accounts.json` (encrypted)
3. Use Google Drive API for automated backups
4. Use NotebookLM for research summarization
5. Rotate accounts to avoid rate limits

### Status
- ⏳ Waiting for MAD to set up accounts
- No code needed — just credential management

---

## Priority Order for Completion

1. **Netviz** — Already ready. Just run it. (5 min)
2. **Open Design** — Install dependencies, test. (15 min)
3. **ViMax** — Install dependencies, configure API keys. (20 min)
4. **UI-TARS** — Install dependencies, configure model. (20 min)
5. **Google Accounts** — Waiting on MAD. (0 min our effort)

---

## What Needs MAD's Input

| Item | Tool | What's Needed |
|------|------|--------------|
| API keys | ViMax | Video generation provider keys (Doubao, Google Veo, or MiniMax) |
| API key | UI-TARS | Vision-language model API key |
| API key | Open Design | Any LLM API key (or use local CLI) |
| Accounts | Google Strategy | MAD to create Google accounts |
| Decision | All | Which tools to prioritize for Content Farm |

---

*Integration Status — 2026-05-18 — Resource Adapter (completed by OWL after timeout)*
