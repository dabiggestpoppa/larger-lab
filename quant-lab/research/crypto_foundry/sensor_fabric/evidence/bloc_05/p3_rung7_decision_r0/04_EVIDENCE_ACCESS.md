# 04 - Evidence access for independent reconciliation

Raw canonical artifacts are **not committed**. They total about 21 MB across
three bundles and the repository is not an artifact store. They are preserved in
two places on this machine, byte-identical (SHA-256 equal in both copies).

## In-place bundles (runner-owned, untracked)

Worktree root: `C:/Users/wifik/Desktop/larger-lab/.worktrees/p3-consumer-rung1`

```
quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/canonical_runs/
  p3-r6-final/                            SUCCESSFUL  6 files   8,399,152 B
  p3-r6-attempt2-workers1-timeout900/     FAILED      5 files   6,382,628 B
  p3-r6-attempt1-workers4/                FAILED     13 files   6,455,663 B
```

Successful bundle contents (the ones Agent 2 needs):

| Role | File |
| --- | --- |
| Collection anchor | `collection.json` |
| Partition manifest | `partition_0.json` |
| Raw execution stream | `results_0.jsonl` |
| Aggregated record | `evidence.json` (carries intended/executed node lists, per-partition record, restoration results, environment) |
| JUnit | `junit_0.xml` |
| Guard baseline | `guard_baseline.json` |

Failed attempts are kept **separately** and are never mixed with the successful
bundle. `p3-r6-attempt1-workers4` has no `evidence.json` for partitions 1-2
because those streams were lost; that loss is the finding, not a gap to fill.

## Shared handoff copy (outside Git, recommended for Agent 2)

```
C:/Users/wifik/Desktop/larger-lab/.p3-r6-evidence/rung7-handoff/
  p3-r6-final/<6 files>
  p3-r6-attempt2-workers1-timeout900/<5 files>
  p3-r6-attempt1-workers4/<13 files>
  ARTIFACTS.sha256        24 lines: "<sha256>  <bundle>/<file>"
  artifact_inventory.json per-bundle status, source path, size and digest per file
  VERIFY_OUTPUT.json      captured `verify --require-anchor` output, exit 0
  run-final.out / run-final.err   captured runner stdout for the green run
```

This directory is outside the Git worktree, so nothing here can be committed by
accident and no large blob enters the repository.

## Integrity check

```bash
cd "C:/Users/wifik/Desktop/larger-lab/.p3-r6-evidence/rung7-handoff"
sha256sum -c ARTIFACTS.sha256
```

All 24 entries must report `OK`. Digests are also recorded in
`bloc_05/p3_rung6_final_r1/03_CANONICAL_EXECUTION.md` and in
`rung6_final_r1.json` for the six successful files.

## Re-verification without re-execution

```bash
cd <worktree>/quant-lab
PYTHONPATH=src python3 research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py verify \
  research/crypto_foundry/sensor_fabric/evidence/bloc_05/canonical_runs/p3-r6-final/evidence.json \
  --expect-count 4952 \
  --expect-digest f2fc909032b3a182bdccd47946af16d4ac179148d3615e60b3e0131c239d1931 \
  --require-anchor
```

This recomputes counts from the raw stream and checks the external anchor; it
does not re-run tests. The same command was run for `VERIFY_OUTPUT.json` and
exited 0.

## What is and is not independently verified here

Independently re-checkable: counts, anchor, digest, restoration, environment,
artifact integrity - all derived from the raw files above.

Not verified by this package: any claim about Agent 2's own findings, and any
behaviour on POSIX or against real PostgreSQL / live network, which this host
did not execute.
