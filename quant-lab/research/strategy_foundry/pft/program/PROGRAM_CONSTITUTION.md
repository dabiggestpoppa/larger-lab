# PFT — Program Constitution

Status: RATIFIED (PFT-B0-PROGRAM-CONSTITUTION)
Branch: `agent/deepers-strategy-foundry`
Base: `main@9f61288679eea56a298e08f718c314f2ca509bc5`
Prior head: `225393631406200909cda8106f09edb2e456fee1`

## 1. Scope of this document

This constitution establishes immutable scientific governance for the
PFT (Petro-Flow Triad) program **before** any experiment exists. It binds
all later checkpoints (B1-B15 and any repairs).

The current build authorizes **B0 through B3 only** (pre-economic
infrastructure). Nothing here authorizes economic testing, optimization,
confirmation, holdout, shadow, demo, live execution, production capital,
Kelly sizing, or portfolio allocation.

## 2. Species

Four species are registered (see `SPEC_REGISTER.json`):

| Species | Status | Meaning |
|---|---|---|
| `PFT-A0-GENESIS` | SPECIMEN_REGISTERED | Original agent formulation; preserved as historical raw specimen |
| `PFT-A1-DEEPERS` | FROZEN_PRIMARY_RAW_SPEC | Deepers Specification Closure v2.2; the primary RAW model |
| `PFT-Q0-TRANSMISSION` | SPECIMEN_REGISTERED | Independent Quant Box transmission-deficit / self-resolution model |
| `PFT-X1-SYNTHESIS` | NOT_AUTHORIZED | Hybrid synthesis; prohibited until attribution, falsification and validation |

No lane is predesignated winner.

## 3. Evidence classes

- **RAW** — literal submitted strategy/model. Never overwritten.
- **TWIN** — separately registered, mathematically consistent alternative.
- **ABLATION** — one component removed or isolated to measure contribution.

RAW and TWIN namespaces are physically isolated. RAW never silently
becomes a TWIN and vice versa.

## 4. Core research law

1. Freeze specification before economic PnL.
2. Same data + same spec + same code + same cost/execution generation
   reproduces the same result.
3. Mechanism before performance.
4. Falsification before promotion.
5. Simple baselines compete with complex mathematics.
6. No post-result threshold repair inside a RAW generation.
7. Risk overlays cannot create alpha; alpha and risk are evaluated separately.
8. Confirmation and holdout are locked until explicit authorization.
9. Every major checkpoint ends with human review.
10. No live deployment, leverage authorization, Kelly sizing or production
    capital from Strategy Foundry.

## 5. Experiment identity

Every experiment receives a permanent immutable ID:

    PFT-<SPECIES>-<SCOPE>-<CLASS>-<NNN>

Examples: `PFT-A1-K1-RAW-001`, `PFT-A1-FULL-RAW-001`, `PFT-Q0-BASE-001`.

An experiment identity fingerprints at minimum: spec generation, data
generation, engine generation, cost generation, execution generation,
parameters, random seed where applicable, and code commit SHA.

Same fingerprint => reproducible rerun. Changed fingerprint => new
experiment generation (see `EXPERIMENT_REGISTRY.json`).

## 6. Generation system

Identifiers: `PFT-<KIND>-GEN-<NNN>` with kind in
{SPEC, DATA, ENGINE, COST, EXEC}. Every artifact carries its generations.
A material change creates a new generation with a parent link. Completed
runs are immutable; bugged runs are invalidated, never deleted.

## 7. Parameter classification

Every parameter is classified (see `PARAMETER_REGISTER.json`):

- `AUTHOR_CONSTANT` — supplied by model author; frozen for RAW.
- `RESEARCH_CONSTANT` — preregistered by the lab before PnL.
- `DATA_DERIVED` — estimated causally from allowed development information.
- `TWIN_PARAMETER` — belongs to a separately registered twin.
- `FORBIDDEN_OPTIMIZATION` — chosen because historical PnL improved.

RAW implementations may reference only AUTHOR_CONSTANT and
RESEARCH_CONSTANT. AUTHOR_CONSTANT values are frozen; mutation is refused
by the governance layer.

## 8. Truth states

`HYPOTHESIS -> MECHANISM_OBSERVED -> DESCRIPTIVE_STRUCTURE ->
DEVELOPMENT_VALIDATED -> CONFIRMATION_VALIDATED -> HOLDOUT_VALIDATED ->
FORWARD_VALIDATED`

No automatic promotion. Language must match state; a "validated" claim
requires the corresponding evidence class.

## 9. Data partitions

- `DEVELOPMENT` — open to research (tentative 2020-2024, frozen at B2 on
  objective data-availability grounds only).
- `CONFIRMATION` — locked (tentative 2025) until explicit authorization.
- `HOLDOUT` — locked (tentative 2026+) until explicit authorization;
  one-use principle.
- `METADATA_ONLY` — always safe (file existence, coverage, integrity).

The partition guard fails CLOSED: unknown partition classes are treated
as protected. Every research-relevant access is recorded in
`DATA_USAGE_LEDGER.json`; blocked accesses are recorded with
`authorized=false` before the guard raises.

## 10. Fail-closed behavior

When a required mathematical condition cannot be computed safely the
affected kernel is marked invalid with a reason code and disabled for
that observation. Algorithms are never silently substituted (e.g. no
pseudoinverse/ridge for the literal K3 OLS inverse). Alternative solvers
belong to TWIN experiments.

## 11. Authority

`AUTHORITY.json` is deny-by-default. At B0:

    economic_testing_authorized   = false
    optimization_authorized       = false
    confirmation_authorized       = false
    holdout_authorized            = false
    deployment_authorized         = false
    production_capital_authorized = false
    next_checkpoint_authorized    = false

## 12. Freeze of Deepers v2.2

`PFT-A1-DEEPERS` specification v2.2 is FROZEN. This prompt does not
authorize changing its economic or mathematical rules, and no agent may
create v2.3. Any discovered contradiction is reported via
`SPEC_BLOCKER.md`; the build stops before economic testing.
