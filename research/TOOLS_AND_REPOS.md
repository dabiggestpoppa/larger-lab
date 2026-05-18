# 🔧 Tools & Repos — MAD's Recommendations

> **Date:** 2026-05-18 08:28 EDT
> **Source:** MAD's GitHub links + tweet
> **Purpose:** Evaluate and integrate into our stack

---

## 1. Open Design (nexu-io/open-design) ⭐ 40k+ stars

**What it is:** Open-source alternative to Claude Design. Local-first, BYOK, agent-native design tool.

**How it works:**
- 19 composable Skills + 71 brand-grade Design Systems
- Auto-detects 16 coding-agent CLIs on your PATH (Claude Code, Codex, Cursor, Gemini, OpenCode, Qwen, Copilot, Hermes, etc.)
- Agent-driven design workflow: type "make me a pitch deck" → interactive form → agent picks visual direction → builds real project folder → 5D critique → emits `<artifact>` in sandboxed iframe
- Exports: HTML, PDF, PPTX, MP4
- Deploys to Vercel

**Relevance to us:**
- 🔥 **HIGH** — This is exactly what the Content Farm needs for creating visual content (pitch decks, social media graphics, carousels, slides)
- Can be used as a **skill** for our content creation agent
- Runs locally, BYOK — fits our security model
- The "agents read HTML better than MD" insight is key — Open Design outputs HTML artifacts

**How to integrate:**
1. Clone `github.com/nexu-io/open-design`
2. Install: `pnpm install` (or npm)
3. Add as a skill for content creation agent
4. Use for: Instagram carousels, pitch decks, social media graphics, marketing materials

**Status:** 📌 Noted — install when ready

---

## 2. ViMax (HKUDS/ViMax)

**What it is:** Agentic video generation — Director, Screenwriter, Producer, and Video Generator all-in-one.

**How it works:**
- Input a concept → autonomously handles scriptwriting, storyboarding, character creation, video generation
- Multi-agent workflow: Director agent → Screenwriter agent → Producer agent → Video generator
- Can transform novels into episodic video content
- Generate video from photos (cameo videos)
- Python 3.12+, uses `uv` package manager

**Relevance to us:**
- 🔥 **HIGH** — Content Farm video production (TikTok, YouTube Shorts, Instagram Reels)
- Multi-agent architecture aligns with our Manager → Optimizer → Researcher pipeline
- Could replace manual video production for content farm

**How to integrate:**
1. Clone `github.com/HKUDS/ViMax`
2. Install: `uv pip install -r requirements.txt`
3. Configure API keys for video generation models
4. Add as a skill for content creation agent

**Status:** 📌 Noted — install when ready

---

## 3. Netviz (ShadowArcanist/netviz)

**What it is:** Browser-based app for designing network architectures visually.

**How it works:**
- Drag-and-drop blocks (servers, proxies, databases) onto canvas
- Connect blocks with edges to map data flow
- Organize into layers
- Export to image
- Local save with IndexedDB (no server needed)
- Can deploy to Coolify, Vercel, any static host
- Node.js 20+ or Bun 1.1+

**Relevance to us:**
- 🟡 **MEDIUM** — Useful for visualizing our agent architecture, network topology, system design
- Could be used to design and document the agent environment's network architecture
- The "agents read HTML better than MD" insight applies — Netviz outputs visual HTML

**How to integrate:**
1. Clone `github.com/ShadowArcanist/netviz`
2. Use for: agent architecture diagrams, network topology docs, system design
3. Deploy to Vercel for team access

**Status:** 📌 Noted — install when ready

---

## 4. Tweet Insight — Google Accounts for NotebookLM

**Source:** @xiaoying_eth on X
**Insight:** Multiple Google accounts = free NotebookLM notebooks (each account gets free storage)

**Relevance to us:**
- 🔥 **HIGH** — Cloud storage + compute at zero cost
- Each Google account = free NotebookLM = free cloud storage
- MAD has multiple Google accounts → significant free storage pool
- Can use for: agent memory backups, strategy research storage, content archives

**How to integrate:**
1. MAD sets up Google accounts for specific purposes
2. Each agent/team gets a Google account for storage
3. Use Google Drive API to store and retrieve files
4. Use NotebookLM for research summarization

**Status:** 📌 Noted — MAD to set up accounts

---

## 5. UI-TARS Desktop (bytedance/UI-TARS-desktop)

**What it is:** Open-source multimodal AI agent stack for browser/desktop automation.

**Relevance to us:**
- 🔥 **HIGH** — Connector layer for platforms without APIs
- Already evaluated and confirmed useful
- `npm install @agent-tars/cli@latest -g` (Node.js 22+)
- Works with our existing LLM keys

**Status:** 📌 Already in progress — credresearch agent incorporating into connector design

---

## Integration Priority

| Priority | Tool | Use Case | Effort |
|----------|------|----------|--------|
| 1 | Open Design | Content creation (graphics, decks, carousels) | Medium |
| 2 | ViMax | Video production (TikTok, YT Shorts, Reels) | High |
| 3 | Google Accounts | Free cloud storage + NotebookLM | Low |
| 4 | Netviz | Architecture visualization | Low |
| 5 | UI-TARS | Platform connectors (browser automation) | Medium |

---

*Last updated: 2026-05-18 08:28 EDT*
*Next: Install and integrate based on MAD's priority*
