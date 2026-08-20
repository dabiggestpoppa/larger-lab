# SW-AJCF-R2 — FROZEN MECHANISM SCREEN — REPORT

Checkpoint: `SW-AJCF-R2-FROZEN-MECHANISM-SCREEN`
Base: `5631f0b5079abacca20921cbcfcd54fdc5ccf7d5`
Parent status: `PASS_R1_SESSION_TRUTH_REPAIRED`
P0 forward runtime: `PASS_FORWARD_RUNTIME_RESTORED` (verified healthy before any R2 economics)

---

## 1. Result summary

| Candidate | Status | N | Gross EV bps | Net EV bps | PF net | WR | z6 rate | Cost bps | Edge/cost |
|---|---|---|---|---|---|---|---|---|---|
| USD_CHF_JPY | **FAIL_R2** | 478 | −1.06 | **−5.86** | **0.21** | 21.3% | 66% | 4.80 | **−0.22** |
| CAD_CHF_JPY | **FAIL_R2** | 783 | −0.28 | **−5.76** | **0.24** | 22.7% | 68% | 5.49 | **−0.05** |

**Both candidates fail. Zero survivors. Program outcome: `STOP_JPY_CHF_FAMILY`.**

The failure is not marginal: gross EV is negative **before cost** on both, PF_net is ~0.2 (vs the 1.20 floor), and monotonicity classifies both `MECHANISM_INVERTED` (primary net EV ≤ 0). Seven of twelve mandatory gates fail on both (A, B, D, E, G, H, plus L borderline).

## 2. Gate matrix

| Gate | USD_CHF_JPY | CAD_CHF_JPY |
|---|---|---|
| A. net EV > 0 | FAIL (−5.86) | FAIL (−5.76) |
| B. PF_net ≥ 1.20 | FAIL (0.21) | FAIL (0.24) |
| C. events ≥ 50 | PASS (478) | PASS (783) |
| D. gross-edge/cost ≥ 1.50 | FAIL (−0.22) | FAIL (−0.05) |
| E. break-even multiple ≥ 1.50 | FAIL (−0.22) | FAIL (−0.05) |
| F. no year > 60% of net PnL | PASS | PASS |
| G. multiple calendar periods positive | FAIL (every year/quarter negative) | FAIL |
| H. mechanism coherent (not inverted) | FAIL (MECHANISM_INVERTED) | FAIL (MECHANISM_INVERTED) |
| I. no rollover-zone entries | PASS (0 rollover entries) | PASS |
| J. causality invariance | PASS | PASS |
| K. data-family integrity | PASS | PASS |
| L. no cost impossibility | PASS | PASS |

## 3. Mechanism diagnosis (non-PnL)

The R2 lifecycle (canonical z3 + W2 + E1 transfer) does NOT reproduce the mechanism R1/R1.1 anatomy appeared to show:

- **R1's z-scale was inflated by data artifacts.** R1's basis/z series included weekend bars and the daily 20:00:00 UTC stale-print spike. On the canonical-consistent series (weekday-only, spike removed) the 200-bar rolling std is ~1.3 bps p50 (vs R1-era ~1.8 bps with artifacts, and the ~11 bps scale the canonical London triangle enjoys). As a result |z|>3 fires on ~4–8 bps moves that are mostly noise relative to 4.8–5.5 bps of cost.
- **Entries trigger deep in dislocations.** Median entry |z| = 6.0 (USD) / 6.4 (CAD) — already at the structural stop level. 66–68% of trades exit via the z6 stop, not E1 reversion. TP trades win (100% at ~+8 bps gross) but are a minority (~19%).
- **Directional asymmetry:** LONG 460/750 vs SHORT 18/33 — the strategy almost only enters LONG in this window; SHORT entries are rare and also lose.
- **Temporal stability:** every calendar year and every quarter with N≥10 shows negative net EV on both candidates. No period is positive.
- **Robustness to data treatment:** the contaminated lane (weekends + 20:00 spike included) also fails (PF 0.24–0.28, net EV −6.1 to −6.5). The conclusion does not depend on the data-truth repair.

## 4. Data-truth repair (documented)

**Finding:** the fetched/PRO family contains a systematic daily 20:00:00 UTC stale-print artifact — 64% of trading days show an anomalous single-bar spike-and-revert in CHFJPY (median 1-bar move 1.41 bps overall vs 5.72 bps at 20:00 UTC; p90 13.85 bps; reverts within 1–2 bars). 20:00 UTC = 15:00 EST sits **inside** the frozen NY_AFTERNOON session and would create phantom z6 stops on open trades.

**Canonical precedent:** the canonical engine never faced this — its EURUSD_M5.csv leg has NO weekend bars (implicitly weekday-only series) and its London session (03:00–12:00 EST = 08:00–17:00 UTC) closed before the 20:00 UTC spike.

**Treatment:** weekday-only (Mon–Fri) series + drop the daily 20:00:00 UTC bar, applied to both candidates and to all causality lanes. Identical in spirit to R1's fetched-family correction. NOT a parameter rescue — the artifact is a proven stale print, and the conclusion holds under both treatments anyway.

## 5. Causality

Future perturbation, tail truncation, and head truncation invariance all PASS for both candidates (completed-events overlap definition). The engine is causal: entries depend only on prior bars.

## 6. Portfolio overlap (descriptive)

- Session: AJCF NY_AFTERNOON_13_16_EST (13:00–16:00 EST) vs canonical/CTBT London (03:00–12:00 EST) — **disjoint hours**.
- Legs: no shared legs with AUD_GBP_NZD / EUR_GBP_USD / GBP_NZD_USD; USD appears in EUR_GBP_USD/GBP_NZD_USD but no identical leg triangle. CHF/JPY appear in no existing family member.
- Moot: both candidates failed; no forward overlap work is applicable.

## 7. Boundaries held

- NO 2025 data opened. NO parameter search. NO session grid. NO filters. NO new candidates. NO orders. NO capital.
- CTBT forward runtime untouched (collector PID 22352 healthy, ledgers intact, dashboards up).
- production/demo/capital = false; human review required.

## 8. Next checkpoint

**NONE.** Zero survivors → `STOP_JPY_CHF_FAMILY`. The JPY/CHF constraint-resolution branch ends here with an honest 0-survivor answer, per the fail-fast policy. Existing TB family (AUD_GBP_NZD, EUR_GBP_USD, GBP_NZD_USD) remains the forward observational focus.
