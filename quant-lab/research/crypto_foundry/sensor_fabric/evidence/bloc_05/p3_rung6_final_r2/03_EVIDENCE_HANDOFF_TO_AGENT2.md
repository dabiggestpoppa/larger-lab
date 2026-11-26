# 03 - Evidence handoff to Agent 2

## What to attack

Candidate `66200f3cb18ee5cea1483d986e64502f388eeb77` on
`agent/crypto-sensor-fabric-p3-production-master-r1` (pushed; parent
`21fd7e473a534c38b237729f9474c46bb94267ee`). Scope is unchanged from the R1
request and deliberately narrow:

1. **F4** - every selected revision must be ordered against the cutoff. Try to
   re-open the hole: interleaved duplicate identities with the late entry first;
   `known_from` that is naive, a string, a `date`, or carries a hostile
   `tzinfo`; `selected ∩ excluded` overlaps; selections whose only late entry is
   the record's own revision; permutations of a mixed selection; equivalent
   offsets; exact-cutoff equality; excluded future revisions (must not be
   refused merely for being future). Attempt to reach `ACCEPT_FIELD_BINDING`.
2. **F5** - no exception-authored text may reach any public verdict field or its
   serialised form. Vectors: typed verifier refusal, `SemanticAuthorityRefusal`
   `str(exc)`, an object naming an unapproved "code", the `_rebind` loader, the
   replay gate's `UnassessableReplayEvidence`, custody, authority-source, a typed
   refusal arriving with an unhashable `refusal`, and `KeyboardInterrupt` /
   `SystemExit` propagation.
3. **Binding boundary** - confirm the claim separation is honest: with
   `REPLAY_RECORD_BINDING_ESTABLISHED = True` and no minted contract the row
   accepts; with it `False` no fully satisfied evaluation reaches
   `ACCEPT_FIELD_BINDING`; no schema was invented, I05 was not weakened, and the
   suite is not a page of blanket refusals.

## Where the canonical evidence is

| Item | Path |
| --- | --- |
| Bundle (accessible, outside the tracked worktree) | `.p3-r6-evidence/final-canonical-r3/bundle/p3-r6-final-r3/` |
| SHA-256 inventory | `.p3-r6-evidence/final-canonical-r3/bundle/ARTIFACT_INVENTORY.sha256` |
| Recollection record (external anchor source) | `.p3-r6-evidence/final-canonical-r3/collection_recollect.json` |
| Runner stdout (verdict) | `.p3-r6-evidence/final-canonical-r3/run.stdout.log` |
| Runner stderr | `.p3-r6-evidence/final-canonical-r3/run.stderr.log` (empty) |
| Hardened verifier output | `.p3-r6-evidence/final-canonical-r3/verifier_output.json` |
| Preserved previous bundle (4,952, `868dd3fc9` only) | `.p3-r6-evidence/final-canonical-r3/preserved-4952-bundle-p3-r6-final/` |
| Failed operational attempts (no evidentiary claim) | `.p3-r6-evidence/final-canonical-r3/prior-attempts/` |
| Repair record and mutation results | `.p3-r6-evidence/r6-repair/REPAIR_RECORD_R1.md`, `targeted_mutation_results.json` |
| Repaired-source reattack harness | `.p3-r6-evidence/f4f5-repro/` |

Contents of the bundle: `evidence.json` (full record), `collection.json`
(collected universe, count and digest), `partition_0.json` (partition manifest:
227 whole files), `results_0.jsonl` (raw pytest reportlog stream, 3.1 MB),
`junit_0.xml` (4,968 testcases, 0 failures, 0 errors, 11 skipped),
`guard_baseline.json` (468 guarded files baseline).

## Anchor and execution configuration

| Item | Value |
| --- | --- |
| External collection anchor | count `4968`, digest `45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9` |
| Partitioning | 1 worker, 1 partition, 227 whole files, disjoint |
| Partition timeout | 5,400 s (actual wall clock 27 m 07 s) |
| Numerical thread caps | `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1` |
| Python / pytest | CPython 3.11.9, pytest 9.0.3 |
| Platform | Windows-10-10.0.26200-SP0, 8 logical CPUs |
| Free disk before / after | 45.85 GB / 45.01 GB |
| Guarded prefixes | `quant-lab/research/crypto_foundry/sensor_fabric/evidence` |

Restoration accounting: attempted true, verified true, 11 side-effected paths
restored and re-hashed, tracked tree clean after, no untracked paths added.

## How to re-measure independently

Do not trust the summary - recompute it:

```bash
python3 research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py verify \
  ".p3-r6-evidence/final-canonical-r3/bundle/p3-r6-final-r3/evidence.json" \
  --expect-count 4968 \
  --expect-digest 45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9 \
  --require-anchor
```

Re-run the targeted reattack harness against the repaired source:

```bash
cd .p3-r6-evidence/f4f5-repro
export AUDIT_QUANT_LAB=<...>/.worktrees/p3-consumer-rung1/quant-lab
export AUDIT_PRIOR_FIXTURES=<...>/.p3-r6-evidence/f4f5-repro/test_second_agent_p01_p06.py.txt
export PYTHONPATH=$AUDIT_QUANT_LAB/src
python3 -m pytest -p no:cacheprovider -q test_r6_reattack.py                    # expect 5 failed, 28 passed
python3 -m pytest -p no:cacheprovider -p flip_binding_flag -q test_r6_reattack.py  # expect 33 passed
```

The five unadjusted failures are the pre-guard positive controls reconciled in
`04`; both original defect tests pass. `-p flip_binding_flag` simulates the
minted-contract state and is measurement only, not production authorization.

If a modified source tree is substituted, pass `-o pythonpath=<tree>/src`:
`pyproject.toml` pins `pythonpath = ["quant-lab/src"]` at `sys.path[0]` ahead of
`PYTHONPATH`, and without the override the measurement silently reads the
unmutated copy.

## Deliverable requested

A file in your own audit tree recording: SHA attacked, each vector attempted,
observed verdict (or refusal reason/status), a per-vector ACCEPTED/CONTRADICTED
line, and an explicit statement whether F4, F5 and the binding boundary are
closed for this candidate.

## Standing constraint on our side

Any production or canonical-test change after this execution invalidates the
applicability of this bundle to the repaired tree. We will reproduce any
concrete material defect before changing the candidate, and we will not
introduce speculative improvements, new architecture or unrelated hardening in
response to a passing or inconclusive reattack.
