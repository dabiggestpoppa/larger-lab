# PFT-A1-DEEPERS — Frozen Specification v2.2

Status: FROZEN PRIMARY RAW SPECIFICATION
Lineage: v1.x -> v2.0 -> v2.1 -> v2.2
Do not reinterpret, repair, optimize or silently substitute formulas in RAW.

## Universe

- `W`: ICE Brent continuous front-month for signal generation; Brent CFD for execution/PnL.
- `E`: EUR/USD.
- `C`: USD/CAD.
- `EC`: direct EUR/CAD CFD for execution/PnL; synthetic return `r_E + r_C` used by the signal where specified.
- `I`: GDAXI cash index for signal generation; DAX CFD for execution/PnL.
- Base timeframe: H1.
- Canonical timezone: `America/New_York`, DST-aware.
- Canonical state window: 720 synchronized chronological hourly slots.

Closed/stale hours retain last known price with `stale=true`; stale/closed returns are `r=0`. If Brent/DAX is stale more than 2 hours, the affected K1/K3 kernel is disabled for that slot. Unexpected missing data must be distinguished from expected closure in B2.

## Returns

`r_t = ln(P_t / P_{t-1})` on H1 close prices. Direct EUR/CAD PnL uses its executable CFD series.

## Parkinson Oil Volatility

```text
sigma_W(t) = sqrt((1/(4 ln 2)) * (1/14) * sum_{i=0}^{13}(ln(H_{t-i}/L_{t-i}))^2) * sqrt(365*24)
```

If prior sigma in the acceleration denominator is zero, acceleration is set to zero.

## K1 — Koopman / DMD Phase State

Observable:

`Psi_t = [r_W, |r_W|, r_E, |r_E|, r_C, |r_C|]`

Rolling exact DMD:

`A = Y X^dagger`, then `A Phi = Phi Lambda`.

Eligible modes satisfy:

- `0.95 < |lambda| < 1.0`
- `Im(lambda) > 0`
- complex-conjugate pair represented by the upper-half-plane mode.

Every eigenvector is unit-L2 normalized before participation measurement.

Participation:

- `P_W = sum(abs(Phi rows 1:2))`
- `P_EC = sum(abs(Phi rows 3:6))`

Choose the eligible mode with highest `P_W` as `lambda_W` and highest `P_EC` as `lambda_EC`. If the same mode wins both assignments, `DeltaPhi = 0`. If no qualifying mode exists, `w3 = 0`.

Circular phase distance:

`DeltaPhi = min(|phi_W - phi_EC|, 2*pi - |phi_W - phi_EC|)` bounded to `[0, pi]`.

If `DeltaPhi > 1.57`:

`w3 = -sign(r_I) * min(DeltaPhi / 2.0, 0.35)`

Else `w3 = 0`.

K1 recomputes at each completed H1 close.

## K2 — Oil Range-Skew / Volatility Acceleration

Raw skew:

`gamma = ((H-C) - (C-L)) / (H-L)`

If `H=L`, `gamma=0`.

Three-hour arithmetic smooth:

`gamma_bar_t = (gamma_t + gamma_{t-1} + gamma_{t-2}) / 3`.

Acceleration:

`Accel_t = sigma_t / sigma_{t-1} - 1`; if `sigma_{t-1}=0`, `Accel_t=0`.

Activation requires both:

- `|gamma_bar| > 0.10`
- `Accel > 0.025`

Corrected v2.2 oil target:

`w1 = -0.45 * sign(gamma_bar) * min(Accel/0.04, 1)`

Otherwise `w1=0`.

K2 recomputes at each completed H1 close.

## K3 — Vietoris-Rips Topology + EUR/CAD Distance Divergence

Four nodes: `{W,E,C,I}`.

For each asset, z-score H1 returns using the 720-slot rolling state. Six-step path distance:

`D_ij(t) = sqrt(sum_{tau=0}^{5}(z_i(t-tau)-z_j(t-tau))^2)`.

Filtration scale, corrected v2.1:

`epsilon_t = 0.45 * median(D_ij) + 0.015 * sigma_W(t)`.

VR construction:

- all four vertices included,
- edge when `D_ij <= epsilon`,
- every 3-clique filled as a 2-simplex,
- every 4-clique filled as a 3-simplex.

Runtime classification uses binary Betti checks, not a full persistence filtration:

- PERSISTENT: `beta1(epsilon)>0` and `beta1(1.15*epsilon)>0`
- FRAGILE: `beta1(epsilon)>0` and `beta1(1.15*epsilon)=0`
- NO_HOLE: `beta1(epsilon)=0`

Only the classification is frozen from the 12:00 New York snapshot until the next day's 12:00 snapshot. The previous classification remains in force during the 11:00–13:00 transition gap. The fresh EUR/CAD base signal continues to recalculate hourly.

### Causal theoretical EC distance

At time `t`:

`y = [D_EC,t-1, ..., D_EC,t-20]^T`

`X` is 20x3 with columns:

1. intercept ones,
2. `[D_WE,t-1, ..., D_WE,t-20]^T`,
3. `[D_WC,t-1, ..., D_WC,t-20]^T`.

Literal RAW coefficients:

`beta_t = (X^T X)^(-1) X^T y`.

Current observation is excluded from fitting.

Prediction:

`Dhat_EC,t = beta0 + beta1*D_WE,t + beta2*D_WC,t`.

Numerical fail-closed rule for RAW: if the literal inverse is singular or fails the preregistered stable-inversion tolerance, set `K3_OLS_VALID=false`, emit `w2=0` for that observation, log the failure, and do not silently use pseudoinverse/ridge. Alternative solvers belong to a TWIN.

Directional alpha, corrected v2.1:

`alpha2 = sign(r_E + r_C) * |D_EC - Dhat_EC|`.

Base:

`base2 = 0.30 * sign(alpha2) * |alpha2| / 0.002`.

Multiplier:

- persistent: `m=1.8`
- fragile: `m=0.6`
- no hole: `m=0`

Final corrected cap:

`w2 = clip(base2*m, -0.30, +0.30)`.

At the daily schedule, the H1 candle ending 12:00 is included in the 12:00 snapshot. The scheduled topology-based adjustment is first executable at the 13:00 bar open. Other fresh alpha2 inputs continue hourly under the frozen topology class.

## K4 — Antisymmetric Coupling / Commutator

`N=20` H1 bars.

`A_t = r_W,t * sigma_W,t`.

`B_t = sample_std([r_EC,t-5, ..., r_EC,t], ddof=1)` using exactly six H1 returns, raw hourly scale, not annualized.

`alpha_D(t) = (1/20) * sum_{k=1}^{20}(A_{t-k}*B_{t-k+1} - B_{t-k}*A_{t-k+1})`.

For `k=1`, current `A_t` and `B_t` enter intentionally.

`w_total = clip(sign(alpha_D) * min(|alpha_D|/0.0005, 1), -1, 1)`.

State boundaries:

- neutral: `|w_total| < 0.05`
- long: `w_total >= 0.05`
- short: `w_total <= -0.05`

K4 recomputes at each completed H1 close.

## Base Portfolio Target

If neutral:

`W_base = [0,0,0]`.

Otherwise:

`W_base = [w_total*w1, w_total*w2, w_total*0.5*w3]`.

`w_total` determines both cluster sign and linear magnitude scaling.

## Gross Cap

Let `g = sum(abs(W_base))`.

If `g>1`, `W_cap = W_base/g`; otherwise `W_cap=W_base`.

Final aggregate gross leverage is capped at 1.0x NAV.

## Reversal Fade

When cluster sign reverses:

- Hour 1: 67% of existing exposure remains.
- Hour 2: exactly flat for the full hour.
- Hour 3: ramp new exposure linearly to 100%.

If the commutator flips again during fade, restart the fade from current exposure toward the new target. If it becomes neutral, continue the fade to zero and stop. Weights otherwise resize hourly within the current state.

## Drawdown Overlay

`DD_t = 1 - NAV_t / max_{s<=t}(NAV_s)` using mark-to-market NAV including open unrealized PnL.

Precedence is frozen:

`W_base -> W_cap -> W_fade -> W_DD -> W_stop -> W_final`.

- `DD < 0.12`: `W_DD = W_fade`
- `0.12 <= DD < 0.18`: `W_DD = W_fade * (1 - (DD-0.12)/0.06)`
- `0.18 <= DD < 0.195`: `W_DD = -0.50 * W_fade`
- `DD >= 0.195`: flatten all and set terminal strategy state.

The 19.5% kill is terminal. No automatic restart; manual/new-generation reinitialization is required.

The kill is a liquidation instruction, not a mathematical guarantee that realized execution DD can never gap beyond 20%.

## Per-Leg Stop

For each leg, rolling six-hour trigger:

`(MtM_Leg_Equity_t - MtM_Leg_Equity_{t-6}) / Current_NAV_t < -0.02`.

Marked leg equity captures realized effects from intra-window resizing and the current marked state. A triggered leg is flattened and banned from execution for 12 completed H1 bars. It continues to participate in cluster signal calculations during the ban. The rolling lookback is not reset by resizing.

## Execution Timing

- K1/K2/K4 signals from a completed H1 bar execute at the next available tick / next eligible bar open.
- K3 noon snapshot uses the H1 candle ending 12:00 and scheduled implementation at the 13:00 bar open.
- No same-close fill unless a future execution dataset can prove post-calculation quote availability; RAW default is next executable quote.

## Costs

The alpha equations assume zero costs. Backtester must separately model and report spread, slippage, swap/financing and CFD-specific execution costs. Gross and net performance must both be retained.

## RAW Invariants

Do not change author constants after PnL. Do not replace RAW singular OLS with another solver. Do not silently replace clock-hour stale-zero construction. Do not change Brent/DAX instruments or thresholds. Any alternative is a separately registered TWIN.
