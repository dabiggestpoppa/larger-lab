# OWL Skills & Tools Master Index

> **Last Cleaned**: 2026-05-16 — Archived 61 dead agency skills, merged 5 duplicates
> **Generated**: 2026-05-16 21:25 EDT
> **Total Items**: 277 inventoried | 163 skills | 46 tools | 39 SRRA-OPH modules | 9 OCE modules
> **Mission**: Every skill and tool OWL needs to build without limits

---

## ACTIVE SKILLS (Tier 1 — Must Have)

### Core Operations
| Skill | Location | Purpose |
|-------|----------|---------|
| system-health | skills/system-health/ | Gateway/config/workspace validation |
| harness-engineering | skills/harness-engineering/ | Agent reliability patterns |
| docker-ops | skills/docker-ops/ | Container management |
| cicd-pipeline | skills/cicd-pipeline/ | GitHub Actions + local CI |
| oce-testing | skills/oce-testing/ | OCE test patterns |
| db-ops | skills/db-ops/ | Database operations |
| srra-oph-build | skills/srra-oph-build/ | SRRA-OPH build patterns |
| agent-team-workflow | skills/agent-team-workflow/ | Team coordination |
| agent-harness-sop | skills/agent-harness-sop/ | 7-phase tool building |
| subagent-manager | skills/subagent-manager/ | Subagent orchestration |
| context-compaction | skills/context-compaction/ | 5-layer context reduction |
| create-tool | skills/create-tool/ | GitHub repo → tool + skill |
| cli-anything | skills/cli-anything/ | Make any software agent-native |
| skill-creator | skills/skill-creator/ | Create/modify skills |
| agent-onboarding | skills/agent-onboarding/ | Onboard new agents |

### Development
| Skill | Location | Purpose |
|-------|----------|---------|
| python-patterns | skills/python-patterns/ | Idiomatic Python |
| python-testing-patterns | skills/python-testing-patterns/ | pytest, TDD |
| fastapi-python | skills/fastapi-python/ | OCE backend patterns |
| fastapi-templates | skills/fastapi-templates/ | Production FastAPI |
| git-workflow-master | skills/agency-engineering-git-workflow-master/ | Git patterns |
| code-reviewer | skills/agency-engineering-code-reviewer/ | Code review |
| as-code-review | skills/as-code-review/ | SRRA-OPH review |
| technical-writer | skills/agency-engineering-technical-writer/ | Documentation |
| spec-kit | skills/spec-kit/ | Spec-driven development |
| beautiful-mermaid | skills/beautiful-mermaid/ | Diagram generation |
| md2html | skills/md2html/ | Markdown → HTML |
| pdf-omni | skills/pdf-omni/ | PDF processing |

### Research & Analysis
| Skill | Location | Purpose |
|-------|----------|---------|
| scrapling | skills/scrapling/ | Web scraping |
| hugging-face-cli | skills/hugging-face-cli/ | HF models/datasets |
| creative-think | skills/creative-think/ | Lateral reasoning |

---

## AVAILABLE SKILLS (Tier 2 — Should Activate)

### Infrastructure
| Skill | Location | Purpose |
|-------|----------|---------|
| agency-testing-api-tester | skills/agency-testing-api-tester/ | API validation |
| agency-testing-performance-benchmarker | skills/agency-testing-performance-benchmarker/ | Benchmarking |
| agency-engineering-devops-automator | skills/agency-engineering-devops-automator/ | CI/CD automation |
| agency-engineering-database-optimizer | skills/agency-engineering-database-optimizer/ | DB optimization |
| agency-engineering-sre | skills/agency-engineering-sre/ | SRE practices |
| agency-engineering-incident-response-commander | skills/agency-engineering-incident-response-commander/ | Incident management |
| agency-specialized-mcp-builder | skills/agency-specialized-mcp-builder/ | Build MCP servers |

### Data & AI
| Skill | Location | Purpose |
|-------|----------|---------|
| pandas-pro | skills/pandas-pro/ | Data analysis |
| scikit-learn | skills/scikit-learn/ | ML pipelines |
| senior-data-scientist | skills/senior-data-scientist/ | Data science |
| statistical-analysis | skills/statistical-analysis/ | Statistics |
| quant-analyst | skills/quant-analyst/ | Quantitative analysis |
| quantitative-research | skills/quantitative-research/ | Quant research |
| vectorbt-expert | skills/vectorbt-expert/ | VectorBT backtesting |

### Frontend
| Skill | Location | Purpose |
|-------|----------|---------|
| next-best-practices | skills/next-best-practices/ | Next.js patterns |
| frontend-design | skills/frontend-design/ | UI design |
| accessibility | skills/accessibility/ | WCAG compliance |

---

## TOOLS (Active)

### Operator Control
| Tool | Location | Purpose |
|------|----------|---------|
| desktop-control.py | tools/operator/ | Screen capture, input sim, window mgmt |
| vscode_bridge.py | tools/operator/ | VS Code control |
| system_operator.py | tools/operator/ | Process, package, env, service, network |
| desktop_api.py | tools/operator/ | FastAPI on port 8001 |
| hermes-watchdog.py | tools/ | OWL safety monitor |

### System Tools
| Tool | Location | Purpose |
|------|----------|---------|
| hermes-watchdog.py | tools/ | Health monitoring |
| workspace_cleanup.py | tools/ | Workspace optimization |
| progress-sync.py | tools/ | Agent progress sync |
| memory_sync_daemon.py | tools/ | Memory management |
| summarize_progress.py | tools/ | LLM progress summarization |
| chat_sync.py | tools/ | Team chat sync |
| self_heal.py | tools/ | Self-healing framework |
| phase-gate.py | tools/ | Phase transition manager |
| cc-workflow.py | tools/ | CC workflow engine |

---

## NEW TOOLS TO INSTALL (From MAD's Links)

### Trading
| Tool | Source | Purpose | Priority |
|------|--------|---------|----------|
| tradingview-mcp-server | pip | Real-time market data + 30+ indicators | HIGH |
| tensortrade | pip | RL trading framework | MEDIUM |
| QuantLib | pip | Quantitative finance | MEDIUM |

### AI & Voice
| Tool | Source | Purpose | Priority |
|------|--------|---------|----------|
| supertonic | pip/HF | On-device multilingual TTS (31 languages) | MEDIUM |
| scientific-agent-skills | pip | 135 scientific research skills | MEDIUM |
| llm_wiki | github | Self-building knowledge base | LOW |

### Memory & Knowledge
| Tool | Source | Purpose | Priority |
|------|--------|---------|----------|
| PAI (v5.0) | github | Life Operating System / Ideal State | MEDIUM |
| agent-hooks | github | Deterministic agent control | HIGH |

---

## ARCHIVE CANDIDATES (Tier 4 — 40 items)

All `skills/agency-*` that are NOT in Tier 1-3:
- accounts-payable-agent, compliance-auditor, blockchain-security-auditor
- solidity-smart-contract-engineer, corporate-training-designer, customer-service
- healthcare-*, hospitality-*, hr-onboarding, legal-*, loan-officer-assistant
- real-estate-*, recruitment-specialist, sales-*, study-abroad-advisor
- supply-chain-strategist, government-digital-presales-consultant

---

## DUPLICATES TO MERGE

| File 1 | File 2 | Action |
|--------|--------|--------|
| skills/creative-think/ | .agents/skills/creative-think/ | Keep .agents version |
| skills/oransim/ | .agents/skills/oransim/ | Keep .agents version |
| skills/scrapling/ | .agents/skills/scrapling/ | Keep .agents version |
| skills/spec-kit/ | .agents/skills/spec-kit/ | Keep .agents version |
| skills/violin/ | .agents/skills/violin/ | Keep .agents version |
| skills/beautiful-mermaid/ | skills/beautiful_mermaid/ | Merge (hyphen vs underscore) |
| tools/md2html.py | tools/md_to_html.py | Merge |
| tools/operator/system-operator.js | tools/operator/system_operator.py | Keep Python |
| tools/operator/vscode-controller.js | tools/operator/vscode_bridge.py | Keep Python |

---

## IMPLEMENTATION STATUS

### Complete ✅
- [x] System Health Skill
- [x] Harness Engineering Skill
- [x] Docker Operations Skill
- [x] CI/CD Pipeline Skill
- [x] OCE Testing Skill
- [x] Database Operations Skill
- [x] Operator Control Layer (Phases A+B+C)
- [x] Hermes Watchdog
- [x] Full workspace audit (277 items)
- [x] Relevance map (163 skills)
- [x] Implementation plan (6 phases)

### In Progress 🔄
- [ ] TradingView MCP installation
- [ ] Deduplication of dead skills
- [ ] Memory architecture overhaul
- [ ] OCE Phase 3 DSPy pipelines

### Pending ⏳
- [ ] TensorTrade integration
- [ ] Scientific Agent Skills installation
- [ ] Agent Hooks system
- [ ] LLM Wiki knowledge base
- [ ] Supertonic TTS integration
- [ ] PAI Ideal State Architecture
