# INFORMATION-FLOW REPORT (Workstream J)

## Method

Transfer entropy (lag-1, 3-bin discretization) between state/flow drivers and
band/chain outcomes, computed after the simpler lagged-correlation tests
(workstreams A/E). Significance via 200 null permutations of the driver series
(block-shuffled, fixed seed). Only three pairs were preregistered for this
checkpoint — this is a confirmation test on the strongest simple results, not a scan.

## Results (`16_INFORMATION_FLOW.csv`)

| pair | TE (nats) | surrogate p | n |
|---|---|---|---|
| CHAIN_TVL → NATIVE_IMPROVING | 1.109 | **0.005** | 2196 |
| STABLECOIN → BAND11_25_VEL | 0.419 | 0.075 | 2196 |
| STABLECOIN → BREADTH | 1.105 | 0.542 | 2196 |

## Reading

1. **Chain TVL → native-asset improvement: significant (p=0.005).** Chain liquidity
   expansion carries incremental information about next-day improvement in
   chain-native Top-500 assets, beyond what the unconditional correlation tests
   (workstream E, 77 FDR-significant links) already showed. This is the cleanest
   informational-flow result of the checkpoint and corroborates
   CHAIN_FLOW_HIERARCHY at L3.
2. **Stablecoin → band velocity: marginal (p=0.075).** Directionally consistent with
   workstream E's STABLECOIN_LEADS_TVL links but does not reach significance — the
   stablecoin channel remains WEAK.
3. **Stablecoin → breadth: not significant (p=0.542).** Stablecoin expansion does
   not carry information about next-day market breadth beyond the unconditional
   relationship.

## Caveats

- Transfer entropy is a predictive-information diagnostic, not physical causality;
  all causal claims are kept at the levels assigned in `11_CAUSALITY_LADDER.csv`
  (CHAIN_FLOW_HIERARCHY L3; INFORMATION_FLOW L2).
- Only 3 pairs tested — no multiple-testing correction was required, and the single
  significant result is corroborated independently by E.
