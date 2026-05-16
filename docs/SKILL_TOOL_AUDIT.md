# SKILL & TOOL AUDIT — Structure Lead Report

> **Generated:** May 16, 2026
> **Auditor:** Structure Lead (Subagent)
> **Scope:** Full workspace inventory — skills, tools, SRRA-OPH, OCE, projects

---

## 1. EXECUTIVE SUMMARY

The workspace contains **~190 skills** (97 in `skills/`, 57 in `.agents/skills/`), **46 Python tools**, **13 operator modules** (Python + JS), **39 SRRA-OPH Python modules**, **9 OCE Python modules**, and **5 project groups** (ads, ai-tools, content, social, trading). Key findings:

- **5 duplicate skills** exist between `skills/` and `.agents/skills/`
- **~70 agency skills** are LOW/DEAD relevance — specialized agents not actively used
- **Operator tools** have Python/JS duplicates (3 pairs)
- **Core active systems:** SRRA-OPH (77 tests passing), OCE (in progress), Operator Control Layer
- **Critical gaps:** No unified skill loader, no capability registry, no automated relevance scoring

---

## 2. FULL INVENTORY

### 2.1 Skills — `skills/` (97 total)

| Skill | Category | Relevance | Notes |
|-------|----------|-----------|-------|
| **system-health** | System Health | CRITICAL | Gateway/config/workspace validation |
| **agent-harness-sop** | System Health | HIGH | Agent harness SOP |
| **agent-team-workflow** | System Health | HIGH | Team workflow patterns |
| **context-compaction** | System Health | HIGH | Context management |
| **subagent-manager** | System Health | HIGH | Subagent orchestration |
| **create-tool** | Development | HIGH | Tool creation patterns |
| **cli-anything** | Development | HIGH | CLI tool patterns |
| **srra-oph-build** | SRRA-OPH | HIGH | SRRA build patterns |
| **deeke-script** | Content Farm | MEDIUM | DeekeScript automation |
| **social-media-agent** | Content Farm | MEDIUM | Social media automation |
| **beautiful-mermaid** | Design | MEDIUM | Mermaid diagram generation |
| **beautiful_mermaid** | Design | MEDIUM | Duplicate of above (underscore vs hyphen) |
| **md2html** | Development | MEDIUM | Markdown to HTML |
| **hugging-face-cli** | AI/ML | MEDIUM | HuggingFace CLI |
| **scrapling** | Research | MEDIUM | Web scraping |
| **oransim** | AI/ML | MEDIUM | Oransim AI platform |
| **motus** | Communication | MEDIUM | Messaging |
| **godfery-tw** | Communication | MEDIUM | Twitter/social |
| **hermes-workflows** | System Health | MEDIUM | Hermes workflow patterns |
| **claude-hermes-mcp** | AI/ML | MEDIUM | Claude/Hermes MCP |
| **twitter-bookmarks** | Research | LOW | Twitter bookmark management |
| **use-my-browser** | Research | LOW | Browser automation |
| **violin** | Design | LOW | Violin visualization |
| **spec-kit** | Development | LOW | Spec kit patterns |
| **as-code-review** | Development | LOW | Code review |
| **agency-** (70 skills) | Agency | LOW/DEAD | Specialized agency agents (see §2.3) |

### 2.2 Skills — `.agents/skills/` (57 total)

| Skill | Category | Relevance | Notes |
|-------|----------|-----------|-------|
| **accessibility** | Design | HIGH | Accessibility auditing |
| **agent-onboarding** | System Health | HIGH | Agent onboarding |
| **fastapi-python** | Development | HIGH | FastAPI patterns |
| **fastapi-templates** | Development | HIGH | FastAPI templates |
| **frontend-design** | Design | HIGH | Frontend design |
| **next-best-practices** | Development | HIGH | Next.js best practices |
| **next-cache-components** | Development | MEDIUM | Next.js caching |
| **next-upgrade** | Development | MEDIUM | Next.js upgrades |
| **nodejs-backend-patterns** | Development | MEDIUM | Node.js backend |
| **python-executor** | Development | HIGH | Python execution |
| **python-patterns** | Development | HIGH | Python patterns |
| **python-testing-patterns** | Development | HIGH | Python testing |
| **pandas-pro** | Data | HIGH | Pandas data analysis |
| **scikit-learn** | AI/ML | HIGH | ML library |
| **senior-data-scientist** | Data | HIGH | Data science |
| **quant-analyst** | Trading | HIGH | Quantitative analysis |
| **quantitative-research** | Trading | HIGH | Quant research |
| **statistical-analysis** | Data | HIGH | Statistics |
| **variance-analysis** | Data | MEDIUM | Variance analysis |
| **vectorbt-expert** | Trading | HIGH | VectorBT backtesting |
| **tradingview-quantitative** | Trading | MEDIUM | TradingView |
| **mt5-strategy-tester** | Trading | MEDIUM | MT5 strategy testing |
| **pine-debugger** | Trading | MEDIUM | Pine Script debugging |
| **pine-developer** | Trading | MEDIUM | Pine Script development |
| **pine-manager** | Trading | MEDIUM | Pine Script management |
| **pine-publisher** | Trading | MEDIUM | Pine Script publishing |
| **pine-visualizer** | Trading | MEDIUM | Pine Script visualization |
| **seo** | Content Farm | LOW | SEO optimization |
| **pdf-omni** | Data | MEDIUM | PDF processing |
| **github-problem-search** | Research | MEDIUM | GitHub search |
| **skill-creator** | Development | HIGH | Skill creation |
| **sleek-design-mobile-apps** | Design | LOW | Mobile app design |
| **threejs-** (8 skills) | Design | LOW | Three.js 3D graphics |
| **vercel-** (2 skills) | Development | LOW | Vercel deployment |
| **web-design-guidelines** | Design | LOW | Web design |
| **project-workflow-analysis-blueprint-generator** | Development | LOW | Workflow blueprints |
| **creative-think** | Research | MEDIUM | Creative thinking (DUPLICATE) |
| **oransim** | AI/ML | MEDIUM | Oransim (DUPLICATE) |
| **scrapling** | Research | MEDIUM | Scrapling (DUPLICATE) |
| **spec-kit** | Development | LOW | Spec kit (DUPLICATE) |
| **violin** | Design | LOW | Violin (DUPLICATE) |

### 2.3 Agency Skills — `skills/agency-*` (70 total)

All agency skills are in `skills/`. Relevance assessment:

| Relevance | Count | Examples |
|-----------|-------|----------|
| **LOW** | ~30 | agency-design-* (8), agency-engineering-* (partial), agency-testing-* (8) |
| **DEAD** | ~40 | agency-accounts-payable, agency-healthcare-*, agency-hospitality, agency-legal-*, agency-real-estate, agency-recruitment, agency-sales-*, agency-supply-chain, agency-study-abroad, agency-government-*, agency-zk-steward, agency-identity-graph, agency-language-translator, agency-loan-officer, agency-lsp-index, agency-specialized-* (8) |

**Key insight:** Agency skills represent a massive library of specialized agent personas. Most are not actively used. The design/engineering/testing subsets could be valuable as reference patterns but are not actively loaded.

### 2.4 Tools — `tools/` (46 Python files)

| Tool | Category | Relevance | Notes |
|------|----------|-----------|-------|
| `workspace_cleanup.py` | System Health | CRITICAL | Loose file detection, oversized progress |
| `memory_sync_daemon.py` | System Health | CRITICAL | Background memory tracker |
| `progress-sync.py` | System Health | CRITICAL | Auto-sync agent progress |
| `summarize_progress.py` | System Health | CRITICAL | LLM progress summarization |
| `phase-gate.py` | SRRA-OPH | CRITICAL | Phase transition manager |
| `cc-workflow.py` | SRRA-OPH | HIGH | CC continuous workflow engine |
| `chat_sync.py` | System Health | HIGH | Team-chat → agent memory sync |
| `self_heal.py` | System Health | HIGH | Self-healing |
| `self_surgery.py` | System Health | HIGH | Self-surgery |
| `context_compaction.py` | System Health | HIGH | Context compaction |
| `subagent_manager.py` | System Health | HIGH | Subagent management |
| `memory_pipeline.py` | System Health | HIGH | Memory pipeline |
| `analyze_errors.py` | System Health | HIGH | Error analysis |
| `codemap-updater.py` | Development | HIGH | Code map updates |
| `import_agency_agents.py` | Agency | MEDIUM | Agency agent importer |
| `content_farm_orchestrator.py` | Content Farm | MEDIUM | Content farm orchestration |
| `claude_hermes_mcp.py` | AI/ML | MEDIUM | Claude/Hermes MCP |
| `hermes_workflows.py` | System Health | MEDIUM | Hermes workflows |
| `hermes-oc2-monitor.py` | System Health | MEDIUM | OC2 monitoring |
| `oc2-watchdog.py` | System Health | MEDIUM | OC2 watchdog |
| `oc2-context-monitor.py` | System Health | MEDIUM | OC2 context monitoring |
| `github_search.py` | Research | MEDIUM | GitHub search |
| `twitter_nitter.py` | Research | MEDIUM | Twitter via Nitter |
| `html_viewer.py` | Development | LOW | HTML viewer |
| `md2html.py` | Development | LOW | Markdown to HTML |
| `md_to_html.py` | Development | LOW | Duplicate of md2html |
| `beautiful_mermaid.py` | Design | LOW | Mermaid diagrams |
| `cli_anything.py` | Development | LOW | CLI anything |
| `create_tool.py` | Development | LOW | Tool creation |
| `motus_agent.py` | Communication | LOW | Motus agent |
| `task-runner.py` | System Health | LOW | Task runner |
| `workflow-runner.py` | System Health | LOW | Workflow runner |
| `cloud-burst.py` | System Health | LOW | Cloud burst |
| `cc-cron.py` | System Health | LOW | CC cron |
| `as-cron-check.py` | System Health | LOW | AS cron check |
| `progress-update-hook.py` | System Health | LOW | Progress update hook |
| `fix-phase-gate.py` | SRRA-OPH | LOW | Phase gate fix |
| `fix_rl_progress.py` | SRRA-OPH | LOW | RL progress fix |
| `agent-onboarding-tool.py` | System Health | LOW | Agent onboarding |
| `__init__.py` | — | — | Package init |

### 2.5 Operator Tools — `tools/operator/` (13 files)

| Tool | Category | Relevance | Notes |
|------|----------|-----------|-------|
| `desktop-control.py` | Operator Control | HIGH | Windows desktop control (Python) |
| `desktop_api.py` | Operator Control | HIGH | Desktop API |
| `system_operator.py` | Operator Control | HIGH | System operations (Python) |
| `vscode_bridge.py` | Operator Control | HIGH | VS Code bridge (Python) |
| `system-operator.js` | Operator Control | MEDIUM | System ops (Node.js) — **DUPLICATE** |
| `system-operator.test.js` | Operator Control | MEDIUM | Tests for above |
| `vscode-controller.js` | Operator Control | MEDIUM | VS Code control (Node.js) — **DUPLICATE** |
| `event-debug.js` | OCE | MEDIUM | Event debugging |
| `event-integration.js` | OCE | MEDIUM | Event integration |
| `observer-debug.js` | OCE | MEDIUM | Observer debugging |
| `observer-integration.js` | OCE | MEDIUM | Observer integration |
| `test-oce-integration.py` | OCE | MEDIUM | OCE integration test |
| `__pycache__/` | — | — | Cache |

### 2.6 SRRA-OPH — `srrs_opc/` (39 Python modules)

| Module | Category | Relevance | Notes |
|--------|----------|-----------|-------|
| `active_collar_fields.py` | SRRA-OPH | HIGH | Active collar fields |
| `adaptive_compression_engine.py` | SRRA-OPH | HIGH | Adaptive compression |
| `agent_bridge.py` | SRRA-OPH | HIGH | Agent bridge |
| `anti_manipulation.py` | SRRA-OPH | HIGH | Anti-manipulation |
| `attractor_reasoning.py` | SRRA-OPH | HIGH | Attractor reasoning |
| `base_patch.py` | SRRA-OPH | HIGH | Base patch |
| `bidirectional_coherence.py` | SRRA-OPH | HIGH | Bidirectional coherence |
| `capability_fields.py` | SRRA-OPH | HIGH | Capability fields |
| `coherence_yield_analyzer.py` | SRRA-OPH | HIGH | Coherence yield |
| `collar_layer.py` | SRRA-OPH | HIGH | Collar layer |
| `collar_topology_engine.py` | SRRA-OPH | HIGH | Collar topology |
| `consistency_validator.py` | SRRA-OPH | HIGH | Consistency validation |
| `constraint_alignment.py` | SRRA-OPH | HIGH | Constraint alignment |
| `constraint_propagator.py` | SRRA-OPH | HIGH | Constraint propagation |
| `continuity_collars.py` | SRRA-OPH | HIGH | Continuity collars |
| `contradiction_resolver.py` | SRRA-OPH | HIGH | Contradiction resolution |
| `distributed_consensus.py` | SRRA-OPH | HIGH | Distributed consensus |
| `drift_detector.py` | SRRA-OPH | HIGH | Drift detection |
| `drift_tracker.py` | SRRA-OPH | HIGH | Drift tracking |
| `dspy_contracts.py` | SRRA-OPH | HIGH | DSPy contracts |
| `dynamic_coupling.py` | SRRA-OPH | HIGH | Dynamic coupling |
| `entropy_budget_manager.py` | SRRA-OPH | HIGH | Entropy budget |
| `execution_patch.py` | SRRA-OPH | HIGH | Execution patch |
| `local_consensus.py` | SRRA-OPH | HIGH | Local consensus |
| `memory_patch.py` | SRRA-OPH | HIGH | Memory patch |
| `operator_continuity.py` | SRRA-OPH | HIGH | Operator continuity |
| `operator_patterns.py` | SRRA-OPH | HIGH | Operator patterns |
| `overlap_aware_tooling.py` | SRRA-OPH | HIGH | Overlap-aware tooling |
| `planner_patch.py` | SRRA-OPH | HIGH | Planner patch |
| `prediction_contracts.py` | SRRA-OPH | HIGH | Prediction contracts |
| `reconstruction_safe_exec.py` | SRRA-OPH | HIGH | Safe execution |
| `reconstruction_synthesizer.py` | SRRA-OPH | HIGH | Reconstruction |
| `recoverability_economics.py` | SRRA-OPH | HIGH | Recoverability economics |
| `recovery_anchors.py` | SRRA-OPH | HIGH | Recovery anchors |
| `reinforcement_engine.py` | SRRA-OPH | HIGH | Reinforcement |
| `repair_patch.py` | SRRA-OPH | HIGH | Repair patch |
| `resource_constrained_cognition.py` | SRRA-OPH | HIGH | Resource-constrained cognition |
| `strategic_preferences.py` | SRRA-OPH | HIGH | Strategic preferences |
| `structural_memory.py` | SRRA-OPH | HIGH | Structural memory |
| `sustainability_governance.py` | SRRA-OPH | HIGH | Sustainability governance |
| `sync_cost_optimizer.py` | SRRA-OPH | HIGH | Sync cost optimization |
| `temporal_attractors.py` | SRRA-OPH | HIGH | Temporal attractors |
| `topological_router.py` | SRRA-OPH | HIGH | Topological router |
| `topology_introspector.py` | SRRA-OPH | HIGH | Topology introspection |
| `topology_observer.py` | SRRA-OPH | HIGH | Topology observer |
| `trajectory_fields.py` | SRRA-OPH | HIGH | Trajectory fields |
| `workspace_integration.py` | SRRA-OPH | HIGH | Workspace integration |

**SRRA-OPH Tests:** 9 test files, 77 tests passing (Phases 1-9 complete)

### 2.7 OCE — `oce/` (9 Python modules)

| Module | Category | Relevance | Notes |
|--------|----------|-----------|-------|
| `backend/main.py` | OCE | CRITICAL | FastAPI Continuity Core API |
| `backend/event_fabric.py` | OCE | CRITICAL | Event fabric |
| `backend/observer_runtime.py` | OCE | HIGH | Observer runtime |
| `backend/srrs_adapter.py` | OCE | HIGH | SRRA-OPH substrate adapter |
| `backend/dspy_pipelines.py` | OCE | HIGH | DSPy pipelines |
| `backend/tests/test_event_fabric.py` | OCE | HIGH | Event fabric tests |
| `tests/conftest.py` | OCE | HIGH | Test configuration |
| `tests/test_oce_adapter.py` | OCE | HIGH | OCE adapter tests |

**OCE Frontend:** Next.js app (`oce/frontend/`) — package.json, tsconfig, tailwind, next.config

### 2.8 Projects — `projects/` (5 groups)

| Project | Category | Relevance | Notes |
|---------|----------|-----------|-------|
| `ads/` (6 sub-projects) | Content Farm | MEDIUM | ad-ai-chat, ad-deeke, ad-deeke-control, ad-dke, ad-tiktok, ad-voice |
| `ai-tools/` (4 sub-projects) | AI/ML | MEDIUM | copilotkit-integration, nailus, oransim, owl-brain, parallel_thought |
| `content/` (10 sub-projects) | Content Farm | MEDIUM | content-farm, deeke-uid, deekescript, DeekeScriptVscodePlugins, GroupControlApp, MediaCrawler, MoneyPrinterPlus, shortLink, Spider_XHS |
| `social/` (2 sub-projects) | Communication | LOW | discord-agent-hq, telegram-bots |
| `trading/` (5 sub-projects) | Trading | MEDIUM | backtests, mt5-mcp, nautilus, nautilus_trader, strategies, xhscrawl |

---

## 3. DUPLICATES

### 3.1 Skill Duplicates (`skills/` ↔ `.agents/skills/`)

| Skill | Location 1 | Location 2 | Recommendation |
|-------|-----------|-----------|----------------|
| `creative-think` | `skills/creative-think/` | `.agents/skills/creative-think/` | Keep `.agents/` version (more recent), archive `skills/` version |
| `oransim` | `skills/oransim/` | `.agents/skills/oransim/` | Keep `.agents/` version, archive `skills/` version |
| `scrapling` | `skills/scrapling/` | `.agents/skills/scrapling/` | Keep `.agents/` version, archive `skills/` version |
| `spec-kit` | `skills/spec-kit/` | `.agents/skills/spec-kit/` | Keep `.agents/` version, archive `skills/` version |
| `violin` | `skills/violin/` | `.agents/skills/violin/` | Keep `.agents/` version, archive `skills/` version |

### 3.2 Tool Duplicates (Python ↔ Node.js)

| Functionality | Python | Node.js | Recommendation |
|---------------|--------|---------|----------------|
| System operations | `system_operator.py` | `system-operator.js` | Keep Python (more complete), archive JS |
| VS Code control | `vscode_bridge.py` | `vscode-controller.js` | Keep Python (more complete), archive JS |
| Mermaid diagrams | `beautiful_mermaid.py` | — | Also `beautiful-mermaid` skill — consolidate |
| Markdown→HTML | `md2html.py` + `md_to_html.py` | — | **Two Python duplicates** — merge into one |

### 3.3 Naming Variants

| Variant A | Variant B | Issue |
|-----------|-----------|-------|
| `beautiful-mermaid` (skill) | `beautiful_mermaid` (skill + tool) | Hyphen vs underscore — confusing |
| `md2html` (skill) | `md2html.py` + `md_to_html.py` (tools) | Three files, same purpose |

---

## 4. GAPS — What's Missing

| Gap | Priority | Description |
|-----|----------|-------------|
| **Unified capability registry** | HIGH | No single file maps all skills → capabilities → OWL usage patterns |
| **Skill loader/discovery** | HIGH | No automated way to discover and load relevant skills at runtime |
| **Relevance scoring** | MEDIUM | No automated system to track which skills/tools are actually used |
| **OCE Phase 3-6 implementation** | HIGH | Observer Runtime (Phase 3) is pending; Structural Memory, Observability, Execution Substrate not started |
| **SRRA-OPH Phase 10** | MEDIUM | Phases 1-9 complete (77/77 tests); next phase not defined |
| **Trading strategy execution** | MEDIUM | Backtesting infrastructure exists (nautilus_trader, vectorbt) but no live execution |
| **Content farm automation** | MEDIUM | Orchestrator exists but DeekeScript projects are fragmented across `projects/ads/` and `projects/content/` |
| **Testing coverage for tools** | LOW | Only SRRA-OPH and OCE have test suites; tools/ has no tests |
| **Documentation generation** | LOW | No auto-generated docs from code; docs/ directory is mostly hand-written |
| **Security audit** | LOW | No active security scanning; agency-security-engineer skill exists but not used |

---

## 5. RECOMMENDED PRIORITY ORDER

### Immediate (P0) — Active Development
1. **OCE Phase 3** — Observer Runtime (OC2 lead)
2. **OCE Phase 2** — Event Fabric completion (CC lead)
3. **System Health** — Keep operational (all agents)
4. **SRRA-OPH maintenance** — 77 tests passing, keep green

### Short-term (P1) — Consolidation
5. **Deduplicate skills** — Archive 5 duplicates from `skills/` that exist in `.agents/skills/`
6. **Deduplicate tools** — Merge `md2html.py` + `md_to_html.py`; archive JS operator files
7. **Archive dead agency skills** — Move ~40 DEAD agency skills to `skills/archive/`
8. **Unified capability registry** — Create `docs/CAPABILITY_REGISTRY.md`

### Medium-term (P2) — Enhancement
9. **OCE Phases 4-6** — Structural Memory, Observability, Execution Substrate
10. **Content farm unification** — Consolidate ads/ + content/ projects
11. **Trading strategy pipeline** — Connect backtesting → live execution
12. **Tool test coverage** — Add tests for critical tools

### Long-term (P3) — Exploration
13. **Three.js visualization** — 8 threejs skills exist but unused
14. **Mobile app development** — sleek-design-mobile-apps skill exists
15. **Agency agent activation** — Evaluate which agency skills to activate

---

## 6. STATISTICS SUMMARY

| Category | Count | CRITICAL | HIGH | MEDIUM | LOW | DEAD |
|----------|-------|----------|------|--------|-----|------|
| Skills (`skills/`) | 97 | 1 | 5 | 10 | 8 | ~40 |
| Skills (`.agents/skills/`) | 57 | 0 | 14 | 15 | 10 | 0 |
| Tools (`tools/*.py`) | 46 | 4 | 10 | 12 | 15 | 0 |
| Operator tools | 13 | 0 | 4 | 6 | 0 | 0 |
| SRRA-OPH modules | ~50 | 0 | ~50 | 0 | 0 | 0 |
| OCE modules | 9 | 2 | 5 | 2 | 0 | 0 |
| Projects | 5 groups | 0 | 0 | 4 | 1 | 0 |
| **TOTAL** | **~277** | **7** | **88** | **49** | **33** | **~40** |

---

## 7. ARCHITECTURE VIEW

```
WORKSPACE
├── CORE (CRITICAL + HIGH)
│   ├── SRRA-OPH (srrs_opc/) — 77 tests passing, Phases 1-9 complete
│   ├── OCE (oce/) — Phases 1-2 done, Phase 3 pending
│   ├── System Health (tools + skills) — Operational
│   ├── Operator Control (tools/operator/) — Desktop, VS Code, System
│   └── Agent Team (progress/, shared-conversations/) — 6 agents active
│
├── ACTIVE PROJECTS (MEDIUM)
│   ├── Content Farm (projects/content/, projects/ads/)
│   ├── Trading (projects/trading/)
│   ├── AI Tools (projects/ai-tools/)
│   └── Social (projects/social/)
│
├── REFERENCE (LOW)
│   ├── Agency Skills (70 skills) — Mostly unused
│   ├── Design Skills (threejs, violin, etc.)
│   └── Development Patterns (python-patterns, etc.)
│
└── ARCHIVE CANDIDATES (DEAD)
    ├── ~40 unused agency skills
    ├── JS operator duplicates
    └── Naming variants (beautiful-mermaid/_mermaid, md2html/md_to_html)
```

---

*End of Structure Lead Report*
