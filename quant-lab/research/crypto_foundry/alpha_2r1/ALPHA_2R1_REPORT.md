# ALPHA-2R1 Report

**Checkpoint:** CRYPTO-ALPHA-2R1-PRICE-PATH-ENGINE-TRUTH-SEAL-AND-FINAL-REPLAY
**Timestamp:** 2026-08-24T17:53:50.383104+00:00
**Base SHA:** e3090083
**Registry Hash Verified:** 2abaf8c21200a67e...

## Engine Provenance

- ALPHA-2: QUARANTINED_ENGINE_ERROR (cross-asset contamination + wrong funding sign)
- ALPHA-2R: QUARANTINED_REPLAY_INTEGRITY (funding fixed but price-path changed)
- ALPHA-2R1: FINAL TRUSTED RESULT (price-source isolated, frozen signal ledger)

## Root Cause: Cross-Asset Contamination

The old ALPHA-2 exit used `bar["perp_close"]` for exit price execution.
Per frozen contract, exit execution should be `next_bar_open`.
The old code exited at current bar close, not next bar open.
This created different exit prices vs the corrected engine.

## Results

- **ALPHA1_S001**: FALSIFIED | trades=848 | net_EV=-5.93 | net_PF=0.80
- **ALPHA1_S002**: FALSIFIED | trades=176 | net_EV=1.28 | net_PF=1.02
- **ALPHA1_S003**: FALSIFIED | trades=174 | net_EV=0.24 | net_PF=1.01
- **ALPHA1_S004**: FALSIFIED | trades=331 | net_EV=-4.24 | net_PF=0.88
- **ALPHA1_S005**: FALSIFIED | trades=45 | net_EV=-10.95 | net_PF=0.77
- **ALPHA1_S006**: FALSIFIED | trades=30 | net_EV=-21.47 | net_PF=0.59
- **ALPHA1_S007**: FALSIFIED | trades=205 | net_EV=-1.75 | net_PF=0.96
- **ALPHA1_S008**: FALSIFIED | trades=76 | net_EV=-21.33 | net_PF=0.62
- **ALPHA1_S009**: FALSIFIED | trades=232 | net_EV=-12.29 | net_PF=0.71
- **ALPHA1_S010**: FALSIFIED | trades=258 | net_EV=-11.82 | net_PF=0.73
- **ALPHA1_S011**: FALSIFIED | trades=79 | net_EV=-0.19 | net_PF=0.99
- **ALPHA1_S012**: FALSIFIED | trades=76 | net_EV=-4.48 | net_PF=0.88
- **ALPHA1_S013**: FALSIFIED | trades=431 | net_EV=-1.18 | net_PF=0.96

## Falsification Counts

- F1: 0
- F2: 2
- F3: 11
- F4: 5
- F5: 0
- F6: 7
- F7: 8
- F8: 7
- F9: 0
- F10: 4
- F11: 0
- F12: 1

## Survivors: 0
## Falsified: 13

## Signal Ledger Hash: 5aae7a639c5344e7...

## Next: CRYPTO-ALPHA-3-FAILURE-ANATOMY-AND-NEW-HYPOTHESES