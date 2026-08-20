# CTBT T2 — One-Shot 2025 Confirmation Report

**Checkpoint:** `SW-CTBT-T2-ONE-SHOT-CANONICAL-TRANSFER-CONFIRMATION`
**Base:** `d5228fbbee23c8f85644ebc36f0ac578a76270a1` (T1.1, PASS_STEP1_SURVIVOR_CONFIRMED)
**Result:** **FOCUSED_TRANSFER_FAMILY** — both T1.1 survivors confirmed.

---

## 1. What was done

The two T1.1 survivors (`EUR_GBP_USD`, `GBP_NZD_USD`) were run through the
**exact sealed canonical-transfer lifecycle** (verified 405/405 + 194/194
against the canonical trade log at T1.1) over the frozen 2025 confirmation
window. The engine source, all lifecycle constants, and the conservative cost
contract are byte-identical to T1.1 — only the calendar window changed.

**Preregistration discipline:** `CTBT_T2_PROTOCOL.md`,
`CTBT_T2_PREREGISTRATION.json`, `CTBT_T2_PREREGISTRATION_HASH.json`
(sha256 `9cff2f9e…`) and `CTBT_T2_T11_SEAL.json` were written and frozen
**before any 2025 economics were computed**.

## 2. Data

- Effective window: `2025-01-02 00:00:00` → `2025-12-31 18:55:00` (Jan 1 was
  a market holiday for the common leg set; recorded in
  `CTBT_T2_CONFIRMATION_WINDOW.json` before interpretation).
- All five required legs carry ~74.4k authentic M5 bars in 2025, zero
  duplicate timestamps, full causal completeness (see `CTBT_T2_DATA_AUDIT.csv`
  with per-file SHA256).
- No 2026 data. No synthetic/forward-filled/interpolated bars.

## 3. Confirmation economics (z3 primary, frozen 1.0× cost)

| Metric | EUR_GBP_USD | GBP_NZD_USD |
|---|---|---|
| N (events) | **146** | **81** |
| Sample state | FULL_CONFIRMATION | FULL_CONFIRMATION |
| Net EV (bps/event) | **+17.75** | **+11.87** |
| PF net | **5.52** | **5.82** |
| Win rate | 77.4% | 74.1% |
| Median net (bps) | +17.48 | +12.88 |
| p5 / worst (bps) | −27.09 / −44.77 | −13.47 / −38.70 |
| Max DD (bps) | 51.0 | 113.7 |
| Avg / med / p90 hold (min) | 178 / 180 / 298 | 209 / 195 / 360 |
| z6 stop rate | 6.9% | 4.9% |
| Hard-exit rate | 38.4% | 42.0% |
| Gross-edge / cost ratio | **3.20** | **2.33** |
| Break-even cost multiple | 3.20 | 2.33 |
| Basket cost (bps) | 8.06 | 8.89 |

## 4. Cost reality

- Decision lane uses the **exact frozen T1.1 conservative contract**
  (1.5-pip floor spread + 1.4 pips/leg commission, pip-size/median-price
  conversion), evidence class `VERIFIED_STATIC_PROVIDER`.
- `OBSERVED_SIGNAL_COST_NOT_AVAILABLE` for the decision lane (frozen engine
  leg files carry no spread columns). An **auxiliary** observed layer from
  `EURUSDPRO_M5_2023_2025.csv` shows EURUSD 2025 observed spreads (median
  16 pts ≈ 1.6 pips, p95 58 pts) — consistent with the conservative floor,
  no cost surprise.
- **Cost stress (diagnostic only):** both candidates remain net-positive at
  1.25× and 1.50×; at 2.00× EUR_GBP_USD +9.70 bps (PF 2.61), GBP_NZD_USD
  +2.98 bps (PF 1.56). The base 1.0× decision stands.

## 5. Bootstrap & multiple testing

Week-block bootstrap, 2000 replicates, seed `20260820`, estimand mean net
bps/event:

| Candidate | Mean | 95% CI | p (vs 0) | BH-FDR q |
|---|---|---|---|---|
| EUR_GBP_USD | +17.75 | [14.25, 21.47] | 0.000 | 0.000 |
| GBP_NZD_USD | +11.87 | [6.16, 17.22] | 0.000 | 0.000 |

Both CIs exclude zero; both q < 0.05. FDR is corroborative; the mechanical
gates are what qualified the candidates.

## 6. Transport / decay vs T1.1 development

| Metric | EUR_GBP_USD (dev→2025) | GBP_NZD_USD (dev→2025) |
|---|---|---|
| Net EV retention | 1.13 (15.74→17.75) | 0.52 (22.84→11.87) |
| PF retention | 1.02 | 0.73 |
| Frequency retention | 0.76 (3.7→2.8/wk) | 0.89 |
| Cost-ratio retention | 1.11 | 0.66 |
| p5 | −22.9→−27.1 | −17.2→−13.5 |
| Worst event | −61.7→−44.8 | −183.3→−38.7 |
| **Classification** | **TRANSPORT_CONFIRMED** | **TRANSPORT_DECAYED_BUT_POSITIVE** |

`EUR_GBP_USD` confirms at development quality or better.
`GBP_NZD_USD` confirms positively but with material EV decay — honest,
weaker-but-positive transfer evidence.

## 7. Causality

Future-perturbation, tail-truncation, and head-truncation invariance all
pass for both candidates (`CTBT_T2_CAUSALITY_AUDIT.json`).

## 8. Canonical reference (descriptive)

`AUD_GBP_NZD` 2025 (frozen engine, descriptive only): 47 z3 events, net EV
+7.97 bps, PF 4.87 — the canonical mechanism is alive in 2025 too. It did
not alter any challenger gate and no canonical forward truth was consumed
(`CTBT_T2_CANONICAL_REFERENCE_STATUS.json`).

## 9. Gates

Both candidates pass **all ten** mandatory preregistered gates (A–J),
including tail-failure, cost-regime, and causality checks
(`CTBT_T2_CANDIDATE_DECISIONS.csv`). No gate was waived.

## 10. Program decision

- **Program decision:** `FOCUSED_TRANSFER_FAMILY`
- Both candidates become `HISTORICALLY_CONFIRMED_TRANSFER_CANDIDATES`.
- **No winner picking** based on PF — both proceed as a family; forward
  evidence may differentiate them.
- Next allowed step (human authorization required):
  `SW-CTBT-T3-TRANSFER-CANDIDATE-SEAL-AND-FORWARD-SHADOW-PREREGISTRATION`
  — sealing + forward-specification only, **no** further historical research.
- `production_authorized = false`, `human_review_required = true`.
- No forward deployment, no demo orders, no live orders.

## 11. Caveats carried forward

- Development M5 evidence remains limited to ~2.25 years (2022-09 →
  2024-12) for every triangle; 2025 is the first genuinely out-of-sample
  calendar period and it confirms — which strengthens the transfer claim.
- The observed-cost layer covers only the EURUSD leg; full signal-time
  basket spreads remain unobserved for the decision lane (conservative
  floor assumed).
