---
name: agency-agents
description: >
  Collection of 147+ specialized AI agent personalities from msitarzewski/agency-agents.
  Each agent has deep domain expertise, personality, workflows, and deliverables.
  Divisions: Engineering (29), Specialized (41), Marketing (30), Design (8), Testing (8),
  Sales (8), Finance (5), Product (5), Project Management (6), Academic (5),
  Spatial Computing (6), Game Development (5+), Paid Media (7), Support (6), Strategy (3).
  Use when you need a specialized agent for a specific task.
version: 1.0.0
source: https://github.com/msitarzewski/agency-agents
---

# 🎭 Agency Agents — Specialized AI Agent Collection

> **Source**: [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) (MIT, 147+ agents)
> **Purpose**: Drop-in specialized agent personalities for specific tasks.
> **Each agent has**: Identity, personality, core mission, critical rules, deliverables, workflows, success metrics.

## How to Use

Each agent is installed as a skill at `skills/agency-<slug>/SKILL.md`.
HTML versions at `html-viewer/agency-<slug>.html`.

### Activate an Agent
Read the agent's SKILL.md to adopt its personality and workflow:
```
Read skills/agency-frontend-developer/SKILL.md → Act as Frontend Developer
Read skills/agency-security-engineer/SKILL.md → Act as Security Engineer
```

### Import New Agents
```bash
# List all available agents
python tools/import_agency_agents.py --list

# Import a division
python tools/import_agency_agents.py --division engineering

# Import a specific agent
python tools/import_agency_agents.py --agent engineering-ai-engineer
```

## Division Roster

### 💻 Engineering (29 agents)
| Agent | Specialty |
|-------|-----------|
| `agency-frontend-developer` | React/Vue/Angular, UI implementation |
| `agency-backend-architect` | API design, database, scalability |
| `agency-mobile-app-builder` | iOS/Android, React Native, Flutter |
| `agency-ai-engineer` | ML models, deployment, AI integration |
| `agency-devops-automator` | CI/CD, infrastructure, cloud ops |
| `agency-rapid-prototyper` | Fast POCs, MVPs |
| `agency-senior-developer` | Laravel/Livewire, advanced patterns |
| `agency-security-engineer` | Threat modeling, secure code review |
| `agency-software-architect` | System design, DDD, patterns |
| `agency-sre` | SLOs, error budgets, observability |
| `agency-data-engineer` | Data pipelines, lakehouse, ETL |
| `agency-database-optimizer` | Schema design, query optimization |
| `agency-code-reviewer` | PR reviews, quality gates |
| `agency-technical-writer` | Developer docs, API reference |
| `agency-git-workflow-master` | Branching strategies, conventional commits |
| `agency-incident-response-commander` | Incident management, post-mortems |
| `agency-embedded-firmware-engineer` | Bare-metal, RTOS, ESP32/STM32 |
| `agency-solidity-smart-contract-engineer` | EVM contracts, DeFi |
| `agency-threat-detection-engineer` | SIEM rules, threat hunting |
| `agency-voice-ai-integration-engineer` | Speech-to-text, Whisper, ASR |
| `agency-email-intelligence-engineer` | Email parsing, MIME extraction |
| `agency-feishu-integration-developer` | Feishu/Lark bots, workflows |
| `agency-wechat-mini-program-developer` | WeChat Mini Programs |
| `agency-cms-developer` | WordPress/Drupal |
| `agency-filament-optimization-specialist` | Filament PHP admin UX |
| `agency-autonomous-optimization-architect` | LLM routing, cost optimization |
| `agency-ai-data-remediation-engineer` | Self-healing data pipelines |
| `agency-codebase-onboarding-engineer` | Fast developer onboarding |
| `agency-minimal-change-engineer` | Surgical code changes |

### 🎯 Specialized (41 agents)
| Agent | Specialty |
|-------|-----------|
| `agency-agents-orchestrator` | Multi-agent coordination |
| `agency-mcp-builder` | MCP servers, AI agent tooling |
| `agency-workflow-architect` | Workflow discovery, mapping, specification |
| `agency-document-generator` | PDF, PPTX, DOCX, XLSX generation |
| `agency-automation-governance-architect` | Automation governance, n8n |
| `agency-agentic-identity-trust` | Agent identity, authentication |
| `agency-identity-graph-operator` | Shared identity resolution |
| `agency-blockchain-security-auditor` | Smart contract audits |
| `agency-compliance-auditor` | SOC 2, ISO 27001, HIPAA |
| `agency-lsp-index-engineer` | Language Server Protocol |
| `agency-model-qa` | ML audits, interpretability |
| `agency-zk-steward` | Knowledge management, Zettelkasten |
| `agency-civil-engineer` | Structural analysis, building codes |
| `agency-salesforce-architect` | Multi-cloud Salesforce |
| `agency-cultural-intelligence-strategist` | Global UX, cultural exclusion |
| `agency-developer-advocate` | Community building, DX |
| `agency-corporate-training-designer` | Enterprise training |
| `agency-recruitment-specialist` | Talent acquisition |
| `agency-supply-chain-strategist` | Supply chain optimization |
| `agency-accounts-payable-agent` | Payment processing |
| `agency-sales-outreach` | Cold prospecting, B2B outreach |
| `agency-sales-data-extraction-agent` | Excel monitoring, sales metrics |
| `agency-data-consolidation-agent` | Sales data aggregation |
| `agency-report-distribution-agent` | Automated report delivery |
| `agency-hr-onboarding` | Pre-boarding, compliance, 30-60-90 |
| `agency-customer-service` | Omnichannel support |
| `agency-healthcare-customer-service` | HIPAA-aware patient support |
| `agency-hospitality-guest-services` | Hotels, resorts, restaurants |
| `agency-retail-customer-returns` | Return processing, fraud prevention |
| `agency-language-translator` | Spanish ↔ English |
| `agency-legal-billing-time-tracking` | Time capture, billing |
| `agency-legal-client-intake` | Prospect qualification |
| `agency-legal-document-review` | Contract review |
| `agency-loan-officer-assistant` | Mortgage lending |
| `agency-real-estate-buyer-seller` | Real estate transactions |
| `agency-study-abroad-advisor` | International education |
| `agency-government-digital-presales-consultant` | China ToG |
| `agency-healthcare-marketing-compliance` | Healthcare advertising |
| `agency-french-consulting-market` | French IT market |
| `agency-korean-business-navigator` | Korean business culture |
| `agency-chief-of-staff` | Chief of Staff workflows |

### 🧪 Testing (8 agents)
| Agent | Specialty |
|-------|-----------|
| `agency-accessibility-auditor` | WCAG auditing |
| `agency-api-tester` | API validation, integration testing |
| `agency-evidence-collector` | Screenshot-based QA |
| `agency-performance-benchmarker` | Load testing, optimization |
| `agency-reality-checker` | Production readiness certification |
| `agency-test-results-analyzer` | Test evaluation, metrics |
| `agency-tool-evaluator` | Technology assessment |
| `agency-workflow-optimizer` | Process optimization |

### 🎨 Design (8 agents)
| Agent | Specialty |
|-------|-----------|
| `agency-brand-guardian` | Brand identity, positioning |
| `agency-image-prompt-engineer` | AI image generation prompts |
| `agency-inclusive-visuals-specialist` | Representation, bias mitigation |
| `agency-ui-designer` | Visual design, component libraries |
| `agency-ux-architect` | Technical architecture, CSS systems |
| `agency-ux-researcher` | User testing, behavior analysis |
| `agency-visual-storyteller` | Visual narratives |
| `agency-whimsy-injector` | Delight, micro-interactions |

### 🎬 Project Management (6 agents)
| Agent | Specialty |
|-------|-----------|
| `agency-experiment-tracker` | A/B tests, hypothesis validation |
| `agency-jira-workflow-steward` | Git workflow, traceability |
| `agency-project-shepherd` | Cross-functional coordination |
| `agency-studio-operations` | Day-to-day efficiency |
| `agency-studio-producer` | High-level orchestration |
| `agency-project-manager-senior` | Realistic scoping, task conversion |

### 📊 Other Divisions
- **Marketing** (30): Growth hacking, content, SEO, social media, China market
- **Sales** (8): Outbound, discovery, deals, proposals, pipeline
- **Finance** (5): Bookkeeping, FP&A, investment research, tax
- **Product** (5): Sprint prioritization, trend research, feedback
- **Academic** (5): Anthropology, geography, history, narratology, psychology
- **Spatial Computing** (6): XR, visionOS, Metal, WebXR
- **Game Development** (5+): Unity, Unreal, Godot, Blender, Roblox
- **Paid Media** (7): PPC, tracking, creative, programmatic
- **Support** (6): Support, analytics, finance, infrastructure, legal
- **Strategy** (3): Business strategy

## Integration with larger-lab

### Agent Workflow
1. **CC** identifies need for specialized expertise
2. **PM** imports relevant agency agents (`import_agency_agents.py`)
3. **All agents** can activate agency personas by reading their SKILL.md
4. Agency agents complement (don't replace) our core team (CC, OC, OC2, AS, PM, RL)

### HTML Standard
All agency agents are available as HTML pages in `html-viewer/` for better agent readability.
Open with: `python tools/html_viewer.py`

### Key Files
- `tools/import_agency_agents.py` — Import script
- `skills/agency-*/SKILL.md` — Agent skill files
- `html-viewer/agency-*.html` — HTML versions
- `C:\Users\wifik\Desktop\projects\agency-agents\` — Source repo
