# OCE Golden System
## Block 7 — Quant Foundation Planning Dossier

**Document ID:** OCE-B7-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependency:** B6 reusable surfaces and certified domain-adapter pattern  
**Exit gate:** Deterministic, reproducible market-data, research, validation, portfolio, risk, and lineage kernels

## 1. Research basis and block contract

This dossier incorporates the operator-provided Cerebus FX manual, *Trading and Exchanges*, *Market Microstructure Theory*, *Algorithmic Trading and DMA*, *Building Algorithmic Trading Systems*, and *WorldQuant Finding Alphas*. Their reusable lessons are encoded as testable contracts: point-in-time data; explicit market/session/order semantics; realistic explicit, implicit and missed-opportunity costs; partial/non-fills; out-of-sample and walk-forward evaluation; resistance to parameter/data snooping; deterministic risk and position sizing; and doctrine claims separated from independently reproduced evidence.

Block 7 builds no agent-generated live strategy and has no execution authority. Cerebus material enters as versioned strategy doctrine and hypotheses, not unquestioned canonical performance truth.

## 2. Chapter 1 — Market Data Truth

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B7.C1.S1 Instruments | Canonicalize venue, asset, symbol history, contract, quote/base, multiplier, tick, lot, currency and lifecycle. | Instrument/Revision registry | Renames, collisions, rolls and unknown mappings handled deterministically. |
| B7.C1.S2 Time/sessions | Encode timezone, UTC normalization, DST, sessions, holidays, auction/continuous states, latency and event timestamps. | calendar/session service | DST/session-boundary golden tests across markets pass. |
| B7.C1.S3 Dataset manifests | Bind source, retrieval, license, coverage, schema, revision, transforms, hashes and intended use. | DatasetManifest and immutable partitions | Same manifest reproduces bytes or explains source revision. |
| B7.C1.S4 Quality rules | Detect gaps, duplicates, outliers, stale quotes, crossed markets, bad bars, corporate actions and inconsistent granularity. | quality engine/report | No silent repair; raw, normalized and rejected data separable. |
| B7.C1.S5 Point-in-time integrity | Enforce availability time, revision/as-of queries, universe membership and no future leakage. | PIT query contract and leakage tests | Synthetic look-ahead/survivorship mutations are rejected. |

## 3. Chapter 2 — Research Kernel

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B7.C2.S1 Strategy specification | Freeze mechanism, universe, timeframe, signals, filters, entries/exits, sizing, invalidation, assumptions and non-goals. | StrategySpec and registry | Semantics complete before backtest; changes create new revision. |
| B7.C2.S2 Feature contracts | Define inputs, availability, units, windowing, warmup, null handling, transformations and provenance. | FeatureSpec/DAG | Batch/incremental equivalence and leakage tests pass. |
| B7.C2.S3 Genuine engine path | Execute chronological event/order/portfolio simulation through canonical engine; fast filters cannot promote. | engine adapter and RunManifest | Claimed backtest tied to exact engine/version/data/spec. |
| B7.C2.S4 Cost/fill models | Model fees, spread, slippage, impact, latency, queue/priority where supported, partial/non-fill and missed opportunity. | versioned execution-assumption models | Optimistic zero-cost/guaranteed-fill cases are explicit simulations only. |
| B7.C2.S5 Reproducibility | Freeze seeds, environment, data, code, parameters, outputs and nondeterminism limits. | reproducibility harness | Repeated run matches tolerances; divergence blocks promotion. |

## 4. Chapter 3 — Validation Kernel

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B7.C3.S1 Fast falsification | Apply cheap logic, data sufficiency, baseline, sign, cost, sensitivity and impossible-result filters. | falsification suite | Filters only reject/prioritize; never certify profitability. |
| B7.C3.S2 Holdout | Pre-register untouched evaluation interval/universe, access controls and one-way reveal policy. | holdout registry and audit | Repeated peeking/retuning creates new research lineage and penalty. |
| B7.C3.S3 Walk-forward | Define training/test windows, purge/embargo where applicable, refit policy and continuous OOS aggregation. | walk-forward engine/report | Window boundaries and parameter history reconstruct exactly. |
| B7.C3.S4 Stress/sensitivity | Stress costs, latency, fills, data perturbation, parameter neighborhoods, regimes, missing data and execution delay. | robustness cube | Edge dependent on narrow/optimistic assumptions is demoted. |
| B7.C3.S5 Promotion decision | Combine economic rationale, statistical uncertainty, OOS/WF, costs, robustness, capacity, risks and independent review. | PromotionPacket | No single metric/Sharpe/win rate can approve; uncertainty explicit. |

## 5. Chapter 4 — Portfolio and Risk

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B7.C4.S1 Position accounting | Deterministic orders, fills, lots, average cost, realized/unrealized P&L, cash, fees, FX and corporate actions. | accounting ledger and reconciliation | Conservation/property tests and independent calculation match. |
| B7.C4.S2 Exposure | Compute gross/net, asset, currency, venue, strategy, factor, correlation and concentration exposure as-of time. | exposure engine | Units/currency/time consistent; missing prices block or degrade. |
| B7.C4.S3 Sizing | Implement fixed risk, volatility, constraint and strategy-specific sizing as versioned deterministic policies. | sizing engine and policy registry | Bounds, rounding, zero/negative/unknown inputs handled safely. |
| B7.C4.S4 Limits | Encode pre-research/paper limits, drawdown, leverage, concentration, liquidity, loss and data-quality stops. | risk rule engine | Limits are independent of agents and deny on stale/unknown state. |
| B7.C4.S5 Portfolio interactions | Evaluate correlation, crowding, shared tail, turnover, cost, capital allocation and strategy degradation jointly. | portfolio simulation/report | Standalone edge cannot hide harmful combined behavior. |

## 6. Chapter 5 — Lineage Integration

| Section | Contract | Deliverables | Evidence/gate |
|---|---|---|---|
| B7.C5.S1 Cerebus doctrine | Parse Cerebus rules/thresholds/regimes/sizing into traceable specs; distinguish manual claim, reproduced test and amendment. | doctrine registry with source locations | No performance claim promoted without independent reproduction. |
| B7.C5.S2 Capital Routing | Inventory and adapt capital-routing concepts to OCE identity/risk/portfolio contracts without execution enablement. | salvage ADR and interfaces | Duplicate or unsafe routing remains quarantined. |
| B7.C5.S3 TB Forward Engine | Reproduce/compare forward-test semantics, data and outcomes against canonical engine. | compatibility/reproduction report | Mismatch visible; no forced reconciliation. |
| B7.C5.S4 MVE and legacy | Classify legacy engines/strategies as keep/adapt/migrate/quarantine/deprecate with consumers and evidence. | lineage and migration manifests | No legacy claim bypasses canonical validation. |
| B7.C5.S5 Canonical strategy wells | Store registered ideas/specs/runs/evidence/promotion state separately from mutable agent notes. | strategy registry and query API | One strategy lineage traceable end-to-end; permissions isolated. |

## 7. Implementation increments

| Increment | Future scope | Gate |
|---|---|---|
| B7-I0 | Freeze quant schemas, reference sources, truth labels and reproducibility protocol | No live/paper execution authority |
| B7-I1 | C1 instruments, time and manifests | Identity/time/data provenance pass |
| B7-I2 | C1 quality/PIT plus C2 strategy/features | Leakage and revision adversarial pass |
| B7-I3 | C2 genuine engine, costs/fills and reproducibility | Repeated realistic run verified |
| B7-I4 | C3 falsification, holdout and walk-forward | OOS protocol and anti-peeking enforcement pass |
| B7-I5 | C3 stress/promotion plus C4 accounting/exposure | Robustness and ledger reconciliation pass |
| B7-I6 | C4 sizing/limits/interactions | Deterministic independent risk denial pass |
| B7-I7 | C5 Cerebus/legacy/strategy-well lineage | Claims classified and one doctrine reproduction complete |
| B7-I8 | Independent statistical, microstructure, leakage, cost and evidence audit | Zero critical realism/reproducibility bypass |
| B7-I9 | Quant foundation gate and B8 dependency contract | Operator-only completion; execution remains locked |

## 8. Mandatory negative evidence

Tests must reject future leakage, revised-data leakage, survivorship bias, symbol/timezone mismatch, deterministic-bar guaranteed fills, omitted costs, impossible turnover/capacity, narrow parameter optimum, repeated holdout reuse, incomplete accounting, agent-overridden limits, and untraceable Cerebus claims.

## 9. Non-goals

No signal mining fleet, research UI, continuous Quant Watch, broker connection, paper orders, shadow execution, live capital, or claim that historical manual results are independently verified.
