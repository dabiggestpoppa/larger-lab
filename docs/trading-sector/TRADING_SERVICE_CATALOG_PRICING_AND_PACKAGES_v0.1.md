# Trading Sector — Service Catalog, Pricing & Packages

**Document ID:** TS-COMM-001  
**Version:** 0.1  
**Date:** 2026-09-14  
**Status:** LAUNCH PRICING BASELINE — revise only from real conversion/margin evidence

---

## 1. Pricing Doctrine

Trading Sector is not competing to be the cheapest Pine developer.

Commercial objective:

```text
simple + fast + low risk       → upper low-end
research + engineering         → middle market
infrastructure + deep research → high-ticket
```

Default minimum accepted project value: **$150**.

Exceptions below $150 require one of:

- less than ~60 minutes total institutional burden;
- strong review/reputation value;
- direct upsell path already visible;
- strategically valuable capability experiment with explicit EXPLORE budget.

Never discount merely because competitors are cheaper.

Prefer reducing scope instead of reducing rate.

---

## 2. Core Launch Packages

## TS-PKG-01 — Pine Quick Build / Repair

**Target:** `$150–$300`  
**Use:** fast, bounded work.

Examples:
- add/fix alerts;
- add a session/filter;
- repair plotting/state bug;
- small indicator modification;
- convert precise rules into a simple indicator;
- eliminate obvious repaint/lookahead issue;
- Pine v4/v5 → v6 cleanup when bounded.

Includes:
- reviewed specification;
- source code;
- basic functional test;
- short implementation note;
- one bounded revision round.

Reject/upgrade if:
- rules are ambiguous;
- strategy research is required;
- multi-timeframe/state logic becomes complex;
- client wants profitability guarantees.

---

## TS-PKG-02 — Custom TradingView Indicator Pro

**Target:** `$300–$650`  
**Primary launch package.**

Examples:
- custom market-structure indicator;
- multi-timeframe logic;
- session/state overlays;
- dashboards/tables;
- dynamic levels;
- alerts;
- fib/state visual logic;
- deterministic discretionary-setup translation.

Includes:
- requirements/specification artifact;
- Pine implementation;
- parameter/input design;
- non-repaint/lookahead review;
- acceptance fixture/screenshots;
- implementation notes;
- up to two bounded revision rounds.

Premium triggers:
- 3+ timeframes;
- complicated state machines;
- multiple independent setup families;
- heavy UI/table requirements;
- large legacy script refactor.

---

## TS-PKG-03 — Indicator → Strategy / Strategy Engineering

**Target:** `$400–$850`

Examples:
- convert indicator rules into backtestable strategy;
- formalize entries/exits/stops/targets;
- add risk/position logic;
- build long/short rule set;
- turn screenshots/natural-language rules into deterministic logic.

Includes:
- rule specification;
- ambiguity ledger;
- Pine or Python strategy implementation;
- baseline backtest;
- trade/metric sanity checks;
- assumptions/limitations;
- one strategy revision based on specification mismatch.

Does **not** include open-ended parameter mining.

---

## TS-PKG-04 — Python Backtest & Strategy Validation

**Target:** `$500–$1,200`  
**Primary differentiation package.**

Client brings:
- code;
- rules;
- indicator;
- strategy idea;
- data; or
- a TradingView implementation.

Possible analysis:
- deterministic Python reconstruction;
- data integrity checks;
- in-sample / out-of-sample split;
- walk-forward where appropriate;
- cost/slippage sensitivity;
- parameter stability;
- time/day/session slices;
- regime/state slices;
- trade distribution;
- drawdown / PF / expectancy / Sharpe-style metrics where appropriate;
- null/falsification checks;
- failure-mode analysis.

Deliverables:
- reproducible code/notebook/scripts;
- result tables/plots;
- research memo;
- explicit assumptions;
- `PASS / CONDITIONAL / FAIL / INSUFFICIENT_EVIDENCE` style conclusion.

No promise that validation will confirm the client's thesis.

---

## TS-PKG-05 — Strategy Audit / Why Is This Broken?

**Target:** `$350–$900`

For:
- strategy performance mismatch;
- suspicious backtests;
- repaint/lookahead concerns;
- wrong entries/exits;
- timestamp/session mismatch;
- unrealistic fills;
- data errors;
- Pine/Python output mismatch;
- live-vs-backtest logic discrepancies not requiring broker-specific MT5 work.

Includes:
- audit map;
- reproduced issue when possible;
- root-cause findings;
- severity ranking;
- repair recommendations;
- optional patch if within scope.

This package is especially strong because internal Quant Lab history includes real strategy-debugging/falsification workflows rather than only green backtests.

---

## TS-PKG-06 — Pine ↔ Python Translation + Equivalence

**Target:** `$500–$1,200`

Not merely syntax translation.

Workflow:

```text
freeze source behavior/spec
→ map data/time semantics
→ implement target version
→ generate common fixtures
→ compare signals/levels/trades
→ document unavoidable differences
```

Deliverables:
- target source code;
- equivalence report;
- fixture/result comparison;
- known semantic differences.

This can become a strong Fiverr/Upwork niche because many translators do not prove equivalence.

---

## TS-PKG-07 — NinjaTrader Translation Pilot

**Target:** `$750–$1,500+`

Status: **PILOT / QCAE-assisted** until internal capability is qualified.

Accept only when:
- source rules are frozen;
- client accepts translation scope;
- economics cover capability acquisition/testing;
- no complex broker/execution-specific requirements are hidden in the brief.

Deliverables mirror TS-PKG-06 with a NinjaScript target.

Never underbid this while capability is still being qualified.

---

## TS-PKG-08 — Quant Research Sprint

**Target:** `$900–$2,000`

For clients who have a thesis but need serious research before software production.

Examples:
- Does setup behavior change by volatility regime?
- Is a session effect statistically persistent?
- Does signal X have information beyond random/vol-matched controls?
- What states lead/follow a market event?
- Which variants survive OOS/cost assumptions?

Possible methods:
- state taxonomy;
- transition matrices;
- conditional distributions;
- bootstrap CIs;
- null models;
- FDR/multiple-testing control when needed;
- survival/time-to-event analysis;
- regime segmentation;
- preregistered hypothesis testing.

Deliverables:
- research specification;
- data/provenance note;
- reproducible analysis;
- report;
- next-build recommendation.

---

## TS-PKG-09 — Quant Research Infrastructure Build

**Target:** `$1,500–$5,000+`

Selective high-ticket package.

Examples:
- backtest engine/research runner;
- data ingestion + normalized storage;
- experiment registry;
- multi-symbol research pipeline;
- reproducible result artifacts;
- strategy testing framework;
- analytics/reporting layer;
- state/feature research tooling.

Pricing is milestone-based after discovery.

Never quote this from a vague one-paragraph brief.

---

## TS-PKG-10 — Ongoing Research / Engineering Retainer

**Target starting range:** `$750–$2,500+/month`

For repeat clients after a successful first delivery.

Can include:
- bounded monthly strategy research;
- indicator enhancements;
- periodic backtest updates;
- data QA;
- research reports;
- translation/maintenance;
- experiment queue.

Retainer must define capacity, not unlimited requests.

---

## 3. Fiverr Packaging

Fiverr should emphasize productized inbound services.

### Gig A — Custom TradingView / Pine Indicator

- Basic: `$150` — bounded indicator/fix
- Standard: `$300–$400` — custom indicator with alerts/inputs
- Premium: `$550–$700` — advanced MTF/state/dashboard implementation

### Gig B — Backtest & Validate Your Trading Strategy in Python

- Basic: `$300–$400` — deterministic baseline test, limited scope
- Standard: `$650–$850` — robustness/OOS/cost analysis
- Premium: `$1,000–$1,500` — deeper regime/falsification/research report

### Gig C — Convert Pine Strategy to Python and Verify It

- Basic: `$400–$550`
- Standard: `$700–$900`
- Premium: `$1,000–$1,300`

### Gig D — Audit / Fix Your Trading Strategy or Backtest

- Basic: `$200–$300` diagnostic
- Standard: `$450–$650` audit + bounded repair
- Premium: `$800–$1,000` forensic comparison + repair + report

Avoid creating 12 weak gigs at launch. Start with 3–4 that demonstrate the strongest differentiation.

---

## 4. Upwork Positioning

Upwork should be proposal-driven.

Preferred jobs:
- `$150+` fixed-price Pine work;
- `$300+` strategy work;
- `$500+` research/backtest work;
- `$50+/hr` when hourly is genuinely appropriate;
- long-term development roles with clear scope and credible client history.

Proposal rule:

> Lead with the client's exact technical problem, then show that Trading Sector can formalize/test/build it. Do not dump an AI-generated biography.

Strong differentiators to mention selectively:
- Python + Pine, not Pine alone;
- reproducible backtests;
- non-repaint/lookahead review;
- OOS/walk-forward capability;
- strategy debugging;
- market-state/regime research;
- evidence/report delivery.

---

## 5. Add-On Price Guide

Indicative add-ons:

- additional symbol: `$75–$200`
- additional major timeframe family: `$75–$150`
- advanced dashboard/UI: `$100–$300`
- data cleaning/reconciliation: `$150–$500+`
- rush priority: `+25–50%`
- extra revision beyond contract: scoped separately
- research memo upgrade: `$150–$400`
- Pine↔Python equivalence testing: `$200–$500` above simple port
- NinjaTrader target: price via TS-PKG-07, never token add-on pricing

---

## 6. Scope Escalation Rules

Hermes must upgrade or re-quote when any of these appear after intake:

- client changes strategy definition;
- new platform added;
- new asset class added;
- historical data must be sourced/cleaned unexpectedly;
- client asks for optimization after ordering implementation;
- discretionary rules remain ambiguous;
- one indicator turns into a full trading system;
- client asks for live broker automation;
- revision is a new requirement rather than defect correction.

Never absorb unlimited scope to protect a review.

---

## 7. Decline / Refer Rules

Decline by default:

- MT5/MQL5/EA jobs;
- guaranteed-return requests;
- account-management/trade-execution work outside authorized business model;
- copying protected/closed-source indicators without rights;
- decompiling paid indicators;
- malware/credential extraction;
- jobs where the client refuses to define acceptance criteria;
- tiny budgets for complex research;
- massive unpaid competition/spec work.

---

## 8. Launch KPI Targets

For first 10 paid projects, record:

- quoted price;
- accepted price;
- package;
- source;
- proposal cost;
- labor/compute/tool burden;
- turnaround;
- revision count;
- gross margin estimate;
- client rating/acceptance;
- upsell/retainer outcome;
- reusable capability created;
- reasons lost/declined.

Do not optimize pricing from anecdotes. Reprice after the first evidence batch.
