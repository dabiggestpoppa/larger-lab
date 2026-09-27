# OCE Opportunity Exchange — Build Plan v0.1

**Date:** 2026-09-12  
**Parent:** `OCE_ARCHITECTURE_AMENDMENT_A011_EXTERNAL_ECONOMIC_ENVIRONMENT_AND_OPPORTUNITY_EXCHANGE_v1.0.md`  
**Peer boundary:** QCAE Amendment A-001  
**Status:** PLANNING ONLY — NO TRANSACTION AUTHORITY  
**Build authorization:** NONE

---

## 1. Mission

Build the Opportunity Exchange as OCE's governed interface to the external economic environment.

The Exchange must be able to discover work, services, bounties, capability providers, direct-client demand, and new marketplaces without making any one venue part of OCE's core architecture.

The initial objective is **observation and learning before execution**.

Canonical doctrine:

```text
OBSERVE BROADLY
QUALIFY EMPIRICALLY
EXECUTE SELECTIVELY
LEARN FROM RESULTS
REVISIT DORMANT SOURCES
```

No source is permanently excluded merely because early desk research suggests low margin, high competition, weak liquidity, or poor fit. Those are hypotheses to test.

A source may be denied transaction authority while remaining valuable as:

- a demand sensor;
- a pricing sensor;
- a capability-gap sensor;
- a service-packaging sensor;
- a reputation/market-structure sensor;
- a QCAE procurement surface;
- a future opportunity source if conditions change.

---

## 2. Source-neutral architecture

```text
Upwork ───────────────┐
Fiverr ───────────────┤
Clustly ──────────────┤
AgentHansa ───────────┤
Toku ─────────────────┤
NEAR Agent Market ────┤
Virtuals ACP ─────────┤
Olas Mech ────────────┤
Daydreams ────────────┤
AgentHire ────────────┤
BountyBook ───────────┤
Claw Earn ────────────┤
AgentPact ────────────┤
gigs.sh / directories ┤
Future venues ────────┘
          ↓
 OpportunitySourceAdapter
          ↓
    Opportunity Exchange
          ↓
 raw evidence + normalization
          ↓
 dedupe + legal/ToS gates
          ↓
 economics + capability fit
          ↓
 portfolio classification
          ↓
 observe / shortlist / pilot / act / no-action
```

The adapter contract is durable; individual venues are replaceable.

---

## 3. Non-exclusion / empirical qualification doctrine

### 3.1 Source states

Every venue has a reversible lifecycle:

```text
DISCOVERED
→ RESEARCHED
→ VERIFIED_READ_ONLY
→ SHADOW_OBSERVE
→ PILOT_ELIGIBLE
→ PILOT_ACTIVE
→ ACTIVE
```

A source may also enter:

```text
DEPRIORITIZED
DORMANT
QUARANTINED
DRIFT_DETECTED
```

These are not deletion states.

Every non-active state should preserve:

- why the state changed;
- evidence supporting the change;
- last verified date;
- re-entry conditions;
- next review date or event trigger.

Permanent removal is reserved for an operator decision, platform closure, legal prohibition, or a source that can no longer be meaningfully identified.

### 3.2 Opportunity rejection is not source rejection

A venue with bad current jobs may still be useful.

```text
bad job ≠ bad source
empty market ≠ dead market
high competition ≠ zero information value
manual checkpoint ≠ unusable
low immediate margin ≠ zero strategic value
```

### 3.3 Observation and transaction authority are separate

A source can be fully useful for read-only market intelligence while autonomous bidding/contracting remains prohibited.

---

## 4. Source lanes

### Lane A — official machine-readable markets

Examples:

- Upwork official MCP;
- AgentHansa API/MCP/SSE;
- Clustly MCP;
- Virtuals ACP;
- Olas Mech;
- other verified agent-native APIs.

Preferred path: typed adapter, authenticated read-only queries, versioned contract tests.

### Lane B — human-first / operator-mediated markets

Examples:

- Fiverr where current terms restrict unauthorized bots/scrapers;
- any platform whose current rules require human review or UI confirmation.

Preferred path: operator-owned account, permitted notification/search surfaces, human confirmation, service-publication workflows, and read-only demand research that does not violate platform rules.

### Lane C — capability procurement

Markets may be useful even when OCE does not sell work there.

Examples:

- Upwork specialists;
- Fiverr specialists;
- Olas Mechs;
- Virtuals ACP providers;
- AgentHire providers.

QCAE can compare:

```text
USE internal
BORROW internal
RENT external
BUY external
ACQUIRE component
BUILD
RESEARCH
DECLINE
```

### Lane D — meta-discovery

Directories such as gigs.sh discover venues and market changes. They never outrank current first-party contracts.

---

## 5. Phase plan

## OX-P0 — Canon, schemas, and source registry

**Goal:** establish contracts before code.

Deliverables:

- active `OpportunitySource` schema;
- active `NormalizedOpportunity` schema;
- `EconomicExperienceRecord` schema;
- source registry + supplements;
- source lifecycle / re-entry contract;
- source authority matrix;
- raw-payload retention rules.

Exit gate:

- at least Upwork, Fiverr, Clustly, AgentHansa, Toku, NEAR, Virtuals ACP, Olas Mech and one meta-directory represented;
- no source record implies transaction permission.

---

## OX-P1 — Read-only adapter SDK + scheduler

**Goal:** one interface for heterogeneous venues.

Adapter primitives:

```text
health_check()
get_contract_version()
list_opportunities(cursor, filters)
get_opportunity(id)
list_services(...)
get_market_metadata()
normalize(raw)
```

Optional primitives when officially supported:

```text
subscribe_events()
get_notifications()
```

Not included in P1:

- apply;
- bid;
- claim;
- message;
- spend;
- stake;
- contract acceptance;
- delivery;
- settlement.

Exit gate: isolated adapters can fail independently without poisoning the Exchange.

---

## OX-P2 — Raw evidence store + normalization spine

**Goal:** preserve source truth while producing one common opportunity language.

Every observation stores:

```text
source_id
retrieved_at
source_contract_version
raw_hash
raw_payload_ref
normalized_record
normalizer_version
```

Requirements:

- immutable raw receipt;
- deterministic normalization where possible;
- explicit unknown values;
- deduplication across reposts and cross-posts;
- freshness/expiry handling.

Exit gate: same source payload can be reproduced into the same normalized record under a pinned normalizer version.

---

## OX-P3 — Demand Intelligence / no-action learning

**Goal:** learn the economy before spending money or reputation.

Compute by source/category:

- opportunity arrival rate;
- payout/rate distribution;
- skill/category frequency;
- proposal/bid competition where visible;
- deadline distribution;
- recurring buyer problems;
- repeated software/tool requirements;
- apparent service-package gaps;
- geographic/account constraints;
- source-specific fee drag;
- opportunity half-life.

Outputs:

```text
DemandCluster
PriceBand
CapabilityDemandSignal
ServicePackagingCandidate
SourceLiquidityReport
```

This phase is useful even if no jobs are executed.

---

## OX-P4 — Opportunity evaluator + portfolio allocator

**Goal:** separate economic viability from strategic learning.

Pipeline:

```text
hard gates
→ expected economics
→ capability/knowledge gap
→ challenge closure cost
→ institutional value vector
→ portfolio class
```

Portfolio classes:

- `EXPLOIT` — positive expected contribution with known capability;
- `EXPLORE` — bounded lower-margin experiment with explicit learning target;
- `STRATEGIC_BUILD` — capability acquisition justified by reusable institutional value;
- `OBSERVE_ONLY` — information valuable, execution not justified;
- `NO_ACTION` — neither execution nor near-term follow-up justified.

`NO_ACTION` is a successful outcome.

---

## OX-P5 — Operator review queue / shadow decisions

**Goal:** measure decision quality before any autonomous external action.

For each candidate, OCE should emit a compact decision packet:

```text
what the job is
why it fits / does not fit
expected net economics
competition / acceptance uncertainty
required capabilities
Research Mesh need
QCAE need
human burden
risk
recommended action
maximum authorized resource envelope
```

Run shadow mode:

- OCE recommends;
- operator accepts/rejects recommendation;
- system records counterfactuals and outcome when observable.

Exit gate: evaluator demonstrates useful precision and bounded false positives.

---

## OX-P6 — Bounded marketplace pilots

**Goal:** obtain real Economic Experience with minimal blast radius.

Pilot order should be determined at build time by current contracts, not frozen permanently now.

A pilot source requires:

- current first-party contract verified;
- permitted automation path;
- explicit fee model;
- explicit identity/KYC path;
- explicit payment/escrow path;
- dispute/revision semantics;
- budget cap;
- human confirmation where required;
- rollback / account-protection plan.

Initial pilot classes:

1. direct assigned work before open competitions when practical;
2. low-capital/no-stake work before collateral-bearing markets;
3. well-specified acceptance criteria before ambiguous creative work;
4. small but economically meaningful jobs before reputation-critical jobs.

---

## OX-P7 — Service publication / inbound work

**Goal:** stop relying only on job chasing.

Candidate institutional services:

- research-as-a-service;
- competitive/market intelligence;
- technical literature and evidence synthesis;
- AI workflow audits;
- business-process automation;
- API/MCP integrations;
- CRM/email/data pipeline automation;
- agent and RAG system implementation;
- automation repair / reliability audits;
- structured data/research pipelines;
- internal knowledge-system setup.

Preferred positioning: **systems engineering and operational automation**, not generic AI marketing.

Fiverr-style package markets and agent-native offering markets should be treated as distinct publication surfaces using the same underlying capability contracts.

---

## OX-P8 — Economic Experience → institutional learning

**Goal:** turn real work into governed evidence.

```text
job / sale / rejection / dispute / strategic decline
→ EconomicExperienceRecord
→ rights/privacy filter
→ generalized lesson
→ Research Mesh / QCAE / Opportunity Exchange / Institution routing
→ reproduce where material
→ A009/A010 governance when structural change is implicated
```

No customer artifact becomes training memory by default.

---

## OX-P9 — Adaptive source allocation

**Goal:** spend observation resources where information value is highest without deleting low-yield sources.

Track:

```text
qualified_opportunities / observation_cost
revenue_opportunities / observation_cost
demand_information_gain / observation_cost
source_contract_stability
false_positive_rate
adapter_maintenance_cost
```

Use these to change cadence and priority, not to erase sources.

A dormant source remains eligible for event-based or scheduled re-check.

---

## OX-P10 — Controlled autonomy

Only after evidence exists may OCE receive bounded action authority.

Authority ladder:

```text
L0 observe
L1 shortlist
L2 draft proposal / response
L3 operator-confirmed submit
L4 bounded autonomous submit under explicit policy
L5 bounded contract/delivery actions
L6 settlement / capital actions under separate authority
```

No platform adapter inherits a higher level because its API technically permits it.

---

## 6. Upwork-specific initial path

Current first-party Upwork material (2026-09-12 verification) supports an official MCP server using OAuth 2.1. It can search jobs, view matched jobs, draft/submit proposals, handle invitations/messages, inspect contracts, and submit milestone work. Write actions use draft/confirm semantics and binding actions finish on Upwork.

Important economics:

- Connects are used to submit most proposals;
- Connects currently cost $0.15 each when purchased;
- freelancer service fee currently ranges from 0% to 15% per contract;
- competition can be high and must be priced;
- unauthorized scraping/botting remains prohibited outside approved API/MCP use.

Initial OCE use:

```text
official MCP read-only search
→ normalized jobs
→ demand intelligence
→ operator-reviewed proposal drafts
→ bounded proposal experiment later
```

Upwork should also be available to QCAE as a human specialist procurement surface.

---

## 7. Fiverr-specific initial path

Fiverr is structurally different: it is primarily a packaged-service/inbound marketplace.

Current observed state includes a large AI-agent/automation category with services ranging from low-cost entry packages to four-figure implementations. Fiverr currently pays freelancers 80% of completed order value; ordinary freelancer earnings are generally subject to a clearing period. Current terms prohibit unauthorized bots, crawlers, scraping and other automation against the site.

Therefore the initial OCE path is:

```text
manual/permitted market research
→ package/pricing intelligence
→ design institutional Gigs / Custom Offer templates
→ operator-owned publication
→ inbound request triage
→ OCE delivery workflow behind the account
```

Fiverr is **not rejected** because full autonomous browsing is restricted. It simply occupies a different authority lane.

Fiverr can also be a QCAE procurement surface for buying bounded specialist work.

---

## 8. First research categories

The Exchange should initially classify demand around capabilities already close to OCE/QCAE/Research Mesh:

```text
AI_AGENT_ENGINEERING
WORKFLOW_AUTOMATION
API_INTEGRATION
MCP_INTEGRATION
N8N_MAKE_ZAPIER_SYSTEMS
CRM_AUTOMATION
EMAIL_AND_INBOX_AUTOMATION
DATA_PIPELINES
DATABASE_AND_STORAGE_AUTOMATION
RAG_AND_KNOWLEDGE_SYSTEMS
RESEARCH_AS_A_SERVICE
COMPETITIVE_INTELLIGENCE
TECHNICAL_RESEARCH
REPOSITORY_ANALYSIS
QA_AND_AUTOMATION_REPAIR
AGENT_SETUP_AND_ORCHESTRATION
```

Adjacent categories remain observable even when not initially targeted.

---

## 9. Milestone commit discipline

Do not implement the Exchange as one monolithic marketplace feature.

Suggested commit sequence:

```text
OX-P0 contracts
OX-P1 adapter SDK
OX-P1 source scheduler
OX-P2 evidence store
OX-P2 normalizer
OX-P3 demand analytics
OX-P4 evaluator
OX-P4 allocator
OX-P5 operator review packets
OX-P6 source-specific pilots one at a time
OX-P7 service publication adapters one at a time
OX-P8 Economic Experience integration
OX-P9 adaptive cadence
OX-P10 bounded autonomy gates
```

Each source adapter receives its own qualification record, tests, and history.

---

## 10. Initial success definition

The first successful Opportunity Exchange does **not** need to make money autonomously.

It succeeds when it can:

1. observe heterogeneous markets lawfully;
2. preserve raw evidence;
3. normalize opportunities;
4. detect demand/capability patterns;
5. estimate real total cost;
6. route gaps to Research Mesh/QCAE;
7. explain why it recommends action or no-action;
8. preserve dormant sources for future re-entry;
9. operate without architecture drift;
10. produce evidence good enough to justify the first bounded real-world pilot.
