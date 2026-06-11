# CEREBUS DTB LAB v2 — MASTER REPORT

**Generated:** 2026-06-11T13:17:57.259643

**Fixes applied:** Vectorized loop detection, Δ_t sample weighting, checkpoint labels

## Phase 1: Macro MLR Lens
- **Samples:** 6062
- **Features:** 7
- **Avg CV MAE:** 2457.162 pips
- **Avg CV R²:** 0.7753

**Feature Importance:**
  - mlr_range_pips: 0.4884
  - target_50_pips: 0.2220
  - dist_to_132_pips: 0.1806
  - target_25_pips: 0.1039
  - is_wednesday_pm: 0.0028
  - bias_encoded: 0.0023
  - time_to_friday_hours: 0.0000

## Phase 2: Micro Atomic Lens
- **Samples:** 15570
- **Features:** 13
- **Avg CV MAE:** 16.636 pips
- **Avg CV R²:** 0.32526

**Feature Importance:**
  - regime_encoded: 0.2335
  - au_pips: 0.1741
  - asian_range_pips: 0.1420
  - regime_ratio: 0.1118
  - loop_duration: 0.0946
  - time_to_12pm_mins: 0.0815
  - entropy_encoded: 0.0514
  - Omega_L: 0.0441
  - L_actual: 0.0364
  - day_of_week: 0.0182
  - is_wednesday_pm: 0.0068
  - L_theoretical: 0.0056
  - Delta_t: 0.0000

## Phase 3: Merge Unified BVP
- **Samples:** 15570
- **Features:** 14
- **Avg CV MAE:** 16.452 pips
- **Avg CV R²:** 0.33148

**Feature Importance:**
  - mlr_range_pips: 0.2772
  - au_pips: 0.1550
  - asian_range_pips: 0.1219
  - regime_ratio: 0.0799
  - time_to_12pm_mins: 0.0687
  - micro_macro_alignment: 0.0676
  - Omega_L: 0.0563
  - L_actual: 0.0522
  - hit_25: 0.0504
  - hit_50: 0.0240
  - day_of_week: 0.0216
  - is_wednesday_pm: 0.0150
  - L_theoretical: 0.0103
  - Delta_t: 0.0000