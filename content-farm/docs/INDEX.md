# 🌾 FBO Content Farm — Master Index

> "Set up those githubs so we can start using them" — MAD, 2026-06-10

## Live Repos

| # | Repo | GitHub | Status | Purpose |
|---|------|--------|--------|---------|
| 1 | **fbo-content-engine** | [dabiggestpoppa/fbo-content-engine](https://github.com/dabiggestpoppa/fbo-content-engine) | ✅ Live | Core content machine — generates podcasts, videos, slides, quizzes from trading research |
| 2 | **fbo-skills** | [dabiggestpoppa/fbo-skills](https://github.com/dabiggestpoppa/fbo-skills) | 🔄 Forking | Agent skill library for trading/quant workflows |
| 3 | **fbo-prediction-pulse** | [dabiggestpoppa/fbo-prediction-pulse](https://github.com/dabiggestpoppa/fbo-prediction-pulse) | 🔄 Forking | Prediction market intelligence for content |
| 4 | **fbo-voice** | [dabiggestpoppa/fbo-voice](https://github.com/dabiggestpoppa/fbo-voice) | 🔄 Forking | Voice AI agents for traders |
| 5 | **fbo-codegraph** | [dabiggestpoppa/fbo-codegraph](https://github.com/dabiggestpoppa/fbo-codegraph) | 🔄 Forking | Code intelligence for quant devs |

## Source Repos (MAD's originals)

| Repo | Source | Use |
|------|--------|-----|
| notebooklm-py | teng-lin/notebooklm-py | → fbo-content-engine |
| skills | mattpocock/skills | → fbo-skills |
| ai-polymarket-agent | kaktusesquire6rmu/ai-polymarket-agent | → fbo-prediction-pulse |
| dograh | dograh-hq/dograh | → fbo-voice |
| codegraph | colbymchenry/codegraph | → fbo-codegraph |

## Content Pipeline

```
Trading Research (CONTENT_FUEL.md — 1,626 stats)
    ↓
fbo-content-engine (notebooklm-py)
    ↓
├── Audio → YouTube / Podcasts / TikTok voiceovers
├── Video → YouTube / TikTok / Reels
├── Slides → Instagram Carousels / LinkedIn
├── Infographics → Instagram / Twitter
├── Quizzes → Twitter Threads / Blog
├── Reports → Blog / Newsletter
└── Mind Maps → Instagram / YouTube

fbo-prediction-pulse (Polymarket data)
    ↓
├── "Prediction markets are pricing in X" — Twitter threads
├── Weekly sentiment report — Newsletter
└── "What does Polymarket say about Y?" — Blog/TikTok

fbo-skills (Agent skill library)
    ↓
├── Each skill = content piece (tutorial, demo)
├── "How to build a trading agent" series
└── Skill spotlight blog posts

fbo-voice (Voice AI)
    ↓
├── Trading voice bot demos — YouTube/TikTok
├── "Build your own trading voice agent" — Tutorial series
└── Daily market briefings — Podcast

fbo-codegraph (Code intelligence)
    ↓
├── "Analyze your trading strategy code" — Dev blog
├── Code review content — Twitter/LinkedIn
└── Tutorial: "Understand any quant codebase in seconds"
```

## Directory Structure

```
content-farm/
├── github-repos/          # Original source clones (reference only)
│   ├── notebooklm-py/
│   ├── skills/
│   ├── ai-polymarket-agent/
│   ├── dograh/
│   └── codegraph/
├── sites/                 # Forked + rebranded FBO projects
│   ├── fbo-content-engine/
│   ├── fbo-skills/
│   ├── fbo-prediction-pulse/
│   ├── fbo-voice/
│   └── fbo-codegraph/
├── docs/                  # Strategy & analysis
│   ├── INDEX.md          # This file
│   ├── REPO_ANALYSIS.md  # Per-repo breakdown
│   └── PLAYBOOK.md       # Content production playbooks
└── pipeline/              # Automation scripts (TBD)
```

## Next Steps

1. ✅ All 5 repos created on GitHub
2. ✅ All 5 repos forked (mirrored from source)
3. ✅ fbo-content-engine rebranded + pushed
4. 🔄其余 4 repos being rebranded (subagents running)
5. ⬜ Deploy landing pages to GitHub Pages
6. ⬜ Set up content production cron jobs
7. ⬜ First content batch from BATCH_1.md
8. ⬜ Connect posting pipeline to social accounts
