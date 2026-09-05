# ALT_MECH_2 — STATE DEFINITIONS

All states are **single-condition, point-in-time, and preregistered** (see
`01_PREREGISTRATION.md` §4). A state holds on day `t` using only information available at
`t`. No combination explosion; states may overlap and their overlap is measured, not
assumed separable.

## 1. Market-condition states (daily, terrain + computed factors)

| State | Condition | Rationale |
|---|---|---|
| `BTC_UP` | btc_return_30d > 0 | broad risk-on / trend filter |
| `BTC_DOWN` | btc_return_30d < 0 | risk-off / trend filter |
| `VOL_HIGH` | median Top-500 realized vol 30d ≥ trailing-252 P70 | elevated volatility regime |
| `VOL_LOW` | median Top-500 realized vol 30d ≤ trailing-252 P30 | calm regime |
| `BREADTH_EXPANDING` | top500_breadth_30d ≥ 0.50 | more than half of Top-500 positive over 30D |
| `BREADTH_CONTRACTING` | top500_breadth_30d < 0.50 | narrow participation |
| `SC_INFLOW` | stablecoin_change_30d > 0 (AVAILABLE_NEXT_DAY) | stablecoin capital expanding |
| `SC_OUTFLOW` | stablecoin_change_30d < 0 (AVAILABLE_NEXT_DAY) | stablecoin capital contracting |
| `CONC_RISING` | top-3 mcap share change over 7D > 0 | capital concentrating into leaders |
| `CONC_FALLING` | top-3 mcap share change over 7D < 0 | capital broadening away from leaders |

Sample rule: ≥120 trading days required for any state to be tested.

## 2. Routing states (MECH-1 `routing_analysis` taxonomy, descriptive)

Reused unchanged from MECH-1 (empirically classified, not hardcoded):

`STABLECOIN_PARKING`, `CAPITAL_EXIT`, `BROAD_RISK_EXPANSION`, `NARROW_LEADERSHIP`,
`ETH_BROADENING`, `LARGE_ALT_ROTATION`, `MID_CAP_ROTATION`, `SMALL_CAP_ROTATION`,
`BTC_CONCENTRATION`, `MIXED_NO_CLEAR_ROUTE`.

Used as the object alphabet for morphism detection (Workstream G).

## 3. Failure / exhaustion signature patterns (Workstream F)

Date-level and asset-level patterns, fixed definitions (see preregistration §8):

`LEADER_WITHOUT_BREADTH`, `VELOCITY_WITHOUT_SHARE`, `TVL_WITHOUT_PARTICIPATION`,
`BREADTH_AND_CONCENTRATION`, `LOWER_RANK_ACCELERATION`.

## 4. Causal-evidence levels (Workstream I)

`L0` descriptive co-movement → `L1` temporal ordering → `L2` conditional lead-lag →
`L3` common-factor-robust → `L4` subperiod/regime-robust → `L5` supported mechanism →
`L6` quasi-causal (defensible assumptions only).

Every claim is assigned the highest level whose entire lower chain passes.
