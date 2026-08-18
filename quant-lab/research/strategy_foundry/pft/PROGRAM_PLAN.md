# PFT — Petro-Flow Triad Official Program Plan

Status: APPROVED PLAN / PRE-ECONOMIC BUILD
Branch: `agent/deepers-strategy-foundry`
Base: `main@9f61288679eea56a298e08f718c314f2ca509bc5`
Current research truth state: `HYPOTHESIS`

## Mission

Test whether an oil-driven cross-asset transmission system contains genuine repeatable alpha across Brent, EUR/CAD and European equity risk, while determining which mathematical components contribute information versus merely describe the sample.

## Frozen Species

- `PFT-A0-GENESIS`: original agent formulation. Historical lineage preserved intact.
- `PFT-A1-DEEPERS`: final Deepers Specification Closure v2.2. This is the primary RAW submitted model.
- `PFT-Q0-TRANSMISSION`: independent Quant Box transmission-deficit / self-resolution model.
- `PFT-X1-SYNTHESIS`: not authorized. May be built only after A0/A1/Q0 attribution, falsification and validation.

No lane is predesignated winner.

## Evidence Classes

- RAW: faithful implementation of the submitted formula/rule.
- TWIN: separately registered mathematically consistent or alternative interpretation.
- ABLATION: one component isolated/removed/substituted to measure contribution.

RAW results are never overwritten by TWIN results.

## Core Research Law

1. Freeze specification before economic PnL.
2. Same data + same spec + same code + same cost/execution generation must reproduce the same result.
3. Mechanism before performance.
4. Falsification before promotion.
5. Simple baselines compete with complex mathematics.
6. No post-result threshold repair inside a RAW generation.
7. Risk overlays cannot create alpha; alpha and risk are evaluated separately.
8. Confirmation and holdout are locked until explicit authorization.
9. Every major checkpoint ends with human review.
10. No live deployment, leverage authorization, Kelly sizing or production capital from Strategy Foundry.

## Research Lifecycle

`HYPOTHESIS -> MECHANISM_OBSERVED -> DESCRIPTIVE_STRUCTURE -> DEVELOPMENT_VALIDATED -> CONFIRMATION_VALIDATED -> HOLDOUT_VALIDATED -> FORWARD_VALIDATED`

## Program Checkpoints

- `PFT-B0-PROGRAM-CONSTITUTION`
- `PFT-B1-SPECIFICATION-SEAL`
- `PFT-B2-DATA-TRUTH-SEAL`
- `PFT-B3-MATH-CAUSALITY-SEAL`
- `PFT-B4-A0-GENESIS-RAW`
- `PFT-B5-A1-ATOMIC-EVIDENCE`
- `PFT-B6-A1-FULL-STACK`
- `PFT-B7-Q0-TRANSMISSION`
- `PFT-B8-ATTRIBUTION-SEAL`
- `PFT-B9-CONSISTENCY-TWINS`
- `PFT-B10-FALSIFICATION-SEAL`
- `PFT-B11-ROBUSTNESS-SEAL`
- `PFT-B12-CONFIRMATION`
- `PFT-B13-HOLDOUT`
- `PFT-B14-SYNTHESIS`
- `PFT-B15-FORWARD-EXECUTION`
- then Capital Routing if independently earned.

## Tentative Data Split

Subject only to B2 common-coverage truth:

- Development: 2020-01-01 through 2024-12-31
- Confirmation: 2025-01-01 through 2025-12-31
- Holdout: 2026+

Dates may change only because of data coverage, never because of PnL.

## Planned Research Layout

```text
quant-lab/
  research/strategy_foundry/pft/
    program/
    shared/
      data_truth/
      time_alignment/
      execution_contract/
      cost_models/
      statistical_protocol/
      null_models/
    a0_genesis/
    a1_deepers_v2/
    q0_transmission/
    comparative/
    synthesis/
  src/strategy_foundry/pft/
  tests/strategy_foundry/pft/
  scripts/strategy_foundry/pft/
```

## Program Controls

Every result must carry:

- `spec_gen`
- `data_gen`
- `engine_gen`
- `cost_gen`
- `exec_gen`
- code/commit hash
- deterministic seed when applicable

Any material change creates a new generation. Completed runs remain immutable; bugged runs are invalidated, not deleted.

## Parameter Classes

- AUTHOR_CONSTANT: supplied by model author; frozen for RAW.
- RESEARCH_CONSTANT: preregistered by the lab before PnL.
- DATA_DERIVED: estimated causally from allowed development information.
- TWIN_PARAMETER: belongs to a separately registered twin.
- FORBIDDEN_OPTIMIZATION: chosen because historical PnL improved.

## Standard Artifacts

As applicable:

- `PROTOCOL.md`
- `THESIS.md`
- `INPUT_HASH_MANIFEST.json`
- `DATA_AUDIT.md`
- `DATA_MANIFEST.json`
- `EXPERIMENT_MANIFEST.json`
- `CAUSALITY_AUDIT.json`
- `ACTIVATION_CENSUS.csv`
- `EVENT_LEDGER.parquet`
- `SCORECARD.csv`
- `ROBUSTNESS.csv`
- `COMPONENT_STATUS.json`
- `REPORT.md`
- `DECISION.json`
- `NEXT_PLAN.md`

Long runs also use `PROGRESS.json`, `RUN_STATE.json` and checkpoint state.

## Promotion Rule

A candidate cannot advance merely because development PF/Sharpe/DD looks attractive. It must establish a mechanism, causal implementation, cost-aware edge, robustness, non-concentration and then survive frozen confirmation and operator-authorized holdout.

## Current State

```text
program_id                 = PFT
program_version            = 1.0
research_state             = HYPOTHESIS
A0_GENESIS                 = SPECIMEN_REGISTERED
A1_DEEPERS_V2_2            = FROZEN_PRIMARY_RAW_SPEC
Q0_TRANSMISSION            = SPECIMEN_REGISTERED
X1_SYNTHESIS               = NOT_AUTHORIZED
current_checkpoint         = PRE-B0
spec_open_items_A1         = 0
economic_testing           = NOT_STARTED
parameter_optimization     = NOT_AUTHORIZED
confirmation_consumed      = false
holdout_consumed           = false
live_deployment            = false
production_capital         = false
human_review_required      = true
next_checkpoint_authorized = false
```
