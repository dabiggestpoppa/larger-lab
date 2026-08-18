# CR-BLOCK4-D1 PROTOCOL — Exposure Feasibility Study Plan

**Checkpoint:** CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN
**Base:** `3fde3bb1cf590c554241c23daa14e3d2242998aa` (D0.1)
**Status:** PREREGISTRATION (no feasibility engine, no broker, no optimization)

## 1. Purpose

Design and preregister the scientific study answering:

> Of the SEALED 826 economically approved Capital Routing events, how many
> can a real account/instrument/broker physically express WITHOUT materially changing the
> economic exposure specified by the sealed research?

This checkpoint freezes the study design BEFORE any empirical feasibility outcome exists.

## 2. Frozen science (NOT touched)

| fact | value |
|---|---|
| events | 890 (A 432 / B 458) |
| ACCEPT_FULL | 826 (A 371 / B 455) |
| REJECT_HEAT_CAP | 64 |
| allocation | A1_70_30 (A 0.70 / B 0.30) |
| policy | H1-1.00-REJ, cap 1.0 f-unit, REJECT |
| f_total | 1.0% |
| 1R | 24.49489742783178 bps — NOT a hard stop |
| economic target | N_t = E_t x admitted_f x pos_t x 1e4 / 24.49489742783178 (D0.1 authoritative) |

## 3. Non-goals

- no feasibility engine implementation
- no leverage / lot / broker selection
- no performance optimization of any physical constraint
- no clipping or rounding defaulted to "faithful"
- no margin fabrication
- no broker orders, no MT5 calls

## 4. Study lanes

| lane | name | input truth required |
|---|---|---|
| A | Pure notional representability | externally specified notional/equity limit L |
| B | Quantity representability | frozen instrument contract |
| C | Margin / buying power | actual or frozen margin contract |
| D | Full physical contract | account + instrument + currency + margin + broker capability |

## 5. Concurrency (verified from frozen source)

- max concurrency: **3** (frozen R1_CONCURRENCY_SUMMARY.csv)
- hours with 2 positions: 565 · 3 positions: 20 · 4+: 0
- max gross exposure: 18.1878 f-units
- episodes (12h): **482** (frozen R1_ROUTING_EPISODES.csv)

## 6. Artifacts in this directory

All 31 files are preregistration contracts. `CR_BLOCK4_D1_DECISION.json` is the
checkpoint decision. Nothing in this directory is an empirical feasibility result.
