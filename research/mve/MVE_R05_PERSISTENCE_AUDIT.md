# MVE R0.5.7 PERSISTENCE AUDIT — MVE_R05_PERSISTENCE_AUDIT.md

## What replaced the print-only functions

The runner's prior `_save_intermediate_results()` / `_save_final_results()`
only `print()`ed and wrote nothing. They are superseded by a real persistence
layer (`src/mve/persistence.py`) driven by `src/mve/runner.py`.

## Layer

- `persist_run(output_dir, config_hash, artifacts, manifest)` writes text and
  CSV artifacts, computes each artifact's SHA-256, attaches the hash map to the
  manifest, and writes `RUN_MANIFEST.json`.
- `write_csv` / `write_json` / `write_text` are deterministic (UTF-8, `\n`
  line endings, `index=False` for CSV).
- `prior_manifest_config_hash()` reads an existing manifest; `persist_run`
  **refuses to overwrite** when the prior `config_hash` differs, so an
  incompatible run cannot clobber prior results. A same-config rerun may
  overwrite (deterministic reproduction).

## Evidence

- Diagnostic run persisted 4 nonempty files under `results/mve/diagnostic/`:
  `DIAGNOSTIC_OHLCV.csv` (529 rows), `DIAGNOSTIC_SUMMARY.json`,
  `DIAGNOSTIC_SUMMARY.md`, `RUN_MANIFEST.json`.
- Output hashes recorded in the manifest match independently recomputed file
  hashes (verified by `test_output_hashes_match_recomputed_files`).
- Overwrite protection verified by `test_stale_artifact_rejection`.

## Known limitation

The committed diagnostic manifest records the `git_sha` of the HEAD at run time
(a3a5c81ce), which necessarily precedes the commit containing the manifest.
Self-referential provenance of the commit itself is recorded in the commit
message, not inside the artifact.
