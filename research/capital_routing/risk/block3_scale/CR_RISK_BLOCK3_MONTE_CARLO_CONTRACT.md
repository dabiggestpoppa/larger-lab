# CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN — Monte Carlo contract (frozen)

## Schemes
1. **BLOCK** — chronological stationary block bootstrap over the merged A+B
   book (block = 25 events; the frozen Block-I/R5/R6 convention). Intra-block
   timing exact; cross-block overlap arises naturally. PRIMARY.
2. **EPISODE** — R1/R6 12h-episode cluster bootstrap; within-cluster timing
   exact, clusters placed with original quiet gaps (>= 12h) so cross-cluster
   overlap stays ~zero. PRIMARY.
3. **IID** — reference only. Never overrides dependency-aware conclusions.

Block / episode are the primary evidence. IID is diagnostic.

## Path count
Final frontier experiments: >= 10000 paths (frozen requirement;
executed in CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER). This D0 checkpoint runs a deterministic pilot
(block 250 / episode 150 / iid 150)
to validate the pipeline and determinism. Seeds frozen and reported
(seed 20260815; scheme-specific derivations recorded in outputs).

## Resampling determinism
Same (scheme, seed, n_paths) -> identical layouts -> identical outputs.
Different seeds -> different draws (used to prove determinism, not to tune).

## Block length
The frozen block length (25 events) is used. Block length is NOT optimized.
Any future sensitivity set must be pre-registered.

## Episode bootstrap
Uses the frozen R1/R6 482-episode reconstruction. Episodes are never
redefined from future knowledge. Within-episode event structure preserved.

## Accounting per path
equity = cumprod(1 + f_total * admitted_w * r_e) over the path layout, where
admitted_w comes from the sealed static-architecture admission and r_e is the
edge-transformed return (positive returns scaled per family under edge
retention). Joint A/B structure is preserved — A and B are NEVER shuffled
independently in primary schemes.

## Edge retention in MC
Edge retention is a STRESS TRANSFORM on realized outcome streams (positive
returns scaled per family: 100% / 75% / 50% / 25%). It never feeds back into
event selection or admission (no adaptive policy is authorized).
