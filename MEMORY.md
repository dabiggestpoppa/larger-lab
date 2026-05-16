# MEMORY.md — Long-Term Memory

> Curated memory. Distilled from daily notes. Updated over time.

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

## 🔧 OC1/OC2 Gateway Status (2026-05-16)
- **OC1** (port 18789, @finalstrawclawbot): Intermittent crashes. Fixed `gateway.cmd` to include `OPENCLAW_HOME`. Still unstable.
- **OC2** (port 18790, @OC2BLRBOT): Stable and running.
- **Root cause**: OC1's gateway.cmd was missing `OPENCLAW_HOME`, causing config cross-contamination with OC2
- **Docker option**: Not available — no container runtime installed. Would need Docker Desktop + reboot.
- **Current approach**: OC2 runs natively on desktop. OC1 gateway.cmd fixed but needs further stability work.
- **Files modified**: `C:\Users\wifik\.openclaw\gateway.cmd` — added `OPENCLAW_HOME` + port 18789