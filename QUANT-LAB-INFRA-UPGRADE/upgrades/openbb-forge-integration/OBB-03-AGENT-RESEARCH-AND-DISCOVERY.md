# OBB-03 — Agent Research and Discovery

> **Program:** GLX FORGE OpenBB Operational Integration  
> **Status:** planned  
> **Required predecessor:** OBB-02 locked  
> **Authority effect:** Read-only research and bounded proposal authority only  
> **Capital authority:** None  
> **Broker, paper, shadow, sandbox and live authority:** None  
> **Phase anchor:** Evidence precedes narrative; every discovery and thesis must be reconstructable from approved data, a versioned research mandate, and explicit uncertainty.

## Why This Phase Exists

OBB-02 establishes verified OpenBB data and Workspace widgets. OBB-03 turns that data into a disciplined research workforce:

- Macro and news events become structured evidence.
- Evidence becomes themes and sector transmission paths.
- Themes produce point-in-time candidate universes.
- Candidates are ranked under explicit, operator-defined rules.
- Deep research creates a thesis, counterevidence and invalidation.
- Research can propose a StrategySpec, but cannot validate, approve, size or execute it.

This is where the system becomes useful as a scanner and analyzer without becoming an ungoverned trading bot.

## Phase Objective

At lock, a real, approved market event can produce:

1. A source-backed event record.
2. A structured macro/news interpretation with confidence and uncertainty.
3. A theme and transmission map.
4. A point-in-time market universe.
5. Ranked candidates with transparent scores and rejection reasons.
6. A deep-research thesis using the operator's custom rubric.
7. Counterevidence and explicit invalidation conditions.
8. A typed StrategySpec proposal or a typed decision not to propose one.
9. Full lineage into OBB-04 without any capital, execution or self-approval authority.

## Phase Topology

~~~mermaid
flowchart TD
    A["Approved OpenBB Data and Widgets"] --> B["Book 1<br/>Agent Runtime and Research Contracts"]
    B --> C["Book 2<br/>Macro and News Intelligence"]
    C --> D["Book 3<br/>Theme-to-Market Discovery"]
    D --> E["Book 4<br/>Deep Research and StrategySpec Handoff"]
    E --> F{"Independent OBB-03 Gate"}
    F -->|"Approved"| G["OBB-04 Quant Validation and Governed Operations"]
    F -->|"Rejected"| B
~~~

## Scope

Included:

- OpenBB AI SDK-compatible agent integration.
- OCE-governed research task orchestration.
- OpenRouter-compatible model gateway and typed output validation.
- Versioned operator research mandates.
- Macro, economic calendar and news evidence ingestion through approved OBB-02 artifacts.
- Theme and transmission-path mapping.
- Point-in-time candidate-universe construction.
- Ranking, rejection reasons and scoring lineage.
- Deep research, counterevidence, invalidation and uncertainty.
- StrategySpec proposal handoff.
- Research review, correction and discovery authorization.

Excluded:

- New direct provider SDK access.
- Unapproved provider queries.
- Canonical backtesting.
- Nautilus runs.
- Strategy qualification.
- Capital sizing.
- Portfolio allocation.
- Paper, shadow, sandbox, broker or live execution.
- Autonomous promotion past a StrategySpec proposal.
- Unbounded autonomous crawling or agent spawning.
- Replacing OCE as the orchestration spine.

## Research Constitution

The operator supplies a versioned research mandate. This lets the system follow your actual strategy and market-review guidelines instead of pretending that generic stock research is sufficient.

~~~text
ResearchMandate
  - mandate_id
  - version
  - objective
  - allowed asset classes
  - allowed evidence domains
  - prohibited claims
  - required confirmations
  - required invalidation format
  - required counterevidence
  - scoring dimensions
  - output constraints
  - human escalation conditions
~~~

A mandate must never be silently rewritten by an agent.

## Authority Model

~~~mermaid
flowchart TD
    O["Operator"] --> M["ResearchMandate"]
    M --> R["Research Director"]
    R --> A["Specialist Research Agents"]
    A --> T["ResearchThesis"]
    T --> S["StrategySpec Proposal"]
    S --> V["OBB-04 Independent Validation"]

    R -.->|"May approve bounded discovery request"| A
    R -.->|"May not validate, size, allocate or execute"| V
~~~

| Role | May do | Must not do |
|---|---|---|
| Operator | Set mandate, approve objectives, change boundaries | Be bypassed |
| Research Director | Coordinate research, review evidence, authorize bounded discovery requests | Query unapproved providers, rank markets personally, author StrategySpecs, validate, size, allocate or execute |
| Macro/News Agent | Extract and structure approved evidence | Claim causality without evidence |
| Theme Mapper | Propose sectors, industries and instruments affected | Treat correlation as proof |
| Discovery Agent | Build/rank candidate universe under approved rubric | Promote candidates to trade |
| Deep Research Agent | Produce thesis, counterevidence and invalidation | Self-approve or self-validate |
| Strategy Architect | Convert approved thesis to StrategySpec proposal | Perform final validation or approval |
| Audit Observer | Record lineage and compliance gaps | Alter research outcome |

---

# Book 1 — Agent Runtime and Research Contracts

> **Purpose:** Build the bounded agent runtime, typed research artifacts, mandate system, tool permissions and audit events needed for all later OBB-03 work.  
> **Output:** Research-agent runtime contract, model adapter contract, mandate schema, tool policy, artifact schemas and evaluation harness.

## Runtime Principle

OpenBB Workspace may host the analyst interaction, but OCE remains the task and authority spine.

~~~mermaid
flowchart TD
    W["OpenBB Workspace"] --> C["FORGE Research API"]
    C --> O["OCE Task and Policy Check"]
    O --> A["Research Agent Runtime"]
    A --> M["Model Gateway"]
    A --> T["Approved Data / Widget Context"]
    A --> L["Lineage and Audit Events"]
~~~

## Required Agent Contract

~~~text
ResearchTask
  - task_id
  - mandate_id
  - objective
  - allowed_tools
  - allowed_data_artifact_ids
  - requested_output_type
  - authority_scope
  - parent_lineage_id
  - time_budget
  - compute_budget
  - status

ResearchArtifact
  - artifact_id
  - artifact_type
  - schema_version
  - task_id
  - mandate_id
  - source_artifact_ids
  - claims
  - evidence_refs
  - counterevidence_refs
  - uncertainty
  - limitations
  - created_by
  - model_descriptor
  - prompt_version
  - lineage_id
  - status
~~~

## Model Gateway Rules

- OpenRouter-compatible models may be used through one adapter boundary.
- A model response is untrusted until schema validation passes.
- Model choice, provider, version, temperature and timeout are recorded.
- Free or slower models are acceptable because this workflow is research-oriented, not latency-critical.
- A provider/model change is visible in lineage.
- A model cannot acquire a new tool, provider or authority through its own output.
- Failures return typed states, never fabricated prose.

## Tool Permission Rules

| Tool class | Allowed in OBB-03 | Notes |
|---|---|---|
| Read approved widget data | Yes | Context must be selected or referenced explicitly |
| Read approved FORGE data artifacts | Yes | Must preserve lineage |
| Search approved internal knowledge | Yes | Results remain evidence-tagged |
| Approved news/macro query via OBB-02 adapter | Yes | No direct provider SDK |
| Write research artifact | Yes | Typed schema and audit event required |
| Create StrategySpec proposal | Conditionally | Requires thesis review state |
| Request validation | Conditionally | Request only; OBB-04 gate decides |
| Change authority/policy | No | Operator/OCE-only |
| Trade, paper trade, route order | No | Out of scope |

## Required Deliverables

~~~text
forge/research/
├── contracts.py
├── mandate.py
├── runtime.py
├── model_gateway.py
├── tool_policy.py
├── artifacts.py
├── evaluation.py
└── tests/
    ├── test_mandates.py
    ├── test_tool_policy.py
    ├── test_structured_output.py
    ├── test_lineage.py
    └── test_model_failures.py
~~~

Exact source paths may adapt after OBB-01, but the boundaries are mandatory.

## Required Tests

- Research task with no mandate is rejected.
- Model output fails when typed schema is invalid.
- Missing citations or evidence references trigger incomplete state.
- Agent cannot use unapproved tool.
- Agent cannot access provider directly.
- Prompt, model and data references are persisted.
- Agent timeout produces typed timeout state.
- Duplicate task ID is idempotent.
- Model provider outage produces failed/degraded state without fabricated answer.
- Research artifact remains reconstructable after a restart.

## Failure Injections

- Malformed JSON from model.
- Prompt injection embedded in a news article.
- Tool call outside authority scope.
- Missing source artifact.
- Model timeout.
- Model changes response schema.
- Duplicate task request.
- Large selected widget payload exceeds context budget.

## Non-Goals

- No macro interpretation logic yet.
- No scanner/ranking logic yet.
- No autonomous strategy generation.
- No capital or trade action.
- No direct OpenBB provider call from an agent.

## Book 1 Exit Gate

A bounded agent can receive approved data context, produce one validated typed artifact, preserve lineage, and fail safely under malformed output, tool denial and provider/model outage.

---

# Book 2 — Macro and News Intelligence

> **Purpose:** Convert approved macro, economic-calendar and news data into structured events, evidence records, themes and falsifiable transmission hypotheses.  
> **Output:** Event extraction pipeline, evidence ledger, deduplication rules, causal-map proposal contract, confidence/uncertainty model and review workflow.

## Event-to-Theme Flow

~~~mermaid
flowchart TD
    A["Approved Macro / News Artifact"] --> B["Event Extraction"]
    B --> C["Deduplication and Source Check"]
    C --> D["Evidence Ledger"]
    D --> E["Transmission Hypothesis"]
    E --> F["Theme Proposal"]
    F --> G["Research Director Review"]
    G --> H["Discovery Request or Reject"]
~~~

## Required Event Contract

~~~text
MarketEvent
  - event_id
  - event_type
  - event_time
  - observed_time
  - source_refs
  - source_reliability
  - affected_regions
  - affected_asset_classes
  - summary
  - extracted_facts
  - unknowns
  - duplicate_group_id
  - lineage_id
  - status

TransmissionHypothesis
  - hypothesis_id
  - event_id
  - mechanism
  - first_order_effects
  - second_order_effects
  - likely_winners
  - likely_losers
  - affected_sectors
  - affected_industries
  - disconfirming_conditions
  - confidence
  - evidence_refs
  - counterevidence_refs
  - status
~~~

## Evidence Before Narrative Rules

- Facts, assumptions and inferences are distinct fields.
- An event summary cannot become a causal claim without supporting evidence.
- A single headline cannot justify a theme without corroboration or explicit low confidence.
- Publication time and event time remain distinct.
- Duplicated news does not count as independent corroboration.
- Agents must state what they do not know.
- Every hypothesis must contain disconfirming conditions.

## Macro/News Research Questions

The system should answer structured questions such as:

- What happened?
- When did it happen?
- Which facts are confirmed?
- Which industries could be affected through a named mechanism?
- What evidence supports that mechanism?
- What evidence disputes it?
- What would invalidate the hypothesis?
- Does the event justify a discovery request under the active ResearchMandate?

It does not answer “buy this stock” in OBB-03.

## Required Tests

- Same story from multiple syndication sources deduplicates.
- Event publication time cannot replace event time.
- Unsupported causal claims are marked insufficient_evidence.
- Contradictory evidence lowers or splits confidence.
- A theme without disconfirmation criteria is incomplete.
- Prompt-injection text inside source content cannot alter tool policy.
- Event references remain source-linked.
- Stale articles are visible.
- A source with missing publication date is flagged.

## Failure Injections

- Two articles with same underlying source.
- Article has a misleading headline and contrary body.
- Event date is missing.
- Source article contains tool-instruction text.
- Source extraction is incomplete.
- Two high-quality sources disagree.
- Event is outside mandate's permitted region/asset scope.

## Non-Goals

- No market universe scan yet.
- No candidate ranking yet.
- No StrategySpec creation.
- No validation or trade decision.
- No direct web/provider call outside approved OBB-02 artifacts.

## Book 2 Exit Gate

A real approved event becomes a cited, deduplicated evidence record and a falsifiable theme proposal, or it is explicitly rejected as insufficient evidence.

---

# Book 3 — Theme-to-Market Discovery and Ranking

> **Purpose:** Turn reviewed themes into point-in-time candidate universes and transparent rankings under the active operator mandate.  
> **Output:** Universe snapshot contract, candidate eligibility rules, ranking engine, rejection ledger, discovery request/response artifacts and explainable scorecards.

## Discovery Flow

~~~mermaid
flowchart TD
    A["Reviewed Theme Proposal"] --> B["Universe Definition"]
    B --> C["Point-in-Time Snapshot"]
    C --> D["Eligibility Filters"]
    D --> E["Candidate Evidence Enrichment"]
    E --> F["Transparent Ranking"]
    F --> G["DiscoveryResult Set"]
    G --> H["Deep Research Queue"]
~~~

## Universe Snapshot Contract

~~~text
UniverseSnapshot
  - universe_snapshot_id
  - as_of_time
  - market
  - asset_class
  - constituent_source
  - constituent_version
  - eligibility_rules_version
  - included_instruments
  - excluded_instruments
  - exclusion_reasons
  - provider_refs
  - lineage_id
  - status
~~~

The current constituents of an index, ETF, industry list or screener cannot be used to recreate a past universe unless the historical membership is documented.

## Candidate Eligibility Rules

Eligibility may include, only when permitted by the ResearchMandate:

- Asset class.
- Exchange/market.
- Region.
- Sector or industry.
- Minimum liquidity.
- Minimum price/history coverage.
- Market capitalization or fund exposure.
- Event/theme relevance.
- Corporate-action data sufficiency.
- Existing portfolio/exclusion rules.

Every exclusion needs a reason. No candidate is silently discarded.

## Ranking Contract

~~~text
CandidateScore
  - candidate_id
  - universe_snapshot_id
  - theme_id
  - score_version
  - score_total
  - score_dimensions
  - evidence_refs
  - data_quality_flags
  - rank
  - rejection_reason
  - confidence
  - computed_at
  - lineage_id
~~~

Scores must be explainable. “AI picked it” is not an explanation.

## Initial Ranking Dimensions

| Dimension | Meaning |
|---|---|
| Theme relevance | How directly the evidence supports exposure to the theme |
| Mechanism clarity | Whether the transmission path is named and credible |
| Catalyst proximity | Whether the event/catalyst is active and time-bounded |
| Data sufficiency | Whether available data supports further work |
| Liquidity/operability | Whether the instrument meets mandate rules |
| Counterevidence | Negative or conflicting support |
| Crowding/ambiguity | Conditions that reduce confidence |
| Research fit | Match to the operator's custom research mandate |

Ranking is not a trade signal.

## Required Tests

- Universe snapshot has a stable as-of time.
- Current constituents cannot satisfy historical discovery request.
- Every exclusion has a reason.
- Rankings are deterministic from same inputs/version.
- Missing data lowers suitability or marks unknown; it never improves a score.
- Ties have deterministic resolution.
- A candidate cannot enter the deep-research queue with missing lineage.
- Out-of-scope asset class is rejected.
- A candidate score exposes contributing dimensions.

## Failure Injections

- Universe provider returns current membership for historical request.
- Liquidity data missing.
- Same candidate appears twice under symbol aliases.
- Ranking version changes mid-run.
- Candidate has contradictory sector classification.
- Theme contains no valid eligible securities.
- Candidate universe is too large for the declared compute budget.

## Non-Goals

- No generic “top stocks to buy” output.
- No direct order/entry recommendation.
- No capital allocation.
- No backtesting.
- No strategy qualification.
- No provider expansion outside OBB-02 capability registry.

## Book 3 Exit Gate

A reviewed theme creates a reproducible universe snapshot, an explainable ranked candidate set, explicit rejections, and a bounded deep-research queue.

---

# Book 4 — Deep Research, StrategySpec Handoff and Intelligence Lock

> **Purpose:** Produce operator-guideline-compliant research theses and translate only approved, evidence-sufficient theses into StrategySpec proposals for independent validation.  
> **Output:** Thesis contract, counterevidence workflow, invalidation policy, StrategySpec proposal adapter, Research Director review and Intelligence Lock Manifest.

## Thesis-to-Strategy Flow

~~~mermaid
flowchart TD
    A["Ranked Candidate"] --> B["Deep Research Task"]
    B --> C["ResearchThesis"]
    C --> D["Counterevidence Review"]
    D --> E{"Research Director Decision"}
    E -->|"Not sufficient"| F["Reject / Monitor / Revisit"]
    E -->|"Sufficient"| G["StrategySpec Proposal"]
    G --> H["OBB-04 Independent Validation"]
~~~

## Research Thesis Contract

~~~text
ResearchThesis
  - thesis_id
  - candidate_id
  - mandate_id
  - thesis_type
  - market_mechanism
  - catalyst
  - expected_path
  - time_horizon
  - evidence_refs
  - counterevidence_refs
  - uncertainty
  - invalidation_conditions
  - data_quality_flags
  - research_questions_answered
  - research_questions_open
  - confidence
  - review_status
  - lineage_id
~~~

## Required Thesis Standard

A thesis must state:

1. The claimed mechanism.
2. The catalyst or structural condition.
3. Evidence supporting the claim.
4. Counterevidence.
5. What would disprove or weaken the thesis.
6. Which facts are unknown.
7. The time horizon.
8. Why this candidate fits the active mandate.
9. Whether the result is suitable for StrategySpec proposal.
10. Why it is not a trade authorization.

## StrategySpec Proposal Rules

The StrategySpec is an implementation-neutral proposal, not final strategy code and not a backtest result.

~~~text
StrategySpecProposal
  - strategy_spec_id
  - thesis_id
  - hypothesis
  - market/instrument scope
  - entry-condition intent
  - invalidation intent
  - time horizon
  - required data
  - candidate signals or features
  - execution assumptions
  - cost assumptions
  - required validation tests
  - prohibited assumptions
  - lineage_id
  - proposal_status
~~~

A StrategySpec proposal may be created only when:

- The thesis is reviewed.
- Counterevidence is present.
- Invalidation is explicit.
- Required data is identified.
- The proposal preserves lineage.
- It has no implied capital permission.
- It is routed to independent OBB-04 validation.

## Research Director Intelligence Lock

The Research Director may:

- Review research quality.
- Demand correction or counterevidence.
- Approve a bounded discovery request.
- Approve a thesis for StrategySpec proposal.
- Reject or defer a thesis.
- Produce an Intelligence Lock Manifest.

The Research Director may not:

- Query unapproved providers.
- Bypass OBB-02 provenance rules.
- Rank markets directly outside the approved discovery system.
- Write final strategy implementation.
- Run canonical backtests.
- Qualify a strategy.
- Set capital.
- Place or route orders.
- Change execution controls.

## Intelligence Lock Manifest

~~~text
intelligence_lock_id
mandate_id
event_id
theme_id
universe_snapshot_id
candidate_ids
thesis_ids
strategy_spec_ids
rejected_candidates
open_questions
data_quality_exceptions
reviewer_id
reviewed_at
lineage_id
status
~~~

## Required Tests

- Thesis missing counterevidence is incomplete.
- Thesis missing invalidation cannot propose StrategySpec.
- StrategySpec proposal with no reviewed thesis is rejected.
- Research Director cannot invoke validation or execution action.
- Confidence without evidence references is rejected.
- Open questions remain visible to the reviewer.
- Manual thesis path is possible only with explicit manual_authoring declaration.
- Two agents producing conflicting theses remain separate; no silent averaging.
- A proposal includes required data and validation tests.

## Failure Injections

- Candidate research lacks source support.
- Counterevidence contradicts core mechanism.
- Agent claims a price target with no mandate support.
- Proposed strategy omits invalidation.
- Research Director tries to request execution.
- Thesis uses stale or wrong-universe data.
- StrategySpec proposal requests unapproved asset class.

## Non-Goals

- No real Nautilus validation.
- No qualification level.
- No capital sizing.
- No paper/shadow deployment.
- No broker routing.
- No automatic trade recommendation.

## Book 4 Exit Gate

A real approved event can produce a cited theme, point-in-time candidate set, reviewed thesis, counterevidence, invalidation conditions, and a lineage-complete StrategySpec proposal for OBB-04.

---

# OBB-03 Lock Gate

OBB-03 locks only when all four books are independently verified and the end-to-end research demonstration uses real approved data artifacts rather than invented values.

~~~mermaid
sequenceDiagram
    participant D as Approved Data Artifact
    participant M as Macro/News Agent
    participant T as Theme Mapper
    participant S as Discovery System
    participant R as Deep Research
    participant O as Research Director

    D->>M: Cited event context
    M->>T: Structured event and evidence
    T->>S: Reviewed theme proposal
    S->>R: Point-in-time ranked candidates
    R->>O: Thesis plus counterevidence
    O->>O: Intelligence lock or rejection
~~~

## Required Gate Evidence

- Active ResearchMandate version.
- Real approved event artifact.
- Source and citation ledger.
- Deduplication result.
- Theme/transmission hypothesis with disconfirming conditions.
- Point-in-time UniverseSnapshot.
- Ranked candidate set and rejection ledger.
- At least one reviewed ResearchThesis.
- Counterevidence and invalidation evidence.
- StrategySpec proposal or justified non-proposal.
- Research Director Intelligence Lock Manifest.
- Independent reviewer record.
- Proof no execution/capital authority was introduced.

## Handoff to OBB-04

Once locked, OBB-04 may take a StrategySpec proposal and perform:

> Genuine Nautilus validation, calculated robustness qualification, operator-approved paper/shadow lifecycle, reconciliation, portfolio visibility and governed operations.

No OBB-03 artifact itself authorizes a trade.
