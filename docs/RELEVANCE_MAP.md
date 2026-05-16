# OWL Relevance Map

> **Generated:** 2026-05-16
> **Author:** Relevance Lead (Subagent Audit)
> **Mission:** Ensure OWL has every tool and skill possible to build without limits.
>
> **Why This Matters:** This organization ensures OWL can self-improve systematically instead of randomly. By knowing what exists, what's missing, and what's priority, OWL can reach for the right capability at the right time — and know when something needs to be built from scratch.

---

## Tier 1: Must Have (Core Operations — OWL uses these NOW)

| Skill/Tool | Location | Status | Action |
|------------|----------|--------|--------|
| **File operations** (read/write/edit) | Built-in tools | ✅ Active | Core capability — no action needed |
| **Shell execution** (exec/process) | Built-in tools | ✅ Active | Core capability — no action needed |
| **Web search & fetch** | Built-in tools | ✅ Active | Core capability — no action needed |
| **Image analysis** | Built-in `image` tool | ✅ Active | Vision model access for screenshots, diagrams |
| **Image generation** | Built-in `image_generate` tool | ✅ Active | Generate diagrams, visual assets |
| **Video generation** | Built-in `video_generate` tool | ✅ Active | Generate demo videos, animations |
| **System health monitoring** | `skills/system-health/SKILL.md` | ✅ Active | Periodic workspace audit — already in use |
| **SRRA-OPH build** | `skills/srra-oph-build/SKILL.md` | ✅ Active | Core build skill for all 9 phases |
| **Agent team workflow** | `skills/agent-team-workflow/SKILL.md` | ✅ Active | Coordination protocol for CC/OC/AS/PM/RL |
| **Agent harness SOP** | `skills/agent-harness-sop/SKILL.md` | ✅ Active | 7-phase tool building pipeline |
| **Subagent manager** | `skills/subagent-manager/SKILL.md` + `tools/subagent_manager.py` | ✅ Active | Sidechain pattern for subagent execution |
| **Context compaction** | `skills/context-compaction/SKILL.md` + `tools/context_compaction.py` | ✅ Active | 5-layer context reduction pipeline |
| **Python testing patterns** | `skills/python-testing-patterns/SKILL.md` | ✅ Active | pytest, fixtures, mocking, TDD |
| **Python patterns** | `skills/python-patterns/SKILL.md` | ✅ Active | Idiomatic Python, PEP 8, type hints |
| **FastAPI Python** | `skills/fastapi-python/SKILL.md` | ✅ Active | OCE backend is FastAPI — directly relevant |
| **FastAPI templates** | `skills/fastapi-templates/SKILL.md` | ✅ Active | Production-ready FastAPI project structures |
| **Git workflow master** | `skills/agency-engineering-git-workflow-master/SKILL.md` | ✅ Active | Branching strategies, conventional commits, rebasing |
| **Code reviewer** | `skills/agency-engineering-code-reviewer/SKILL.md` | ✅ Active | Constructive code review methodology |
| **AS code review** | `skills/as-code-review/SKILL.md` | ✅ Active | SRRA-OPH specific review checklist |
| **Technical writer** | `skills/agency-engineering-technical-writer/SKILL.md` | ✅ Active | API docs, READMEs, tutorials |
| **Spec Kit** | `skills/spec-kit/SKILL.md` | ✅ Active | Spec-driven development (constitution→spec→plan→tasks) |
| **Create tool** | `skills/create-tool/SKILL.md` + `tools/create_tool.py` | ✅ Active | GitHub repo → agent tool + skill pipeline |
| **CLI-Anything** | `skills/cli-anything/SKILL.md` + `tools/cli_anything.py` | ✅ Active | Make any software agent-native |
| **Skill creator** | `skills/skill-creator/SKILL.md` | ✅ Active | Create/modify/measure skill performance |
| **Agent onboarding** | `skills/agent-onboarding/SKILL.md` + `tools/agent-onboarding-tool.py` | ✅ Active | Onboard new agents into workspace |
| **Scrapling** | `skills/scrapling/SKILL.md` | ✅ Active | Adaptive web scraping when web_fetch fails |
| **Hugging Face CLI** | `skills/hugging-face-cli/SKILL.md` | ✅ Active | Manage HF models, datasets, spaces |
| **PDF-Omni** | `skills/pdf-omni/SKILL.md` | ✅ Active | PDF text extraction, OCR, image analysis |
| **md2html** | `skills/md2html/SKILL.md` + `tools/md2html.py` | ✅ Active | Convert Markdown docs to beautiful HTML |
| **Beautiful Mermaid** | `skills/beautiful-mermaid/SKILL.md` + `tools/beautiful_mermaid.py` | ✅ Active | Render Mermaid diagrams as SVG/ASCII |
| **Creative Think** | `skills/creative-think/SKILL.md` | ✅ Active | Structured lateral reasoning framework |

---

## Tier 2: Should Have (Project Acceleration — Significantly speed up current work)

| Skill/Tool | Location | Status | Action |
|------------|----------|--------|--------|
| **API Tester** | `skills/agency-testing-api-tester/SKILL.md` | 🔶 Available, not actively used | Use for OCE endpoint validation |
| **Performance Benchmarker** | `skills/agency-testing-performance-benchmarker/SKILL.md` | 🔶 Available, not actively used | Benchmark OCE pipeline performance |
| **Test Results Analyzer** | `skills/agency-testing-test-results-analyzer/SKILL.md` | 🔶 Available, not actively used | Analyze test output systematically |
| **DevOps Automator** | `skills/agency-engineering-devops-automator/SKILL.md` | 🔶 Available, not actively used | CI/CD pipeline automation |
| **Database Optimizer** | `skills/agency-engineering-database-optimizer/SKILL.md` | 🔶 Available, not actively used | Schema design, query optimization |
| **Data Engineer** | `skills/agency-engineering-data-engineer/SKILL.md` | 🔶 Available, not actively used | Data pipelines, ETL/ELT |
| **Backend Architect** | `skills/agency-engineering-backend-architect/SKILL.md` | 🔶 Available, not actively used | System design, microservices |
| **Software Architect** | `skills/agency-engineering-software-architect/SKILL.md` | 🔶 Available, not actively used | DDD, architectural patterns, ADRs |
| **Security Engineer** | `skills/agency-engineering-security-engineer/SKILL.md` | 🔶 Available, not actively used | Threat modeling, secure code review |
| **SRE** | `skills/agency-engineering-sre/SKILL.md` | 🔶 Available, not actively used | SLOs, error budgets, observability |
| **Incident Response Commander** | `skills/agency-engineering-incident-response-commander/SKILL.md` | 🔶 Available, not actively used | Production incident management |
| **Minimal Change Engineer** | `skills/agency-engineering-minimal-change-engineer/SKILL.md` | 🔶 Available, not actively used | Minimum-viable diffs, no scope creep |
| **Rapid Prototyper** | `skills/agency-engineering-rapid-prototyper/SKILL.md` | 🔶 Available, not actively used | Fast PoC/MVP development |
| **AI Engineer** | `skills/agency-engineering-ai-engineer/SKILL.md` | 🔶 Available, not actively used | ML model development, deployment |
| **AI Data Remediation** | `skills/agency-engineering-ai-data-remediation-engineer/SKILL.md` | 🔶 Available, not actively used | Self-healing data pipelines |
| **Autonomous Optimization Architect** | `skills/agency-engineering-autonomous-optimization-architect/SKILL.md` | 🔶 Available, not actively used | Performance/cost guardrails |
| **MCP Builder** | `skills/agency-specialized-mcp-builder/SKILL.md` | 🔶 Available, not actively used | Build MCP servers for custom tools |
| **Workflow Architect** | `skills/agency-specialized-workflow-architect/SKILL.md` | 🔶 Available, not actively used | Complete workflow tree mapping |
| **Model QA Specialist** | `skills/agency-specialized-model-qa/SKILL.md` | 🔶 Available, not actively used | Audit ML/statistical models |
| **Document Generator** | `skills/agency-specialized-document-generator/SKILL.md` | 🔶 Available, not actively used | Generate PDF, PPTX, DOCX, XLSX |
| **LSP/Index Engineer** | `skills/agency-lsp-index-engineer/SKILL.md` | 🔶 Available, not actively used | Code intelligence, semantic indexing |
| **Pandas Pro** | `skills/pandas-pro/SKILL.md` | 🔶 Available, not actively used | DataFrame operations, data analysis |
| **Scikit-learn** | `skills/scikit-learn/SKILL.md` | 🔶 Available, not actively used | Classical ML, pipelines |
| **Senior Data Scientist** | `skills/senior-data-scientist/SKILL.md` | 🔶 Available, not actively used | Statistical modeling, experimentation |
| **Statistical Analysis** | `skills/statistical-analysis/SKILL.md` | 🔶 Available, not actively used | Hypothesis testing, outlier detection |
| **Variance Analysis** | `skills/variance-analysis/SKILL.md` | 🔶 Available, not actively used | Financial variance decomposition |
| **Quant Analyst** | `skills/quant-analyst/SKILL.md` | 🔶 Available, not actively used | Financial models, backtesting |
| **Quantitative Research** | `skills/quantitative-research/SKILL.md` | 🔶 Available, not actively used | Alpha generation, factor models |
| **VectorBT Expert** | `skills/vectorbt-expert/SKILL.md` | 🔶 Available, not actively used | VectorBT backtesting |
| **Python Executor** | `skills/python-executor/SKILL.md` | 🔶 Available, not actively used | Sandboxed Python with 100+ libraries |
| **Node.js Backend Patterns** | `skills/nodejs-backend-patterns/SKILL.md` | 🔶 Available, not actively used | Express/Fastify, middleware, auth |
| **Next.js Best Practices** | `skills/next-best-practices/SKILL.md` | 🔶 Available, not actively used | OCE frontend is Next.js |
| **Next.js Cache Components** | `skills/next-cache-components/SKILL.md` | 🔶 Available, not actively used | PPR, cache directives |
| **Vercel React Best Practices** | `skills/vercel-react-best-practices/SKILL.md` | 🔶 Available, not actively used | React performance optimization |
| **Vercel Composition Patterns** | `skills/vercel-composition-patterns/SKILL.md` | 🔶 Available, not actively used | Scalable component architecture |
| **Frontend Design** | `skills/frontend-design/SKILL.md` | 🔶 Available, not actively used | Production-grade UI interfaces |
| **Accessibility** | `skills/accessibility/SKILL.md` | 🔶 Available, not actively used | WCAG 2.2 compliance |
| **Web Design Guidelines** | `skills/web-design-guidelines/SKILL.md` | 🔶 Available, not actively used | UI review against best practices |
| **SEO** | `skills/seo/SKILL.md` | 🔶 Available, not actively used | Search engine optimization |
| **Project Workflow Analysis** | `skills/project-workflow-analysis-blueprint-generator/SKILL.md` | 🔶 Available, not actively used | End-to-end workflow documentation |
| **GitHub Problem Search** | `skills/github-problem-search/SKILL.md` | 🔶 Available, not actively used | Intent-based repo discovery |
| **Use My Browser** | `skills/use-my-browser/SKILL.md` | 🔶 Available, not actively used | Control real Chrome via Tampermonkey |
| **Twitter Bookmarks** | `skills/twitter-bookmarks/SKILL.md` | 🔶 Available, not actively used | Read/organize Twitter bookmarks |
| **Social Media Agent** | `skills/social-media-agent/SKILL.md` | 🔶 Available, not actively used | X/Twitter automation |
| **Godfery TW (Twitter)** | `skills/godfery-tw/SKILL.md` | 🔶 Available, not actively used | Twitter search + post via SkillBoss |
| **Hermes Workflows** | `skills/hermes-workflows/SKILL.md` + `tools/hermes_workflows.py` | 🔶 Available, not actively used | 9 Chief of Staff automation workflows |
| **Motus** | `skills/motus/SKILL.md` + `tools/motus_agent.py` | 🔶 Available, not actively used | Agent framework, ReAct, task graphs |
| **DeekeScript** | `skills/deeke-script/SKILL.md` | 🔶 Available, not actively used | Android automation for content farms |
| **Oransim** | `skills/oransim/SKILL.md` | 🔶 Available, not actively used | Causal marketing simulation |
| **Dall-e / Image Gen** | Built-in `image_generate` tool | ✅ Active | Already accessible — no skill needed |
| **Video Gen** | Built-in `video_generate` tool | ✅ Active | Already accessible — no skill needed |

---

## Tier 3: Nice to Have (Specialized — Useful but not urgent)

| Skill/Tool | Location | Status | Action |
|------------|----------|--------|--------|
| **TradingView Quantitative** | `skills/tradingview-quantitative/SKILL.md` | 🔷 Low priority | Trading analysis — future use |
| **MT5 Strategy Tester** | `skills/mt5-strategy-tester/SKILL.md` | 🔷 Low priority | MT5 backtesting — future use |
| **Pine Script Developer** | `skills/pine-developer/SKILL.md` | 🔷 Low priority | TradingView indicators — future use |
| **Pine Script Debugger** | `skills/pine-debugger/SKILL.md` | 🔷 Low priority | Pine debugging — future use |
| **Pine Script Manager** | `skills/pine-manager/SKILL.md` | 🔷 Low priority | Pine project orchestration |
| **Pine Script Publisher** | `skills/pine-publisher/SKILL.md` | 🔷 Low priority | Pine publication — future use |
| **Pine Script Visualizer** | `skills/pine-visualizer/SKILL.md` | 🔷 Low priority | Trading idea decomposition |
| **Three.js Fundamentals** | `skills/threejs-fundamentals/SKILL.md` | 🔷 Low priority | 3D visualization — future use |
| **Three.js Animation** | `skills/threejs-animation/SKILL.md` | 🔷 Low priority | 3D animation — future use |
| **Three.js Geometry** | `skills/threejs-geometry/SKILL.md` | 🔷 Low priority | 3D geometry — future use |
| **Three.js Interaction** | `skills/threejs-interaction/SKILL.md` | 🔷 Low priority | 3D interaction — future use |
| **Three.js Lighting** | `skills/threejs-lighting/SKILL.md` | 🔷 Low priority | 3D lighting — future use |
| **Three.js Loaders** | `skills/threejs-loaders/SKILL.md` | 🔷 Low priority | 3D asset loading — future use |
| **Three.js Materials** | `skills/threejs-materials/SKILL.md` | 🔷 Low priority | 3D materials — future use |
| **Three.js Postprocessing** | `skills/threejs-postprocessing/SKILL.md` | 🔷 Low priority | 3D effects — future use |
| **Three.js Shaders** | `skills/threejs-shaders/SKILL.md` | 🔷 Low priority | Custom GLSL — future use |
| **Three.js Textures** | `skills/threejs-textures/SKILL.md` | 🔷 Low priority | 3D textures — future use |
| **Violin (Video Translation)** | `skills/violin/SKILL.md` | 🔷 Low priority | Video dubbing/translation |
| **Sleek Design Mobile Apps** | `skills/sleek-design-mobile-apps/SKILL.md` | 🔷 Low priority | Mobile app design |
| **Next.js Upgrade** | `skills/next-upgrade/SKILL.md` | 🔷 Low priority | Next.js version migration |
| **Frontend Design Templates** | `skills/fastapi-templates/SKILL.md` | 🔷 Low priority | Already in Tier 1 — cross-ref |
| **Claude Hermes MCP** | `skills/claude-hermes-mcp/SKILL.md` | 🔷 Low priority | Claude↔Hermes bridge |
| **Identity Graph Operator** | `skills/agency-identity-graph-operator/SKILL.md` | 🔷 Low priority | Multi-agent identity resolution |
| **Agentic Identity & Trust** | `skills/agency-agentic-identity-trust/SKILL.md` | 🔷 Low priority | Agent auth/trust systems |
| **ZK Steward** | `skills/agency-zk-steward/SKILL.md` | 🔷 Low priority | Zettelkasten knowledge management |
| **Evidence Collector** | `skills/agency-testing-evidence-collector/SKILL.md` | 🔷 Low priority | Screenshot-obsessed QA |
| **Reality Checker** | `skills/agency-testing-reality-checker/SKILL.md` | 🔷 Low priority | Evidence-based certification |
| **Tool Evaluator** | `skills/agency-testing-tool-evaluator/SKILL.md` | 🔷 Low priority | Tool assessment & recommendation |
| **Workflow Optimizer** | `skills/agency-testing-workflow-optimizer/SKILL.md` | 🔷 Low priority | Process improvement |
| **Accessibility Auditor** | `skills/agency-testing-accessibility-auditor/SKILL.md` | 🔷 Low priority | WCAG auditing |
| **Inclusive Visuals Specialist** | `skills/agency-design-inclusive-visuals-specialist/SKILL.md` | 🔷 Low priority | Culturally accurate imagery |
| **UI Designer** | `skills/agency-design-ui-designer/SKILL.md` | 🔷 Low priority | Visual design systems |
| **UX Architect** | `skills/agency-design-ux-architect/SKILL.md` | 🔷 Low priority | CSS systems, UX foundations |
| **UX Researcher** | `skills/agency-design-ux-researcher/SKILL.md` | 🔷 Low priority | User research, usability testing |
| **Visual Storyteller** | `skills/agency-design-visual-storyteller/SKILL.md` | 🔷 Low priority | Visual narratives |
| **Whimsy Injector** | `skills/agency-design-whimsy-injector/SKILL.md` | 🔷 Low priority | Brand delight/playfulness |
| **Image Prompt Engineer** | `skills/agency-design-image-prompt-engineer/SKILL.md` | 🔷 Low priority | AI photography prompts |
| **Brand Guardian** | `skills/agency-design-brand-guardian/SKILL.md` | 🔷 Low priority | Brand identity strategy |
| **Language Translator** | `skills/agency-language-translator/SKILL.md` | 🔷 Low priority | Spanish↔English translation |
| **Cultural Intelligence Strategist** | `skills/agency-specialized-cultural-intelligence-strategist/SKILL.md` | 🔷 Low priority | Cross-cultural software design |
| **Developer Advocate** | `skills/agency-specialized-developer-advocate/SKILL.md` | 🔷 Low priority | Developer community building |
| **French Consulting Market** | `skills/agency-specialized-french-consulting-market/SKILL.md` | 🔷 Low priority | French freelance ecosystem |
| **Korean Business Navigator** | `skills/agency-specialized-korean-business-navigator/SKILL.md` | 🔷 Low priority | Korean business culture |
| **Study Abroad Advisor** | `skills/agency-study-abroad-advisor/SKILL.md` | 🔷 Low priority | Study abroad planning |

---

## Tier 4: Archive (Not Relevant to OWL's Role)

| Skill/Tool | Location | Reason |
|------------|----------|--------|
| **Accounts Payable Agent** | `skills/agency-accounts-payable-agent/` | Finance ops — not OWL's role |
| **Compliance Auditor** | `skills/agency-compliance-auditor/` | SOC 2 / HIPAA compliance — not relevant |
| **Blockchain Security Auditor** | `skills/agency-blockchain-security-auditor/` | Smart contract auditing — not relevant |
| **Solidity Smart Contract Engineer** | `skills/agency-engineering-solidity-smart-contract-engineer/` | EVM development — not relevant |
| **Corporate Training Designer** | `skills/agency-corporate-training-designer/` | Enterprise training — not relevant |
| **Customer Service** | `skills/agency-customer-service/` | Customer support — not relevant |
| **Healthcare Customer Service** | `skills/agency-healthcare-customer-service/` | Healthcare support — not relevant |
| **Healthcare Marketing Compliance** | `skills/agency-healthcare-marketing-compliance/` | Healthcare marketing — not relevant |
| **Hospitality Guest Services** | `skills/agency-hospitality-guest-services/` | Hotel/restaurant — not relevant |
| **HR Onboarding** | `skills/agency-hr-onboarding/` | HR processes — not relevant |
| **Legal Billing & Time Tracking** | `skills/agency-legal-billing-time-tracking/` | Legal billing — not relevant |
| **Legal Client Intake** | `skills/agency-legal-client-intake/` | Legal intake — not relevant |
| **Legal Document Review** | `skills/agency-legal-document-review/` | Legal review — not relevant |
| **Loan Officer Assistant** | `skills/agency-loan-officer-assistant/` | Mortgage lending — not relevant |
| **Real Estate Buyer & Seller** | `skills/agency-real-estate-buyer-seller/` | Real estate — not relevant |
| **Recruitment Specialist** | `skills/agency-recruitment-specialist/` | Hiring — not relevant |
| **Sales Outreach** | `skills/agency-sales-outreach/` | B2B sales — not relevant |
| **Sales Data Extraction** | `skills/agency-sales-data-extraction-agent/` | Sales metrics — not relevant |
| **Report Distribution** | `skills/agency-report-distribution-agent/` | Sales reports — not relevant |
| **Retail Customer Returns** | `skills/agency-retail-customer-returns/` | Retail ops — not relevant |
| **Supply Chain Strategist** | `skills/agency-supply-chain-strategist/` | Procurement — not relevant |
| **Government Digital Presales** | `skills/agency-government-digital-presales-consultant/` | Gov IT sales — not relevant |
| **Automation Governance Architect** | `skills/agency-automation-governance-architect/` | n8n governance — not relevant |
| **Data Consolidation Agent** | `skills/agency-data-consolidation-agent/` | Sales dashboards — not relevant |
| **Email Intelligence Engineer** | `skills/agency-engineering-email-intelligence-engineer/` | Email parsing — not relevant |
| **Embedded Firmware Engineer** | `skills/agency-engineering-embedded-firmware-engineer/` | Hardware firmware — not relevant |
| **Feishu Integration Developer** | `skills/agency-engineering-feishu-integration-developer/` | Feishu/Lark — not relevant |
| **Filament Optimization** | `skills/agency-engineering-filament-optimization-specialist/` | PHP admin — not relevant |
| **WeChat Mini Program Developer** | `skills/agency-engineering-wechat-mini-program-developer/` | WeChat dev — not relevant |
| **Mobile App Builder** | `skills/agency-engineering-mobile-app-builder/` | Mobile dev — not relevant |
| **Frontend Developer** | `skills/agency-engineering-frontend-developer/` | Frontend dev — not relevant |
| **Senior Developer** | `skills/agency-engineering-senior-developer/` | Laravel/Three.js — not relevant |
| **CMS Developer** | `skills/agency-engineering-cms-developer/` | Drupal/WordPress — not relevant |
| **Threat Detection Engineer** | `skills/agency-engineering-threat-detection-engineer/` | SIEM/security ops — not relevant |
| **Voice AI Integration Engineer** | `skills/agency-engineering-voice-ai-integration-engineer/` | Speech pipelines — not relevant |
| **Codebase Onboarding Engineer** | `skills/agency-engineering-codebase-onboarding-engineer/` | Dev onboarding — not relevant |
| **Experiment Tracker** | `skills/agency-project-management-experiment-tracker/` | A/B testing PM — not relevant |
| **Jira Workflow Steward** | `skills/agency-project-management-jira-workflow-steward/` | Jira workflows — not relevant |
| **Project Shepherd** | `skills/agency-project-management-project-shepherd/` | Project management — not relevant |
| **Studio Operations** | `skills/agency-project-management-studio-operations/` | Studio ops — not relevant |
| **Studio Producer** | `skills/agency-project-management-studio-producer/` | Creative production — not relevant |
| **Senior Project Manager** | `skills/agency-project-manager-senior/` | PM — not relevant |
| **Chief of Staff** | `skills/agency-specialized-chief-of-staff/` | Executive coordination — not relevant |
| **Civil Engineer** | `skills/agency-specialized-civil-engineer/` | Structural engineering — not relevant |
| **Salesforce Architect** | `skills/agency-specialized-salesforce-architect/` | Salesforce — not relevant |
| **Agents Orchestrator** | `skills/agency-agents-orchestrator/` | Pipeline management — CC's role |
| **Agency Agents (collection)** | `skills/agency-agents/` | Meta-collection — already decomposed |

---

## Gaps (Need to Create)

| Gap | Priority | Description |
|-----|----------|-------------|
| **Docker/Container Management** | 🔴 High | No skill for Docker, docker-compose, or container orchestration. Needed for OCE deployment. |
| **CI/CD Pipeline Management** | 🔴 High | No skill for GitHub Actions, GitLab CI, or similar. Needed for automated testing/deployment of OCE. |
| **Database Operations** | 🔴 High | Database Optimizer skill exists but is generic. Need a practical skill for running migrations, backups, and queries against the actual DB. |
| **OCE-Specific Testing** | 🔴 High | API Tester exists but no OCE-specific test patterns. Need skill for testing event fabric, adapter contracts, and pipeline endpoints. |
| **DSPy Integration** | 🟡 Medium | DSPy pipelines exist in code but no skill for building new DSPy modules, optimizing signatures, or managing DSPy programs. |
| **Subagent Orchestration** | 🟡 Medium | Subagent manager exists but no skill for complex multi-agent workflows, dependency chains, or parallel execution patterns. |
| **Monitoring & Alerting** | 🟡 Medium | System health check exists but no skill for setting up Prometheus/Grafana, log aggregation, or alert routing. |
| **API Documentation** | 🟡 Medium | Technical Writer exists but no skill specifically for OpenAPI/Swagger doc generation or API spec management. |
| **Performance Profiling** | 🟡 Medium | Performance Benchmarker exists but no skill for Python profiling (cProfile, py-spy, memory profiling). |
| **Security Scanning** | 🟡 Low | Security Engineer exists but no skill for automated dependency scanning (safety, snyk, trivy). |
| **Data Visualization** | 🟡 Low | Pandas Pro exists but no skill for creating charts, dashboards, or reports from data. |
| **Release Management** | 🟡 Low | No skill for versioning, changelog generation, or release automation. |

---

## Recommended Implementation Order

### Immediate (This Week)
1. **Docker/Container Management** skill — OCE needs containerized deployment
2. **CI/CD Pipeline Management** skill — Automate OCE test runs on commit
3. **OCE-Specific Testing** skill — Standardize how we test event fabric, adapters, pipelines
4. **Database Operations** skill — Practical DB management for OCE persistence layer

### Short-Term (Next 2 Weeks)
5. **DSPy Integration** skill — Formalize DSPy pipeline development patterns
6. **Subagent Orchestration** skill — Complex multi-agent workflow patterns
7. **Monitoring & Alerting** skill — Production observability for OCE
8. **API Documentation** skill — Auto-generate OpenAPI specs for OCE endpoints

### Medium-Term (Next Month)
9. **Performance Profiling** skill — Python profiling for optimization work
10. **Data Visualization** skill — Charts and dashboards for research output
11. **Security Scanning** skill — Automated dependency vulnerability scanning
12. **Release Management** skill — Versioning and changelog automation

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Total skills reviewed** | 163 |
| **Tier 1 (Must Have)** | 30 |
| **Tier 2 (Should Have)** | 47 |
| **Tier 3 (Nice to Have)** | 46 |
| **Tier 4 (Archive)** | 40 |
| **Gaps identified** | 12 |
| **Built-in tools (no skill needed)** | 7 (read, write, edit, exec, process, web_search, web_fetch, image, image_generate, video_generate, memory_search, memory_get, sessions_yield) |

---

## Key Insight

OWL has **strong coverage** of core operations (Tier 1) and a **deep bench** of specialized skills (Tier 2-3). The main gaps are in **infrastructure operations** (Docker, CI/CD, monitoring) and **OCE-specific patterns** (testing, DSPy, database ops). The 40 Tier-4 skills are almost entirely agency-agent personalities from msitarzewski/agency-agents that have no relevance to OWL's research/pipeline role. These should be archived to reduce cognitive load during skill selection.

**The path forward:** Fill the 4 high-priority gaps first, then systematically work through medium-priority items. Each new skill should follow the Agent Harness SOP (7-phase pipeline) and be measured with the Skill Creator eval framework.
