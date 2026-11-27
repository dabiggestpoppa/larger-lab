# 02 - Evidence handoff and bundle integrity

No new execution is part of this closeout. What follows confirms that Agent 2
can reach exactly the artifacts that were executed, and that they are still the
artifacts that were executed.

## Location

Bundle root, outside the tracked worktree so no publication can touch it:

```
C:\Users\wifik\Desktop\larger-lab\.p3-r6-evidence\final-canonical-r3\bundle\p3-r6-final-r3\
```

It is a plain directory of six files with no symlinks, no generated sources and
no secrets. The published package `p3_rung6_final_r2/` in the repository carries
the same hashes, so the two can be cross-checked against each other.

## Artifact inventory, recomputed at this closeout

Every line below was recomputed with `sha256sum` at the closeout and matches the
recorded values and `bundle/ARTIFACT_INVENTORY.sha256` exactly.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `collection.json` | 701,543 | `b8ad4e8e8cc6b5acd167d6f7bad0c196b2db44f17d813e9a8e2694f3f36f3df4` |
| `evidence.json` | 2,957,549 | `5936680f1601da807a478736d3dc163159a91091640ac86974c24c9b0bf9ebbe` |
| `guard_baseline.json` | 83,998 | `8929be1370f95525941b96fa1ab1f0c99012e0fd1cb8a7f3d0c9fe051b59124d` |
| `junit_0.xml` | 860,274 | `8d037df3199903f9fc5ff1cc24397eb8f504e1d7266dcc89c2588389ea6fa7c4` |
| `partition_0.json` | 718,574 | `6ff0dcd93aa5ea8a57f25f8773b1156c96e07bcf0c5a44cafeff8b1646e4844a` |
| `results_0.jsonl` | 3,107,638 | `18a8cea3d966c2a125f065669eb1e731065dfcf6d2b3d221829b86f7e5a05673` |

Companion files in the evidence root, with the hashes recorded in
`EVIDENCE_DIR.sha256`:

| File | SHA-256 |
| --- | --- |
| `collection_recollect.json` (anchor source) | `15630fabca2012b73acac7e47b2e2222f42dbe07281ac7d0eaf62bade6f99638` |
| `run.stdout.log` | `eee2b8161aad1083756ca73b064bdabd6fde58b85d01b76076003d8d49190caf` |
| `run.stderr.log` (empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `verifier_output.json` | `5aee71149c14225b59d4233d054be63fa9acdbb25a6e33a425d94cd6f8fb5ec4` |
| `AGENT2_HANDOFF_R2.md` | `8033962ebde8ea3d6399d7280ed4d189fb4bdaa6f620b157d940e196c31114a0` |
| `bundle/ARTIFACT_INVENTORY.sha256` | `4867e8b751de5fafb2229a4badb9c11d05f3785f98be8a8cdc8da27288c39ae9` |

Note for an auditor: `run.stdout.log` holds the runner's reduced reconciliation
view. The full anchored reconciliation - including
`external_anchor_count`, `external_anchor_digest_checked` and
`external_anchor_checked` - is in `verifier_output.json`. Treat that file as the
verifier receipt and the log as the run's console summary.

## External collection anchor

| Field | Value |
| --- | --- |
| Count | **4,968** |
| Digest | `45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9` |
| Source | `collection_recollect.json`, collected 2026-11-26T12:10:45Z from the frozen candidate in 53.83 s, exit 0 |
| Supplied to both the run and the verifier as an external value | yes |
| Self-consistent bundle without an external anchor would be refused | yes (`--require-anchor`) |

## Execution accounting

| Field | Value |
| --- | --- |
| Run id | `p3-r6-final-r3` |
| Started / finished (UTC) | 2026-11-26T12:11:39Z / 2026-11-26T12:38:46Z |
| Wall clock | 27 m 07 s |
| Workers / partition timeout | 1 / 5,400 s, thread caps 1 |
| Partitions | 1, 227 whole files, disjoint and exhaustive |
| Groups | 13 |
| Collected / executed | 4,968 / 4,968 |
| Passed / failed / errored / skipped | 4,957 / 0 / 0 / 11 |
| Missing / extra / duplicate nodes | 0 / 0 / 0 |
| Interrupted | false |
| Disposition / assurance / outcome | `COMPLETE` / `ANCHORED_COMPLETE` / `GREEN` |

The eleven skips are the same eleven the previous candidate skipped - eight
POSIX/symlink/mode-bit/case/`pathconf` mechanics on Windows, three opt-in live
network or real-PostgreSQL integrations. Each is enumerated with its JUnit
reason in `p3_rung6_final_r2/02_CANONICAL_EXECUTION_R2.md`; none is a suppressed
failure.

## Universe delta, re-verified node by node

The previous package described the delta as "exactly the sixteen regression
nodes the repair added, and nothing else entered or left the universe". The net
count is right; the second half is not exact, and this closeout corrects it
rather than repeating it. Comparing the preserved 4,952-node collection with
`collection_recollect.json` node by node:

| Measure | Value |
| --- | --- |
| Added node ids | **17** |
| Removed node ids | **1** |
| Net delta | **+16** (4,952 -> 4,968) |
| Files whose node count changed | 2 (`..._rebinding.py` +9, `..._security.py` +7) |

The removed id is a **rename**, not a lost control:

```
- ...test_b5_p3_consumer_policy.py::test_the_accepting_branch_is_reachable_only_through_the_test_double
+ ...test_b5_p3_consumer_policy.py::test_the_accepting_branch_requires_the_record_binding_contract
```

That is the binding control itself: once the replay-binding guard exists, the
accepting branch is no longer reachable through a test double, it requires the
unminted contract, so the control was renamed to state the new truth. Its file's
node count is therefore unchanged (one out, one in), which is why the per-file
delta shows only the rebinding and security files.

The seventeen additions are the 8 F4 controls, the 7 F5 controls, the new
binding-guard control `test_f1_the_unresolved_binding_guard_is_executable_and_off`,
and the renamed policy control above. No other file gained or lost a node, and
no pre-existing control disappeared without a same-purpose successor.

Recompute it:

```bash
# node-set difference between the preserved 4,952 collection and the recollected 4,968 one
python3 - <<'PY'
import json
def nodes(p):
    c = json.load(open(p))
    return c['collection']['nodes'] if isinstance(c.get('collection'), dict) else c['nodes']
new = nodes('<evidence-root>/collection_recollect.json')
old = nodes('<evidence-root>/preserved-4952-bundle-p3-r6-final/collection.json')
print(len(new), len(old), len(set(new)-set(old)), len(set(old)-set(new)))
PY
```

## Hardened verifier receipt

```json
{"disposition":"COMPLETE","assurance":"ANCHORED_COMPLETE","test_outcome":"GREEN",
 "reasons":[],"missing_nodes":[],"missing_count":0,"extra_nodes":[],"extra_count":0,
 "counts":{"passed":4957,"failed":0,"errored":0,"skipped":11},
 "reconciliation":{"recomputed_counts":{"passed":4957,"failed":0,"errored":0,"skipped":11},
 "external_anchor_count":4968,"external_anchor_digest_checked":true,
 "recorded_anchor_checked":true,"external_anchor_checked":true,"anchored":true}}
```

Exit 0, recomputed from `results_0.jsonl` rather than from the summary. JUnit
independently totals 4,968 tests, 0 failures, 0 errors, 11 skipped.

## Guard baseline and restoration accounting

| Field | Value |
| --- | --- |
| Guarded prefix | `quant-lab/research/crypto_foundry/sensor_fabric/evidence` |
| Baseline file hashes | 468 (`guard_baseline.json`) |
| Restoration attempted | true |
| Restoration verified by re-hash | true |
| Restored / side-effected paths | 11 |
| Tracked tree clean after | true |
| Untracked paths added | none (evidence-tree writes excluded by prefix) |

## Raw stream and partition manifest

- `results_0.jsonl` - one JSON object per executed node, 3,107,638 bytes; this is
  the stream the verifier reconciles, and the only input it trusts for counts.
- `partition_0.json` - the single partition's 227-file membership, disjoint and
  exhaustive against the collection.
- `junit_0.xml` - the independent total used to cross-check the count, with the
  eleven skip reasons inline.

## Verifying it yourself

```bash
cd <worktree>
python3 research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py verify \
  "<evidence-root>/bundle/p3-r6-final-r3/evidence.json" \
  --expect-count 4968 \
  --expect-digest 45c206d6771cf9fbb8f49525fa9dafa263a18a432c981f1d8dbfb8febd6b00c9 \
  --require-anchor
```

Expected: `COMPLETE` / `ANCHORED_COMPLETE` / `GREEN`, 4,957 passed, 0 failed,
0 errored, 11 skipped, 0 missing, 0 extra, external anchor checked, exit 0.

## One label corrected

The evidence store places three directories under `prior-attempts/`. Two are
genuinely failed operational attempts with no evidentiary claim (four workers,
then one worker with a 900 s timeout). The third,
`prior-attempts/p3-r6-final-r3/`, is the **successful** run's original directory
and is byte-identical to `bundle/p3-r6-final-r3/` - verified by `diff -r` and by
all six hashes matching. Nothing was moved or deleted at this closeout; a
`prior-attempts/README.md` now states which is which, and
`bundle/p3-r6-final-r3/` remains the authoritative copy.

## What the access confirmation does and does not mean

It means the artifacts exist, are readable, hash-verified and reproducible from
the raw stream. It does not mean they have been independently reconciled: that
is the one open dependency in `04_RUNG7_ACCEPTANCE_RECORD.md` §4, and this
package does not simulate it by reading its own bundle.
