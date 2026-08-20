# SW-CTBT-T1.1 — Reference Parity and Gate Enforcement Repair

## Executive summary

The original T1 screen was **NOT ACCEPTED** because its reference parity, cost
contract, monotonicity gate, year-stability gate, and cost source were all flawed.
This checkpoint repaired each of those flaws by reconstructing the canonical TB
lifecycle from first principles and re-running the four preregistered challengers.

**Result: reference parity now passes EXACTLY (405/194 + full economic parity),
and the canonical cost contract (10.2 pips) is restored. Two challengers
(EUR_GBP_USD, GBP_NZD_USD) satisfy every frozen gate; two fail cleanly.**

## 1. Reference parity — REPAIRED (the critical fix)

The prior T1 claimed parity on the basis of "206 z3 / 288 z2.5 events", which
matches nothing canonical. The canonical frozen fingerprint is **194 PRIMARY /
405 CONTROL**.

An independent reconstruction (`run_t11_reference_parity.py`) of the canonical
lifecycle reproduces the canonical 405-trade log **exactly**:

| Field | Match |
|---|---|
| control event count | 405 / 405 |
| primary event count | 194 / 194 |
| entry time | 405 / 405 |
| direction | 405 / 405 |
| exit time | 405 / 405 |
| exit reason (TP/SL/TIMEOUT) | 405 / 405 |
| entry z-score | 405 / 405 |
| gross PnL | 405 / 405 (max diff 0.0) |
| cost (10.2 pips) | 405 / 405 |
| net PnL | 405 / 405 |
| leg sizes (W2 weights) | 405 / 405 (max diff 0.0) |

Two lifecycle details were the source of the prior divergence and are now frozen:
(1) the hard noon exit is checked **before** TP/SL; (2) the rolling z is a
200-bar population-std window over **previous bars only** (current excluded).

## 2. Cost contract — REPAIRED

The prior T1 used an "ASSUMED" 16.2-pip basket cost. The canonical frozen cost
is **10.2 pips round trip** (`strategy_freeze.json`: spread 1.5 + 2.5 + 2.0 +
commission 1.4×3). The prior 16.2 pips over-stated the canonical cost by ~59%.

For challengers, cost is measured in the same conservative, canonical-consistent
structure (1.5-pip floor + 1.4-pip commission per leg), converted to unit-free
basis bps. Every leg has a **documented** provider spread
(`spread_commission_config.py`, OxSecurities MT5), so no challenger falls to the
ASSUMED (level-5) evidence class. The conservative cost used for the gate is
strictly higher than the documented spec (fail-closed).

## 3. Challenger screen — REPAIRED (z3.0 primary, conservative cost)

| Triangle | Window (M5) | Events | Net EV (bps) | PF net | WR % | Edge/Cost | Monotonicity | +Years | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| EUR_GBP_JPY | 2021-10→2024-12 | 256 | -3.56 | 0.14 | 9.4 | 0.49 | STRONG | 0/4 | FAIL |
| CHF_GBP_JPY | 2021-10→2024-12 | 232 | +0.41 | 1.16 | 42.7 | 1.07 | STRONG | 2/4 | FAIL |
| EUR_GBP_USD | 2022-09→2024-12 | 435 | +15.74 | 5.42 | 78.2 | 2.88 | STRONG | 3/3 | **PASS** |
| GBP_NZD_USD | 2022-09→2024-12 | 210 | +22.84 | 8.02 | 84.3 | 3.56 | STRONG | 3/3 | **PASS** |

- **EUR_GBP_JPY** fails decisively: negative net EV, PF 0.14, zero positive years.
  The mechanism does not transfer.
- **CHF_GBP_JPY** fails: marginally positive EV but PF 1.16 (< 1.20) and only
  2/4 positive years. Mechanism is weak.
- **EUR_GBP_USD** and **GBP_NZD_USD** pass all ten gates: strong net EV, high PF,
  MONOTONIC_STRONG (z3.0 strictly better than z2.5), and 3/3 positive years.

## 4. Data window finding (material)

The "2020–2024 M5" coverage claimed in T1 does not exist. The `_fetched.csv` and
`PRO` files are **daily (1 bar/day) before ~2022-08**, then switch to true M5.
Consequently every triangle (reference included) has only **~2.25 years of valid
M5 development data (2022-09 → 2024-12)**.

This has two consequences:
1. The qualifying candidates are labelled **SHORTER_DEVELOPMENT_WINDOW**.
2. Gate G ("3 calendar years") is met literally (2022, 2023, 2024 all net-positive)
   but 2022 is a ~3-month fragment. This is recorded as a **material caveat**.

## 5. Decision

- Status: **PASS_STEP1_SURVIVOR_CONFIRMED**
- Qualified: **EUR_GBP_USD**, **GBP_NZD_USD** (2 candidates, within the cap)
- Step 2: **NOT authorized** — explicit human review required before any 2025
  confirmation economics are opened.

The year-depth caveat is the single most important thing the human must weigh:
the two survivors show a strong, monotonic mechanism over ~2.25 years, but that is
shorter than the three-full-years ideal.
