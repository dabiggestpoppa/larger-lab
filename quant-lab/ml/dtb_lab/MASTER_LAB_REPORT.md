# CEREBUS DTB LAB — MASTER REPORT

**Generated:** 2026-06-11T12:52:02.035731

**Total combinations scanned:** 101 firms × 54 pairs = 5,454

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
- **Avg CV MAE:** 17.154 pips
- **Avg CV R²:** 0.29396

**Feature Importance:**
  - au_pips: 0.2005
  - asian_range_pips: 0.1810
  - regime_encoded: 0.1631
  - regime_ratio: 0.1484
  - loop_duration: 0.1174
  - day_of_week: 0.0475
  - is_wednesday_pm: 0.0368
  - Delta_t: 0.0353
  - entropy_encoded: 0.0266
  - L_theoretical: 0.0233
  - time_to_12pm_mins: 0.0201
  - L_actual: 0.0000
  - Omega_L: 0.0000

## Phase 3: Merge Unified BVP
- **Samples:** 15570
- **Features:** 14
- **Avg CV MAE:** 17.052 pips
- **Avg CV R²:** 0.296

**Feature Importance:**
  - mlr_range_pips: 0.2614
  - au_pips: 0.1672
  - asian_range_pips: 0.1204
  - regime_ratio: 0.1043
  - micro_macro_alignment: 0.0904
  - hit_25: 0.0876
  - day_of_week: 0.0506
  - hit_50: 0.0473
  - is_wednesday_pm: 0.0391
  - L_theoretical: 0.0174
  - time_to_12pm_mins: 0.0143
  - L_actual: 0.0000
  - Omega_L: 0.0000
  - Delta_t: 0.0000