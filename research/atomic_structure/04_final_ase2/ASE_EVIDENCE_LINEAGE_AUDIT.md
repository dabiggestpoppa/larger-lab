# ASE_EVIDENCE_LINEAGE_AUDIT.md

Checkpoint: ASE-2.3-FINAL-MECHANISM-AND-RLOCK-FALSIFICATION-SEAL
Branch: agent/atomic-structure-foundry
Base: 846fa919f13fa50d67bcb734f6c297a0c35f5c80

## Purpose

Evidence status must be carried forward with discipline: a previously sealed
evidence category may only be downgraded if a later experiment directly
falsifies it. This audit reconstructs the lineage and resolves the one
unsupported mutation found (ASE-2.2 recording `SCALE = WEAK`).

## Lineage (from the four official decision files)

| Checkpoint | Decision file | Status | SCALE | NORMALIZATION | STATE | TIME | CAUSALITY |
|---|---|---|---|---|---|---|---|
| ASE-1.1 | ASE_R1_1_DECISION.json | CONTRACT_REPRODUCED_WITH_DATA_DRIFT | PASS | PASS | PASS | PASS | PASS |
| ASE-2   | ASE_R2_DECISION.json     | PARTIAL_TRANSITION_STRUCTURE  | (absent) | (absent) | (absent) | (absent) | (absent) |
| ASE-2.1 | ASE_R2_1_DECISION.json  | PARTIAL_TRANSITION_STRUCTURE  | (absent) | (absent) | (absent) | (absent) | PASS |
| ASE-2.2 | ASE_R2_2_DECISION.json  | PARTIAL_TRANSITION_STRUCTURE  | WEAK | PASS | PARTIAL | PARTIAL | PASS |

## The SCALE transition — resolution

- ASE-1.1 sealed SCALE = PASS on the basis of the Generation-A gated
  calibration: `AR > 45` NO-GO gate, k=3 on the calibration universe,
  frozen-centroid transport stability, and the tier reproduction itself.
- ASE-2 recorded no evidence matrix at all (an omission, neither a pass nor
  a downgrade).
- ASE-2.1 recorded CAUSALITY separately as PASS.
- ASE-2.2 is the FIRST file to record `SCALE = WEAK`. No scale-specific
  experiment (cluster rediscovery, centroid transport, or tier distribution)
  was run in ASE-2.2, and ASE-2.2's mission was noon/post-25 event-geometry +
  scoring completion. The `WEAK` marker there is therefore **not supported
  by a direct falsification test**.

## Ruling

Per the ASE evidence policy (sealed category may only be downgraded by a
direct falsifying experiment):

- `SCALE = PASS` from ASE-1.1 is RESTORED as the carried classification.
- The ASE-2.2 `SCALE = WEAK` value is recorded as an unbacked editorial
  inference, archived in the lineage JSON as `downgrade_supported: false`,
  and does not count as a falsification.
- ASE-2.3 keeps `SCALE = PASS` throughout, except as a direct scope
  limitation: ASE-2.3 does not re-test tier scale; it tests the surviving
  R_LOCK mechanism.

Note for downstream readers: ASE-2.3's final decision may still be negative
for the broad transition engine on STATE/TIME grounds; that is a legitimately
recorded set of falsifications (remaining-range hierarchy OOS, transition
scoring OOS), not an SCALE downgrade.

## Frozen falsified / unsupported hypotheses (not to be rescued)

- NOON_LOCK_GENERAL: NOT SUPPORTED (T3 H17 touch hold 36%, not ~98%)
- POST25_UNIVERSAL_LOCK: NOT SUPPORTED (reversal 50% overall / 23% T3, not
  ~4.2%)
- REMAINING_RANGE_ATOMIC_HIERARCHY: NOT SUPPORTED OUT OF SAMPLE (matched
  evaluation; hierarchy MAE 0.24-0.53 worse than B0; bootstrap P(improve)=0.0005)
- NEXT_LOOP_DIRECTION_ATOMIC_STATE: NOT SUPPORTED OUT OF SAMPLE
- FAILURE_TYPE_DIRECTIONAL_EDGE: LOW / NOT SUPPORTED