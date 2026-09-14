# Trading Sector — R0 Charter

**Document ID:** TS-R0-CTX-001  
**Version:** 0.1  
**Status:** ACTIVE PLANNING BASELINE  
**Branch:** `agent/trading-sector-hermes-program`  
**Parent:** OCE Opportunity Exchange / Institution branch  
**Date:** 2026-09-14

---

## 0. Purpose

Trading Sector is the first specialized commercial vertical built on the OCE Opportunity Exchange specifically for quantitative/trading engineering work.

It is **not** a cheap Pine-script shop, signal-selling business, managed-account service, or promise-of-profit operation.

It is a governed **Trading Research + Strategy Engineering + Indicator Production System** operated by Hermes and backed by existing Larger Lab / Quant Lab / CEREBUS / Crypto Foundry capabilities.

The immediate commercial objective is to dominate the upper low-end and middle market, with a practical starting floor around **$150 per accepted position/project** unless the work is exceptionally trivial and strategically useful.

The long-run objective is to graduate into high-ticket research, validation, strategy infrastructure, and custom quantitative systems without pretending that every client idea has edge.

Canonical positioning:

> **Bring the trading idea, indicator, rules, or broken system. We formalize it, test it, build it, and return code plus evidence.**

---

## 1. Strategic Market Position

Trading Sector targets three bands:

### Band A — Fast-entry / upper low-end

Typical ticket: `$150–$350`

Purpose:
- build reputation;
- generate quick wins;
- acquire client feedback;
- surface repeatable demand;
- feed better clients into larger packages.

Allowed work:
- simple custom Pine indicators;
- Pine bug fixes/refactors;
- alert logic;
- strategy conversion where rules are already precise;
- small Python research utilities;
- bounded indicator translation.

### Band B — Core middle market

Typical ticket: `$350–$1,500`

This is the primary launch target.

Work includes:
- discretionary idea → deterministic specification → implementation;
- Pine strategy/indicator engineering;
- Python strategy backtesting;
- validation/robustness studies;
- indicator/strategy audits;
- Pine ↔ Python translation;
- Python → NinjaTrader translation/implementation when scope is clear;
- data cleaning + research pipeline work;
- strategy diagnostics and repair.

### Band C — High-ticket

Typical ticket: `$1,500–$5,000+`

Selective initially.

Work includes:
- custom quant research systems;
- multi-stage research + implementation engagements;
- trading analytics infrastructure;
- strategy research engines;
- production-grade data/backtest pipelines;
- multi-asset studies;
- ongoing research retainers;
- complex system architecture.

The system should actively cultivate Band C relationships while harvesting Band B consistently.

---

## 2. Technology Scope

### Core supported

- Python
- Pine Script / TradingView
- CSV / Parquet / DuckDB style research flows
- VectorBT-style analysis
- custom Python backtests
- statistical research
- strategy specification
- NinjaTrader translation/implementation when bounded and economically justified

### Secondary / opportunistic

- broker-neutral API/data integration
- webhook/interface design
- notebooks/reports/dashboards
- external trading frameworks that QCAE can qualify economically

### Explicit non-core

- MT5 / MQL5 development
- EA maintenance
- broker-specific MT5 debugging
- MetaTrader synchronization work

MT5 work is **declined by default** unless the operator explicitly changes policy for a specific high-value case.

Reason: it is outside the preferred technical stack, carries high maintenance/translation burden, and competes for time better spent on Python/Pine/quant work.

---

## 3. Product Doctrine

Trading Sector sells **engineering and evidence**, not outcomes it cannot guarantee.

Never promise:
- profitability;
- win rate;
- future returns;
- funded-account passing;
- investment performance;
- a strategy that cannot lose.

Permitted promises are concrete deliverables:
- code that matches the agreed specification;
- a reproducible backtest under stated assumptions;
- identified bugs/failure modes;
- documented parameters;
- defined validation methods;
- research findings with uncertainty;
- translation between supported environments;
- bounded revision support.

Client acceptance is not evidence of alpha.

---

## 4. Existing-System Relationship

Canonical ownership:

```text
Opportunity Exchange → discovers and qualifies client opportunities
Hermes              → relationship + commercial operator
OCE                 → governs objectives, authority, state, delivery
Research Mesh       → external/domain knowledge acquisition when needed
Quant Lab           → trading research / empirical testing substrate
CEREBUS branches    → evidence of advanced state/structure research capability
Crypto Foundry      → evidence of provenance, mechanism, falsification and sensor capability
QCAE                → acquire/qualify missing engineering capability
Institution         → experience filtering / validated evolution
```

Trading Sector shall **reuse** these systems. It shall not clone them into a separate monolith.

---

## 5. Hermes Role

Hermes operates Trading Sector similarly to Grant Sector: the agent is an operator of a governed product, not the product itself.

Hermes responsibilities:
- scan/receive trading opportunities;
- classify service/package fit;
- collect missing client requirements;
- estimate effort and risk;
- prepare proposal/draft response;
- maintain job state;
- route research/build work to specialist tools/agents;
- enforce QA gates;
- assemble delivery packets;
- handle bounded revision loops;
- record economic experience;
- surface reusable capability/market lessons.

Hermes must not:
- invent performance claims;
- sell proprietary internal strategies unless separately authorized;
- leak CEREBUS/Quant Lab proprietary IP;
- silently reuse client-confidential logic across clients;
- accept MT5 work by default;
- bid below pricing floors merely to win work;
- turn every client request into a new framework.

---

## 6. Client / Internal IP Boundary

Internal research capabilities may be used to solve client work, but internal proprietary strategy logic is not automatically a client deliverable.

Three classes:

### `CLIENT_OWNED_INPUT`
Client code, strategy logic, datasets and private documents. Isolated to the job.

### `GENERAL_CAPABILITY`
Generic parsers, test harnesses, backtest utilities, plotting, validation methods, translation patterns. May become reusable after rights/privacy review.

### `INTERNAL_PROPRIETARY_RESEARCH`
CEREBUS doctrine, unpublished strategy edges, proprietary thresholds, internal trading rules and other protected research. Not exposed without explicit operator approval.

---

## 7. Initial Commercial Objective

Initial target:

1. establish 3–5 high-confidence package families;
2. acquire first 5–10 paid trading-engineering jobs;
3. maintain average project value above `$150`;
4. bias toward `$300–$1,000` work where current capability is strong;
5. use small jobs only when delivery is truly cheap or strategically useful;
6. convert good buyers into larger validation/research/maintenance engagements;
7. collect real conversion, revision, effort and margin data before changing pricing aggressively.

The objective is not maximum job count.

The objective is **profitable proof of competence + compounding reusable capability**.

---

## 8. Launch Invariants

1. Python-first.
2. Pine is a supported front-end/product surface, not the whole business.
3. NinjaTrader is a translation/implementation option, not a core research environment.
4. MT5/MQL is excluded by default.
5. `$150` is the normal minimum project floor unless operator-approved exception.
6. Research claims remain claims until tested.
7. Client ideas are not presumed profitable.
8. No lookahead/repainting is hidden.
9. Every backtest states data, costs, assumptions and limitations.
10. Every delivery has acceptance criteria.
11. Client-specific knowledge does not automatically become institutional doctrine.
12. High-value reusable capability routes through QCAE/Institution instead of ad-hoc copy/paste.
13. Hermes can recommend a decline.
14. High-ticket work is welcomed when capability/risk gates pass; the system must not artificially cap itself at small jobs.
