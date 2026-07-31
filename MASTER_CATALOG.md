# 📋 LARGER-LAB MASTER CATALOG

> **Last Updated:** 2026-06-14 | **Version:** 1.0.0
> **Purpose:** Single source of truth for ALL GitHub repos, apps, agents, tools, and docs in the workspace.

---

## 🗺️ Quick Navigation

| Section | Description |
|---------|-------------|
| [GitHub Repos (17)](#-github-repos-17-total) | All forked repos organized by phase |
| [Content Agents (2)](#-content-agents-2) | PO-callable + VS Code agents |
| [Architecture Docs (12)](#-architecture-docs-12) | All README.md + ARCHITECTURE.md files |
| [Content Farm Tools](#-content-farm-tools) | Presentations, video, image, voice |
| [Services Running](#-services-running) | OCE, Telegram, CEREBUS |
| [Test Coverage](#-test-coverage) | All test counts |
| [Key Config Files](#-key-config-files) | Bible, brand voice, env |

---

## 📦 GitHub Repos (17 Total)

### Phase 1.2 — Parser Orchestration
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 1 | microsoft/markitdown | https://github.com/microsoft/markitdown | `core/parser/markitdown/` | — | ✅ Forked |
| 2 | opendataloader-project/opendataloader-pdf | https://github.com/opendataloader-project/opendataloader-pdf | `core/parser/odl-pdf/` | — | ✅ Forked |
| 3 | run-llama/liteparse | https://github.com/run-llama/liteparse | `core/parser/liteparse/` | — | ✅ Forked |
| 4 | datalab-to/chandra | https://github.com/datalab-to/chandra | `core/parser/chandra/` | — | ✅ Forked |

### Phase 1.3 — Vector Cognition
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 5 | RyanCodrai/turbovec | https://github.com/RyanCodrai/turbovec | `core/semantic/vector/turbovec/` | 11.2k | ✅ Forked |

### Phase 1.5 — Knowledge Graph
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 6 | colbymchenry/codegraph | https://github.com/colbymchenry/codegraph | `tools/codegraph/` | 48.1k | ✅ Forked |

### Phase 1.6 — Procedural Cognition
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 7 | virgiliojr94/book-to-skill | https://github.com/virgiliojr94/book-to-skill | `core/cognition/procedural/book-to-skill/` | 5.3k | ✅ Forked |
| 8 | maipianworni/SkillTree | https://github.com/maipianworni/SkillTree | `core/cognition/router/skilltree/` | 51 | ✅ Forked |
| 9 | mattpocock/skills | https://github.com/mattpocock/skills | `skills/` | 127k | ✅ Forked |

### Phase 2 — Distillation
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 10 | teng-lin/notebooklm-py | https://github.com/teng-lin/notebooklm-py | `content-farm/github-repos/notebooklm-py/` | 16.3k | ✅ Forked |

### Phase 3 — Research Signals
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 11 | Thysrael/Horizon | https://github.com/Thysrael/Horizon | `core/research/horizon/` | 6k | ✅ Forked |

### Phase 4 — Embodiment
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 12 | dograh-hq/dograh | https://github.com/dograh-hq/dograh | `vtuber_integration/dograh/` | 4.4k | ✅ Forked |
| 13 | LottieFiles/dotlottie-web | https://github.com/LottieFiles/dotlottie-web | `vtuber_integration/dotlottie-web/` | 789 | ✅ Forked |

### Content Farm
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 14 | nexu-io/open-design | https://github.com/nexu-io/open-design | `content-farm/design/open-design/` | 63.9k | ✅ Forked |
| 15 | averygan/reclip | https://github.com/averygan/reclip | `content-farm/sites/reclip/` | 6.1k | ✅ Forked |

### Infrastructure
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 16 | terrastruct/d2 | https://github.com/terrastruct/d2 | `tools/d2/` | 24.4k | ✅ Forked |

### Tools
| # | Repo | GitHub URL | Local Location | Stars | Status |
|---|------|-----------|----------------|-------|--------|
| 17 | capcom6/android-sms-gateway | https://github.com/capcom6/android-sms-gateway | `tools/sms-gateway/` | 4.5k | ✅ Forked |
| 18 | jamiepine/voicebox | https://github.com/jamiepine/voicebox | `tools/voicebox/` | — | ✅ Forked |
| 19 | Leonxlnx/taste-skill | https://github.com/Leonxlnx/taste-skill | `skills/taste-skill/` | — | ✅ Forked |

### Still Need Forking
| # | Repo | GitHub URL | Purpose |
|---|------|-----------|---------|
| 20 | unslothai/unsloth | https://github.com/unslothai/unsloth | Fine-tune LLMs 5x faster, 70% less VRAM |
| 21 | debpalash/OmniVoice-Studio | https://github.com/debpalash/OmniVoice-Studio | Multi-engine TTS/voice cloning |

---

## 🤖 Content Agents (2)

### 1. Content Creator
- **File:** `agents/content-creator.agent.md`
- **VS Code:** `.github/agents/content-creator.agent.md`
- **PO Command:** `/content <type> <topic>`
- **Types:** `script` | `deck` | `image` | `social` | `video`
- **Example:** `/content script "90% win rate proof"`
- **Uses:** Open Design, ReClip, dotLottie, Brand Voice

### 2. Content Strategist
- **File:** `agents/content-strategist.agent.md`
- **VS Code:** `.github/agents/content-strategist.agent.md`
- **PO Command:** `/strategy <task> [params]`
- **Tasks:** `calendar` | `repurpose` | `analytics` | `plan`
- **Example:** `/strategy calendar next-week`
- **Channels:** X, TikTok, YouTube, Reddit, Newsletter, Instagram

---

## 📚 Architecture Docs (12)

| # | File | Description |
|---|------|-------------|
| 1 | `ARCHITECTURE.md` | Full system architecture + Mermaid graphs |
| 2 | `oce/ARCHITECTURE.md` | OCE backend (30+ modules, API endpoints) |
| 3 | `quant-lab/ARCHITECTURE.md` | CEREBUS scanner (engines + ML pipeline) |
| 4 | `quant-lab/ml/CEREBUS_PREDICTION_REFERENCE.md` | All predictions + accuracy data |
| 5 | `core/parser/README.md` | Parser orchestration (Phase 1.2) |
| 6 | `core/semantic/README.md` | Semantic memory (Phase 1.3) |
| 7 | `core/knowledge/graph/README.md` | Knowledge graph (Phase 1.5) |
| 8 | `core/research/README.md` | Research mesh (Phase 1-3) |
| 9 | `content-farm/README.md` | Content farm architecture |
| 10 | `vtuber_integration/README.md` | VTuber system |
| 11 | `docs/DESIGN_AND_APP_REPOS.md` | Design/app GitHub repos catalog |
| 12 | `docs/CONTENT_FARM_TOOLS.md` | Presentation, video, image tools |

---

## 🎬 Content Farm Tools

### Presentations & Decks
| Tool | Location | Output |
|------|----------|--------|
| Open Design | `content-farm/design/open-design/` | HTML, PDF, PPTX, MP4 |
| D2 Diagrams | `tools/d2/` | SVG, PNG, PDF |
| Presentation Skills | Open Design `deck-*` | 5 deck styles |
| Design Systems | Open Design | 150 brand-grade systems |
| Plugins | Open Design | 261 official plugins |

### Video
| Tool | Location | Purpose |
|------|----------|---------|
| ReClip | `content-farm/sites/reclip/` | Video downloader (1000+ sites) |
| Open Design Video | `content-farm/design/open-design/plugins/_official/video-templates/` | 50+ video templates |
| dotLottie | `vtuber_integration/dotlottie-web/` | Animation engine |
| Free External | — | cobalt.tools, yt-dlp, 4K Video Downloader, greenvideo.cc, tiktokio.bio, savefrom.net, openshorts, openscreen |

### Images
| Tool | Location | Purpose |
|------|----------|---------|
| Open Design Image | `content-farm/design/open-design/plugins/_official/image-templates/` | 45+ image templates |
| Free External | — | Photopea, MagicEraser, TinyWow |

### Voice & Audio
| Tool | Location | Replaces |
|------|----------|---------|
| Dograh | `vtuber_integration/dograh/` | Vapi + Retell |
| VoiceBox | `tools/voicebox/` | ElevenLabs |
| OmniVoice-Studio | Not forked yet | ElevenLabs |
| Whisper | Not forked yet | Otter.ai |

### Social Media
| Tool | Location | Platform |
|------|----------|---------|
| Social Cards | Open Design `social-*-card` | X, Reddit, Spotify |
| Templates | `content-engine/templates/` | TikTok, Tweet |

---

## 🖥️ Services Running

| Service | Port/ID | Status | Process |
|---------|---------|--------|---------|
| OCE Backend | 8000 | ✅ Healthy | PID varies |
| OCE Frontend | 3000 | ✅ Running | PIDs 6488, 13340 |
| Telegram Gateway | — | ✅ Connected | PID 11836 |
| Telegram Bot | @P01999BOT | ✅ Active | — |
| CEREBUS Monitor | — | ✅ Running | PID 8316 |

---

## 📊 Test Coverage

| System | Tests | Status |
|--------|-------|--------|
| OCE Backend | 492 | ✅ All passing |
| Research Mesh (L1-L3) | 106 | ✅ All passing |
| CEREBUS Scanner (Wave 1-3) | 120 | ✅ All passing |
| SRRA-OPH | 57 | ✅ All passing |
| **Total** | **775+** | ✅ |

---

## 🔑 Key Config Files

| File | Purpose |
|------|---------|
| `QUANTLAB_BIBLE.md` | Locked parameters + 20 calibrated assets |
| `QUANT_BIBLE.md` | Alternate bible (older version) |
| `CEREBUS_ONTOLOGY.md` | Strategy philosophy + MAD's definitions |
| `ontology/manual_ontology.md` | 55 Q&As on market physics |
| `CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md` | 4-step build plan |
| `CEREBUS_PREDICTION_REFERENCE.md` | All predictions + accuracy |
| `reports/SWEEP_MATRIX.md` | Accuracy-frequency curve (28 pairs) |
| `reports/trigger_sweep_*.json` | Per-pair trigger optimization (20+ files) |
| `ml/dtb_lab/MASTER_LAB_REPORT.md` | DTB training results (R²=0.97) |
| `ml/BUILD_NOTES_CEREBUS.md` | Scanner build results (120 tests) |
| `content-engine/BRAND_VOICE.md` | Brand voice + content pillars |
| `content-engine/knowledge/CONTENT_FUEL.md` | 1,626 stats for content |
| `content-engine/knowledge/DATA_SOURCES.md` | Master index of ALL data sources |
| `content-engine/templates/TIKTOK_TEMPLATE.md` | TikTok script template |
| `content-engine/templates/TWEET_TEMPLATE.md` | Twitter post template |
| `tools-catalog.md` | All free/app tools (OC2 curated) |
| `.env` | API keys (Telegram, OpenRouter, etc.) |
| `pyproject.toml` | Python dependencies |
| `requirements.txt` | Python requirements |

---

## 📁 Workspace Structure (Key Directories)

```
larger-lab/
├── ARCHITECTURE.md                    ← System architecture
├── MASTER_CATALOG.md                  ← THIS FILE
├── README.md                          ← Project overview
├── QUANTLAB_BIBLE.md                  ← Trading parameters
├── workspace-state.md                 ← Current system state
│
├── oce/                               ← Observer Core Environment
│   ├── backend/                       ← FastAPI (30+ modules, 492 tests)
│   │   ├── main.py                    ← App entry point
│   │   ├── observer_runtime.py       ← Observer lifecycle
│   │   ├── structural_memory.py       ← 3-tier memory
│   │   ├── event_fabric.py            ← Event routing
│   │   ├── research_api.py            ← Research mesh API
│   │   ├── ml_api.py                  ← ML endpoints
│   │   ├── po_api.py                  ← PO endpoints
│   │   ├── po_idle.py                 ← PO idle runtime
│   │   ├── command_center.py          ← Command center
│   │   ├── governance_engine.py       ← Governance
│   │   ├── consensus_engine.py        ← Consensus
│   │   ├── drift_detector.py          ← Drift detection
│   │   ├── self_healing_engine.py     ← Self-healing
│   │   ├── execution_engine.py        ← Task execution
│   │   ├── topology_api.py            ← Topology endpoints
│   │   └── ARCHITECTURE.md            ← Backend architecture doc
│   └── frontend/                      ← Next.js UI
│       ├── app/
│       │   ├── chat/                  ← Chat page
│       │   ├── topology/              ← Topology page
│       │   ├── agents/                ← Agents page
│       │   ├── attractors/            ← Attractors page
│       │   ├── entropy/               ← Entropy page
│       │   ├── repair/                ← Repair page
│       │   └── vault/                 ← Vault page
│       └── stores/                    ← Zustand stores
│
├── core/                              ← Cognition substrate
│   ├── parser/                        ← Phase 1.2 — Parser orchestration
│   │   ├── markitdown/                ← Microsoft MarkItDown
│   │   ├── odl-pdf/                   ← OpenDataLoader PDF
│   │   ├── liteparse/                 ← LiteParse
│   │   ├── chandra/                   ← Chandra OCR
│   │   └── orchestration/             ← Router + engines
│   ├── semantic/                      ← Phase 1.3 — Embeddings + vectors
│   │   ├── chunking/                  ← Semantic chunker
│   │   ├── embeddings/                ← Embedding engine
│   │   └── vector/turbovec/           ← TurboQuant vector search
│   ├── knowledge/                     ← Phase 1.5 — Knowledge graph
│   │   └── graph/                     ← Entity extractor + graph store + ontology
│   ├── cognition/procedural/          ← Phase 1.6 — Skills + workflows
│   │   ├── book-to-skill/             ← Document → skill
│   │   └── router/skilltree/          ← Skill router
│   ├── research/                      ← Research mesh
│   │   ├── ingestion/                 ← Source clients + cache
│   │   ├── distillation/              ← Distiller + doctrine
│   │   ├── agents/                    ← Gap detector + research agent
│   │   ├── distiller/                 ← Phase 2 distillation
│   │   └── horizon/                   ← News radar
│   └── observer/                      ← Observer system
│       ├── po_agent.py                ← PO agent
│       ├── command_router.py          ← Telegram command router
│       ├── autonomous_orchestrator.py ← Task orchestrator
│       └── vault.py                   ← Obsidian vault integration
│
├── quant-lab/                         ← Quantitative trading
│   ├── engines/                       ← P90 + Symmetry Trap
│   ├── ml/                            ← ML pipeline (5 phases)
│   │   ├── phase1_data/               ← Data foundation
│   │   ├── phase2_classifier/        ← XGBoost classifier
│   │   ├── phase3_rag_oracle/         ← RAG oracle
│   │   ├── phase4_guardian/           ← Guardian
│   │   ├── phase5_hardening/          ← Hardening
│   │   └── shap/                      ← SHAP explainability
│   ├── mt5/                           ← MT5 bridge
│   ├── backtest/                      ← Backtesting
│   └── ARCHITECTURE.md                ← Quant Lab architecture
│
├── content-farm/                      ← Content generation
│   ├── design/open-design/            ← Open Design workspace
│   ├── sites/reclip/                  ← Video downloader
│   └── github-repos/                  ← Cloned repos
│       ├── notebooklm-py/             ← NotebookLM
│       ├── ai-polymarket-agent/       ← Trading agent
│       ├── codegraph/                 ← CodeGraph
│       ├── dograh/                    ← Dograh
│       ├── skills/                    ← mattpocock/skills
│       └── RuView/                    ← RuView
│
├── content-engine/                    ← Brand + content
│   ├── BRAND_VOICE.md                 ← Brand voice
│   ├── templates/                     ← TikTok + Tweet templates
│   ├── posts/                         ← Generated content
│   └── knowledge/                     ← Research material
│
├── vtuber_integration/                ← VTuber system
│   ├── Open-LLM-VTuber/              ← Avatar runtime
│   ├── dograh/                        ← Voice AI
│   └── dotlottie-web/                 ← Animation engine
│
├── agents/                            ← Agent definitions
│   ├── content-creator.agent.md       ← Content Creator
│   └── content-strategist.agent.md    ← Content Strategist
│
├── .github/agents/                    ← VS Code agent configs
│   ├── content-creator.agent.md
│   └── content-strategist.agent.md
│
├── skills/                            ← Agent skills
│   ├── taste-skill/                   ← Leonxlnx/taste-skill
│   └── (mattpocock/skills)            ← Engineering skills
│
├── tools/                             ← Shared tools
│   ├── codegraph/                     ← CodeGraph
│   ├── d2/                            ← D2 diagrams
│   ├── sms-gateway/                   ← Android SMS gateway
│   └── voicebox/                      ← VoiceBox
│
├── scripts/                           ← Utility scripts
│   ├── telegram_gateway.py            ← Telegram gateway
│   ├── cerebus_monitor.py             ← CEREBUS monitor
│   └── start_*.bat/ps1                ← Startup scripts
│
├── docs/                              ← Documentation
│   ├── DESIGN_AND_APP_REPOS.md        ← Design/app repos
│   ├── CONTENT_FARM_TOOLS.md          ← Content tools
│   └── plans/                         ← Build plans
│
├── srrs_opc/                          ← SRRA-OPH observatory
│   ├── frontend/                      ← Observatory UI
│   └── (33 Python files, 57 tests)    ← Core observer system
│
├── O2C-VAULT/                         ← Obsidian vault (symlink)
├── data/                              ← Data files
├── logs/                              ← Log files
└── progress/                          ← Progress tracking
```

---

## 🚀 Quick Start Commands

```bash
# Start OCE Backend
cd larger-lab
.venv\Scripts\python.exe -m uvicorn oce.backend.main:app --host 0.0.0.0 --port 8000

# Start OCE Frontend
cd larger-lab\oce\frontend
npm run dev

# Start Telegram Gateway
cd larger-lab
.venv\Scripts\python.exe scripts\telegram_gateway.py

# Run all tests
python -m pytest oce/backend/tests/ -v --ignore=oce/backend/tests/test_observer_runtime.py
python -m pytest core/research/ -v
python -m pytest quant-lab/ml/tests/ -v
python -m pytest srrs_opc/tests/ -v
```

---

## 📞 Communication Channels

| Channel | How to Use | Context Shared |
|---------|-----------|----------------|
| Telegram | Message @P01999BOT | ✅ Full field context |
| Web Chat | `http://127.0.0.1:3000/chat` | ✅ Full field context |
| VS Code | Agent panel | ✅ Direct code access |

All channels feed into the same session store and field awareness.
