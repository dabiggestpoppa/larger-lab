# CR-BLOCK4-D1.1 REPORT

**Checkpoint:** CR-RISK-BLOCK-IV-D1.1-BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE
**Base:** `f52d5f482a3d5ff5b133a6335e9996ab98cb0bb3` · **Status:** PASS
**Science changed:** FALSE · **Broker execution:** FALSE
**Truth class:** HYPOTHETICAL_DIAGNOSTIC — no actual leverage / production-cap claim

## Frozen science (verified)

890 events (A 432 / B 458) · ACCEPT_FULL 826 (A 371 / B 455) ·
REJECT_HEAT_CAP 64 · 1R 24.49489742783178 bps (not a hard stop)

## Grid replication (vs D1 preregistration)

PASS — D0.1 translations
cross-checked against the R1 multipliers ledger: True.

## Coverage surface

| L | targets | surviving | blocked | survival % |
|---|---|---|---|---|
| 0.5 | 826 | 39 | 787 | 4.72% |
| 1 | 826 | 178 | 648 | 21.55% |
| 2 | 826 | 417 | 409 | 50.48% |
| 4 | 826 | 655 | 171 | 79.30% |
| 8 | 826 | 786 | 40 | 95.16% |
| 16 | 826 | 817 | 9 | 98.91% |
| 32 | 826 | 825 | 1 | 99.88% |
| 64 | 826 | 826 | 0 | 100.00% |

## Family distortion (surviving A / B, coverage, A-share shift vs 44.915% original)

| L | A | B | A cov % | B cov % | A share shift |
|---|---|---|---|---|---|
| 0.5 | 2 | 37 | 0.54% | 8.13% | -0.3979 |
| 1 | 17 | 161 | 4.58% | 35.38% | -0.3536 |
| 2 | 77 | 340 | 20.75% | 74.73% | -0.2645 |
| 4 | 227 | 428 | 61.19% | 94.07% | -0.1026 |
| 8 | 333 | 453 | 89.76% | 99.56% | -0.0255 |
| 16 | 363 | 454 | 97.84% | 99.78% | -0.0048 |
| 32 | 370 | 455 | 99.73% | 100.00% | -0.0007 |
| 64 | 371 | 455 | 100.00% | 100.00% | +0.0000 |

## Performance diagnostic (physical book: blocked -> 0; descriptive only, NO selection)

| L | n surv | WR | mean EV % | PF | cum % | max DD % | loss streak |
|---|---|---|---|---|---|---|---|
| 0.5 | 39 | 0.0363 | 0.0219 | 3.40716 | 18.05 | -4.78 | 126 |
| 1 | 178 | 0.1634 | 0.1098 | 4.220683 | 90.68 | -4.63 | 50 |
| 2 | 417 | 0.3366 | 0.2042 | 2.73067 | 168.65 | -7.49 | 18 |
| 4 | 655 | 0.4988 | 0.2796 | 2.286067 | 230.96 | -7.57 | 12 |
| 8 | 786 | 0.5969 | 0.3305 | 2.181916 | 273.00 | -9.12 | 10 |
| 16 | 817 | 0.6186 | 0.3409 | 2.131029 | 281.62 | -9.47 | 10 |
| 32 | 825 | 0.6259 | 0.3594 | 2.175083 | 296.90 | -7.95 | 10 |
| 64 | 826 | 0.6259 | 0.3586 | 2.168831 | 296.17 | -7.95 | 10 |

`preferred_cap_selected=false` · `performance_based_selection=false` ·
`production_cap_selected=false` — all eight cells retained.

## Episode / concurrency distortion (12h episodes, frozen definition)

| L | eps w/ orig | eps w/ surv | fully preserved | partial | fully eliminated | surv max conc |
|---|---|---|---|---|---|---|
| 0.5 | 482 | 31 | 9 | 22 | 451 | 2 |
| 1 | 482 | 129 | 55 | 74 | 353 | 3 |
| 2 | 482 | 283 | 174 | 109 | 199 | 3 |
| 4 | 482 | 404 | 334 | 70 | 78 | 3 |
| 8 | 482 | 459 | 442 | 17 | 23 | 3 |
| 16 | 482 | 477 | 473 | 4 | 5 | 3 |
| 32 | 482 | 481 | 481 | 0 | 1 | 3 |
| 64 | 482 | 482 | 482 | 0 | 0 | 3 |

Original global max concurrency (frozen source): 3.
Episode-level concurrency is structural distortion only — NOT margin feasibility.

## Equity invariance

True — fixtures {5k, 25k, 100k}; N = m x E
linear; m_t and classification identical across account sizes
(20 events x 8 caps checked).

## Missing physical truth

All 22 D1 register fields carried forward UNKNOWN / blocking. None resolved by
assumption. Lane A requires none of them (notional-only).

## Artifacts

20 files in this directory. Decision: `CR_BLOCK4_D1_1_DECISION.json`.
