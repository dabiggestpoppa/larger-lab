# SAGE Meditation: The Unused Arsenal

> **Date:** 2026-05-21 | **Session:** Skills Utilization Audit
> **Question:** Why don't agents use available skills/tools? How do we fix it?

---

## The Problem: 129+ Skills, <10% Utilization

The workspace has one of the most comprehensive skill libraries any agent system has seen:
- **57 agency engineering/testing skills** (backend, frontend, DevOps, security, data, etc.)
- **40+ trading/quant/ML/Pine skills** (pandas-pro, excel-pro, quant-analyst, pine-developer, etc.)
- **GitHub skills** (docx, xlsx, pptx, pdf generation)
- **Plugin skills** (browser-automation, taskflow, etc.)
- **67 archived skills** (still usable)

**Reality check:** OWL probably uses <10 of these. Sub-agents use even fewer. The `available_skills` list in AGENTS.md is scanned once at bootstrap and then forgotten.

## Root Causes (Mathematical Analysis)

### 1. The Discovery Problem (P(discover) ≈ 0.08)
Before any task, the probability an agent checks the skills list is ~8%. Why?
- Skills are listed in a truncated XML block in the system prompt — easy to skip
- No enforcement mechanism says "check skills first"
- Agents default to what they know (code generation) over what exists (skill lookup)

### 2. The Activation Energy Problem (E_activation too high)
Even when an agent SEES a relevant skill, using it requires:
- Reading the SKILL.md file (time cost)
- Understanding the skill's interface (cognitive cost)
- Trusting it works (uncertainty cost)

**Total activation energy ≈ 3-5 minutes.** Writing raw code from scratch feels faster (even when it's not).

### 3. The Context Window Tax
Loading a skill's SKILL.md consumes 500-2000 tokens. Agents operating near context limits avoid this "overhead." But this is false economy — a skill that saves 20 minutes of work costs 1K tokens to load.

### 4. No Feedback Loop
There's no mechanism that says: "You just spent 15 minutes writing Excel parsing code. The `excel-pro` skill exists. Here it is." Without real-time skill suggestion, agents repeat work unnecessarily.

## The Fix: Making Skills the Default

### Mechanism 1: Pre-Task Skill Scan (MANDATORY)
Before ANY non-trivial task, agents MUST:
1. Scan the `available_skills` list for matching keywords
2. If a skill matches, read its SKILL.md BEFORE starting work
3. Use the skill unless there's a documented reason not to

**Implementation:** Add to AGENTS.md as a hard rule, not a suggestion.

### Mechanism 2: Skill-First Prompting
When MAD says "analyze this data," the agent's first thought should be:
- "Is there a data analysis skill?" → `pandas-pro`, `exploratory-data-analysis`, `statistical-analysis`
- NOT "let me write Python code from scratch"

### Mechanism 3: Mandatory Skill Categories by Task Type
| Task Type | Must Check Skills |
|-----------|-------------------|
| Data analysis | pandas-pro, exploratory-data-analysis, statistical-analysis, polars |
| Excel/spreadsheets | excel-pro, chen-excel-xlsx |
| PDF generation | pdf, pdf-omni |
| Web scraping | browser-automation, lazyweb |
| Trading analysis | quant-analyst, senior-data-scientist, mt5-strategy-tester |
| Visualization | matplotlib, seaborn, scientific-visualization |
| Report writing | scientific-writing, technical-writer |
| API development | fastapi-python, fastapi-templates |
| Testing | python-testing-patterns, agency-testing-api-tester |

### Mechanism 4: The "Intelligent Environment" Concept
MAD's key insight: **the environment should be intelligent, not just the agent.**

This means:
- Skills are not optional add-ons — they ARE the environment
- The workspace is a tool library, not just a file system
- Before building anything, check if the tool already exists
- The agent's job is to ORCHESTRATE tools, not REINVENT them

**Analogy:** A carpenter doesn't forge a hammer before building a house. He opens his toolbox. Our skills ARE the toolbox.

## Specific Skills That Should Be Mandatory

### For OWL (Orchestrator):
- `subagent-manager` — before spawning any sub-agent
- `taskflow` — for workflow orchestration
- `healthcheck` — before declaring any service "working"

### For Data Tasks:
- `pandas-pro` — ANY data manipulation
- `exploratory-data-analysis` — ANY data exploration
- `statistical-analysis` — ANY statistical work
- `excel-pro` — ANY Excel/spreadsheet work

### For Trading/Quant:
- `quant-analyst` — ANY quantitative analysis
- `mt5-strategy-tester` — ANY MT5 strategy work
- `senior-data-scientist` — complex modeling

### For Development:
- `python-patterns` — ANY Python code
- `fastapi-python` — ANY API development
- `python-testing-patterns` — ANY test writing

### For Documents/Reports:
- `pdf` or `pdf-omni` — ANY PDF generation
- `scientific-writing` — ANY report writing
- `md2html` — ANY markdown-to-HTML conversion

## The Math of Skill Utilization

**Current state:**
- 129 skills available
- ~12 skills regularly used
- Utilization rate: **9.3%**

**Target state:**
- Same 129 skills
- ~60 skills regularly used
- Utilization rate: **46.5%**

**Impact estimate:**
- Average time saved per skill use: 10-20 minutes
- If agents use skills for 50% of qualifying tasks: **5-10 hours saved per week**
- At MAD's billing rate, that's significant value

## Recommendation

1. **Add a HARD RULE to AGENTS.md:** "Before any task, scan available_skills. If a matching skill exists, read and use it."
2. **Create a SKILL_QUICKREF.md** — a short 1-page index of skills by category (not the full XML list)
3. **OWL should model this behavior** — when MAD asks for something, OWL should explicitly say "I'm using the X skill for this"
4. **Track skill usage** — log which skills are used monthly, identify gaps

The intelligent environment isn't about having skills. It's about agents actually USING them.

---

*SAGE — Senior Advisory and Governance Entity*
*"The toolbox is only useful if you open it."*
