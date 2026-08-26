# PFT-B5 — A1 Atomic Evidence / Kernel Attribution Protocol

**checkpoint**: PFT-B5-A1-ATOMIC-EVIDENCE
**species_id**: PFT-A1-DEEPERS
**evidence_class**: ATOMIC_EVIDENCE
**date**: 2026-08-26

## Mission

Determine whether the individual mathematical components of PFT-A1-DEEPERS v2.2 contain reproducible information even though the frozen RAW full stack is dormant.

## Known B3 Dormancy

| Kernel | RAW Activations | Status |
|--------|----------------|--------|
| K1 | 0 | Eigenvalue band empty |
| K2 | 3,955 (22.6%) | Only active kernel |
| K3 | 0 | NO_HOLE everywhere |
| K4 | 0 | FSM always NEUTRAL |

## Analysis Framework

### Observable Extraction

For each kernel, extract the **continuous** mathematical output before author-specified activation thresholds:

**K1 Continuous Observables:**
- `lambda_magnitude`: dominant eigenvalue magnitude
- `lambda_angle`: dominant eigenvalue angle
- `lambda_imag`: imaginary component
- `spectral_radius`: maximum eigenvalue magnitude
- `delta_phi`: circular phase distance
- `mode_persistence`: fraction of variance in dominant mode
- `reconstruction_error`: DMD reconstruction residual
- `lambda_distance_to_1`: `|1 - |lambda||`

**K2 Continuous Observables:**
- `gamma_raw`: raw range skew
- `gamma_bar`: 3-hour smoothed gamma
- `acceleration`: volatility acceleration
- `gamma_distance`: distance to `|gamma_bar| > 0.10`
- `accel_distance`: distance to `accel > 0.025`

**K3 Continuous Observables:**
- `D_WE`, `D_WC`, `D_EC`, `D_WI`: pairwise distances
- `median_distance`: median pairwise distance
- `epsilon`: filtration scale
- `edge_density`: fraction of edges below epsilon
- `distance_to_cycle`: edges needed for 4-cycle

**K4 Continuous Observables:**
- `alpha_D`: oriented lead-lag area
- `alpha_D_abs`: absolute area
- `w_total_raw`: continuous weight before FSM thresholding
- `distance_to_fsm`: `|w_total_raw| - 0.05`
- `sign_persistence_5`: rolling sign agreement

### Future Outcome Registry

| Target | Definition |
|--------|-----------|
| `future_return_W_h{H}` | Brent return at horizon H |
| `future_return_E_h{H}` | EURUSD return at horizon H |
| `future_return_C_h{H}` | USDCAD return at horizon H |
| `future_return_I_h{H}` | DAX return at horizon H |
| `future_return_EC_h{H}` | EURCAD return at horizon H |
| `future_direction_{X}_h{H}` | Binary direction label |
| `future_dispersion_h{H}` | Cross-asset dispersion |
| `future_rv_h{H}` | Realized volatility |

### Horizons (Frozen)

H1, H2, H4, H6, H12, H24

### Information Metrics

For each observable-target pair:
- Pearson correlation
- Spearman rank IC
- R²
- Bucketed conditional mean information ratio
- p-values

### Baseline Comparisons

For each kernel observable, compare against:
1. Oil return alone
2. EURCAD return alone
3. Equity return alone
4. Rolling correlation
5. Realized volatility
6. Time-of-day

### Decomposition Tests

For each kernel, test whether the effect can be reproduced by simpler inputs:
- K1 vs raw returns/volatility
- K2 gamma vs signed return momentum
- K3 topology vs pairwise correlation/dispersion
- K4 area vs simple lagged cross-correlation

### Multiple Testing Control

Apply BH-FDR at α = 0.05 across all hypothesis families.

### Subperiod Stability

Evaluate separately for 2023 and 2024.

### Kernel Dependence

Measure cross-kernel correlation matrix.

## Decision Criteria

- **ATOMIC_INFORMATION_SUPPORTED**: effect exists, survives uncertainty, beats baselines
- **ATOMIC_INFORMATION_WEAK**: effect exists but is conditional/fragile
- **NO_INCREMENTAL_INFORMATION**: observable adds nothing beyond simpler inputs
- **RAW_GATE_DORMANT_BUT_OBSERVABLE_INFORMATIVE**: dormant gate, informative observable
- **RAW_GATE_DORMANT_AND_OBSERVABLE_UNINFORMATIVE**: dormant gate, uninformative observable
