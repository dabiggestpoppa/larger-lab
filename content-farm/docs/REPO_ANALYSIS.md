# Content Farm — Repo Analysis & Strategy

> MAD Directive: "Set up those githubs so we can start using them"
> Date: 2026-06-10

## Repo Breakdown

### 1. ruvnet/RuView — WiFi Sensing / Agent Visualization
- **Tech:** Rust, Python, Docker, ESP32, HuggingFace
- **What it does:** Turns WiFi signals into spatial intelligence — presence detection, vitals, pose estimation through walls
- **Content Farm Use:** ❌ Not directly applicable to content farm. This is hardware/IoT. Keep for reference but not a content property.
- **Verdict:** SKIP for content farm. Potential future IoT content angle.

### 2. colbymchenry/codegraph — Semantic Code Intelligence
- **Tech:** Node.js (bundled CLI), MCP server, Python bindings
- **What it does:** Gives AI agents semantic understanding of codebases — graph-based code analysis, 16% cheaper token usage, 58% fewer tool calls
- **Content Farm Use:** ✅ **HIGH VALUE.** This IS a content product. "CodeGraph for Traders" — semantic analysis of trading code, strategy repos, quant codebases. Can be forked as a dev-tool content site.
- **Verdict:** FORK → "FBO CodeGraph" — code intelligence for quant devs. Content angle: tutorials, case studies, "analyze your trading strategy code" demo.

### 3. mattpocock/skills — Agent Skill Patterns
- **Tech:** Markdown-based skills, CLI installer, agent-agnostic
- **What it does:** Production-ready agent skills for Claude Code, Codex, etc. — grill-me, triage, context docs, domain-driven design
- **Content Farm Use:** ✅ **HIGH VALUE.** This is literally a content farm for AI engineering. Fork → "FBO Skills" — agent skills for trading/quant agents. Each skill = content piece.
- **Verdict:** FORK → "FBO Agent Skills" — repackage as trading agent skill library. Content: skill tutorials, "build your own trading agent" series.

### 4. dograh-hq/dograh — Voice AI Agent Platform
- **Tech:** Python (FastAPI), React, Docker, Pipecat, LLM-agnostic
- **What it does:** Open-source alternative to Vapi/Retell — build voice AI agents with drag-and-drop workflow builder
- **Content Farm Use:** ✅ **HIGH VALUE.** "Build a Trading Voice Agent" — voice bot that reads market data, gives trade alerts, explains setups. Fork as FBO voice agent platform.
- **Verdict:** FORK → "FBO Voice" — voice AI for traders. Content: "build your own trading voice agent in 60 seconds" demos, tutorials.

### 5. teng-lin/notebooklm-py — NotebookLM Python API
- **Tech:** Python, CLI, MCP, PyPI package
- **What it does:** Unofficial Python API for NotebookLM — generate podcasts, videos, slide decks, quizzes, flashcards, mind maps from any content
- **Content Farm Use:** ✅ **HIGHEST VALUE.** This IS the content machine. Feed it trading research → get podcasts, videos, slides, quizzes automatically. This is the content farm engine.
- **Verdict:** FORK → "FBO Content Engine" — automated content generation from trading research. This powers ALL platforms: YouTube, TikTok, Twitter, blog.

### 6. kaktusesquire6rmu/ai-polymarket-agent — Prediction Market AI Agent
- **Tech:** Node.js, MCP server, Polymarket API
- **What it does:** AI agent for prediction markets — search markets, get odds, analyze trends, automated trading insights
- **Content Farm Use:** ✅ **HIGH VALUE.** "What do prediction markets say about X?" — content angle: market sentiment analysis, "prediction markets are pricing in Y" content series.
- **Verdict:** FORK → "FBO Prediction Pulse" — prediction market intelligence for content. Daily/weekly "what the markets are predicting" content.

---

## Content Farm Architecture

```
content-farm/
├── github-repos/          # Original clones (reference)
├── sites/                 # Forked + rebranded projects
│   ├── fbo-codegraph/     # Code intelligence for quant devs
│   ├── fbo-skills/        # Agent skill library
│   ├── fbo-voice/         # Voice AI for traders
│   ├── fbo-content-engine/ # Automated content generation (notebooklm-py fork)
│   └── fbo-prediction-pulse/ # Prediction market intelligence
├── docs/                  # Strategy, analysis, playbooks
└── pipeline/              # Content production pipeline scripts
```

## Priority Order (MAD's "Capital Maxer" — max gain, min effort)

1. **fbo-content-engine** (notebooklm-py fork) — Powers everything. One input → 10 content formats.
2. **fbo-skills** (mattpocock/skills fork) — Each skill = content piece. Low effort, high output.
3. **fbo-prediction-pulse** (polymarket fork) — Automated market intelligence content.
4. **fbo-voice** (dograh fork) — Voice content angle. Medium effort.
5. **fbo-codegraph** (codegraph fork) — Dev-tool content. Higher effort, niche audience.

## Content Engine Pipeline (notebooklm-py powered)

```
Trading Research (CONTENT_FUEL.md)
    ↓
notebooklm-py API
    ↓
├── Audio Overviews → YouTube / Podcasts
├── Video Overviews → YouTube / TikTok / Reels
├── Slide Decks → Instagram Carousels / LinkedIn
├── Infographics → Instagram / Twitter
├── Quizzes → Twitter Threads / Blog
├── Flashcards → Instagram Stories / Blog
├── Reports → Blog / Newsletter / LinkedIn
├── Data Tables → Twitter / Blog
└── Mind Maps → Instagram Carousels / YouTube
```
