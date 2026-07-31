# CEREBUS × External Tools — Integration Plan

> **Date:** 2026-06-10 | **Scope:** Evaluate and integrate external tools into CEREBUS build

---

## 1. RuView (ruvnet/RuView) — WiFi Sensing Platform

### What It Is
WiFi DensePose — turns commodity WiFi signals into spatial intelligence. Detects people, breathing, heart rate, pose estimation through walls. No cameras, no wearables.

### Key Components
- **wifi-densepose**: 17-keypoint pose estimation from WiFi CSI signals (82.69% torso-PCK@20)
- **Breathing/Heart Rate Extraction**: Contactless vital signs from radio wave perturbations
- **Multi-person counting**: Adaptive P95 normalization + dedup
- **Fall detection**: Phase-acceleration threshold + 3-frame debounce
- **Through-wall sensing**: Fresnel-zone geometry + multipath modeling
- **105 edge modules**: Health, security, building, retail, industrial, AI, swarm

### Integration Points with CEREBUS
| CEREBUS Component | RuView Integration | Value |
|-------------------|-------------------|-------|
| Guardian Alert Pipeline | RuView presence detection as additional signal | Confirm trader is at desk before alerting |
| Trade Orchestrator | RuView vital signs (stress detection) | Reduce position size when stress detected |
| Markov Chain | RuView occupancy state as additional input | Adjust regime probability based on room activity |
| RAG Oracle | RuView documentation as additional knowledge base | Query RuView manual for hardware setup |

### Recommendation
**LOW PRIORITY for now.** RuView is a hardware-dependent sensing platform (ESP32 + Cognitum Seed). Interesting for future "smart trading desk" integration but not core to the CEREBUS ML pipeline. Revisit after Wave 3 testing complete.

---

## 2. CodeGraph (colbymchenry/codegraph) — Semantic Code Intelligence

### What It Is
Pre-indexed knowledge graph for codebases. Gives AI agents (Claude Code, Cursor, Codex) instant code understanding without expensive grep/Read exploration.

### Key Features
- **20+ language support**: TypeScript, Python, Go, Rust, Java, C#, PHP, Ruby, C, C++, Swift, Kotlin, Dart, Svelte, Vue, Lua, etc.
- **Framework-aware routing**: Django, Flask, FastAPI, Express, NestJS, Laravel, Rails, Spring, Gin, React Router, SvelteKit
- **Cross-language bridging**: Swift↔ObjC, React Native bridge, Expo Modules, Fabric/Paper views
- **Impact analysis**: Trace callers, callees, blast radius of any symbol
- **100% local**: SQLite database, no cloud, no API keys
- **Benchmark**: 16% cheaper, 47% fewer tokens, 22% faster, 58% fewer tool calls

### Integration Points with CEREBUS
| CEREBUS Component | CodeGraph Integration | Value |
|-------------------|----------------------|-------|
| Codebase understanding | Index `quant-lab/ml/` for agent navigation | Faster development, fewer context mistakes |
| Impact analysis | Trace feature dependencies before changes | Safer refactoring of feature engineering |
| RAG Oracle | Code structure as additional knowledge base | Query code relationships alongside manual rules |
| Testing | `codegraph affected` → find tests for changed files | Run only relevant tests after changes |

### Recommendation
**HIGH PRIORITY.** CodeGraph directly accelerates CEREBUS development. Install it on the workspace so all agents (CC, PM, PM2, AS, RL) can navigate the 77 Python files / 13,700 lines instantly.

**Action items:**
1. `npm i -g @colbymchenry/codegraph`
2. `codegraph init -i` in workspace root
3. `codegraph install --target=claude,cursor --yes`

---

## 3. notebooklm-py (teng-lin/notebooklm-py) — Google NotebookLM API

### What It Is
Unofficial Python API + CLI + agentic skill for Google NotebookLM. Full programmatic access including features the web UI doesn't expose.

### Key Features
- **Complete NotebookLM coverage**: Notebooks, sources, chat, research, sharing
- **Content generation**: Audio Overview (podcast), video, slide deck, quiz, flashcards, infographic, mind map, data table, report
- **Beyond web UI**: Batch downloads, quiz/flashcard JSON export, mind map extraction, PPTX export, slide revision, source fulltext access
- **Multi-account profiles**: Switch between Google accounts
- **Agent integration**: Claude Code skill, Codex prompts, OpenClaw skills

### Integration Points with CEREBUS
| CEREBUS Component | notebooklm-py Integration | Value |
|-------------------|--------------------------|-------|
| RAG Oracle | Use NotebookLM to summarize PDFs before chunking | Better chunk quality from 55 PDFs |
| Research Mesh | NotebookLM research agents for web/Drive research | Complement O2C research pipeline |
| Content Generation | Auto-generate Audio Overviews of manual sections | Audio summaries of CEREBUS rules |
| Knowledge Export | Export mind maps from NotebookLM for visualization | Visual CEREBUS ontology maps |

### Recommendation
**MEDIUM PRIORITY.** notebooklm-py is useful for preprocessing the 55 PDFs before RAG ingestion. Can also generate audio summaries of the manual. But it depends on Google's unofficial API which may break.

**Action items:**
1. `pip install "notebooklm-py[browser]"` for PDF preprocessing
2. Use `notebooklm source add` + `notebooklm ask` to extract key rules from each PDF
3. Feed extracted rules into RAG Oracle chunker for better-quality chunks

---

## 4. Other Notable Mentions

### dograh-hq/dograh
AI agent framework. Could complement OCE backend for agent orchestration. **LOW PRIORITY** — OCE already has agent infrastructure.

### RyanCodrai/turbovec
Vector database / embedding tool. Could complement or replace ChromaDB for RAG Oracle. **MEDIUM PRIORITY** — evaluate after Wave 3 testing.

---

## Integration Priority Matrix

| Tool | Priority | Effort | Impact | When |
|------|----------|--------|--------|------|
| CodeGraph | 🔴 HIGH | Low | High | Now |
| notebooklm-py | 🟡 MEDIUM | Medium | Medium | After AS testing |
| RuView | 🟢 LOW | High | Low | Future |
| turbovei | 🟡 MEDIUM | Medium | Medium | After Wave 3 |

---

## Recommended Next Steps

1. **Install CodeGraph** on workspace (5 min) — immediate productivity boost
2. **Run notebooklm-py** on 55 PDFs to extract structured rules → feed into RAG Oracle
3. **Continue with AS test suite** — CodeGraph will make test development faster
4. **Evaluate turbovec** as ChromaDB alternative if RAG query performance needs improvement
