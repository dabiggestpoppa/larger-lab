# MECH-18 — GLOBAL LAW FREEZE MAP (33)

AGENT 1 · CANONICAL FIELD CARTOGRAPHER · terrain research only
Parent: MECH-17 (f49bfefd) · Branch: agent/crypto-quant-foundry
Computed from the canonical MECH-16 daily panel (2196 days, 2020-06 → 2026-08).

This map says what freezes, what re-fits, and what stays research-only — for the
Field Model v1 GLOBAL adaptive-law layer. It does NOT grant a freeze. It audits it.

---

## 1. ROAD SYSTEM — TOPOLOGY LAYER (carried, NOT reopened)

| Object | Status | Evidence (MECH-17, uncontradicted) |
|---|---|---|
| BREADTH×DISPERSION state topology | FROZEN_CANDIDATE | 4-state 0.67 / 6-cell 0.77 / 8-cell 0.90 self-transition ordering |
| 6-cell operational surface | FROZEN_CANDIDATE | stable self-transitions, subperiod coverage 1.0 for dominant edges |
| 8-cell rank-depth surface | FROZEN_CANDIDATE | same, 8-cell edges re-confirmed in 02 registry |
| LOCAL HIGHWAYS / dominant exits | FROZEN_CANDIDATE | 6C_3→6C_4 (PRIMARY, p=0.53, 0.8 subperiod coverage) stable across 2020-2026 |
| EXIT-PRESSURE branch geometry | FROZEN_CANDIDATE | 04 discriminates 14 state-regimes robustly |

No contradiction surfaced in MECH-18. State matrix stays 6-cell + 8-cell. Not expanded.

---

## 2. LAW LAYER — WHAT FREEZES (structural geometry)

| Law object | Verdict | Key numbers (this MECH) |
|---|---|---|
| EDGE REGISTRY | **PROMOTE → STRUCTURAL_CORE** | 93 edges (6C+8C); STAY 14, PRIMARY 4, SECONDARY 0 (post-fix), MINOR 51, NEAR_ZERO 24; dominant exits span all 5 subperiods |
| FORCING FAMILIES (9) | **PROMOTE → ADAPTIVE_LAW** | near-orthogonal; mean |cross-family rho| ≈ 0.12–0.21 (09b); primitives mostly single-variable |
| THRESHOLD BANDS | **PROMOTE → ADAPTIVE_LAW** | bands transport better than points; drift is a fraction of band width |
| SATURATION SHAPE | **PROMOTE → ADAPTIVE_LAW** | UNIVERSALISH data collapse (pooled/local test RMSE ratio 1.02); 1-param ≈ 3-param reconstruction |
| RESPONSE FINGERPRINT | **PROMOTE → ADAPTIVE_LAW** | onset / half-sat / slope / ceiling / persistence / hysteresis-gap per patch × subperiod (13) |
| ROUTE DEFORMATION | **LOCAL** | JS divergence well-bounded (median 0.010 prev-day / 0.127 state-hist / 0.269 regime) |
| ENTROPY REGIME LABELS | **LOCAL** | OPEN_STABLE / OPEN_COLLAPSING / OPEN_REOPENING / CONSTRAINED_STABLE / CONSTRAINED_COLLAPSING / CONSTRAINED_REOPENING earned descriptively |

## 3. LAW LAYER — WHAT RE-FITS (adaptive / state-local)

| Law object | Verdict | Key numbers |
|---|---|---|
| SATURATION NODES | **ADAPTIVE (re-fit)** | x0/k/ceiling roll (180d windows); nodes PARTIAL_COUPLING — k×ceiling anti-coupled (r −0.42…−0.88), so re-fit nodes jointly, not independently |
| ROUTE-SPECIFIC FORCING LOADINGS | **ADAPTIVE (re-fit)** | different families load different routes (10): e.g. 6C_0 stay ← PHYSICAL_DISTURBANCE +0.33; 6C_3→6C_4 ← VOLATILITY −0.30; 6C_5 stay ← VOLATILITY +0.32 |
| THRESHOLD BAND LOCATIONS | **ADAPTIVE (re-fit)** | band centers move by subperiod; 2022 26-100 band width 61.8 vs 9.7 in 2023 |
| CAPACITY CEILINGS | **ADAPTIVE (re-fit)** | state-local 0.81–1.10 (6-cell); step-like, excluded from 2022 event vector |
| TRANSFER EFFICIENCY | **ADAPTIVE (re-fit)** | state × subperiod; supports propagation link (ρ 0.53) |
| HYSTERESIS | **PARKED (state-local)** | deep patches survive controls (gap 0.085–0.136, p ≤ 0.02), shallow patches CONTROLLED_AWAY |
| MEMORY VARIABLES | **STATE_LOCAL_MEMORY (weak)** | best ΔR² test ≈ 0.004–0.006 (time_since_peak); no global horizon |
| BIRTH VIABILITY ENVELOPE | **ADAPTIVE (re-fit)** | first-leaver coordinate mostly demand (51%); per-coordinate separation small |

## 4. LAW LAYER — RESEARCH-ONLY / RESOLVED NEGATIVES

| Object | Status | Why |
|---|---|---|
| ONE UNIVERSAL STATE-AGE CLOCK | DISSOLVED (confirmed) | 4/6 states NO_STABLE_EDGE_CLOCK; at most WEAK_EDGE_TIMING (6C_2, 6C_5) |
| ONE MASTER FORCING SCALAR | DISSOLVED (confirmed) | 9 near-orthogonal families; no single factor |
| GLOBAL MEMORY KERNEL | NOT EARNED | all kernels LEVEL_SUFFICIENT vs contemporaneous level |
| GLOBAL FORCING HIERARCHY | NOT EARNED | upstream score only PARTICIPATION +0.065; rest ≈ 0 |
| 2022 AS PERMANENT REGIME | NOT GRANTED | kept as reserved stress archetype |
| FREE EXTERNAL DATA (SoSoValue etc.) | DATA_BLOCKED | no verified free local feed (per tech-stack v0.2) |

## 5. THE 2022 STRUCTURAL SCAR — WHAT FREEZE MUST CARRY

- Multivariate deviation vector (saturation nodes + daily law variables):
  **onset 2021-12-16 → break confirmed 2021-12-19 → peak 2022-02-24 (index 5.6σ)
  → early recovery 2022-03-16 → shape normalization 2022-06-08 → snapback
  2022-06-12 (14d/30d; 60d window sensitive, 2023-04-05).**
- Variable strip ordering: recruitment/p1 peak late Feb; ceiling Feb; demand mid-Mar;
  propagation mid-Apr; slope/onset late May. First normalizers 2022-02-25
  (slope, entropy, p1, breadth, propagation); last = onset (coincided with snapback).
- **Residue is REAL and structural:** response slope stayed flattened after the
  headline snapback — slope_FIELD post-event max |z| 5.4σ (vs pre-event mean 0.67),
  ceiling +0.34σ mean residue, exit entropy re-breached 3σ. Most daily variables
  show NO_RESIDUE. The market returned to normal fast; the RESPONSE LAW did not.
- Freeze consequence: the Field Model v1 must model 2022 as a **response-law
  regime-modulation episode with slope/ceiling residue**, not as a demand anomaly.
  Any frozen saturation slope must carry a 2022-flag.

## 6. FREEZE VERDICT

```
GLOBAL COMPONENT (law layer): PARTIAL — freeze candidate for objects in §2;
                             re-fit layer for objects in §3; carry §5 scar.
GLOBAL COMPONENT (topology):  FROZEN_CANDIDATE (unchanged from MECH-17).
GLOBAL LAW FREEZE:            NOT GRANTED — requires MECH-19 hardening of
                             saturation-node drift law + slope residue
                             identification before v1 freeze.
```
