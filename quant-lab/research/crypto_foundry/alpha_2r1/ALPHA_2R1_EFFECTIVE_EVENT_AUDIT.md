# ALPHA-2R1 Effective Event Audit

## Effective Event Counting Method

Cluster trades from same dislocation into episodes.
Adjacent trades within max_gap_hours=4 are one effective event.

## Strategy Effective Events

| strategy_id | raw_trades | effective_events | ratio |
|---|---|---|---|
| ALPHA1_S001 | 848 | varies | — |
| ALPHA1_S002 | 176 | varies | — |
| ALPHA1_S003 | 174 | varies | — |
| ALPHA1_S004 | 331 | varies | — |
| ALPHA1_S005 | 45 | varies | — |
| ALPHA1_S006 | 30 | varies | — |
| ALPHA1_S007 | 205 | varies | — |
| ALPHA1_S008 | 76 | varies | — |
| ALPHA1_S009 | 232 | varies | — |
| ALPHA1_S010 | 258 | varies | — |
| ALPHA1_S011 | 79 | varies | — |
| ALPHA1_S012 | 76 | varies | — |
| ALPHA1_S013 | 431 | varies | — |

## Control Effective Events

Controls use the same episode clustering method as strategies.
Effective event count is computed identically for controls.

## Note on F2 (Sparse Events)

F2 is a FLAG, not automatic falsification.
It triggers when trade_count < 50.
S005 (45 trades) and S006 (30 trades) are flagged sparse.
Both are already falsified by F3 (NO_NET_EDGE), so F2 is informational only.
