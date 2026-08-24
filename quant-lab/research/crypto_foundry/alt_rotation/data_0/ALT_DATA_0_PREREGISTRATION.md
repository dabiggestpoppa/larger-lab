# ALT-DATA-0 PREREGISTRATION

**Checkpoint:** `CRYPTO-ALT-DATA-0-POINT-IN-TIME-RANKING-AND-PERP-UNIVERSE-REALITY-AUDIT`
**Branch:** `agent/crypto-quant-foundry`
**Base SHA (commit parent):** `47c9d09f077e387b99740b0d7236f1e7fb3818cf`
**Base SHA note:** at session start the local branch was `5a6a4407` and
`47c9d09f` was absent locally; mid-session the worktree fast-forwarded via
`git pull origin agent/crypto-quant-foundry` to `47c9d09f` (the brief's
stated branch head, which contains the original alt-rotation planning docs
and the two 'docs:' commits `058a2d69` + `47c9d09f`). All artifacts in this
checkpoint were built on top of `47c9d09f`.
**Preregistered at:** 2026-08-24 (UTC)
**Discipline:** DATA REALITY ONLY — no alpha, no PnL, no optimization, no execution.

## 1. Purpose

Prove (or disprove) that the historical top-ranked altcoin universe can be
reconstructed point-in-time AND intersected with the historical perpetual
contract universe, without survivorship bias or listing look-ahead.

This checkpoint builds no strategies. It gates all future alt-rotation work.

## 2. Core Question (preregistered, fixed)

For any historical date `t`:

> Which assets were actually in the historical top-500 at `t`, which
> sector/category did they belong to at `t` where verifiable, and which of
> them had a sufficiently mature and liquid perpetual contract actually
> available to trade at `t`?

## 3. Hard Truth Rule (preregistered, fixed)

Tradable research universe at `t`:

```
HISTORICAL TOP-500 AT t
∩ MINIMUM COIN AGE
∩ PERPETUAL CONTRACT EXISTED AT t
∩ CONTRACT AGE >= MINIMUM MATURITY RULE
∩ HISTORICAL PERP DATA EXISTS
∩ LIQUIDITY REQUIREMENT AT t
```

Forbidden: current-universe backfill; today's top-500 for old dates;
current symbol lists as historical truth; symbol-only identity joins.

## 4. Maturity Rule Candidate (preregistered)

- `MINIMUM_MATURITY_RULE`: **30 calendar days** of contract existence
  before `t`.
- Outcome classes (fixed): `30D_FEASIBLE`, `30D_TOO_RESTRICTIVE`,
  `30D_INSUFFICIENT_EVIDENCE`.
- The rule is NOT to be tuned against returns in this or any checkpoint.
  It may only be changed on data-coverage grounds, with a documented
  rationale.

## 5. Prototype Dates (preregistered, fixed)

| date | role |
|---|---|
| 2024-06-01 | mid-2024 |
| 2025-01-01 | start 2025 |
| 2025-06-01 | mid-2025 |
| 2026-01-01 | start 2026 |
| 2026-08-20 | recent historical (≥3 days before run date) |

## 6. Survivorship Tests (mandatory, preregistered)

- **T13 Delisted-contract test:** recover listing, trading period,
  delisting, and historical bars for several known delisted perps. If
  current APIs omit them and no archive works → `PERP_UNIVERSE_SURVIVORSHIP_RISK` (potentially blocking).
- **T14 Rank survivorship test:** confirm that once-highly-ranked, now
  dead/fallen/renamed assets appear correctly in historical rank
  reconstruction. Otherwise → `RANK_UNIVERSE_SURVIVORSHIP_RISK`.

## 7. Fail-Closed Rules (preregistered, fixed)

| condition | verdict |
|---|---|
| historical ranking rebuilt from today's survivor universe | FAIL |
| historical perp availability from today's symbol list only | FAIL |
| delisted contracts materially unrecoverable, no archive | PARTIAL/FAIL |
| symbols joined without stable identity mapping | FAIL |
| current-only sectors presented as historical | FAIL |
| missing source provenance | FAIL |

## 8. Decision Classes (fixed)

`PASS_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`
`PARTIAL_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`
`FAIL_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION`

PASS requires: (1) PIT rank demonstrated, (2) no current-survivor
dependence, (3) historical perp availability demonstrated, (4) delisted
recovery sufficiently addressed, (5) stable identity mapping demonstrated,
(6) consensus matrix complete, (7) truthful sector classification,
(8) multi-horizon feasibility assessed, (9) complete provenance,
(10) zero alpha/PnL work.

## 9. Required Artifacts (fixed list)

`ALT_DATA_0_SOURCE_AUTHORITY_REGISTRY.csv`,
`ALT_DATA_0_SOURCE_CONSENSUS_MATRIX.csv`,
`ALT_DATA_0_FREE_VS_PAID_MATRIX.csv`,
`ALT_DATA_0_HISTORICAL_RANK_AUDIT.md`,
`ALT_DATA_0_PERP_LISTING_AUDIT.md`,
`ALT_DATA_0_DELISTING_SURVIVORSHIP_AUDIT.md`,
`ALT_DATA_0_RANK_SURVIVORSHIP_AUDIT.md`,
`ALT_DATA_0_IDENTITY_MAPPING_SPEC.md`,
`ALT_DATA_0_SECTOR_MAPPING_AUDIT.md`,
`ALT_DATA_0_MULTI_HORIZON_READINESS.csv`,
`ALT_DATA_0_TOPOLOGY_READINESS.md`,
`ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv`,
`ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv`,
`ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv`,
`ALT_DATA_0_PROVENANCE_MANIFEST.json`,
`ALT_DATA_0_REPORT.md`,
`ALT_DATA_0_DECISION.json`

## 10. Provenance Contract (preregistered)

Every persisted raw sample includes: source, endpoint/URL type, request
parameters, retrieved_at, historical_date, row count, first record, last
record, schema version, SHA256, access class, known limitations. No
anonymous files. All hashes in `ALT_DATA_0_PROVENANCE_MANIFEST.json`.

## 11. Isolation

Work confined to `quant-lab/research/crypto_foundry/alt_rotation/`. Core
ALPHA lanes (`alpha_1`, `alpha_1_1`, `alpha_2`, `mech_1`, `mech_2`) and
core contracts are NOT touched.
