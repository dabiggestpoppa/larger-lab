# Trading Sector

Hermes-operated trading research and software-engineering vertical built on OCE Opportunity Exchange, Quant Lab, Research Mesh and QCAE.

**Branch:** `agent/trading-sector-hermes-program`
**Core stack:** Python + Pine Script; NinjaTrader is a qualified pilot; MT5/MQL5 are outside the default service scope.
**Commercial focus:** normal floor ~$150; concentrate on $300–$1,200 middle-market work with selective deeper research/infrastructure engagements.

## Canonical Reading Order

1. `TRADING_SECTOR_R0_CHARTER_v0.1.md`
2. `TRADING_SECTOR_R0_BRANCH_ARCHAEOLOGY_AND_CAPABILITY_SALVAGE_v0.1.md`
3. `TRADING_SERVICE_CATALOG_PRICING_AND_PACKAGES_v0.1.md`
4. `TRADING_SERVICE_CATALOG_AMENDMENT_A001_IDEA_RESEARCH_OPTIMIZATION_v0.1.md`
5. `TRADING_SERVICE_PACKAGE_REGISTRY_v0.2.json` — current package registry; supersedes v0.1 for routing
6. `TRADING_HERMES_OPERATOR_PROGRAM_v0.1.md`
7. `TRADING_SECTOR_CONTINUOUS_EXECUTION_PROMPT_AMENDMENT_A001_v0.1.md`
8. `TRADING_JOB_SPEC.schema.json`
9. `TRADING_SECTOR_MASTER_BUILD_AND_LAUNCH_PLAN_v0.1.md`
10. `TRADING_SECTOR_CONTINUOUS_EXECUTION_MASTER_PROMPT_v0.1.md`

Hermes must read the master prompt together with Prompt Amendment A001.

## Product Flow

```text
IDEA / MODEL / CODE / EXISTING SYSTEM
                ↓
         deterministic scope
                ↓
     research / feasibility test
                ↓
      ┌─────────┼──────────┐
      ↓         ↓          ↓
    STOP     INDICATOR   SYSTEM MODEL
                \          /
                 VALIDATION
                     ↓
                OPTIMIZATION
                     ↓
              delivery packet
```

The product includes disciplined judgment about whether a concept should become software, remain human-assisted through an indicator, receive deeper research, or stop.

## Current Package Set

| ID | Package | Launch Range |
|---|---|---:|
| TS-PKG-01 | Pine Quick Build / Repair | $150–$300 |
| TS-PKG-02 | Custom TradingView Indicator Pro | $300–$650 |
| TS-PKG-03 | Indicator → Strategy / Strategy Engineering | $400–$850 |
| TS-PKG-04 | Python Backtest & Strategy Validation | $500–$1,200 |
| TS-PKG-05 | Strategy Audit / Forensic Debug | $350–$900 |
| TS-PKG-06 | Pine ↔ Python Translation + Equivalence | $500–$1,200 |
| TS-PKG-07 | NinjaTrader Translation Pilot | $750–$1,500+ |
| TS-PKG-08 | Quant Research Sprint | $900–$2,000 |
| TS-PKG-09 | Quant Research Infrastructure Build | $1,500–$5,000+ |
| TS-PKG-10 | Ongoing Research / Engineering Retainer | $750–$2,500+/month |
| TS-PKG-11 | Idea / Model → Feasibility & System Specification | $350–$900 |
| TS-PKG-12 | Quick Research / Hypothesis Test | $150–$450 |
| TS-PKG-13 | Model Optimization & Robustness | $500–$1,500 |

## A001 Routing Rules

**Idea but no deterministic model:** TS-PKG-11. Outcome can be system specification, decision-support indicator, deeper research, or stop.

**One focused research question:** TS-PKG-12. Keep scope narrow; route larger work to TS-PKG-04 or TS-PKG-08.

**Existing reproducible baseline needing improvement:** TS-PKG-13. Freeze the baseline first; evaluate stability and robustness instead of only selecting a historical maximum.

## Hermes Boot

When Hermes is installed:

1. point it to this branch;
2. provide `TRADING_SECTOR_CONTINUOUS_EXECUTION_MASTER_PROMPT_v0.1.md`;
3. require `TRADING_SECTOR_CONTINUOUS_EXECUTION_PROMPT_AMENDMENT_A001_v0.1.md` immediately afterward;
4. use `TRADING_SERVICE_PACKAGE_REGISTRY_v0.2.json` as current package truth;
5. follow the canonical reading order before implementation or marketplace operation.

## Core Invariants

- reuse before rebuild;
- Python/Pine first;
- separate research scope from implementation scope;
- no optimization before a reproducible baseline exists;
- do not expand quick research into a full study without re-scoping;
- protect internal and client-specific intellectual property;
- preserve evidence, assumptions, and limitations;
- route missing executable capability through QCAE rather than silently rebuilding it.
