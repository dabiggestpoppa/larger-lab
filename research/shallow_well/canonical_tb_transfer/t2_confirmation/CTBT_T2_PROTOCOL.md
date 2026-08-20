# CTBT T2 — One-Shot Canonical-Transfer Confirmation (2025)

**Checkpoint:** `SW-CTBT-T2-ONE-SHOT-CANONICAL-TRANSFER-CONFIRMATION`
**Authoritative base:** `d5228fbbee23c8f85644ebc36f0ac578a76270a1`
**Parent:** `SW-CTBT-T1.1-REFERENCE-PARITY-AND-GATE-ENFORCEMENT-REPAIR` (PASS_STEP1_SURVIVOR_CONFIRMED)
**Human authorization:** STEP 2 AUTHORIZED.

This is the **final historical test** in the Canonical-TB-Transfer program.
It answers one question:

> Does the canonical TB transfer mechanism survive a NEW calendar period (2025)?

---

## 1. Scope

- Run ONE preregistered confirmation test on the exact two T1.1 survivors:
  1. `EUR_GBP_USD`
  2. `GBP_NZD_USD`
- No tuning. No optimization. No additional candidates. No alternative exits.
  No filters. No rescue checkpoint after failure.
- `EUR_GBP_JPY` and `CHF_GBP_JPY` FAILED T1.1 and are **closed** (historical
  provenance only).

## 2. Frozen engine

The confirmation uses the **exact repaired canonical transfer implementation**
sealed at T1.1 (verified 405/405 control + 194/194 primary against the
canonical trade log, with exact economic parity):

- **Basis:** `b = ln(A) - ln(B) + ln(C)` per triangle, from closed-bar mids.
  - `EUR_GBP_USD`: A=EURGBP, B=EURUSD, C=GBPUSD
  - `GBP_NZD_USD`: A=GBPNZD, B=GBPUSD, C=NZDUSD
- **Rolling z:** 200 completed bars, population std (ddof=0), **current bar
  excluded**, causal only.
- **Weight:** W2 exact-neutral (uniform market-neutral basket; equal
  unit-free log-weight per leg).
- **Entry:** strict `|z| > 3.0` PRIMARY (decision lane); `|z| > 2.5` CONTROL
  lane run descriptively for mechanism-sign context.
  - z > +3.0 → SHORT; z < -3.0 → LONG.
- **Exit E1:** canonical signed overshoot — SHORT exits on `z <= -0.25`,
  LONG exits on `z >= +0.25` (primary lane); control lane exits at zero
  crossing. This is the sealed T1.1 `run_lifecycle` contract, identical to
  the reference reproduction.
- **Structural stop:** `|z| > 6.0` (SL).
- **Session:** canonical London `03:00–12:00` EST (fixed UTC-5), hard exit at
  `12:00` EST checked **before** TP/SL.
- **Minimum runway:** 120 minutes to hard exit at entry.
- **Concurrency:** max one active basket per candidate.
- **Re-entry:** canonical deterministic lifecycle (no cooldown).

No parameter differs from the T1.1 sealed implementation.

## 3. Confirmation window

- `2025-01-01 00:00` through `2025-12-31 23:59:59` (UTC timestamps as stored),
  subject only to actual causally complete M5 coverage per leg.
- Exact effective window (first/last common timestamp) is recorded in
  `CTBT_T2_CONFIRMATION_WINDOW.json` **before** economics are interpreted.
- NO 2026 data. NO extension. NO shortening based on performance.
- If any required leg lacks sufficient authentic 2025 M5 data → candidate
  state `INVALID_DATA` or `LOW_N` as appropriate. No synthetic data.

## 4. Cost contract (frozen T1.1 conservative methodology)

- Basket round-trip cost (bps) = Σ over legs
  `(spread_pips + commission_pips) × pip_size / median_close × 1e4`
  - spread = 1.5 pips floor (canonical-consistent conservative; reference
    legs use canonical 1.5/2.5/2.0)
  - commission = 1.4 pips/leg (canonical)
- Cost evidence class per survivor: `VERIFIED_STATIC_PROVIDER` (documented
  OxSecurities MT5 spec; conservative floor is STRICTER than the documented
  spec).
- **No cost reduction.** The base confirmation decision uses exactly the
  frozen conservative contract (1.0×).

### 4.1 Cost stress lanes (diagnostics only)

Lanes at 1.0× (base), 1.25×, 1.50×, 2.00× of frozen cost. Reported
separately: EV, PF, gross-edge/cost ratio. They do **not** replace the
preregistered base-cost decision.

### 4.2 Observed cost reality

If authentic 2025 observed provider spread data exist in the workspace they
are reported as a **separate** `OBSERVED_COST_DIAGNOSTIC` layer. The frozen
engine's leg files carry no spread columns for the survivor legs, so the
decision lane is marked `OBSERVED_SIGNAL_COST_NOT_AVAILABLE`; an auxiliary
observed-spread diagnostic is drawn from `EURUSDPRO_M5_2023_2025.csv`
(EURUSD leg only) where present. No fabricated spreads anywhere.

## 5. Sample-state logic

- N ≥ 30 → `FULL_CONFIRMATION`
- N 15–29 → `PROVISIONAL_CONFIRMATION`
- N < 15 → `LOW_N` (may NOT receive full confirmation)

## 6. Primary pass gates (z3 PRIMARY lane, base 1.0× cost)

A candidate confirms **only if ALL** mandatory gates pass:

| Gate | Rule |
|---|---|
| A | net EV > 0 |
| B | PF_net ≥ 1.20 |
| C | N ≥ 30 (full) |
| D | gross-edge / cost ratio ≥ 1.50 |
| E | break-even cost multiple ≥ 1.50 |
| F | same mechanism / expectancy sign as T1.1 |
| G | no catastrophic tail failure |
| H | no material cost-regime collapse |
| I | no data / causality invalidation |
| J | no config deviation |

No discretionary override. 9/10 is not a pass.

## 7. Tail failure (preregistered mechanical rule)

Flag structural tail deterioration when confirmation (vs T1.1 development)
shows BOTH:

1. worst-event and p5 both worse, AND
2. max DD per-event-scaled worse by > 50%.

A candidate is not failed on a single noisy metric in a shorter sample, but
structural deterioration is flagged and recorded.

## 8. Bootstrap

- Week-block bootstrap (ISO week of entry), 2000 replicates.
- **Seed: 20260820** (frozen before economics).
- Primary estimand: **mean net bps/event**.
- Report: mean, 2.5% / 97.5% CI, two-sided p-value against zero.

## 9. Multiple testing

Exactly two primary confirmation hypotheses (`EUR_GBP_USD`,
`GBP_NZD_USD`). Apply BH-FDR, alpha = 0.05. Reference excluded;
cost-stress lanes excluded. FDR significance is **corroborative**; the
mechanical economic gates remain mandatory.

## 10. Transport / decay analysis

Compare T1.1 development vs 2025 confirmation on: event frequency, net EV,
PF, WR, median EV, gross-edge/cost ratio, p5, worst event, hold, z6 rate.

- `EV_RETENTION = confirmation_EV / development_EV`
- `PF_RETENTION`, `FREQUENCY_RETENTION`, `COST_RATIO_RETENTION`
- Classify: `TRANSPORT_CONFIRMED` / `TRANSPORT_DECAYED_BUT_POSITIVE` /
  `FAILED_EDGE` / `FAILED_COST_ECONOMICS` / `FAILED_MECHANISM` /
  `LOW_N` / `INVALID_DATA`.

## 11. Causality audits

- **Future perturbation invariance:** appending a future bar (same close as
  terminal bar) must leave all prior events identical.
- **Truncation invariance:** events inside the overlap of a truncated window
  must be identical to the full-window events.
- Any material failure → `INVALID_TEST`.

## 12. Canonical reference (descriptive only)

`AUD_GBP_NZD` runs over 2025 with the identical frozen engine and the frozen
10.2-pip canonical cost contract **only as a descriptive reference**. It is
not tuned, does not alter challenger gates, and does not consume canonical
forward truth. If running it would violate the independent TB Forward
evidence contract, it is NOT run and
`REFERENCE_NOT_RUN_DUE_FORWARD_SEPARATION` is recorded.

## 13. Program decision (final)

- Both fail → `STOP_CANONICAL_TB_TRANSFER` — no further clone research;
  return focus to canonical TB forward evidence.
- Exactly one confirms → `SINGLE_TRANSFER_CANDIDATE` — that candidate is a
  `HISTORICALLY_CONFIRMED_TRANSFER_CANDIDATE`; next step is forward-shadow
  preregistration only.
- Both confirm → `FOCUSED_TRANSFER_FAMILY` — both are
  `HISTORICALLY_CONFIRMED_TRANSFER_CANDIDATES`; **no winner picking based on
  PF**; both proceed to forward-shadow preregistration.
- No winner picking. Failed candidates are sealed, not rescued.

## 14. STOP rules

- This is the final historical test. No T2.x optimization, no T3 historical
  research, no alternate exits/sessions/costs/filters.
- After this checkpoint: STOP for human review. NO forward deployment, NO
  demo orders, NO live orders.

## 15. Artifacts

All artifacts are written under
`research/shallow_well/canonical_tb_transfer/t2_confirmation/`
(22 files per master prompt). Nonregression: T1/T1.1 artifacts, the
canonical 405/194 anchors, the 10.2-pip contract, and T1.1 candidate
fingerprints remain unchanged.
