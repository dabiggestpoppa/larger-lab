# Cleanroom verifier

Canonical, rerunnable, **read-only** verification for the repository
cleanroom evidence closure of `dabiggestpoppa/larger-lab`.

## Files

| File | Role |
|---|---|
| `verifier.py` | The canonical verifier. Python 3.8+ stdlib (PyYAML optional). Never mutates branches, tags, stashes, trash, LFS objects, or working files. |
| `expected-state.json` | Expected-state contract: repository identity, branch, subject, main SHA, protected/restored/tag expectations (SHAs come from the reference manifests), trash, stash, LFS, gitleaks, NOT_RUN suites. |
| `evidence/branch-reference-manifest.json` | Expected branch/tag reference snapshot (F13) with per-branch divergence facts. |
| `evidence/restored-file-manifest.json` | The 50 restored Quant/CEREBUS/P90 files with SHA-256 and main blob identity. |

## Usage

```bash
# run from the cleanroom worktree; outputs MUST go outside the repo
python cleanroom/verifier.py --output-dir /tmp/cr-evidence --subject <sha>
```

`--subject` (or `CR_SUBJECT`) pins the tested subject commit; if omitted the
verifier validates current HEAD and records it. To validate the authoritative
F15 implementation commit after it is pushed, pass that SHA.

## Outputs

- `cleanroom-verification.json` — machine-readable checks (PASS / FAIL /
  BLOCKED / SKIPPED / NOT_RUN), totals, snapshot semantics
  (`observed_at_utc`, `observed_branch_sha`, `tested_subject_commit`,
  `evidence_commit`, live branch state, `branch_advanced_after_observation`),
  and the exact exit code.
- `cleanroom-verification-summary.md` — human-readable summary.
- `tool-versions.json`, `trash-inventory.json`, `stash-inventory.json` —
  observed tool versions and inventories.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | No mandatory FAIL or BLOCKED checks |
| 1 | At least one mandatory FAIL |
| 2 | At least one mandatory BLOCKED (and no mandatory FAIL) |
| 3 | Internal error / bad usage |

The same code is written into `cleanroom-verification.json`.

## Semantics

- Protected branches: must exist at the expected SHA on `origin`; a pure
  descendant advance is reported as `ADVANCED` (recorded in
  `branch_advanced_after_observation`) and does not fail the check. Rewinds
  and replacements fail.
- `main`: strict exact match (reported without altering main if moved).
- Restored branches and archive tags: exact-match required.
- Gitleaks: authoritative secret scan of the cleanroom branch's own commits
  (`main..HEAD`), so the check answers "did the cleanroom introduce
  credentials". The full-history repo scan is documented in the report as an
  observation (the repo's pre-existing history contains many scanner findings,
  mostly token/address data and placeholder secrets). If the binary is missing
  the check is BLOCKED (the repository contract runs gitleaks in CI). The
  regex scan is a separate, informational, non-equivalent fallback.
- `.gitleaksignore` lists verified false-positive fingerprints (e.g. a git SHA
  matched as a generic key) with a comment explaining each entry.
- NOT_RUN suites (protected-branch test suites) are declared and counted in
  the totals — the verifier never reports zero NOT_RUN while listing suites
  that were not executed.
