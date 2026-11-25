# SENSOR-B5-P3-R6-FINAL-VERIFICATION-R1 - evidence index

Mission: `SENSOR-B5-P3-R6-FINAL-VERIFICATION-R1`
Directive: `AUTHORIZE_R6_BOUNDED_VERIFICATION_AND_REPAIR`
Branch: `agent/crypto-sensor-fabric-p3-production-master-r1`
Starting SHA: `5ee268b1d872fe4040d2d1505d012f344e7b5d54`
Verified candidate SHA: `868dd3fc91b5a38d02742bd3705da0c1d78b66c3`

Disposition: **`P3_RUNG6_CANONICAL_GREEN_AWAITING_OPERATOR_ACCEPTANCE`**

The canonical Rung 6 execution over the frozen candidate is `COMPLETE`
(`ANCHORED_COMPLETE`) with `test_outcome = GREEN`: 4,952 anchored nodes,
4,941 passed, 0 failed, 0 errored, 11 explained skips, 0 missing, 0 extra,
0 duplicate executions. This is a verification result, not an acceptance:
provider approval, custody-source authorization, manifest activation, trust
promotion, gate advancement and Bloc 6 are all untouched (see 04 and 05).

## Contents

| File | What it records |
| --- | --- |
| `01_FINAL_IMPLEMENTATION_AND_REPAIR_LADDER.md` | The commit ladder from the starting SHA to the verified candidate, and what each repair changed. |
| `02_H01_H06_DISPOSITIONS.md` | H01-H06: the defect, the repair, the executed evidence that closes it, and what remains outside this mission. |
| `03_CANONICAL_EXECUTION.md` | Collection anchor, the four execution attempts, the green bundle's totals, digests, artifact hashes, environment and skip reasons. |
| `04_GOVERNANCE_AND_INVARIANTS.md` | G16 and G17 disclosures, audit/producer reconciliation, manifest and `INTEGRATION_REQUIRED` invariants, inventory. |
| `05_LIMITATIONS_AND_RUNG7.md` | What this package does not prove, the unresolved contracts, and the Rung 7 recommendation. |
| `rung6_final_r1.json` | The same facts as a machine-readable record. |

## Reproduction

Run from `quant-lab` in the worktree, with the environment pinned as recorded:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONIOENCODING=utf-8 \
python3 research/crypto_sensor_fabric/scripts/canonical_runner.py run \
  --worktree "<worktree>" \
  --expect-branch agent/crypto-sensor-fabric-p3-production-master-r1 \
  --workers 1 --timeout 5400 --run-id p3-r6-final \
  --expect-count 4952 \
  --expect-digest f2fc909032b3a182bdccd47946af16d4ac179148d3615e60b3e0131c239d1931
```

and re-evaluate the result independently of the run:

```bash
python3 research/crypto_sensor_fabric/scripts/canonical_runner.py verify \
  <bundle>/evidence.json --expect-count 4952 \
  --expect-digest f2fc909032b3a182bdccd47946af16d4ac179148d3615e60b3e0131c239d1931 \
  --require-anchor
```
