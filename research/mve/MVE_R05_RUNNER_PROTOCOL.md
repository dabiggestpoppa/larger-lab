# MVE R0.5.6/7 RUNNER PROTOCOL — MVE_R05_RUNNER_PROTOCOL.md

## CLI

```
python research/mve/run_mve_research.py --phase {4|5|6|7}
python research/mve/run_mve_research.py --diagnostic [--slice START,END]
python research/mve/run_mve_research.py --phase N --dry-run
```

Options: `--phase`, `--diagnostic`, `--dry-run/--validate-only`, `--output`
(default `results/mve`), `--slice START,END` (UTC YYYY-MM-DD), `--seed`
(default 42).

## Phase isolation

- `--phase 4` executes Phase 4 **only**; there is no auto-advance and no
  "run all" path. Verified: a phase run creates no downstream phase directory.
- Unknown phases and missing `--phase`/`--diagnostic` exit nonzero.

## Prerequisite gates (fail-closed)

- Environment prerequisites: canonical data file exists and its SHA-256 matches
  the frozen hash (otherwise exit 1).
- Phase dependencies: each phase declares prior-phase artifacts (see
  `MVE_R05_PHASE_DEPENDENCY_MAP.json`). A missing **or corrupt** prior
  `RUN_MANIFEST.json` (must be valid JSON containing `config_hash`) fails closed.
- Scientific implementation gate: phases 4-7 are
  `BLOCKED_SCIENTIFIC_IMPLEMENTATION`. Requesting one refuses to fabricate
  output and exits 1. This status is intentional and honest — scientific
  internals are not part of this checkpoint.

## Persistence

`src/mve/persistence.py` writes CSV/JSON/Markdown artifacts and a
`RUN_MANIFEST.json` with full provenance (git SHA, branch, canonical path +
SHA-256, M5/H1 row counts, H1 fingerprint, slice, config hash, seed,
input/output artifact hashes, timestamp, runner version/status). Outputs go to
`results/mve/{phase4,phase5,phase6,phase7,diagnostic}/`.

## Output integrity

- Every artifact's SHA-256 is recorded in the manifest.
- Overwriting is refused when a prior run's `config_hash` differs (same config
  hash → deterministic rerun may overwrite).
- No stale-artifact reuse without hash verification.

## Holdout guard

`FINAL_HOLDOUT_PENDING` is preserved. The slice interface rejects any range
outside the authorized development/confirmation windows, so 2026+ cannot be
auto-labeled as an untouched holdout.

## Determinism

Same config + seed + slice → byte-identical data artifacts and a manifest that
differs only in `execution_timestamp` (see `MVE_R05_DETERMINISM_REPORT.md`).
