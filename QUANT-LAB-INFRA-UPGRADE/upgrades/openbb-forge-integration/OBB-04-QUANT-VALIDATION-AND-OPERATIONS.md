# OBB-04 — Quant Validation and Governed Operations

> **Program:** GLX FORGE OpenBB Operational Integration  
> **Status:** planned  
> **Required predecessor:** OBB-03 locked  
> **Authority effect:** Validation, paper and shadow workflows may be designed and implemented only through explicit OCE gates  
> **Live authority:** Disabled  
> **Final OBB-04 authority state:** Production-ready-not-authorized  
> **Phase anchor:** A research proposal becomes eligible for testing, never entitled to capital, execution, or autonomous promotion.

## Why This Phase Exists

OBB-03 can create a lineage-complete StrategySpec proposal. It does not prove that the strategy works, survives realistic costs, remains stable across regimes, can operate in paper/shadow conditions, or fits the portfolio.

OBB-04 replaces simulated backtests, manually assigned qualification levels and constructed deployment states with real, reproducible evidence.

The end state is not automatic live trading. The end state is a governed system that can validate, paper test, shadow monitor, reconcile, pause, recover and retire strategies while production routing remains disabled unless a separate current authorization exists.

## Phase Objective

At lock, a reviewed StrategySpec can:

1. Resolve a versioned historical dataset and experiment manifest.
2. Run through the canonical NautilusTrader event-driven validation path.
3. Produce reproducible artifacts, metrics, costs and fingerprints.
4. Survive independent validation and robustness gates.
5. Request—not receive by default—paper or shadow admission.
6. Enter paper/shadow only with operator and OCE approval.
7. Maintain ownership, reservation, portfolio and reconciliation evidence.
8. Pause safely, recover through independent approval, and retire without losing continuity.
9. Remain production-ready-not-authorized for live capital.

## Phase Topology

~~~mermaid
flowchart TD
    A["Reviewed StrategySpec Proposal"] --> B["Book 1<br/>Nautilus Experiment Bridge"]
    B --> C["Book 2<br/>Validation Ladder and Qualification"]
    C --> D["Book 3<br/>Paper and Shadow Lifecycle"]
    D --> E["Book 4<br/>Portfolio Reconciliation and Operations Lock"]
    E --> F{"Independent OBB-04 Gate"}
    F -->|"Approved"| G["Production-Ready-Not-Authorized"]
    F -->|"Rejected"| B
~~~

## Scope

Included:

- StrategySpec-to-Nautilus translation.
- Historical data manifest selection.
- Reproducible event-driven backtest runs.
- Cost, slippage and execution-assumption configuration.
- Validation ladder and calculated qualification.
- Paper and shadow deployment requests.
- OCE-gated lifecycle transitions.
- Portfolio ownership, reservation and exposure reconciliation.
- Pausing, recovery, retirement and incident controls.
- GLX/OCE operational visibility.
- Production-readiness evidence without live routing.

Excluded:

- Automatic live execution.
- Standing capital allocation.
- Permanent reusable execution permits.
- Broker account funding or withdrawal.
- Unofficial production broker APIs.
- Autonomous strategy promotion.
- Generic or unscoped flatten-all control.
- Automatic resume after suspension.
- Treating a paper or shadow success as live authorization.
- Treating Nautilus portfolio state as capital-allocation authority.

## Promotion Principle

~~~mermaid
flowchart TD
    A["StrategySpec Proposal"] --> B["Nautilus Validation"]
    B --> C{"Calculated Qualification"}
    C -->|"Fail"| D["Reject, Revise or Retire"]
    C -->|"Pass"| E["Paper Request"]
    E --> F{"OCE + Operator Approval"}
    F -->|"Approved"| G["Paper Active"]
    G --> H["Shadow Request"]
    H --> I{"OCE + Operator Approval"}
    I -->|"Approved"| J["Shadow Active"]
    J --> K["Production-Ready-Not-Authorized"]
~~~

No arrow in this phase leads directly to live trading.

## Book Sequence

| Book | Name | Primary output | Cannot begin until |
|---|---|---|---|
| 1 | Nautilus Experiment Bridge | Genuine backtest job and artifact contract | OBB-03 lock |
| 2 | Validation Ladder and Calculated Qualification | Reproducible qualification evidence | Book 1 |
| 3 | Paper and Shadow Lifecycle | Governed non-live operation with health evidence | Book 2 |
| 4 | Portfolio Reconciliation and Operations Lock | Recovery, controls and production-ready-not-authorized evidence | Book 3 |

---

# Book 1 — StrategySpec to Genuine Nautilus Experiment Bridge

> **Purpose:** Translate an approved StrategySpec proposal into a reproducible NautilusTrader experiment without allowing the experiment to invent data, costs or strategy behavior.  
> **Output:** Experiment manifest, Nautilus adapter, dataset selector, result parser, artifact store and reproducibility tests.

## Canonical Experiment Flow

~~~mermaid
flowchart TD
    A["StrategySpec Proposal"] --> B["ExperimentManifest"]
    B --> C["Historical Data Manifest"]
    C --> D["Nautilus Adapter"]
    D --> E["Event-Driven Backtest Run"]
    E --> F["Run Artifacts"]
    F --> G["ValidationReport Input"]
~~~

## Experiment Manifest

~~~text
ExperimentManifest
  - experiment_id
  - strategy_spec_id
  - strategy_code_fingerprint
  - strategy_spec_version
  - dataset_manifest_id
  - data_fingerprint
  - start_time
  - end_time
  - instrument_scope
  - bar/tick frequency
  - venue model
  - execution model
  - fee model
  - slippage model
  - corporate-action policy
  - session/calendar policy
  - parameter_set
  - engine_version
  - run_environment
  - requested_by
  - authority_scope
  - lineage_id
  - status
~~~

## Nautilus Adapter Rules

- NautilusTrader is the canonical event-driven backtesting path.
- Fast Pandas/vectorized tests may reject weak ideas earlier, but cannot qualify a strategy.
- The adapter must translate StrategySpec intent explicitly; it cannot silently add logic.
- Data must come from a versioned historical manifest, not a live/current provider query.
- Fees, spread, slippage, session logic and execution assumptions must be declared.
- Engine and adapter version are recorded.
- A failed engine run produces a failed artifact, not a fallback performance result.
- The result parser must preserve raw artifacts and expose only verified derived metrics.

## Required Deliverables

~~~text
forge/validation/nautilus/
├── adapter.py
├── experiment_manifest.py
├── dataset_selector.py
├── run_manager.py
├── result_parser.py
├── artifacts.py
└── tests/
    ├── test_spec_translation.py
    ├── test_manifest.py
    ├── test_dataset_selection.py
    ├── test_run_failures.py
    └── test_reproducibility.py
~~~

## Required Tests

- A StrategySpec without review/lineage cannot start an experiment.
- A historical request requires a dataset manifest and fingerprint.
- Run artifacts include engine, code, data and configuration fingerprints.
- Fee and slippage assumptions are visible in the result.
- A code change invalidates an old result.
- A data change invalidates an old result.
- Engine failure does not return performance metrics.
- Same manifest reproduces the same job identity.
- A result parser rejects incomplete/unknown engine output.
- A direct dashboard-generated performance value cannot satisfy the experiment contract.

## Failure Injections

- Missing historical dataset.
- Dataset range does not cover requested period.
- Changed strategy parameters after manifest creation.
- Changed data fingerprint.
- Missing fee model.
- Engine timeout.
- Corrupt result artifact.
- Live/OpenBB response passed as historical test input.
- Mismatched instrument or venue configuration.

## Non-Goals

- No qualification decision yet.
- No paper or shadow deployment.
- No broker adapter use.
- No automatic retry that changes parameters or dataset.
- No use of current constituents/revised data in historical experiments.

## Book 1 Exit Gate

A reviewed StrategySpec produces a genuine Nautilus run artifact with complete reproducibility metadata, or a typed failure with no invented metrics.

---

# Book 2 — Validation Ladder and Calculated Qualification

> **Purpose:** Convert genuine experiment evidence into an independent, repeatable qualification decision that rejects unstable, biased or under-specified strategies.  
> **Output:** Validation plan, robustness test suite, qualification calculation, rejection ledger, validation report and review handoff.

## Validation Ladder

~~~mermaid
flowchart TD
    A["Genuine Nautilus Run"] --> B["Data and Lineage Check"]
    B --> C["Cost and Execution Check"]
    C --> D["Bias and Leakage Check"]
    D --> E["Robustness and Regime Tests"]
    E --> F["Portfolio Compatibility Precheck"]
    F --> G{"Calculated Qualification"}
    G -->|"Fail"| H["Reject / Revise / Retire"]
    G -->|"Pass"| I["Eligible to Request Paper"]
~~~

## Required Validation Dimensions

| Dimension | Question |
|---|---|
| Data integrity | Is data point-in-time, complete and manifest-linked? |
| Reproducibility | Can the same manifest be replayed? |
| Leakage | Is future/revised/survivorship information excluded? |
| Execution realism | Are fees, spread, slippage and venue assumptions declared? |
| Trade sufficiency | Is the result supported by enough eligible observations/trades? |
| Parameter robustness | Does small parameter change collapse the result? |
| Regime behavior | Is performance concentrated in one regime or window? |
| Walk-forward behavior | Does the strategy survive out-of-sample testing? |
| Drawdown behavior | Is drawdown measured and bounded by declared policy? |
| Capacity assumptions | Are liquidity and scale assumptions explicit? |
| Portfolio compatibility | Does candidate exposure conflict with declared constraints? |
| Operational feasibility | Can the strategy run under the declared runtime capabilities? |

## Qualification Contract

~~~text
QualificationDecision
  - qualification_id
  - strategy_spec_id
  - validation_run_ids
  - criteria_version
  - overall_status
  - pass_fail_by_dimension
  - metrics
  - rejected_reasons
  - limitations
  - required_next_actions
  - reviewer_id
  - reviewed_at
  - code_fingerprint
  - data_fingerprint
  - lineage_id
~~~

A named label such as GOLD, SILVER or REJECTED may be shown only if it is calculated from recorded criteria and validation evidence.

## Required Tests

- Qualification cannot be manually constructed as pass without run evidence.
- Missing data lineage blocks qualification.
- Changed code/data fingerprint invalidates qualification.
- Leak detection failure rejects the strategy.
- Cost omission rejects the strategy.
- Insufficient trade/observation evidence blocks qualification.
- Parameter perturbation collapse rejects or downgrades qualification.
- Out-of-sample failure rejects or downgrades qualification.
- Qualification criteria are versioned.
- Builder/author identity cannot independently approve qualification.
- A pass is eligibility to request paper, not capital permission.

## Failure Injections

- Look-ahead field included in feature set.
- Revised macro/fundamental value used before its release date.
- Strategy works only in a single month/regime.
- Parameters changed after backtest.
- Cost model removed.
- Trade count below policy.
- Result artifact missing raw transactions.
- Author attempts to approve its own qualification.

## Non-Goals

- No paper admission without separate approval.
- No portfolio allocation.
- No broker connection.
- No live-route permission.
- No “high Sharpe” override for failed integrity checks.

## Book 2 Exit Gate

A qualification decision is calculated from genuine artifacts, rejects deliberate bias/instability fixtures, and grants only eligibility to request paper operation.

---

# Book 3 — Governed Paper and Shadow Lifecycle

> **Purpose:** Implement state-based, non-live paper and shadow operation that respects OCE authority, runtime health, ownership, monitoring and explicit promotion/rollback rules.  
> **Output:** Deployment manifest, paper/shadow runtimes, health records, approval flow, state machine and lifecycle evidence.

## Deployment State Machine

~~~mermaid
stateDiagram-v2
    [*] --> Proposed
    Proposed --> BacktestApproved
    BacktestApproved --> Validated
    Validated --> Qualified
    Qualified --> PaperRequested
    PaperRequested --> PaperApproved
    PaperApproved --> PaperStarting
    PaperStarting --> PaperActive
    PaperActive --> ShadowRequested
    ShadowRequested --> ShadowApproved
    ShadowApproved --> ShadowStarting
    ShadowStarting --> ShadowActive

    Proposed --> Rejected
    Validated --> Rejected
    Qualified --> Rejected
    PaperRequested --> Rejected
    PaperActive --> Paused
    ShadowActive --> Paused
    Paused --> Retired
    Paused --> RecoveryReview
    RecoveryReview --> PaperActive
    RecoveryReview --> ShadowActive
    RecoveryReview --> Retired
~~~

## Core Rule

A strategy may be qualified, but it does not own:

- A permanent portfolio weight.
- An account.
- A venue.
- An order quantity.
- A right to trade.
- An active autonomy lease.
- A reusable execution permit.

## Deployment Manifest

~~~text
DeploymentManifest
  - deployment_id
  - strategy_spec_id
  - qualification_id
  - deployment_mode: paper or shadow
  - instrument_scope
  - account_scope
  - venue_scope
  - data_feed_scope
  - order_simulation_scope
  - monitoring_requirements
  - health_requirements
  - expiry_time
  - approval_id
  - owner_id
  - rollback_plan
  - lineage_id
  - status
~~~

## Paper vs Shadow

| Mode | Meaning | Market effect |
|---|---|---|
| Paper | Simulated orders and portfolio accounting against real/approved market data | No venue order |
| Shadow | Strategy observes live/approved feed and compares intended actions/outcomes without venue routing | No venue order |
| Live | Actual venue/broker routing | Outside OBB-04 scope |

## Approval Rules

- Paper and shadow admission require an explicit OCE policy decision.
- Approval is specific to strategy, account scope, instrument scope, mode, time window and monitoring policy.
- Approval expires.
- Approval cannot be reused after material code/data/criteria change.
- Suspension blocks new risk but preserves required open-exposure management and reconciliation responsibilities.
- Suspension never resumes automatically.
- Recovery requires a separate independent approval.

## Required Tests

- Qualified strategy cannot start paper without approval.
- Paper admission includes exact strategy/instrument/time scope.
- Shadow cannot route a venue order.
- Expired approval pauses/no-ops admission.
- Code/data/criteria change invalidates deployment approval.
- Runtime health failure pauses new work.
- Suspension preserves reconciliation and open-exposure-management logic.
- Recovery cannot resume without independent approval.
- State transitions are idempotent.
- Duplicate deployment request does not create duplicate portfolio instances.
- Paper/shadow event stream includes lineage and owner identity.

## Failure Injections

- Paper feed outage.
- Shadow feed lag.
- Worker restart during active deployment.
- Approval expiry mid-run.
- Strategy code fingerprint change.
- Data feed schema change.
- Duplicate start request.
- Shadow runtime tries to call an execution adapter.
- Health monitor reports stale state.

## Non-Goals

- No live broker order.
- No capital allocation.
- No autonomous promotion from paper/shadow to live.
- No blanket “paper active” without a runtime heartbeat.
- No automatic recovery/resume.

## Book 3 Exit Gate

A qualified strategy can enter bounded paper or shadow mode only after explicit approval, expose live health/lineage, pause safely, and require independent review to resume.

---

# Book 4 — Portfolio Reconciliation, Controls and Operations Lock

> **Purpose:** Reconcile strategy-level intent with portfolio state, enforce exact-scope controls, preserve recovery integrity, and produce a production-ready-not-authorized operational lock.  
> **Output:** Ownership and reservation ledger, reconciliation service, control policy, incident runbook, operations dashboard contract and OBB-04 Lock Manifest.

## Reconciliation Topology

~~~mermaid
flowchart TD
    A["Strategy Intent and Deployment Manifest"] --> B["Ownership Ledger"]
    B --> C["Reservation / Capital Envelope Ledger"]
    C --> D["Expected Paper or Shadow State"]
    D --> E["Runtime / Nautilus Portfolio State"]
    E --> F["Venue or Provider State if Applicable"]
    F --> G["Reconciliation Report"]
    G --> H{"Match and Control Check"}
    H -->|"Match"| I["Continue Monitored Operation"]
    H -->|"Mismatch"| J["Pause / Incident / Recovery Review"]
~~~

## Reconciliation Requirements

Reconciliation compares, where applicable:

- Mandate and approval scope.
- Strategy ownership ledger.
- Reservation and capital-envelope ledger.
- Expected order/position state.
- Actual paper/shadow runtime state.
- Nautilus account/portfolio state.
- Provider/venue orders, fills, positions, cash, fees and margin when available.
- Valuation and aggregate exposure.
- Drawdown and control state.
- Code/data/criteria fingerprints.
- Health and heartbeat evidence.

A net position match alone is insufficient if strategy ownership is wrong.

## Reconciliation Cadence

Run reconciliation:

- Before each job/admission.
- At startup, restart and reconnect.
- After allocation/reservation changes.
- After each relevant lifecycle event.
- On account/control changes.
- At time/session boundaries.
- Before a phase/book/operations lock.
- During incident response.
- Before declaring pause, flat, recovered, retired or reconciled.

## Exact-Scope Controls

~~~mermaid
flowchart TD
    A["Control Request"] --> B["Scope Validation"]
    B --> C["Ownership Validation"]
    C --> D["Policy and Approval Check"]
    D --> E["Adapter Capability Check"]
    E --> F["Control Execution Intent"]
    F --> G["Reconciliation Evidence"]
    G --> H["Control Outcome"]
~~~

Control scope must bind:

- Ownership.
- Strategy/deployment.
- Orders and positions.
- Account and venue.
- Instruments.
- Quantity/notional.
- Prices where relevant.
- Time window.
- Sequence.
- Intended action.

There is no generic flatten_all control in certified paths.

A control intent alone cannot call an adapter.

## Pause and Recovery Rules

- Pause blocks new risk.
- Pause does not erase open-exposure/reconciliation responsibilities.
- Reduce/close control cannot consume another strategy's ownership without explicit portfolio policy and reconciliation.
- A control path cannot claim success or flat without reconciliation evidence.
- Auto-resume is forbidden.
- Recovery requires independent approval.
- Retirement preserves complete artifacts and lineage.

## Required Deliverables

~~~text
forge/operations/
├── reconciliation.py
├── ownership_ledger.py
├── reservation_ledger.py
├── control_scope.py
├── pause_recovery.py
├── incidents.py
├── operations_lock.py
└── tests/
    ├── test_reconciliation.py
    ├── test_ownership.py
    ├── test_controls.py
    ├── test_pause_recovery.py
    └── test_operations_lock.py
~~~

## Required Tests

- Reconciliation detects expected/actual position mismatch.
- Reconciliation detects ownership mismatch even if net position matches.
- Startup/restart triggers reconciliation.
- Suspension blocks new risk and retains required monitoring.
- No automatic resume after pause.
- Recovery requires separate approval.
- Control request with insufficient scope is rejected.
- Control request cannot affect another strategy's reserved/owned position.
- Adapter capability mismatch blocks action.
- “Flat” state requires evidence, not an intent.
- Retired deployment preserves lineage and artifacts.
- Production lock has no standing capital allocation, autonomy lease, execution permit or live routing.

## Failure Injections

- Restart during a pending/cancel-pending order.
- Position mismatch between paper runtime and portfolio.
- Same instrument owned by two strategies.
- Stale provider account/venue data.
- Control request uses overly broad instrument/account scope.
- Pause during open exposure.
- Recovery attempt with same approver as failed runtime action.
- Venue reports order canceled while local state remains live.
- Portfolio ledger has reservation with no deployment.
- Attempt to mark system flat without provider and portfolio reconciliation.

## Production-Ready-Not-Authorized State

The final OBB-04 lock must record:

~~~text
production_capital_grant: null
standing_capital_allocation: none
active_autonomy_lease: null
reusable_execution_permit: null
production_routing: disabled
live_authorization: false
~~~

This is success. It proves the system can be operated safely without accidentally granting real-money authority.

## Book 4 Exit Gate

The system can reconcile, pause, recover through independent approval, retire and preserve evidence across paper/shadow workflows. It remains production-ready-not-authorized.

---

# OBB-04 Lock Gate

OBB-04 locks only when all four books are independently verified and the complete non-live chain succeeds against real internal seams.

~~~mermaid
sequenceDiagram
    participant R as Reviewed StrategySpec
    participant N as Nautilus
    participant V as Independent Validator
    participant O as OCE
    participant P as Paper/Shadow Runtime
    participant L as Portfolio Ledger
    participant C as Reconciliation

    R->>N: Experiment manifest
    N->>V: Genuine run artifacts
    V->>O: Calculated qualification
    O->>P: Explicit paper/shadow approval
    P->>L: Expected state and ownership
    L->>C: Reconciliation request
    C->>O: Match, pause or incident result
~~~

## Required Gate Evidence

- StrategySpec and Research Director Intelligence Lock lineage.
- Real Nautilus experiment artifacts.
- Reproducible data/code/config fingerprints.
- Calculated validation and qualification report.
- Deliberate bias/leakage/cost failure evidence.
- Explicit paper or shadow approval record.
- Runtime health and lifecycle evidence.
- Ownership and reservation ledger evidence.
- Reconciliation reports across normal, restart and mismatch cases.
- Pause and independent recovery evidence.
- Incident/retirement evidence.
- Independent reviewer record.
- Production-ready-not-authorized manifest.

## OBB Program Completion

When OBB-01 through OBB-04 are locked, the documentation and implementation track can truthfully say:

> The GLX FORGE OpenBB integration program is capable of evidence-backed research, point-in-time discovery, independent Nautilus validation, governed paper/shadow operation, portfolio reconciliation and controlled recovery.

It must still not claim live trading authority. Live activation, if ever desired, is a separate current human-authorized program with its own capability certification, capital scope and safety review.
