# CRYPTO-ALT-MECH-7 — SUMMARY

**Global context of isolated downside vs coordinated upside, breadth×dispersion
lifecycle, field-state sequencing & cross-agent handoff.**

PARENTS: MECH-5 `244ca246` · MECH-6 `9c3dcd32` · LOWER-FIELD-2 `af2ed678`
VERDICT: **PASS_MECH7_FIELD_CONTEXT** (tentative — see 23_DECISION)

## 1. Event reconstruction parity

| family | n_events | n_dates | reversal_rate | med_fwd7_sigma |
|---|---|---|---|---|
| BAND_BROAD_UPSIDE | 61128 | 2031 | 0.588 | -0.216 |
| COORDINATED_DOWNSIDE | 58851 | 1833 | 0.552 | 0.115 |
| MULTI_BAND_UPSIDE | 39317 | 608 | 0.525 | -0.063 |
| LOCAL_CLUSTER_DOWNSIDE | 10575 | 1791 | 0.554 | 0.133 |
| OTHER | 6785 | 1150 | 0.629 | -0.335 |
| ISOLATED_DOWNSIDE_EXTREME | 1023 | 812 | 0.558 | 0.152 |
| ISOLATED_UPSIDE | 187 | 169 | 0.674 | -0.473 |

## 2. Isolated downside field anatomy (WS1)

- **ALL** (n=1023, 812 dates): state_mode=MIXED_NO_CLEAR_ROUTE, breadth30_med=0.330, disp30_med=0.311, BREADTH_EXPANDING=0.342, BTC_UP=0.532, RISK_ON=0.579
- **REVERSAL** (n=385, 350 dates): state_mode=MIXED_NO_CLEAR_ROUTE, breadth30_med=0.356, disp30_med=0.344, BREADTH_EXPANDING=0.379, BTC_UP=0.548, RISK_ON=0.631
- **PARTIAL_RECOVERY** (n=186, 178 dates): state_mode=MIXED_NO_CLEAR_ROUTE, breadth30_med=0.299, disp30_med=0.293, BREADTH_EXPANDING=0.323, BTC_UP=0.505, RISK_ON=0.543
- **CONTINUATION** (n=452, 405 dates): state_mode=MIXED_NO_CLEAR_ROUTE, breadth30_med=0.321, disp30_med=0.308, BREADTH_EXPANDING=0.319, BTC_UP=0.529, RISK_ON=0.549

## 3. Coordinated upside field anatomy (WS2)

- **ALL** (n=100445, 2110 dates): state_mode=BTC_CONCENTRATION, breadth30_med=0.446, BREADTH_EXPANDING=0.456, BTC_UP=0.631, VOL_HIGH=0.342
- **CONTINUATION** (n=43585, 2101 dates): state_mode=BTC_CONCENTRATION, breadth30_med=0.504, BREADTH_EXPANDING=0.502, BTC_UP=0.673, VOL_HIGH=0.347
- **GIVEBACK** (n=36085, 2102 dates): state_mode=MIXED_NO_CLEAR_ROUTE, breadth30_med=0.404, BREADTH_EXPANDING=0.422, BTC_UP=0.596, VOL_HIGH=0.349
- **FAILURE** (n=20775, 2074 dates): state_mode=MIXED_NO_CLEAR_ROUTE, breadth30_med=0.414, BREADTH_EXPANDING=0.419, BTC_UP=0.603, VOL_HIGH=0.320

## 4. Breadth × dispersion 2×2 (WS3)

| cell | n_days | freq_share | prop7 | reentry7 | isol_dn/day | coord_up/day | up_down_bal |
|---|---|---|---|---|---|---|---|
| HIGH_BREADTH_HIGH_DISP | 770 | 0.351 | 0.484 | 0.248 | 0.475 | 21.804 | 38.686 |
| HIGH_BREADTH_LOW_DISP | 327 | 0.149 | 0.214 | 0.401 | 0.502 | 18.034 | 27.529 |
| LOW_BREADTH_HIGH_DISP | 274 | 0.125 | 0.077 | 0.230 | 0.471 | 38.562 | -0.646 |
| LOW_BREADTH_LOW_DISP | 825 | 0.376 | 0.062 | 0.227 | 0.441 | 31.029 | 2.373 |

## 5. HIGH_BRD_HIGH_DISP lifecycle (WS4)

| dimension | path | n_episodes | median_dwell | p_7d_success | p_30d_success | p_7d_reentry |
|---|---|---|---|---|---|---|
| entry_order | BRD_FIRST | 33 | 2.0 | 0.273 | 0.121 | 0.333 |
| entry_order | DISP_FIRST | 23 | 3.0 | 0.261 | 0.304 | 0.261 |
| entry_order | FRESH | 23 | 7.0 | 0.217 | 0.261 | 0.391 |
| exit_order | BRD_FIRST_EXIT | 28 | 3.5 | 0.143 | 0.250 | 0.321 |
| exit_order | COUPLED_EXIT | 19 | 7.0 | 0.368 | 0.368 | 0.421 |
| exit_order | DISP_FIRST_EXIT | 31 | 2.0 | 0.290 | 0.097 | 0.258 |
| exit_order | STAYS_HH | 1 | 3.0 | 0.000 | 0.000 | 1.000 |

## 6. Breadth composition (WS5)

- **R1_25**: med_breadth_7d=0.491, share_of_top500=0.272, corr_total=0.353
- **R26_100**: med_breadth_7d=0.440, share_of_top500=0.259, corr_total=0.386
- **R101_250**: med_breadth_7d=0.433, share_of_top500=0.254, corr_total=0.398
- **R251_500**: med_breadth_7d=0.368, share_of_top500=0.216, corr_total=0.390

## 7. Breadth primitive audit (WS6)

| model | features | d_logloss | d_brier | d_auc | cv_auc |
|---|---|---|---|---|---|
| M0_level | breadth level | 0.000 | 0.000 | 0.000 | 0.899 |
| M+velocity | velocity:breadth_vel | 0.011 | 0.003 | -0.016 | 0.883 |
| M+acceleration | acceleration:breadth_accel | 0.013 | 0.003 | -0.006 | 0.893 |
| M+persistence | persistence:breadth_persistence | 0.024 | 0.011 | -0.049 | 0.850 |
| M+divergence | divergence:breadth_divergence | 0.016 | 0.007 | -0.023 | 0.876 |
| M+oscillation | oscillation:breadth_oscillation | 0.016 | 0.006 | -0.027 | 0.872 |
| M+depth | depth:rank_depth_rel+depth:med_ret30_201_500 | -0.028 | -0.011 | -0.005 | 0.894 |
| M+composition | composition:pos_vel7_share+composition:pos_ret_share | -0.002 | -0.001 | -0.020 | 0.879 |
| M_FULL | all breadth families | 0.031 | 0.013 | -0.053 | 0.845 |

## 8. Rank deterioration × isolated shock bridge (WS9)

- **RANK_STABLE** (n=35): reversal=0.571, med_fwd7_sigma=0.152, med_ret1d=-0.109
- **RANK_IMPROVING** (n=316): reversal=0.487, med_fwd7_sigma=-0.037, med_ret1d=-0.177
- **RANK_DETERIORATING** (n=672): reversal=0.591, med_fwd7_sigma=0.251, med_ret1d=-0.153

## 9. Dead-node reinterpretation (WS10)

See 17_DEAD_NODE_REINTERPRETATION.csv. SHMC and volatility rechecks were
run against the LF2 frame; RETEST_RELOAD / early-decay / accumulation
carried from M4/M5 audits; sector and broad-sector organization remain
DATA_BLOCKED (no residual sensor).

## 10. Sequence atlases (WS7/WS8)

12_COORDINATED_UP_SEQUENCE_ATLAS.csv and 13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv
report persistent atom sequences (0-3D and 0-3-7D) around event dates
with lift vs event-date baseline and FDR.

## 11. Cross-agent export (WS11)

20_CROSS_AGENT_FIELD_CONTEXT.parquet: one row per lower-field extreme
event with full canonical global field context at t0 (schema:
20b_CROSS_AGENT_FIELD_CONTEXT_SCHEMA.md). No target leakage.

## 12. Governance

TERRAIN ONLY. human_review_required = TRUE · next_checkpoint_authorized = FALSE

## 13. First-divergence interpretation (WS1/WS2, outputs 15/16)

**Coordinated upside — continuation vs giveback** (n_cont=43,585 / n_gb=36,085):
ALL key coordinates already separate at **-14D**, i.e. the field state two
weeks BEFORE the push largely determines whether the coordinated push
continues or gives back:

| coordinate | continuation med | giveback med | first sig lag |
|---|---|---|---|
| top500_breadth_30d | 0.392 | 0.359 | -14D |
| btc_return_30d | 0.047 | 0.034 | -14D |
| top500_dispersion_30d | 0.349 | 0.331 | -14D |
| med_ret30_201_500 | -0.011 | -0.022 | -14D |

A coordinated push arriving into an already-broad, BTC-supported,
disperse-but-breadth-deep field continues; the same surface move arriving
into a narrower field gives back. **Continuation vs giveback is largely
pre-determined by pre-event field state, not by the push itself.**

**Isolated downside — reversal vs continuation** (n_rev=385 / n_con=452):

| coordinate | reversal med | continuation med | first sig lag |
|---|---|---|---|
| top500_dispersion_30d | 0.347 | 0.293 | -14D |
| btc_return_30d | 0.030 | 0.001 | -7D |
| med_ret30_201_500 | -0.013 | -0.042 | +1D |
| top500_breadth_30d | 0.405 | 0.298 | +3D |

For isolated downside, the pre-event predictors are **dispersion and BTC
strength** (reversal more likely when the field is fragmented and BTC is
supportive), while **breadth rises only AFTER the reversal begins** (breadth
is a concurrent confirmation, not a predictor of isolated-down reversal).

**Asymmetry:** coordinated-upside outcome is predictable from pre-event field
breadth/depth (L1 temporal ordering, no causal claim); isolated-downside
reversal is predicted by dispersion/BTC, with breadth as confirmation.
