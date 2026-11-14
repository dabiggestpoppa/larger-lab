# P3 I09 — HISTORICAL PRODUCER CI VERIFICATION

**Checkpoint:** SENSOR-B5-I09P3-HISTORICAL-PRODUCER-CI-VERIFICATION
**Role:** Independent Governance Verification Engineer
**Branch:** `agent/crypto-sensor-fabric-p3-i09-ci-verification` (base `d85ba823fd…`)
**Disposition:** **HISTORICAL_PRODUCER_VERIFIED**

The governance auxiliary that two local attempts left blocked on disk space is now **closed**, and it closed on the evidence rather than on convenience: the producer executed against its own historical snapshot and its measured digest equals the ratified pin byte for byte.

---

## Phase 0 — access and CI capability

| Check | Result |
|---|---|
| Repository visibility | **PUBLIC** (`isPrivate: false`, default branch `main`) |
| Actions enabled | `{"enabled": true, "allowed_actions": "all", "sha_pinning_required": false}` |
| Default workflow permissions | `read` |
| Pre-existing workflows | **0** — nothing to collide with, nothing to modify |
| Pinned commit reachable | `03522870d…` present on the runner; 29 remote refs contain it |
| Runner disk | **84 G free of 145 G (43% used)** — the binding local constraint disappears |

Runner availability was not assumed from visibility; each point above was queried through the API before the workflow existed.

## Phase 1 — isolated execution

A new ephemeral `ubuntu-latest` runner, not the exhausted host. The local checkout was **not** attempted again.

- permissions: `contents: read` only; `persist-credentials: false`
- no secrets, no provider credentials, no deployment permissions, no provider network tests
- `timeout-minutes: 30`, `concurrency` bounded per ref
- `fetch-depth: 0` so the pinned historical commit is available; an explicit assertion fails the job if either the workflow commit or `03522870d` is missing
- minimal dependencies only: `pydantic>=2,<3`, `numpy`, `pandas`, `pyarrow` (not the repo's `torch`-sized `pyproject`)
- `PYTHONPATH: src` is deliberately **relative**: the verifier runs the producer with `cwd=<snapshot>/quant-lab`, so the historical snapshot's own package is imported, never this branch's
- the verifier was executed **unchanged**. `sha256` on the runner `7b9a08ae…` is identical to the branch's copy:

```
7b9a08ae51d1b5f556f68b7fb35da1375539109920ff6f0b9d50c3d6f2f9a4cd
```

### Two runs, both reported

| Run | Head | Outcome |
|---|---|---|
| `43639204394` | `c55bfb3a…` | **failure** — `actions/checkout` post-step `git submodule foreach` exited 128: `fatal: No url found for submodule path 'projects/ai-tools/oransim' in .gitmodules`. The checkout itself had completed; the harness broke, no producer ran. Counted **not** as verification. |
| `43639340503` | `fa8c796b…` | **success** — all seven steps green |

The fix for the first run was made in the harness, not the verifier: the checkout step is non-fatal and a separate assertion now demands the workflow commit and the pinned commit be present, so a genuine checkout failure still stops the job.

## Phase 2 — producer identity and digest

| Field | Value |
|---|---|
| Exact source commit | `03522870d40b839a2eac28eff7841bfb161e05f3` |
| Snapshot identity | detached worktree of that commit, `worktree_created: true`, `worktree_removed: true` |
| Producer entry point | `scripts/b5_i08_units.py` |
| Expected digest | `260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4` |
| Measured digest | `260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4` |
| `bytes_match_pin` | **true** |
| Producer exit code | **0** |
| Producer reported | `U08-01..U08-20`, rows 55, pass 55, fail 0 |
| Verifier exit code | **0** |
| Verifier verdict | **PASS** |
| Environmental errors | none |

Three independent values agree: the file the harness hashed, the digest the producer reported about its own output, and the ratified pin. That is producer-output equivalence, not merely a stored constant being echoed back.

The verifier's own distinction stands unchanged: this proves the **sealed I08 artifact against the source snapshot it measured**. It is not a claim about the current tree — the current-tree U08-19 refusal remains documented and owned by the pytest scope audits.

## Phase 3 — evidence binding

Everything below is committed under `evidence/bloc_05/i09_ci_verification/`, tied to run `43639340503` on `fa8c796b…`:

| File | sha256 |
|---|---|
| `producer-verification.json` | `f5d6818c589f5afd24a82eea17ead9764ac39a2bcf7fd6635491a74b12cb1ad0` |
| `environment.txt` | `7e5cb41c6a2b2cfbf64d26c12034afc3fb261fa34bbdd7eeae247fb65c397032` |
| `verdict-summary.txt` | `625bc72e6c16375eed93a070c1d600c5f1c583acacc8428f67f86129f6b991ad` |
| `verifier-exit.txt` | `da5483ed57d1f2f972bca08a8f5fdf56156bab9f5c4c9ef88b0d5f145c1f703b` |
| `artifact-hashes.txt` | `42331c916f3dfc5d4cf1ec2efd044af6e3ce66d05b9a43b05310388c21552113` |
| `producer-verification.stderr` | `e3b0c442…b855` (empty) |

Run URL: `https://github.com/dabiggestpoppa/larger-lab/actions/runs/43639340503`. Artifact retained 30 days. Evidence binds to the unchanged candidate `6de26be9…`, canonical evidence `5c38d0d6…`, closeout `d85ba823…`, historical producer `03522870d…`.

The 4,733-node regression was **not** rerun.

## Phase 4 — governance

| Check | Result |
|---|---|
| Tracked Python inventory | **1,102 / 1,102** |
| I11R2 inventory pin | **1,102** |
| Approval manifest | **empty** (`artifacts: {}`, no revoked ids) |
| Integration state | `INTEGRATION_REQUIRED` |
| Frozen governance constraints | unchanged — **75 passed** |
| Production source changes | **0** |
| Authorization changes | **0** |

### A governance law caught the harness

With the workflow committed, **2 governance tests failed**:

```
AssertionError: unauthorized staged path: .github/workflows/i09-historical-producer-verification.yml
```

The frozen I10 scope audit admits only its own path allowlist, and `.github/` is not on it. A verification harness is not permitted to buy its result by widening a sealed scope law. The workflow was therefore archived verbatim into the evidence tree — `workflow/i09-historical-producer-verification.yml.archived`, sha256 `36fee20a…b65656` — and **removed from the tracked tree**, returning it to its base state. After that: **75 passed**. The file is reported here explicitly as a workflow change: added, executed, archived, removed.

## Phase 5 — publication

Additive only, on `agent/crypto-sensor-fabric-p3-i09-ci-verification` from `d85ba823fd…`:

1. `P3_I09_CI_VERIFICATION.json`
2. this document
3. `i09_ci_verification/` — raw payload, environment facts, exit status, artifact hashes, archived workflow
4. references to the untouched canonical evidence and governance closeout

No historical evidence rewritten. No ledger section added or renumbered. No production code modified. No branch merged.

---

## Adjudication

**HISTORICAL_PRODUCER_VERIFIED.** The previously blocked governance auxiliary is **resolved**, and the strict checkpoint condition that failed twice for environmental reasons now passes on a clean runner.

The regression standing is unchanged: **ANCHORED_COMPLETE / GREEN**, 4,733 collected, 4,733 executed, 4,722 passed, 11 skipped, 0 failed, 0 errors.

This qualifies regression and governance verification only.

## Hard stop

No production merge. No provider certification. No trust promotion. No custody authorization. No program-gate advancement. No self-ratification.

It does **not** close the independent R6 security audit.
