# SENSOR-B5-P3-R6-FINAL-CLOSEOUT-R3 - evidence index

Mission: `SENSOR-B5-P3-R6-FINAL-CLOSEOUT-R3`
Directive: `AUTHORIZE_FINAL_CANONICAL_EXECUTION`
Branch: `agent/crypto-sensor-fabric-p3-production-master-r1`
Final repaired candidate: `66200f3cb18ee5cea1483d986e64502f388eeb77`
Previous canonical candidate: `868dd3fc91b5a38d02742bd3705da0c1d78b66c3`
Previous decision package: `21fd7e473a534c38b237729f9474c46bb94267ee`
Independent pre-repair audit: `d6b3f9f83a0cf5bb92f8e37b72e044beeaed6740`
(`agent/crypto-sensor-fabric-p3-production-master-audit-r3`, "arm the closure
reattack and pin the baseline")

Disposition: **`P3_CANONICAL_GREEN_AWAITING_FINAL_INDEPENDENT_RECONCILIATION`**

The canonical regression over the repaired candidate is `COMPLETE`
(`ANCHORED_COMPLETE`) with `test_outcome = GREEN`: **4,968** anchored nodes,
**4,957 passed, 0 failed, 0 errored, 11 explained skips, 0 missing, 0 extra,
0 duplicate executions**, guarded-evidence restoration attempted and verified,
tracked tree clean after. The hardened verifier reproduces that verdict from the
raw result stream with the external collection anchor supplied
(`--expect-count 4968 --expect-digest 45c206d6... --require-anchor`), exit 0.

Operator directive reconciled the outstanding sequencing dependency: this
canonical execution was authorized to proceed while Agent 2 performs its
targeted reattack. Agent 2's targeted acceptance has **not** been received, and
none is claimed here. That is the only reason this package is not
`P3_FINAL_REPAIRS_CLOSED_CANONICAL_GREEN_AWAITING_RATIFICATION`.

This is a verification result, not an acceptance: provider approval, custody-
source authorization, manifest activation, trust promotion, gate advancement and
Bloc 6 are all untouched.

## Contents

| File | What it records |
| --- | --- |
| `01_FINAL_CANDIDATE_AND_REPAIRS.md` | Freeze verification, the F4 and F5 repairs, their targeted controls and mutation results, and the executable replay-binding guard disposition. |
| `02_CANONICAL_EXECUTION_R2.md` | Universe recollection, the anchor, execution accounting, the eleven explained skips, restoration, artifact hashes and verifier output. |
| `03_EVIDENCE_HANDOFF_TO_AGENT2.md` | The Agent 2 handoff: bundle path, inventory, anchor, partition manifest, raw streams, baseline and re-measurement instructions. |
| `04_GOVERNANCE_RECONCILIATION.md` | Invariants re-measured at this candidate, manifest byte-identity, inventory, and the reconciliation of previously accepted controls. |
| `05_RUNG7_RECOMMENDATION_R1.md` | The updated Rung 7 acceptance recommendation and what this package does not prove. |
| `rung6_final_r2.json` | The same facts as a machine-readable record. |

## Reproduction

Run from `quant-lab` in the worktree, with the environment pinned as recorded:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
python3 research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py run \
  --worktree "<worktree>" \
  --expect-branch agent/crypto-sensor-fabric-p3-production-master-r1 \
  --workers 1 --timeout 5400 --run-id p3-r6-final-r3 \
  --expect-count 4968 \
  --expect-digest 45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9
```

Re-check the preserved bundle without executing anything:

```bash
python3 research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py verify \
  "<bundle>/evidence.json" \
  --expect-count 4968 \
  --expect-digest 45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9 \
  --require-anchor
```

Calibration note: `pyproject.toml` sets `pythonpath = ["quant-lab/src"]`, which
pytest inserts ahead of `PYTHONPATH`. A run substituted from another tree must
pass `-o pythonpath=<tree>/src` or it silently measures the wrong source copy.

## Scope of the two green bundles

| Bundle | Candidate it describes | Nodes |
| --- | --- | --- |
| `p3-r6-final` (R1 package, `p3_rung6_final_r1/`) | `868dd3fc9` only | 4,952 |
| `p3-r6-final-r3` (this package) | `66200f3cb` only | 4,968 |

The 4,952-node result is **not** evidence about the repaired candidate and was
neither overwritten nor reinterpreted. The delta is exactly the 16 regression
nodes added by the repair commit (8 F4, 7 F5, 1 binding-guard).
