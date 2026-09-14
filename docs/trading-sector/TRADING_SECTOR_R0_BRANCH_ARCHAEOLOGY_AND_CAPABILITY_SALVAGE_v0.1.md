# Trading Sector — R0 Branch Archaeology & Capability Salvage Map

**Document ID:** TS-R0-SALVAGE-001  
**Version:** 0.1  
**Date:** 2026-09-14  
**Status:** PLANNING / SOURCE MAP  

---

## 1. Purpose

Before Trading Sector builds new commercial capability, Hermes must inspect and reuse the substantial trading/research work already present across Larger Lab.

This document is a **capability map**, not an instruction to merge branches wholesale.

Canonical rule:

> Salvage capability, methods, contracts, and proven components. Do not blindly merge historical branch state.

---

## 2. Sources Reviewed

### `main`

Primary reusable surfaces observed:

- `quant-lab/strategies/CEREBUS_V5_LIVE_PERFECT_FORM.pine`
- `quant-lab/strategies/p90_cascade_activation.py`
- `quant-lab/backtests/run_cascade_backtest.py`
- `quant-lab/backtests/run_full_backtest.py`
- stored backtest result artifacts
- Quant Lab research/status/findings structure
- `vectorbt-expert` skill/rules including walk-forward, parameter optimization, data loading/resampling and backtest pitfalls
- `quantitative-research` skill covering regime detection, statistical arbitrage, OOS/walk-forward and transaction-cost modeling

### `cerebus-mve-implementation`

Observed advanced reusable research concepts/components:

- 7 volatility estimators;
- 6 structural-anchor calculations;
- volatility-normalized morphic coordinates;
- sigma-state classification/detection;
- occupancy/acceptance logic;
- volatility regime transition model;
- multiple rekey hypotheses;
- five signal models;
- eight backtest/analysis types;
- research runner architecture;
- phased research/validation workflow.

This branch demonstrates that the organization has already built beyond ordinary indicator coding into **state-based market research frameworks**.

### `agent/crypto-quant-foundry` / `agent/crypto-sensor-fabric-build`

Observed reusable research-engineering capability:

- canonical dataset freezing;
- SHA/provenance lineage;
- source truth repair;
- data-vs-execution authority separation;
- multi-venue adapters;
- mechanism anatomy before strategy generation;
- null-model comparisons;
- bootstrap confidence intervals;
- FDR correction;
- state taxonomy and transition matrices;
- survival analysis;
- information/entropy measurements;
- preregistered strategy contracts;
- explicit no-PnL-before-hypothesis-freeze discipline;
- falsification before optimization;
- immutable raw evidence lake;
- source revision/mutation registry;
- provider/parser conformance;
- durable job-state work;
- large automated test surface.

This is directly reusable as **quality doctrine** for client strategy validation and research infrastructure work.

### `grant-sector-g1-production`

Not trading capability, but highly reusable commercial-agent operating architecture:

- branch archaeology before rebuild;
- salvage/reject/gap maps;
- product constitution;
- capability registry;
- role contracts;
- bounded worker context;
- evidence lineage;
- reality locks;
- continuous-execution master prompts;
- client feedback loops;
- explicit approval/authority boundaries;
- system truth outside agent memory.

Trading Sector should reuse this program structure rather than inventing another agent-business architecture.

### `agent/oce-institutional-stress-suite-build`

Commercial/evolution substrate already available:

- Opportunity Exchange;
- source-neutral market adapters;
- Upwork/Fiverr market research;
- normalized opportunities;
- hard gates before scoring;
- exploration/exploitation budgets;
- Economic Experience records;
- Experience → Evolution firewall;
- platform drift handling;
- human-first vs agent-native participation modes.

Trading Sector is a **vertical on this substrate**, not a parallel marketplace system.

---

## 3. Commercial Capability Registry — Initial

### TS-CAP-001 — Pine indicator engineering

**Evidence:** Existing nontrivial CEREBUS Pine implementation.  
**Commercial status:** READY_WITH_REVIEW.  
**Use cases:** indicators, dashboards, sessions, levels, alerts, MTF logic, refactors, non-repaint repair.

### TS-CAP-002 — Pine strategy engineering

**Evidence:** TradingView strategy work and existing strategy logic.  
**Commercial status:** READY_WITH_REVIEW.  
**Use cases:** indicator→strategy conversion, entry/exit logic, risk/target rules, backtestable Pine.

### TS-CAP-003 — Python strategy implementation

**Evidence:** Python strategy modules and research runners.  
**Commercial status:** READY.  
**Use cases:** deterministic strategy logic, data transforms, analytics, custom backtests.

### TS-CAP-004 — Backtest engineering

**Evidence:** full/cascade runners, stored results, Quant Lab workflows.  
**Commercial status:** READY; client-specific assumptions must be stated.  
**Use cases:** historical simulation, diagnostics, scenario comparisons.

### TS-CAP-005 — Robustness / validation

**Evidence:** walk-forward/OOS skill doctrine + Crypto Foundry falsification/null/FDR discipline.  
**Commercial status:** READY_AS_MANAGED_WORKFLOW.  
**Use cases:** OOS, walk-forward, parameter stability, regime slicing, cost sensitivity, null checks, overfit diagnostics.

### TS-CAP-006 — Strategy audit / forensic debugging

**Evidence:** Quant Lab has explicitly identified strategy bugs including inverted stops/targets, loose entries and bad reward/risk structures.  
**Commercial status:** READY.  
**Use cases:** why backtest/live behavior differs, logic inspection, timing bugs, hidden lookahead/repaint, execution assumptions.

### TS-CAP-007 — Discretionary concept formalization

**Evidence:** CEREBUS repeatedly converts market concepts into tiers, states, transition rules and testable contracts.  
**Commercial status:** READY.  
**Use cases:** trader explains setup in natural language/screenshots → deterministic specification → testable implementation.

### TS-CAP-008 — Market-state / regime research

**Evidence:** CEREBUS MVE + Crypto Foundry state taxonomy.  
**Commercial status:** READY_FOR_HIGHER_TICKET.  
**Use cases:** volatility regimes, session state, transition matrices, conditional behavior, state-conditioned performance.

### TS-CAP-009 — Data provenance / research dataset QA

**Evidence:** Crypto Foundry truth repair, frozen datasets, hashes and source authority.  
**Commercial status:** READY_FOR_HIGHER_TICKET.  
**Use cases:** bad data audits, source reconciliation, timestamp/session repair, point-in-time integrity.

### TS-CAP-010 — Quant research infrastructure

**Evidence:** Quant Lab + Sensor Fabric architecture.  
**Commercial status:** SELECTIVE HIGH-TICKET.  
**Use cases:** research pipelines, adapter layers, evidence stores, reproducible experiment runners.

### TS-CAP-011 — Pine ↔ Python translation

**Evidence:** both environments already used internally.  
**Commercial status:** READY_WITH_CONTRACT_TEST.  
**Use cases:** port logic while preserving signals/semantics; compare output on fixture data.

### TS-CAP-012 — NinjaTrader translation

**Evidence:** not yet proven as a mature internal delivery surface.  
**Commercial status:** QCAE_REQUIRED / PILOT.  
**Use cases:** translate a frozen Pine/Python strategy specification to NinjaScript when pricing supports acquisition/validation cost.

### TS-CAP-013 — MT5/MQL5

**Commercial status:** DECLINE_BY_DEFAULT.  
**Reason:** operator preference; maintenance burden; poor stack alignment.  
**Re-entry:** explicit operator exception only.

---

## 4. What We Should NOT Sell Yet As a Standard Package

Do not standardize these until proven through a client pilot or internal benchmark:

- fully autonomous live execution;
- broker-specific execution guarantees;
- HFT/latency-sensitive systems;
- options pricing engines outside existing proof;
- complex NinjaTrader projects before QCAE qualification;
- ML alpha systems with vague requirements;
- portfolio optimization using client capital without a proper contract/risk boundary;
- MT5/MQL5 development.

High-ticket does not mean accept everything expensive.

---

## 5. Internal IP Firewall

Existing proprietary strategies demonstrate capability but are **not portfolio source code**.

Public/client-facing proof should show:

- architecture sophistication;
- methodology;
- sanitized charts/examples;
- generic code excerpts created for demonstration;
- backtest/validation process;
- before/after bug repair examples;
- synthetic or permissioned samples.

Do not expose:

- proprietary CEREBUS thresholds;
- private alpha logic;
- unreleased state mappings;
- client-confidential strategies;
- live account rules.

---

## 6. Gap Map

### Immediate gaps to close before aggressive selling

1. Build 3–5 sanitized portfolio examples.
2. Create canonical client strategy specification template.
3. Create reproducible delivery QA checklist.
4. Create client-data isolation workspace pattern.
5. Create Pine↔Python equivalence test harness.
6. Benchmark one NinjaTrader translation path through QCAE.
7. Create standard report template for validation jobs.
8. Create effort estimator from historical jobs.
9. Create Upwork proposal templates by package family.
10. Create Fiverr Gig/service copy by package family.

### Gaps that do NOT block launch

- full autonomous Opportunity Exchange;
- all agent-native marketplaces;
- perfect NinjaTrader tooling;
- advanced cloud deployment;
- MT5 support.

The launch can begin with human/operator checkpoints and strong existing research capability.

---

## 7. Salvage Rule for Hermes

Before accepting any project that appears to require new capability:

```text
client requirement
→ search Trading Sector capability registry
→ inspect main / relevant branch artifacts
→ reuse proven generic component if lawful
→ if missing, ask QCAE BUILD/BORROW/BUY/RENT
→ cost the acquisition into the bid
→ decline if economics no longer work
```

Hermes must never answer “we need to build that from scratch” before checking the existing system.
