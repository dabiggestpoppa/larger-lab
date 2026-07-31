# OBB-01 — Truth and Seam Lock

> **Program:** GLX FORGE OpenBB Operational Integration  
> **Status:** planned  
> **Authority effect:** None  
> **Required predecessor:** Existing GLX FORGE planning corpus and current repository evidence  
> **Required successor:** OBB-02 — OpenBB Foundation  
> **Phase anchor:** No module, metric, workflow, dashboard state, or phase label may claim more than its executable evidence supports.

## Why This Phase Exists

The current repository now contains substantial FORGE domain modules and a dashboard workflow. That is valuable infrastructure, but current source and documentation contain different levels of truth:

- Some modules are executable contracts.
- Some dashboard workflows create simulated results.
- Some scenario tests demonstrate compatibility rather than real integration.
- Some dashboard labels and status documents claim completion beyond operational evidence.

OBB-01 does not remove the scaffold. It makes the scaffold measurable and safe to extend.

## Phase Objective

At lock, a future agent can reliably determine:

1. Which components are contracts only.
2. Which components operate locally against real inputs.
3. Which workflows are simulations.
4. Which integrations are external and verified.
5. Which claims are stale or contradictory.
6. Which service owns each part of the final system.
7. Which lineage and authority fields must exist before a workflow advances.
8. Which tests support every displayed state.

## Phase Topology

~~~mermaid
flowchart TD
    A["Existing FORGE and OCE Source"] --> B["Book 1<br/>Reality Audit"]
    B --> C["Book 2<br/>Dual-Cockpit Constitution"]
    C --> D["Book 3<br/>Lineage and Seam Contracts"]
    D --> E["Book 4<br/>Truthful Gates and Status"]
    E --> F{"Independent OBB-01 Gate"}
    F -->|"Approved"| G["OBB-02 OpenBB Foundation"]
    F -->|"Rejected"| B
~~~

## Scope

Included:

- Source and test evidence audit.
- Simulation and placeholder identification.
- Documentation conflict reconciliation.
- OpenBB/FORGE/OCE/Nautilus boundary decision.
- Canonical artifact IDs and parent-lineage contracts.
- State transitions and truthful status claims.
- Dashboard claim/evidence requirements.
- Test classification and independent review requirements.

Excluded:

- Installing OpenBB.
- Calling OpenBB APIs.
- Building Workspace widgets.
- Running Nautilus jobs.
- Modifying trading strategies.
- Enabling paper, shadow, sandbox, broker, or live execution.
- Refactoring legacy FORGE modules solely for cleanliness.
- Rewriting historical documents without preserving their evidence value.

## Phase Deliverables

~~~text
phase-01/
├── capability-matrix.md
├── module-inventory.json
├── simulation-debt-register.md
├── documentation-conflicts.md
├── ADR-001-dual-cockpit.md
├── responsibility-matrix.md
├── lineage-contract.md
├── workflow-state-machine.md
├── phase-gate-registry.md
├── dashboard-truth-contract.md
└── independent-review-record.md
~~~

## Book Sequence

| Book | Name | Primary output | Cannot begin until |
|---|---|---|---|
| 1 | Implementation Reality Audit | Evidence-backed capability map | Phase entry conditions |
| 2 | Dual-Cockpit Constitution | Locked responsibility and dependency boundaries | Book 1 |
| 3 | Canonical Lineage and Seam Contracts | Versioned artifact and state-machine contracts | Book 2 |
| 4 | Truthful Gates, Dashboard States and Operational Claims | Evidence-backed status and gate system | Book 3 |

---

# Book 1 — Implementation Reality Audit

> **Purpose:** Identify what is actually implemented and classify every significant FORGE capability by evidence level.  
> **Output:** Capability matrix, module inventory, simulation debt register, test evidence index, documentation conflict report.  
> **State before work:** admitted only after an active implementation-part plan exists.

## Inputs

- Current main-branch source.
- Current FORGE and OCE test trees.
- Current dashboard code and workflow code.
- Current phase, status, progress, memory and architecture documents.
- Current commit and dirty-worktree record.
- Existing original GLX FORGE plans.

## Audit Questions

For each module or workflow, answer:

| Question | Required answer form |
|---|---|
| What does it claim to do? | Short capability statement |
| Where is source evidence? | Path and symbol |
| What inputs does it use? | Real, synthetic, mocked, unknown |
| What outputs does it produce? | Artifact and schema |
| Does it contact a real dependency? | Yes, no, unknown |
| Is any metric hardcoded? | Yes/no plus location |
| What test covers it? | Exact test path and command |
| Was the test run currently? | passed, failed, not_run, blocked |
| Is it independently verified? | Yes/no plus review record |
| What is its true classification? | Approved vocabulary |

## Required Classification Matrix

| Class | Meaning | Example |
|---|---|---|
| contract_only | Type, enum, schema, or interface exists | Dataclass for an order or provider |
| local_functional | Real deterministic behavior occurs locally | Parser validates real input fixture |
| simulation | Invented data or synthetic behavior drives outcome | Hardcoded return or manually created fill |
| external_integrated | Calls a real external system through approved seam | Provider response normalized through adapter |
| builder_verified | Current builder test passed | Unit or contract test with command evidence |
| independently_verified | Separate reviewer reproduced the evidence | Independent gate record |
| production_certified | Separate production authority exists | Explicit certification only |
| unknown | Evidence is missing, stale, or contradictory | A claimed feature with no reproducible proof |

## Known Initial Audit Targets

- FORGE data gateway and provider abstractions.
- Discovery scanner and ranking engine.
- Dashboard workflow orchestrator.
- Validation engine and robustness qualification.
- Simulation and paper-trading classes.
- Execution adapter and lifecycle classes.
- Portfolio and capital-envelope classes.
- OCE governance integration points.
- Nautilus directory and existing test runners.
- Dashboard phase cards, badges and metrics.
- Root README, AGENTS, GLX progress, build status and architecture documents.

## Simulation Debt Register Format

| Debt ID | Location | Behavior | Why simulated | Risk if mislabeled | Replacement phase |
|---|---|---|---|---|---|
| SD-001 | Dashboard scan workflow | Creates discovery result | No provider query | False scanner confidence | OBB-02/03 |
| SD-002 | Dashboard backtest workflow | Returns fixed performance | No Nautilus run | False qualification | OBB-04 |
| SD-003 | Qualification workflow | Constructs GOLD state | No calculated gate | False promotion | OBB-04 |
| SD-004 | Paper workflow | Creates portfolio object | No feed/order/reconciliation loop | False operational state | OBB-04 |
| SD-005 | Execution demo | Constructs connected adapter/order | No proven venue connection | Unsafe authority inference | OBB-04 |

The implementation audit may find more debt. It must not hide it.

## Required Tests

- Every in-scope module appears once and only once in the inventory.
- Every dashboard workflow has a classification.
- Static hardcoded performance values are detected.
- Static phase-complete labels are detected.
- A current test result includes command, timestamp, environment and result.
- A missing result is represented as not_run or blocked.
- Conflicting documentation claims create a conflict record.
- Inventory generation is deterministic against the same revision.

## Failure Injections

- Omit one module from the inventory.
- Mark a known simulated workflow as externally integrated.
- Delete a supporting test reference.
- Change a status document without changing evidence.
- Add a new source file without refreshing the inventory.

## Non-Goals

- No code refactor.
- No removal of historical claims.
- No new provider dependency.
- No “quick” reclassification based on filenames alone.
- No metrics rewrite.

## Book 1 Exit Gate

Book 1 is complete only when all in-scope claims have a classification, evidence links, unknown states, and a conflict record where required.

---

# Book 2 — Dual-Cockpit Constitution

> **Purpose:** Lock the responsibility boundaries that stop OpenBB, FORGE, OCE, Nautilus, agents and dashboards from becoming overlapping control systems.  
> **Output:** ADR-001, responsibility matrix, dependency rules, authority map and integration boundary tests.

## Core Decision

~~~mermaid
flowchart TD
    subgraph Analyst["Research Cockpit"]
        W["OpenBB Workspace"]
        A["Research and Scanner Agents"]
        M["Market, News and Thesis Widgets"]
    end

    subgraph Control["Operations Cockpit"]
        O["OCE Governance"]
        G["GLX/OCE Console"]
        J["Workflow and Job Control"]
    end

    subgraph Quant["Quant Runtime"]
        S["StrategySpec"]
        N["NautilusTrader"]
        P["Paper and Shadow Runtime"]
    end

    M --> A
    A --> S
    S --> O
    G --> O
    O --> N
    N --> P
~~~

The final architecture is dual-cockpit:

- OpenBB Workspace is for analyst work: market data, research, scanning, visual context, cited agent output, and candidate review.
- GLX/OCE is for operations: jobs, approvals, resource health, lifecycle, incidents, execution state, capital limits and kill controls.

## Responsibility Matrix

| Component | May do | Must not do |
|---|---|---|
| OpenBB Workspace | Display data, host widgets, collect analyst context, present agent output | Route orders or grant authority |
| OpenBB Data Adapter | Normalize supported provider responses | Become the canonical historical store |
| Research Agent | Research, classify, rank, propose | Approve or execute |
| FORGE | Create domain artifacts and bounded workflow requests | Override OCE policy |
| OCE | Govern lifecycle, enforce authority, coordinate workers | Invent research claims |
| Nautilus | Run canonical validation | Grant capital approval |
| Execution adapter | Perform approved bounded routing only | Self-authorize orders |
| Human operator | Define goals, limits and approvals | Be bypassed |

## Dependency Rules

Allowed:

~~~text
OpenBB Workspace -> FORGE Workspace API
FORGE Workspace API -> FORGE domain contracts
FORGE workflow -> OCE policy and job requests
OCE -> Nautilus validation adapter
OCE -> approved paper/shadow runtime
OCE -> execution adapter only after separate authority
~~~

Forbidden:

~~~text
OpenBB Workspace -> broker API
OpenBB agent -> execution adapter
Research agent -> approval action
Strategy author -> self-validation and self-promotion
Nautilus result -> automatic capital allocation
Dashboard button -> direct execution bypassing OCE
~~~

## Required Tests

- Architecture test rejects direct Workspace-to-broker imports.
- Architecture test rejects OpenBB SDK imports outside approved adapter paths.
- Every state transition identifies an owning service.
- Every capital-bearing transition requires an OCE authority evaluation.
- The author/validator/approver/executor roles cannot collapse into a single identity.

## Failure Injections

- Simulate a widget calling an execution adapter.
- Simulate a research role calling an approval endpoint.
- Add an OpenBB import to a strategy module.
- Submit a state change without an OCE request ID.
- Register a service without a responsibility declaration.

## Book 2 Exit Gate

Book 2 is complete when an agent can answer who owns every workflow step and when automated tests reject prohibited dependency directions.

---

# Book 3 — Canonical Lineage and Seam Contracts

> **Purpose:** Define the stable artifacts and IDs that carry context from market event through research, strategy, validation and operation.  
> **Output:** Versioned lineage contract, artifact registry, workflow state machine, identity convention and migration map.

## Artifact Flow

~~~mermaid
flowchart TD
    E["MarketEvent"] --> T["ThemeHypothesis"]
    T --> U["UniverseSnapshot"]
    U --> R["ResearchThesis"]
    R --> S["StrategySpec"]
    S --> X["ExperimentManifest"]
    X --> V["ValidationReport"]
    V --> Q["QualificationDecision"]
    Q --> D["DeploymentManifest"]
    D --> P["PortfolioSnapshot"]
~~~

## Required Artifact Fields

Every artifact must include:

~~~text
artifact_id
artifact_type
schema_version
lineage_id
parent_ids
created_at
created_by
owner_service
authority_scope
status
input_fingerprint
configuration_fingerprint
evidence_refs
error_refs
~~~

## Canonical IDs

| Artifact | Required ID |
|---|---|
| Market event | event_id |
| Theme | theme_id |
| Universe snapshot | universe_snapshot_id |
| Research thesis | thesis_id |
| Strategy | strategy_spec_id |
| Experiment | experiment_id |
| Validation run | validation_run_id |
| Qualification | qualification_id |
| Deployment | deployment_id |
| Order intent | order_intent_id |
| Portfolio snapshot | portfolio_snapshot_id |
| Full lineage | lineage_id |

## State Machine

~~~mermaid
stateDiagram-v2
    [*] --> Proposed
    Proposed --> EvidenceReady
    EvidenceReady --> StrategySpecified
    StrategySpecified --> ValidationQueued
    ValidationQueued --> Validated
    Validated --> Qualified
    Qualified --> PaperApproved
    PaperApproved --> PaperActive
    PaperActive --> ShadowApproved
    ShadowApproved --> ShadowActive

    Proposed --> Rejected
    EvidenceReady --> Rejected
    StrategySpecified --> Rejected
    ValidationQueued --> Failed
    Validated --> Rejected
    Qualified --> Paused
    PaperActive --> Paused
    ShadowActive --> Paused
    Paused --> Retired
~~~

## Required Tests

- A thesis without a universe snapshot is rejected.
- A StrategySpec without a thesis is rejected unless explicitly tagged manual_authoring.
- A validation report without an experiment manifest is rejected.
- A qualification with no validation parent is rejected.
- Duplicate requests are idempotent.
- Schema mismatch fails loudly.
- Broken parent lineage becomes an explicit broken_lineage state.
- A provider-backed artifact records provider and retrieval time.

## Failure Injections

- Remove parent IDs.
- Change schema version with no migration.
- Submit one experiment twice.
- Use current data in a historical experiment.
- Attempt qualification from a fabricated validation report.

## Book 3 Exit Gate

Book 3 is complete when every downstream artifact can be reconstructed from parent artifacts, configurations and evidence references.

---

# Book 4 — Truthful Gates, Dashboard States and Operational Claims

> **Purpose:** Replace blanket completion labels and demonstration success with evidence-backed states, gates and dashboard behavior.  
> **Output:** Gate registry, dashboard truth contract, claim-reconciliation policy and independent-review template.

## Evidence Levels

~~~mermaid
flowchart TD
    A["Design truth"] --> B["Source exists"]
    B --> C["Current builder test"]
    C --> D["Independent verification"]
    D --> E["Real operational integration"]
    E --> F["Separate production certification"]
~~~

## Dashboard Claim Rules

| Dashboard claim | Minimum evidence |
|---|---|
| Module exists | Source inventory record |
| Tested | Current command, result and timestamp |
| Integrated | Real seam test result |
| OpenBB connected | Health and capability proof |
| Backtest completed | Nautilus run artifact |
| Qualified | Calculated validation report |
| Paper active | Runtime heartbeat and deployment manifest |
| Shadow active | Shadow comparison evidence |
| Production ready | Separate certification evidence |
| Live | Explicit authority and reconciliation state |

## Required Status Behavior

- Missing evidence maps to unknown or blocked.
- Stale evidence maps to stale.
- Simulated metrics show simulated.
- Changed code/data fingerprints invalidate dependent results.
- Approval expiry pauses promotion.
- Dashboard cards derive state from artifacts, not constants.
- A complete phase label requires a locked phase-gate record.

## Required Tests

- A dashboard card cannot show verified without evidence.
- A simulated result cannot show as a backtest result.
- A changed strategy fingerprint invalidates qualification.
- A changed data fingerprint invalidates validation.
- An expired approval blocks deployment.
- A builder cannot self-lock a phase.
- A dashboard claim with a missing artifact displays unknown.

## Failure Injections

- Delete required evidence.
- Hardcode a phase-complete label.
- Modify code after validation.
- Modify data manifest after validation.
- Promote a simulated result to paper state.
- Attempt independent review with the builder identity.

## Book 4 Exit Gate

Book 4 is complete when all status and dashboard claims can be traced to current evidence and no workflow can promote beyond its authority.

---

# OBB-01 Lock Gate

OBB-01 locks only when:

1. Books 1–4 are verified.
2. All evidence artifacts are stored and reproducible.
3. The independent reviewer is not the builder.
4. OpenBB/FORGE/OCE/Nautilus boundaries are locked.
5. Dashboard truth rules are adopted.
6. No live, paper, sandbox, broker, or capital authority was added.

~~~mermaid
flowchart TD
    B1["Book 1 verified"] --> G["OBB-01 Gate"]
    B2["Book 2 verified"] --> G
    B3["Book 3 verified"] --> G
    B4["Book 4 verified"] --> G
    G -->|"All conditions pass"| L["OBB-01 locked"]
    G -->|"Any condition fails"| R["Return to affected book"]
~~~

## Handoff to OBB-02

Once locked, OBB-02 may begin with a clean mandate:

> Connect one real OpenBB data response through the approved adapter boundary, preserve lineage, and render it in a Workspace widget without granting any execution authority.
