# Trading Sector — Master Build & Launch Plan

**Document ID:** TS-PLAN-001  
**Version:** 0.1  
**Date:** 2026-09-14  
**Branch:** `agent/trading-sector-hermes-program`  
**Status:** IMPLEMENTATION / COMMERCIAL-LAUNCH PLAN

---

## 1. End State

Trading Sector becomes a Hermes-operated commercial vertical that can:

1. discover/receive trading-engineering demand;
2. qualify jobs against capability, economics and risk;
3. scope messy trader requests into deterministic specifications;
4. quote/package work consistently;
5. orchestrate Pine/Python/research specialists;
6. validate output independently;
7. deliver professional code + evidence;
8. manage revisions and client continuity;
9. learn pricing/demand/capability lessons without leaking client IP;
10. escalate missing capability through QCAE;
11. turn repeat work into retainers/high-ticket research infrastructure.

Primary launch markets:
- Upwork;
- Fiverr;
- direct referrals/clients;
- later trading-aligned opportunities from the broader Opportunity Exchange.

---

## 2. Program Architecture

```text
                   OPERATOR
                      │
                      ▼
               TRADING HERMES
                      │
      ┌───────────────┼─────────────────┐
      │               │                 │
 MARKET/CLIENT      CONTROL          DELIVERY
      │               │                 │
 Upwork/Fiverr    Job State        Pine Engineer
 Direct/OX        Scope/Price      Python Quant
                  Authority        Researcher
                  Client State     Translator
                                   Validator
      │               │                 │
      └───────────────┼─────────────────┘
                      ▼
                 QA + EVIDENCE
                      ▼
                   CLIENT
                      ▼
             ECONOMIC EXPERIENCE
                      ▼
      QCAE / Quant Lab / Institution
```

---

## 3. Build Blocks

## TS-B0 — Reality Lock / Capability Proof

**Goal:** prove what exists before building commercial wrappers.

Required actions:
- inspect `main` trading/Quant Lab assets;
- inspect `cerebus-mve-implementation`;
- inspect current Crypto Foundry / Sensor Fabric branches;
- inspect current OCE Opportunity Exchange branch;
- inspect Grant Sector architecture for reusable Hermes patterns;
- create artifact/capability manifest with commit/blob references;
- classify `PROVEN`, `PROVEN_WITH_ADAPTATION`, `PILOT`, `DECLINE`;
- create reject/do-not-port ledger;
- identify proprietary internal artifacts that must never become portfolio content.

Exit gate:
- no package claims capability without evidence reference;
- no known duplicate subsystem scheduled for rebuild.

---

## TS-B1 — Commercial Product Constitution

**Goal:** freeze what Trading Sector sells and refuses.

Required artifacts:
- service/package registry;
- pricing floors;
- supported stack;
- explicit MT5/MQL default exclusion;
- NinjaTrader pilot rule;
- research-claims policy;
- client IP policy;
- internal proprietary IP firewall;
- revision/scope-change semantics;
- refund/cancellation policy aligned to platforms;
- legal/tax/business fields left as operator-configurable.

Exit gate:
- every opportunity can map to a package, custom-scope path, or decline reason.

---

## TS-B2 — Portfolio & Proof Pack

**Goal:** show capability without leaking proprietary alpha.

Create 5 sanitized proof pieces:

### Demo 1 — Pine Advanced Indicator

Show:
- MTF/session/state logic;
- dashboard/alerts;
- polished inputs;
- non-repaint discipline.

Use synthetic/generic rules, not proprietary CEREBUS thresholds.

### Demo 2 — Pine → Python Equivalence

Show:
- source Pine logic;
- Python translation;
- common fixtures;
- signal comparison;
- mismatch report.

### Demo 3 — Strategy Validation Report

Use a public/simple strategy and demonstrate:
- baseline;
- OOS/walk-forward;
- costs;
- parameter stability;
- regime slices;
- failure findings.

The value is methodology, not impressive returns.

### Demo 4 — Broken Backtest Audit

Intentionally construct or use a safe historical example with:
- lookahead/repaint/timing/fill issue;
- diagnosis;
- repair;
- before/after result.

### Demo 5 — Quant Research Sprint

Public/synthetic research question showing:
- hypothesis;
- provenance;
- states/conditional analysis;
- bootstrap/null model;
- conclusion that may reject the thesis.

Exit gate:
- each demo has code or reproducible artifact;
- client-facing screenshots/summary;
- no internal proprietary edge exposure.

---

## TS-B3 — Client Intake & Job Contract

**Goal:** prevent vague client messages from reaching builders directly.

Build:
- `TradingOpportunity` schema;
- `TradingJobSpec` schema;
- client intake questionnaire by package;
- ambiguity ledger;
- acceptance criteria template;
- asset/timeframe/timezone semantics;
- data rights/source fields;
- platform/source/target fields;
- deliverables and explicit non-goals;
- price/revision state.

State machine:

```text
DISCOVERED
→ QUALIFIED
→ SCOPING
→ READY_TO_PROPOSE
→ PROPOSED
→ WON | LOST | EXPIRED
→ ACTIVE
→ QA
→ DELIVERED
→ REVISION | ACCEPTED | DISPUTED
→ CLOSED
```

Exit gate:
- builders consume only normalized `TradingJobSpec` objects.

---

## TS-B4 — Market Operations

### Upwork lane

Implement operator-assisted workflow around current official/allowed interfaces:
- search filters;
- saved search strategy;
- opportunity normalization;
- Connects/proposal-cost tracking;
- proposal drafting;
- proposal approval gate;
- interview tracking;
- offer/contract normalization;
- milestone/work submission tracking.

No unauthorized bot/scrape fallback.

### Fiverr lane

Implement:
- 3–4 initial Gigs from package catalog;
- profile/service portfolio;
- inbound brief normalization;
- message triage;
- custom offer builder;
- order/job state mapping;
- review/upsell closeout.

No unauthorized scraping/automation.

### Opportunity Exchange lane

Later consume normalized trading-aligned opportunities from:
- agent-native task markets;
- direct clients;
- other approved sources.

Exit gate:
- Hermes can produce a daily shortlist with package, expected margin, capability fit and proposal draft.

---

## TS-B5 — Delivery Engines

Build reusable client-safe delivery kernels.

### Pine kernel
- project skeleton;
- input conventions;
- session/timezone helpers;
- non-repaint checklist;
- fixture/screenshots;
- lint/compile/manual validation path.

### Python research kernel
- data adapters;
- normalized OHLCV contract;
- time/session handling;
- strategy interface;
- backtest runner;
- configurable costs;
- metrics;
- plots;
- artifact manifest.

### Translation kernel
- semantic mapping document;
- fixture generator;
- source/target output comparator;
- tolerance policy;
- equivalence receipt.

### Audit kernel
- issue reproduction;
- time/data/logic checks;
- suspicious-result detectors;
- before/after regression packet.

Exit gate:
- each core package can be delivered without reinventing workspace structure.

---

## TS-B6 — Research / QA Constitution

Adopt proven Quant Lab / Crypto Foundry discipline proportionate to client scope.

Required quality dimensions:
- reproducibility;
- data provenance;
- leakage/lookahead;
- transaction cost realism;
- sample sufficiency;
- parameter fragility;
- regime dependence;
- multiple testing where applicable;
- acceptance-test coverage;
- claim calibration.

Define research depth classes:

### R1 — ENGINEERING CHECK
Functional correctness only.

### R2 — BASELINE BACKTEST
Deterministic historical test + basic costs/metrics.

### R3 — ROBUSTNESS
OOS/walk-forward/stability/regime/cost sensitivity.

### R4 — RESEARCH GRADE
Preregistered hypotheses where useful, falsification/nulls/bootstrap/FDR/provenance.

Package price determines promised research depth.

Exit gate:
- Hermes cannot sell R4 methodology at R1 price.

---

## TS-B7 — QCAE Capability Extension

Initial required QCAE tasks:

1. qualify NinjaTrader/NinjaScript development path;
2. identify best local/testable compilation workflow;
3. build minimal translation fixture harness;
4. register reusable Pine/Python components;
5. duplicate-capability scan before adding libraries;
6. qualify any new data source before client reliance.

MT5 remains out of scope unless operator explicitly reopens it.

Exit gate:
- Ninja target can be priced from measured acquisition burden or remains unavailable.

---

## TS-B8 — Pilot Batch: First 5–10 Paid Jobs

Purpose: collect reality before aggressive automation.

Portfolio allocation target:
- 2–3 Pine builds/repairs;
- 1–2 strategy conversions;
- 1–2 Python backtest/validation jobs;
- 1 audit/forensic job;
- optional 1 research sprint or translation job.

For every job record:
- acquisition channel;
- impressions/proposals if known;
- proposal cost;
- quote;
- realized revenue;
- platform fees;
- human/compute/tool burden;
- QA defects;
- revision burden;
- client acceptance/rating;
- upsell;
- reusable capability;
- pricing error.

Operator reviews every delivery during pilot.

Exit gate:
- enough evidence exists to compute rough package-level margin and revision profiles.

---

## TS-B9 — Pricing / Market Recalibration

After pilot batch:

Re-evaluate:
- `$150` floor;
- package ranges;
- which Fiverr Gigs convert;
- Upwork proposal win rate;
- Connects spent per win;
- source quality;
- actual labor burden;
- revision-heavy client patterns;
- best upsells;
- Ninja economics.

Possible actions:
- raise floor;
- drop low-margin package;
- narrow Gig;
- create specialized service;
- increase deposit/milestone size;
- favor direct/retainer clients;
- move high-demand capability into QCAE roadmap.

Do not lower prices automatically after losses. Determine whether the problem is price, targeting, proof, proposal quality or scope.

---

## TS-B10 — Retainers & High-Ticket Expansion

Only after delivery baseline is proven.

Build:
- monthly research retainer;
- ongoing indicator/strategy engineering retainer;
- research infrastructure discovery engagement;
- multi-stage quant-system project;
- direct-client case study flow;
- referral workflow.

Target trajectory:

```text
$150–$300 quick proof
        ↓
$400–$1,200 core work
        ↓
$900–$2,000 research sprint
        ↓
$1,500–$5,000+ infrastructure/system
        ↓
recurring retainer
```

---

## 4. Launch Sequence

Recommended order:

```text
B0 reality lock
→ B1 constitution/packages
→ B2 portfolio
→ B3 intake contracts
→ B5 reusable delivery kernels
→ B6 QA rules
→ B4 marketplace setup
→ B8 paid pilot
→ B9 recalibrate
→ B7/B10 capability + high-ticket expansion as demand justifies
```

B7 can run opportunistically when a real high-value job exposes a gap.

---

## 5. No-Rebuild Rule

Before implementing any trading feature or commercial workflow:

1. search `main`;
2. search relevant current trading/Quant Lab files;
3. inspect CEREBUS branch when state/research logic is relevant;
4. inspect Crypto Foundry/Sensor Fabric when data/provenance/research infrastructure is relevant;
5. inspect Grant Sector when agent/business workflow is relevant;
6. inspect OCE/Institution when authority/economic-learning is relevant;
7. use QCAE if capability still appears missing.

Document why reuse was rejected before building a competing component.

---

## 6. Definition of Launch-Ready

Trading Sector is launch-ready when:

- package registry is active;
- portfolio has at least 3 strong sanitized examples;
- intake/spec templates exist;
- Upwork profile/proposal assets are prepared;
- Fiverr has at least 3 productized offerings prepared;
- client-safe workspace pattern exists;
- Pine and Python QA checklists exist;
- job closeout/economic record exists;
- operator can review one concise Hermes daily report;
- first-job delivery does not require exposing CEREBUS proprietary IP.

Full OCE automation is not required for launch.
