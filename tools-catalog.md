# 🔧 TOOLS CATALOG — Complete Reference

> Curated by MAD | Sorted by use case | All free/open-source unless noted
> Last updated: 2026-06-10

---

## 🔴 TOP PRIORITY

### ⚡ TurboVec — High-Performance Vector Index
- **URL:** https://github.com/RyanCodrai/turbovec
- **What:** Rust-based vector index with Python bindings, built on Google Research's TurboQuant algorithm. A 10M document corpus takes 31GB as float32 — TurboVec fits it in **4GB** and searches **faster than FAISS**.
- **Key Features:**
  - Online ingest — add vectors, no train step, no rebuilds
  - 12–20% faster than FAISS on ARM, match-or-beat on x86
  - Filter at search time (id allowlist/bitmask) — no over-fetching
  - Pure local — no managed service, air-gapped RAG possible
  - `pip install turbovec` / available on crates.io
- **Use Case:** RAG systems where privacy, memory efficiency, or latency matters. Drop-in FAISS replacement.
- **Install:** `pip import turbovec` then `index = TurboQuantIndex(dim=1536, bit_width=4)`

---

## 🎬 VIDEO & CONTENT CREATION

### Downloaders

| Tool | URL | What | Notes |
|------|-----|------|-------|
| **reclip** | https://github.com/averygan/reclip | Self-hosted video/audio downloader via yt-dlp. Clean web UI, MP4/MP3, bulk downloads. | Python + Flask, ~150 lines backend. Docker support. |
| **cobalt.tools** | https://cobalt.tools | Download video/audio from YouTube, TikTok, Instagram, Twitter/X, 30+ sites. No ads. | Best all-around downloader. |
| **greenvideo.cc** | https://greenvideo.cc | Bilibili, Weibo, Xiaohongshu downloader (Chinese platforms) | Doesn't cover YouTube |
| **tiktokio.bio** | https://tiktokio.bio | Watermark-free TikTok/Douyin downloader | Works for both CN + Intl versions |
| **savefrom.net** | https://en1.savefrom.net/ | Instagram/Facebook video downloader | Classic stable tool |
| **yt-dlp** | https://github.com/yt-dlp/yt-dlp | Open-source YouTube downloader, 4K batch downloads, subtitles | CLI tool, command-line only |
| **4K Video Downloader** | https://www.4kdownload.com | Desktop YouTube downloader, one-click playlists | For non-CLI users |

### Watermark Removal

| Tool | URL | What |
|------|-----|------|
| **MagicEraser (video)** | https://magiceraser.org/remove-watermark-from-video/ | Video watermark removal |
| **MagicEraser (image)** | https://magiceraser.org | Image watermark removal |

### AI Video Platforms (Open Source Replacements)

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **openshorts** | (search GitHub) | Opus Clip ($19/mo) + Submagic ($16/mo) | AI video clipping, auto-subtitles, face tracking. Uses free Gemini + ElevenLabs tiers. Docker self-host. |
| **openscreen** | (search GitHub) | Screen Studio ($29/mo) | Clean screen recorder for demos. Blur, cursor highlighting, annotations. MP4/GIF export. |

### Animation

| Tool | URL | What |
|------|-----|------|
| **dotlottie-web** | https://github.com/LottieFiles/dotlottie-web | Official LottieFiles player for web. Rust+WASM core, supports React/Vue/Svelte/SolidJS. Theming, state machines, audio. |

---

## 🎙️ VOICE & AUDIO

### AI Voice Studios (Local-First)

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **Voicebox** | https://github.com/jamiepine/voicebox | ElevenLabs ($22/mo) + WisprFlow ($15/mo) | Local AI voice studio. Clone voices from 3 sec audio, 7 TTS engines, 23 languages, dictate into any app with global hotkey. Apple Silicon/CUDA/ROCM. |
| **OmniVoice Studio** | https://github.com/debpalash/OmniVoice-Studio | ElevenLabs | Open-source voice cloning, design, dubbing, dictation. 646 languages. Desktop app (macOS/Linux/Windows). |
| **Dograh** | https://github.com/dograh-hq/dograh | Vapi + Retell | Open-source self-hosted voice AI platform. Drag-and-drop workflow builder, telephony support, MCP native. |

### Transcription

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **Whisper** | https://github.com/openai/whisper | Otter ($17/mo) | OpenAI's open-source STT. 99 languages, translate to English, timestamps. Runs locally on CPU/GPU. |

---

## 🤖 AI & LLM TOOLS

### Free AI API Aggregators

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **freellmapi** | (search GitHub) | ChatGPT Pro + Claude Pro ($20/mo each) | Stacks 14 free AI providers (Google, Groq, Cerebras, OpenRouter, GitHub Models + 9 more). ~800M tokens/month. Smart router with failover. Dashboard included. |

### Model Training & Fine-Tuning

| Tool | URL | What |
|------|-----|------|
| **Unsloth** | https://github.com/unslothai/unsloth | Train/run 500+ models locally. 2x faster training, 70% less VRAM. Supports Gemma, Qwen, DeepSeek. Web UI (Unsloth Studio). |

### AI Browser Control

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **playwright-mcp** | (search GitHub) | Browserbase ($39/mo) + Browser Use ($25/mo) | Microsoft's official MCP server for AI agent browser control. Uses accessibility trees, not screenshots. Works with Claude Code, Cursor, Windsurf, Codex. |

### Research & Knowledge

| Tool | URL | What |
|------|-----|------|
| **notebooklm-py** | https://github.com/teng-lin/notebooklm-py | Unofficial Python API for Google NotebookLM. Bulk-import sources, generate podcasts/videos/slides/quizzes, download artifacts. |
| **Horizon** | https://github.com/Thysrael/Horizon | AI-powered news radar. Daily briefings in English & Chinese from HN, Reddit, Telegram, RSS, GitHub. Deduplication, scoring, context enrichment. |

### AI Agents & Skills

| Tool | URL | What |
|------|-----|------|
| **mattpocock/skills** | https://github.com/mattpocock/skills | Production-grade agent skills (grill-me, grill-with-docs, triage). Composable, model-agnostic. |
| **taste-skill** | https://github.com/Leonxlnx/taste-skill | "Anti-Slop" frontend framework for AI agents. Upgrades layout, typography, motion, spacing in AI-built UIs. |
| **SkillTree** | https://github.com/maipianworni/SkillTree | Aggregates skills into hierarchical routing trees for AI agents. Supports Claude Code, Codex, OpenClaw, OpenCode, Hermes, Cursor. |
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | Turn any technical book PDF into a Claude Code skill for on-demand reference. |

---

## 📱 ANDROID & MOBILE AUTOMATION

| Tool | URL | What |
|------|-----|------|
| **DeekeScript** | https://github.com/DeekeScript + https://doc.deeke.cn/ | Chinese Android automation platform. JSON-configured UI, accessibility services, packaging, SaaS licensing system. Targets Chinese app ecosystem (Douyin, etc.). |
| **android-sms-gateway** | https://github.com/capcom6/android-sms-gateway | Turn Android phone into SMS gateway. Send/receive SMS via API. No registration required. |

---

## 💹 TRADING & FINANCE

| Tool | URL | What |
|------|-----|------|
| **ai-polymarket-agent** | https://github.com/kaktusesquire6rmu/ai-polymarket-agent | MCP server for Polymarket. AI agents can analyze markets, fetch real-time odds, execute trades. |
| **vibe-trading** | (search GitHub) | Replaces TradingView Premium ($60/mo). Natural-language finance research agent. 7 backtest engines, 75 specialist skills, 29 multi-agent swarm presets. |

---

## 🎨 DESIGN & GRAPHICS

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **Photopea** | https://photopea.com | Photoshop | Full Photoshop in browser. Opens PSD files. 100% free. |
| **open-design** | https://github.com/nexu-io/open-design | Claude Design | Local-first design tool. 259+ skills, 142+ design systems. Prototypes, slides, images, videos. HTML/PDF/PPTX/MP4 export. |

---

## 📊 DIAGRAMS & VISUALIZATION

| Tool | URL | What |
|------|-----|------|
| **D2** | https://github.com/terrastruct/d2 | Modern diagram scripting language. Text → diagrams. Clean syntax, multiple themes, exports to SVG/PNG/PDF. |
| **codegraph** | https://github.com/colbymchenry/codegraph | Pre-indexed code knowledge graph for Claude Code, Codex, Cursor, etc. ~16% cheaper tokens, ~58% fewer tool calls. 100% local. |

---

## 🔧 DEVELOPER TOOLS

| Tool | URL | What |
|------|-----|------|
| **TurboVec** | https://github.com/RyanCodrai/turbovec | Vector index (see TOP PRIORITY above) |
| **codegraph** | https://github.com/colbymchenry/codegraph | Code knowledge graph for AI coding agents |
| **SkillTree** | https://github.com/maipianworni/SkillTree | Skill routing tree for AI agents |
| **book-to-skill** | https://github.com/virgiliojr94/book-to-skill | PDF → Claude Code skill converter |
| **taste-skill** | https://github.com/Leonxlnx/taste-skill | Anti-slop design skills for AI agents |
| **mattpocock/skills** | https://github.com/mattpocock/skills | Engineering agent skills |

---

## 📦 FILE STORAGE & SYNC

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **Nextcloud** | https://nextcloud.com | Google Drive, Dropbox, iCloud | Self-hosted cloud storage. Unlimited storage on your own server. |
| **Syncthing** | https://syncthing.net | Dropbox, iCloud, OneDrive | P2P file sync between devices. Zero cloud, zero subscription. |

---

## 🔓 KNOWLEDGE & RESEARCH

| Tool | URL | What |
|------|-----|------|
| **Sci-Hub** | https://sci-hub.red | Free access to 88+ million research papers |
| **Anna's Archive** | https://annas-archive.gl | World's largest open knowledge archive. Any book, textbook, or paper. |
| **Internet Archive** | https://archive.org | Free movies, books, software, music, 800B archived web pages since 1996 |
| **Ladder** | https://github.com/everywall/ladder | Self-hosted proxy that bypasses paywalls (NYT, WSJ, Bloomberg, Nature, etc.) |
| **TinyWow** | https://tinywow.com | 300+ free tools for PDF, image, video, AI tasks. No signup. |

---

## 📅 PRODUCTIVITY & SCHEDULING

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **CalCom** | https://cal.com | Calendly ($12/mo) + SavvyCal ($12/mo) | Open-source scheduling. One-on-ones, group events, round-robin, team booking, Stripe payments. Self-host in 10 min. 40k stars. |
| **Ninite** | https://ninite.com | — | Install all programs on a new PC in one click. No bloatware. |

---

## 🔐 SECURITY & PASSWORDS

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **Vaultwarden** | https://github.com/dani-garcia/vaultwarden | 1Password ($8/mo) | Unofficial Bitwarden-compatible server in Rust. Works with all official Bitwarden clients. Runs on $5 VPS. |

---

## 🌐 SOCIAL MEDIA

| Tool | URL | Replaces | What |
|------|-----|----------|------|
| **Postiz** | https://github.com/gitroomhq/postiz | Buffer ($15/mo) | AI-powered social media scheduler. X, LinkedIn, Instagram, TikTok, Threads, Bluesky, Mastodon, YouTube, Pinterest. AI captions + hashtags. Analytics. 31k stars. |

---

## 💰 AI TO EARN (Content Monetization)

| Tool | URL | What |
|------|-----|------|
| **AiToEarn** | https://github.com/yikart/AiToEarn | **THE money printer.** AI-powered content creation + publishing + monetization across 12+ platforms (Douyin, Xiaohongshu, Kuaishou, Bilibili, TikTok, YouTube, Facebook, Instagram, Threads, Twitter/X, Pinterest, LinkedIn). Supports OpenClaw integration, MCP protocol, Docker deployment. Has a content marketplace. |

---

## 📡 OFF-GRID / HARDWARE

| Tool | URL | What |
|------|-----|------|
| **Blackbox Node** | https://github.com/wadadawadada/blackbox_node | Off-grid mesh node with local AI, TAK integration, Bitcoin Cashu payments. Built on Meshtastic/LoRa. For disaster response, field operations, community mesh networks. |
| **RuView** | https://github.com/ruvnet/RuView | Turns commodity WiFi signals into real-time spatial intelligence, vital sign monitoring, presence detection — no video. |

---

## 📝 QUICK REFERENCE — PAID TOOLS & THEIR FREE REPLACEMENTS

| Paid Tool | Cost | Free Replacement | Category |
|-----------|------|-----------------|----------|
| Screen Studio | $29/mo | openscreen | Screen Recording |
| ElevenLabs + WisprFlow | $37/mo | Voicebox | AI Voice |
| Opus Clip + Submagic | $35/mo | openshorts | AI Video Clipping |
| ChatGPT Pro + Claude Pro | $40/mo | freellmapi | AI APIs |
| Browserbase + Browser Use | $64/mo | playwright-mcp | AI Browser Control |
| TradingView Premium | $60/mo | vibe-trading | Finance Research |
| Calendly + SavvyCal | $24/mo | CalCom | Scheduling |
| Otter.ai | $17/mo | Whisper | Transcription |
| Buffer | $15/mo | Postiz | Social Media |
| 1Password | $8/mo | Vaultwarden | Passwords |

**Total monthly savings: ~$329/month** if you replace all paid tools above.

---

## 🗺️ CONTENT CREATION STACK (MAD's Use Case)

Here's how these tools fit together for free content creation:

1. **Script/Idea** → freellmapi (free AI writing)
2. **Voiceover** → Voicebox or OmniVoice Studio (local TTS + voice cloning)
3. **Video Clipping** → openshorts (AI auto-clips from long videos)
4. **Screen Recording** → openscreen (polished demos)
5. **Video Downloading** → reclip (self-hosted) or cobalt.tools
6. **Watermark Removal** → MagicEraser
7. **Editing/Design** → Photopea (Photoshop replacement) + open-design
8. **Animation** → dotlottie-web (Lottie animations)
9. **Publishing** → AiToEarn (auto-publish to 12+ platforms) + Postiz (social scheduling)
10. **Monetization** → AiToEarn (content marketplace + multi-platform)

---

*This catalog is yours to evolve. Add new tools as you find them.*
