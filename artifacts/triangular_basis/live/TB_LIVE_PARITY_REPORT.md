# TB-LIVE-PARITY-02 Report

Canonical commit: 2435d04e77eb31b42ab14ba76482efb729965b83
Architecture commit: 683ba90124cd5dd43367430d4cd4faa667fa02ea
Strategy file SHA256: 657d30ece2a8dbf0a6373f176038b706...
Config: lookback=200 entry_z=2.5 stop_z=6.0 London-only

## Data
- GBPAUD bars: 277100
- GBPNZD bars: 277117
- AUDNZD bars: 279540
- Synchronized snapshots: 265809

## Parity Results
- basis comparisons: 265809 | divergence: 0 | max diff: 0.00e+00
- zscore comparisons: 265809 | divergence: 0 | max diff: 0.00e+00
- session sample rows: 267
- PATH A trades: 405 | PATH B opens: 405 | closes: 405
- Entries only in A: 0 | only in B: 0

## Exactly-Once
- Duplicate reprocess -> no_action: True

## Missing Leg
- None snapshot graceful: no_action

## Restart
- split: 132904 | resumed active baskets: 0

## Isolation
- Triangular magic: 31082026 | Symmetry magic: 20260531 | unique: True

## Acceptance
- GATE A (bar/basis divergence): PASS
- GATE B (magic unique): PASS
- GATE E (exactly-once): PASS
- GATE G (no magic collision): PASS

Overall: PASS
