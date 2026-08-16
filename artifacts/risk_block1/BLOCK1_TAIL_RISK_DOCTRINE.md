# BLOCK-I TAIL-RISK DOCTRINE (R4 authoritative)

Paths are kept distinct: **historical** (sealed ledger), **resampled**
(block bootstrap), **synthetic stress** (tail injections).

## Tail-shock stress (synthetic, at f = 1%)

| variant | max DD | terminal equity |
|---|---|---|

| historical | 10.0% | 20.80x |
| worst5_x1_25 | 10.4% | 18.43x |
| worst5_x1_50 | 12.3% | 16.31x |
| worst5_x2_00 | 16.0% | 12.74x |
| insert_worst_1 | 10.0% | 20.04x |
| insert_worst_2_consec | 10.9% | 19.38x |
| insert_p99_loss_cluster | 17.6% | 17.92x |

- Amplifying the worst 5% of losses 1.25x/1.5x/2x moves max DD
  10.4% /
  12.3% /
  16.0% (baseline
  10.0%)
- A 5-trade p99-loss cluster raises max DD to 17.6%
  (terminal 17.92x vs 20.80x baseline)

## Loss-streak stress (median loser = -0.64R)

| f | 5-streak DD | 10-streak DD | 15-streak DD |
|---|---|---|---|

| 0.5% | 1.6% | 3.2% | 4.7% |
| 1.0% | 3.2% | 6.3% | 9.2% |
| 2.0% | 6.3% | 12.2% | 17.7% |
| 5.0% | 15.1% | 27.9% | 38.8% |

## Doctrine

Historical, resampled and synthetic paths are NOT interchangeable. Survival
claims must cite which path type produced them. Technical ruin was zero under
the tested historical-resampling framework at all ladder fractions - that is a
framework property (strong edge), NOT a safety certificate.
