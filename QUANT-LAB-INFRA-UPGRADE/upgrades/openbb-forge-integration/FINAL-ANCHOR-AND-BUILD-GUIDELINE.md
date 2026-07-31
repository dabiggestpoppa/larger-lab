# GLX FORGE OpenBB Extension — Final Anchor and Build Guideline

> **Document class:** Cross-program operating anchor  
> **Applies to:** Every OBB-01 through OBB-04 decision, implementation part, test, dashboard claim, and handoff  
> **Authority effect:** None  
> **Capital / execution effect:** None  
> **Primary build program:** [QUANT LAB INFRA UPGRADE](../../README.md)  
> **Primary build status:** [Canonical Build Status](../../BUILD_STATUS.md)  
> **Integration crosswalk:** [One Build / Two Lenses](IMPLEMENTATION-CROSSWALK.md)

## 1. One Build, Not Two

The Phase 0–11 FORGE program is the canonical build order. OBB-01 through OBB-04 are the OpenBB integration lens applied to that same build.

OBB does not create a second orchestration spine, a parallel status system, a shortcut around a Phase Lock, or a separate path to execution. It names the OpenBB-specific seams that must be designed and proven as the existing FORGE program progresses.

~~~mermaid
flowchart TD
    A["Phase 0–11 FORGE program<br/>owns build order and Locks"] --> C["One admitted implementation part"]
    B["OBB-01–04 integration lens<br/>owns OpenBB-specific seams"] --> C
    C --> D["Tests, failure injection,<br/>and evidence artifacts"]
    D --> E["Independent review<br/>and truthful status"]
~~~

A piece of work is admissible only when its owning FORGE phase/book and its relevant OBB seam agree on scope, authority, evidence, and handoff. If a requested change has no relevant OBB seam, it records **OBB: not_applicable**; it does not invent one.

## 2. Decision Precedence and Truth

Follow the repository's established precedence. For this integration work, the practical order is:

1. OPERATOR_RULES.md
2. CLAUDE.md
3. QUANT-LAB-INFRA-UPGRADE/AGENTS.md
4. QUANT-LAB-INFRA-UPGRADE/GLX_FORGE_MASTER_BLUEPRINT.md
5. QUANT-LAB-INFRA-UPGRADE/GLX_FORGE_BUILD_GUIDE.md
6. QUANT-LAB-INFRA-UPGRADE/BUILD_STATUS.md
7. The active Phase 0–11 README, book, and implementation part
8. This anchor and the OBB book that owns the OpenBB seam
9. Current source, tests, manifests, and independently reproducible evidence

The Phase 0–11 Build Status owns overall phase and book progress. The OBB Build Status records OpenBB-specific seam evidence. Neither document can raise the effective state above the other. If they conflict, the effective state is the least optimistic supported state and the conflict is a blocker until resolved.

## 3. Current Alignment

| Scope | Supported current state | Meaning |
|---|---|---|
| Phase 0, Book 1, Part 1 | **implemented_unverified** | A deterministic repository/core-component inventory exists; independent review is still pending. |
| Phase 0, Book 1, Parts 2–4 | **planned** | The original program already defines the remaining inventory parts. |
| Phase 0 Reality Lock | **planned** | No Book 1–4 completion or independent Phase Lock exists. |
| OBB-01, Book 1 | **planned** with usable Phase 0 evidence input | It must consume and reconcile Phase 0 inventory evidence; it must not duplicate an audit tool under a new name. |
| OBB-02 through OBB-04 | **planned** | Their prerequisite locks are absent. |
| Capital, paper, shadow, sandbox, broker-writing, and live routing | not authorized | No planning, source, or dashboard artifact grants these powers. |

The existing Phase 0 Part 1 evidence is an input to the OBB reality audit, not proof that OBB-01 or Phase 0 is locked.

## 4. Non-Negotiable System Boundaries

| System / role | Owns | Must not own |
|---|---|---|
| Human operator (MAD) | Objectives, research rules, approval, capital scope, autonomy limits | Automatic override by an agent, dashboard, or config file |
| OCE | Lifecycle orchestration, gates, governance, recovery, execution control | Market-data truth, strategy semantics, or analyst cockpit responsibility |
| FORGE | Domain artifacts and traceable research-to-strategy workflow | Hidden authority or an alternate execution lifecycle |
| OpenBB data boundary | Controlled provider access and normalized research responses | Canonical point-in-time historical store or final validation authority |
| OpenBB Workspace | Research and analyst interaction | Broker routing, capital authority, or an execution console |
| NautilusTrader | Canonical event-driven validation | Research policy, capital allocation, or self-approval |
| Research agents | Evidence collection, ranking, proposals, typed research artifacts | Capital, approval, validation certification, or execution authority |

The following paths are always forbidden:

- OpenBB Workspace -> broker or exchange adapter
- research agent -> qualification approval, deployment approval, or broker adapter
- dashboard button -> execution adapter without OCE authorization and exact permit
- current provider response -> historical backtest without a point-in-time DatasetManifest
- strategy author -> its own final validator, approver, and executor

## 5. Builder Contract for Every Session

Before changing code or status, a builder must:

1. Read the canonical build status, active original implementation part, this anchor, the relevant OBB book, and current source/tests.
2. State one bounded objective, exact allowed paths, explicit non-goals, authority effect, rollback path, and independent reviewer.
3. Establish a red proof: a failing test, missing evidence condition, or explicitly recorded proof gap.
4. Implement the smallest canonical behavior for that part only.
5. Run the declared success tests and relevant failure injections.
6. Produce redacted, reproducible evidence with code/config/data fingerprints where applicable.
7. Update both statuses only to the least optimistic supported state.
8. Hand off with exact commands, results, blockers, artifact paths, rollback, and the next admitted or planned part.

No builder may claim a higher state merely because source compiles, a UI renders, a route returns success, a model produces prose, or a container starts.

~~~mermaid
stateDiagram-v2
    [*] --> planned
    planned --> admitted
    admitted --> in_progress
    in_progress --> implemented_unverified
    implemented_unverified --> verified
    verified --> locked
    implemented_unverified --> blocked
    verified --> invalidated
    locked --> invalidated
    blocked --> planned
~~~

Only an independent reviewer may move an implementation from **implemented_unverified** to **verified**. A Lock certifies only the exact scope it names.

## 6. Tests That Matter

| Claim | Required proof |
|---|---|
| Deterministic inventory | Re-run against unchanged workspace; stable identity fields match; generated output does not contaminate the next scan. |
| Real OpenBB integration | One actual read-only provider path flows through the FORGE adapter into a visible Workspace artifact, with timeout/schema/rate-limit failures surfaced. |
| Point-in-time research or backtest | DatasetManifest records provider, parameters, observed/retrieved times, normalization version, quality state, and exact data identity. |
| Agent research | Typed output separates fact, source, inference, uncertainty, counterevidence, and invalidation; malformed output and tool denial fail closed. |
| Nautilus validation | A real engine run artifact links StrategySpec, data, code/config fingerprints, execution assumptions, and rejection-first tests. |
| Paper or shadow operation | OCE-controlled, time-bounded approval; restart/reconciliation and pause/failure behavior are proven; no live route exists. |
| Dashboard status | The UI reads canonical evidence and labels fixture/simulated/unverified states plainly. |

## 7. Assumptions That Are Never Safe

- A present library, route, test, or dashboard widget means operational capability.
- Free/current market data is valid for historical, point-in-time backtesting.
- Adjusted prices, ticker symbols, or a modern constituent list establish historical truth.
- A model response is cited, current, unbiased, or safe because it sounds confident.
- A ranking score is an entry signal or capital recommendation.
- OpenBB Pro/Workspace replaces the existing OCE governance boundary.
- A passing backtest is a qualified strategy.
- Paper mode makes authorization, reconciliation, or incident controls unnecessary.
- A repository-wide test count proves the active part passed.
- A planning document, merged PR, or successful push changes execution authority.

Unknown, absent, blocked, skipped, failed, and simulated states remain explicit. Never coerce them into success.

## 8. Failure and Scope Rules

Stop, preserve evidence, and report a blocker when:

- an original FORGE book and OBB book disagree;
- an upstream artifact or fingerprint is missing, stale, or contradictory;
- a dependency is unavailable and the test cannot be meaningful;
- a change would install a provider/broker dependency, alter a legacy trading engine, or introduce routing outside the admitted part;
- raw credential/account data would enter a log, manifest, artifact, or commit;
- a model/provider result cannot be attributed or its time semantics are ambiguous;
- a requested action would expand capital, autonomy, paper, shadow, sandbox, broker-writing, or live authority.

Do not “solve” a blocker by relabeling the capability, weakening a test, deleting evidence, or skipping the parent phase.

## 9. Exact Next Engineering Sequence

The next engineering sequence is defined by the original program and detailed in the [Implementation Crosswalk](IMPLEMENTATION-CROSSWALK.md):

1. Reproduce and independently review Phase 0 Book 1 Part 1.
2. Resolve the Part 2 admission dependency explicitly: Part 2 calls for verified Part 1 inputs while the current Part 1 state is **implemented_unverified**.
3. Only then admit the bounded Phase 0 Book 1 Part 2 census of trading files, dependency manifests, and data/result metadata.
4. Continue Parts 3 and 4; use their merged inventory to fulfill the OBB-01 Book 1 audit rather than creating a duplicate implementation.
5. Do not begin OBB-02 runtime/provider work until the actual OBB-01 lock criteria are met.

## 10. Final Program Goal

A mature system can trace an operator-authorized research question from source lineage through point-in-time discovery, cited research, StrategySpec, genuine validation, calculated qualification, governed paper/shadow operation, and reconciled portfolio state.

The OBB-04 end state is **production-ready-not-authorized**, not live:

~~~yaml
production_capital_grant: null
standing_capital_allocation: none
active_autonomy_lease: null
reusable_execution_permit: null
production_routing: disabled
live_authorization: false
~~~

No later implementation, dashboard, model, or external integration may weaken these boundaries without a separately approved architecture and authority change.
