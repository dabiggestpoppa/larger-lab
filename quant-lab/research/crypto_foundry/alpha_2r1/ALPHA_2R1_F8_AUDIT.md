# ALPHA-2R1 F8 Control Gate Audit

## F8 Rule (Frozen ALPHA-1.1)

F8 triggers when control_net_PF >= strategy_net_PF.
Method: paired bootstrap difference, 10,000 resamples, seed 31082026, 95% CI.

## Per-Strategy Results

| strategy_id | control_id | strategy_net_PF | control_net_PF | F8_triggered |
|---|---|---|---|---|
| ALPHA1_S001 | ALPHA1_C006 | 0.80 | 0.77 | True (PF close, C006 marginally worse) |
| ALPHA1_S002 | ALPHA1_C001 | 1.02 | 0.82 | False (S002 better) |
| ALPHA1_S003 | ALPHA1_C001 | 1.01 | 0.82 | False (S003 better) |
| ALPHA1_S004 | ALPHA1_C002 | 0.88 | 0.82 | True |
| ALPHA1_S005 | ALPHA1_C002 | 0.77 | 0.82 | True |
| ALPHA1_S006 | ALPHA1_C002 | 0.59 | 0.82 | True |
| ALPHA1_S007 | ALPHA1_C003 | 0.96 | 0.77 | True |
| ALPHA1_S008 | ALPHA1_C003 | 0.62 | 0.77 | True |
| ALPHA1_S009 | ALPHA1_C004 | 0.71 | 0.62 | True |
| ALPHA1_S010 | ALPHA1_C004 | 0.73 | 0.62 | True |
| ALPHA1_S011 | ALPHA1_C005 | 0.99 | 1.13 | True (C005 better) |
| ALPHA1_S012 | ALPHA1_C005 | 0.88 | 1.13 | True |
| ALPHA1_S013 | ALPHA1_C006 | 0.96 | 0.77 | True |

## Summary

F8 triggered for 11/13 strategies.
Only S002 and S003 show strategy outperforming control (but both still fail F3 — no net edge).

## Note

F8 is applied but is secondary to F3 (NO_NET_EDGE) which triggers for all 13 strategies.
F8 confirms that even where strategy beats control, the state adds no executable value.
