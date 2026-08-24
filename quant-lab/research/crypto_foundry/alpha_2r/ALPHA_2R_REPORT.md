# ALPHA-2R Report

**Checkpoint:** CRYPTO-ALPHA-2R-ENGINE-TRUTH-REPAIR-AND-SEALED-REPLAY
**Timestamp:** 2026-08-24T17:24:20.745206+00:00
**Scientific Parent:** 5a6a4407b042b0ca6013a1c71e0241c6fefae433
**Quarantined ALPHA-2:** 21a426f1c33445e33f51cdc86c6d2dfed2b7ddd5
**Registry Hash Verified:** 2abaf8c21200a67e...

## Repairs Applied

1. **Funding Sign**: LONG pays when funding > 0 (Hyperliquid venue convention)
2. **Funding Frequency**: hourly settlements using actual Hyperliquid observations
3. **F8 Control Gate**: mechanical PF comparison trigger
4. **Control Mapping**: all 13 strategies mapped to controls for F8

## Price-Path Invariance

- Strategy trade counts: CHECK MANUALLY
- Gross EV: same strategies preserved

## Data

- Development period: 2026-01-25 to 2026-06-15
- BTC bars: 3401
- ETH bars: 3401
- BTC funding obs: 28175
- ETH funding obs: 28175

## Results

- **ALPHA1_S001**: FALSIFIED | trades=848 | ee=169 | net_EV=-9.39bps | net_PF=0.48 | WR=16.2%
- **ALPHA1_S002**: FALSIFIED | trades=212 | ee=87 | net_EV=-6.83bps | net_PF=0.91 | WR=45.8%
- **ALPHA1_S003**: FALSIFIED | trades=174 | ee=96 | net_EV=-4.35bps | net_PF=0.67 | WR=10.3%
- **ALPHA1_S004**: FALSIFIED | trades=344 | ee=140 | net_EV=-9.85bps | net_PF=0.59 | WR=22.4%
- **ALPHA1_S005**: FALSIFIED | trades=45 | ee=30 | net_EV=-24.66bps | net_PF=0.50 | WR=26.7%
- **ALPHA1_S006**: FALSIFIED | trades=30 | ee=25 | net_EV=-9.33bps | net_PF=0.71 | WR=33.3%
- **ALPHA1_S007**: FALSIFIED | trades=205 | ee=62 | net_EV=-13.21bps | net_PF=0.57 | WR=23.4%
- **ALPHA1_S008**: FALSIFIED | trades=76 | ee=22 | net_EV=-26.17bps | net_PF=0.43 | WR=19.7%
- **ALPHA1_S009**: FALSIFIED | trades=234 | ee=132 | net_EV=-19.37bps | net_PF=0.41 | WR=19.2%
- **ALPHA1_S010**: FALSIFIED | trades=259 | ee=137 | net_EV=-18.65bps | net_PF=0.44 | WR=16.2%
- **ALPHA1_S011**: FALSIFIED | trades=79 | ee=70 | net_EV=-3.65bps | net_PF=0.56 | WR=10.1%
- **ALPHA1_S012**: FALSIFIED | trades=78 | ee=67 | net_EV=-18.47bps | net_PF=0.40 | WR=19.2%
- **ALPHA1_S013**: FALSIFIED | trades=431 | ee=123 | net_EV=-0.09bps | net_PF=1.00 | WR=33.2%

## Falsification Counts

- F1: 0 strategies
- F2: 2 strategies
- F3: 13 strategies
- F4: 9 strategies
- F5: 3 strategies
- F6: 3 strategies
- F7: 5 strategies
- F8: 11 strategies
- F9: 0 strategies
- F10: 3 strategies
- F11: 0 strategies
- F12: 1 strategies

## Survivors: 0
## Weak: 0
## Falsified: 13
## Insufficient: 0
## Control Equivalent: 0
## Cost Fragile: 0

## Forward Candidates: 0

## Engine Integrity: PASS
## Future Perturbation (F9): PASS

## Next Checkpoint
CRYPTO-ALPHA-3-FAILURE-ANATOMY-AND-NEW-HYPOTHESES