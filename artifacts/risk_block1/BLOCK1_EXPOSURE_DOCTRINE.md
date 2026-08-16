# BLOCK-I EXPOSURE DOCTRINE (R1/R1.1 + R4 authoritative)

## Concurrency

- max **3** simultaneous positions (never 4+)
- in-market hours 4735 (18.9% of calendar)
- 2-position hours 565; 3-position hours 20
- same-direction overlap 367h; opposing 228h

## Exposure states (R4_ACCOUNT_HEAT_STATES)

| state | hours | gross R median | gross R max | net R max |
|---|---|---|---|---|
| 0_position | 20377 | 0.00 | 0.00 | 0.00 |
| 1_position | 4150 | 0.76 | 1.00 | 1.00 |
| 2_opposing | 218 | 1.49 | 1.91 | 0.59 |
| 2_same_dir | 347 | 1.41 | 1.82 | 1.82 |
| 3_positions | 20 | 2.22 | 2.39 | 2.39 |

## Key truths

- **OPPOSING POSITIONS ARE NOT AUTOMATICALLY RISKLESS**: A long USDJPY (Family A)
  and B short USDJPY (Family B) do not cancel economically - they hedge the same
  instrument but at different times/vols; gross heat during opposing overlap is
  real (R1: opposing heat up to 1.00R).
- Worst portfolio CAE 3.06R -> **3.1%**
  account impact at f=1% (R4_ACCOUNT_HEAT_MAP).
- **Overlap-exact vs sequential**: at f=1% the worst day under real overlap is
  -5.6% vs -3.7% sequential - overlap materially
  worsens the downside day; R4 uses the overlap-exact hourly path as authoritative.
- Episodes (R1.1 repaired): 71.5% of events sit in >=2-event 12h clusters, but
  conditional expectancy is flat across within-cluster rank (8.6/8.4/7.5/10.1 bps)
  - clustered events behave **independent, not duplicated** (descriptive; episode
  sizing is NOT authorized).
