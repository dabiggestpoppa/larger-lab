# MEMORY.md — Long-Term Memory

> Curated memory. Distilled from daily notes. Updated over time.
>
> **📚 Tools & Skills Discovery:** See `WORKSPACE_TOOLS_AND_SKILLS.md` for complete guide to available tools and skills.

## 2026-05-15 — Day One
- First session. Fresh workspace. No prior memory.
- MAD reached out via Telegram. Set up identity (OWL 🦉) and user profile.
- Workspace has: MT5 MCP server, Nautilus Trader, agent infrastructure, trading strategies.
- Model: OpenRouter OWL Alpha.

## Progress Sync Summary (CC)
> **Last Sync:** 2026-05-16 (current)
> **Status:** 🟢 Active
> **Active Phase:** SRRA-OPH Phase 7 — Overlap Cognition (COMPLETE)
> **Tests:** 39/39 passing across 7 phases
> **Working Memory:** `progress/claude-code-memory.md`
> **Agent Roster:** CC, OC, OC2, AS, PM, RL (6 agents active)

## 🦉 [RL] OWL — Research Lead
- **Role:** Research Lead / DSPy Integration / Pipeline Optimization
- **Registered:** 2026-05-16
- **Identity:** `progress/RL_IDENTITY.md`
- **Focus:** Evaluating and integrating new AI tools (DSPy, etc.) with minimal disruption
- **Onboarding skill:** `skills/agent-onboarding/SKILL.md`
- **CLI tool:** `tools/agent-onboarding-tool.py`

## 🎻 Violin — Video Translation (2026-05-16)
- **Package:** `violin` v0.1.1 (Python)
- **Skill:** `skills/violin/SKILL.md` / `.agents/skills/violin/SKILL.md`
- **CLI:** `violin <input> <output> --language <Lang>`
- **API:** `violin-api` (FastAPI server)
- **Use when:** User wants to translate/dub a video, generate subtitles, or add voice-over
- **Supports:** 33 target languages, 6 style profiles, SRT subtitle generation
- **Requires:** `ffmpeg` on PATH, `TOGETHER_API_KEY`
- **Pipeline:** ffmpeg | Whisper | LLM (DeepSeek V4 Pro) | TTS (Cartesia Sonic 3) | ffmpeg remux
- **GitHub:** https://github.com/shang-zhu/violin
- **Demo:** https://www.violin-ai.com
- **Note:** Fixed f-string syntax bug in `pipeline/costs.py` for Python 3.11 compat

## 🕷️ Scrapling — Web Scraping (2026-05-16)
- **Package:** `scrapling` v0.4.8 (Python)
- **Skill:** `skills/scrapling/SKILL.md` / `.agents/skills/scrapling/SKILL.md`
- **CLI:** `scrapling extract get|fetch|stealthy-fetch <url> <output>`
- **Use when:** `web_fetch` fails, anti-bot protection, JS rendering, full crawls
- **Key classes:** `Fetcher`, `StealthyFetcher`, `DynamicFetcher`, `Spider`
- **GitHub:** https://github.com/D4Vinci/Scrapling

## 🤖 DeekeScript — Android Automation (2026-05-16)
- **Package:** `deeke-script-app` v1.9.3 (Node.js/TypeScript)
- **Skill:** `skills/deeke-script/SKILL.md`
- **Source:** `deekescript/` cloned from https://github.com/DeekeScript/deekescript
- **Use when:** Android automation, content farm bots, auto-posting, engagement automation
- **Capabilities:** Simulate clicks, image recognition, multi-threading, device control
- **GitHub:** https://github.com/DeekeScript/deekescript
- **Website:** https://deeke.cn | Docs: https://doc.deeke.cn

## 📋 Spec Kit - Spec-Driven Development (2026-05-16)
- **CLI:** `specify` v0.8.9 (installed via uv tool)
- **Skill:** `skills/spec-kit/SKILL.md` / `.agents/skills/spec-kit/SKILL.md`
- **Use when:** New projects, structured AI dev, multi-phase builds
- **Workflow:** Constitution -> Spec -> Plan -> Tasks -> Implement
- **GitHub:** https://github.com/github/spec-kit | Docs: https://github.github.io/spec-kit/

## 🍊 Oransim - Causal Marketing Engine (2026-05-16)
- **Package:** `oransim` v0.2.0a0 (Python, Apache-2.0)
- **Skill:** `skills/oransim/SKILL.md` / `.agents/skills/oransim/SKILL.md`
- **Source:** `oransim/` cloned from https://github.com/OranAi-Ltd/oransim
- **Use when:** Campaign ROI prediction, KOL selection, budget allocation, content strategy
- **Three workflows:** Pre-launch ranking, mid-campaign intervention, post-mortem counterfactuals
- **Mock mode:** Works without LLM API key
- **Enterprise data:** 4.3M+ xhs notes, 2.1M+ creators, 100K+ consumer panel (contact cto@orannai.com)
- **Company:** OranAI Ltd. (Shenzhen), 70+ enterprise clients, RMB 20M+ revenue
- **Links:** https://oran.cn/oransim | https://datacenter.oran.cn/

## 🔧 OC1/OC2 Gateway Status (2026-05-16)
- **OC1** (port 18789, @finalstrawclawbot): Intermittent crashes. Fixed `gateway.cmd` to include `OPENCLAW_HOME`. Still unstable.
- **OC2** (port 18790, @OC2BLRBOT): Stable and running.
- **Root cause**: OC1's gateway.cmd was missing `OPENCLAW_HOME`, causing config cross-contamination with OC2
- **Docker option**: Not available — no container runtime installed. Would need Docker Desktop + reboot.
- **Current approach**: OC2 runs natively on desktop. OC1 gateway.cmd fixed but needs further stability work.
- **Files modified**: `C:\Users\wifik\.openclaw\gateway.cmd` — added `OPENCLAW_HOME` + port 18789