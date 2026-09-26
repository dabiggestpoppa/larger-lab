# BLOC 04 — SENSOR-B4-I11R2 HISTORICAL GOVERNANCE TEST DECOUPLING

## Scope

This append-only checkpoint repairs **test architecture only**.  It changes no
production source, no I11R1 measured behaviour, no committed historical evidence
and no frozen research or plan contract.  I12 `RawEvidenceQuery` and I12+ remain
unauthorized; research remains frozen.

Machine evidence in this checkpoint:

- `BLOC_04_I11R2_GOVERNANCE_REGRESSION_MATRIX.json` — 10 rows (9 `OK`, 1
  deliberately synthetic `FAIL`).
- `BLOC_04_I11R2_REGRESSION_RUN_RECORD.txt` — the verbatim trailing summary
  lines of the real pytest runs, the full skip ledger, the PostgreSQL fault
  record and the line-ending verification method.

Suite numbers below are **parsed out of the committed run record** by
`test_i11r2_evidence.py`.  No suite result is hand-declared in the matrix.

---

## 1. Accepted operator finding

The two failures that blocked G4-10 were **governance-test architecture
failures, not PostgreSQL implementation failures**.

Two accepted *historical* checkpoint tests were reading the **mutable** top-level
`## Current state` dashboard table:

- `test_i10r2_evidence.py::_ledger_current_state_parity` sliced
  `## Current state` and required the table to still say
  `Current checkpoint | SENSOR-B4-I10R2` together with the I10R2-era proposal
  verdicts.
- `test_job_state_r1i.py::test_ledger_operator_state_is_truthful` required the
  live table to still name `SENSOR-B4-I07R1I`, hold all five upstream I07
  approvals at `OPERATOR_HOLD`, and report
  `DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE`.

Both assertions became false the moment the operator legitimately ratified those
checkpoints and work advanced to I11.  The dashboard is *supposed* to advance.
An immutable historical claim bound to it therefore has a bounded lifetime that
ends at the next legitimate ratification — a test that is guaranteed to fail
eventually, for reasons that have nothing to do with the code it appears to
test.  `postgres_metadata.py` and every I11R1 measured behaviour are untouched;
the production diff for this checkpoint is exactly **zero**.

### Failure-first proof (recorded at the mandatory start HEAD)

```
test_i10r2_evidence.py::test_i10r2_evidence_is_measured_and_committed
  quant-lab\tests\...\test_i10r2_evidence.py:479: AssertionError
  E   AssertionError: assert 'FAIL' == 'OK'
  E     - OK
  E     + FAIL

test_job_state_r1i.py::test_ledger_operator_state_is_truthful
  quant-lab\tests\...\test_job_state_r1i.py:582: AssertionError
  E   AssertionError: PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED
  E   assert 'PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED=OPERATOR_HOLD'
      in 'Current Bloc|4 — IMMUTABLE T0 RAW EVIDENCE LAKE\nCurrent checkpoint|SENSOR-B4-I11R1: ...'
```

---

## 2. Governance model, now explicit in the suite

| Layer | Mutability | What it may be used for |
|---|---|---|
| `## Current state` table | **MUTABLE dashboard** — must advance with every checkpoint | the present checkpoint's truth only |
| `## SENSOR-B4-<NAME> ...` sections | **APPEND-ONLY** — immutable once written | that checkpoint's historical truth |
| committed evidence matrices / microseals | **IMMUTABLE measured artifacts** | measured historical truth |

Three laws, now enforced by tests rather than convention:

1. A **historical** checkpoint test binds to exactly one immutable source and
   never reads the dashboard.
2. A **current-state** test never claims to represent a superseded checkpoint.
3. The superseding verdict is never allowed to go unpinned just because the
   proposal it replaced stopped being interesting.

### `extract_checkpoint_section(text, heading_exact)`

The shared enforcement point, added to
`tests/crypto_sensor_fabric/storage/_sibling_import.py`:

- the heading must match **exactly** — no prefix, no substring, no glob, and not
  even trailing whitespace;
- it must occur **exactly once**; missing *and* ambiguous both fail closed;
- the section is **bounded** by the next heading of the same or higher rank;
- no dependence on `## Current state`;
- **no document-wide string search**, and deliberately **no general Markdown
  parser**.

---

## 3. Repointed historical bindings

### I07R1I proposal truth

**Source: `BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json`** — the committed,
measured, append-only I07R1I ledger-structure matrix.  `test_ledger_operator_state_is_truthful`
now asserts, by exact case name:

- `i07_hold_chain_truthful` → `result = PASS`, `proposal_pending = true`, and
  `hold_keys` **exactly equal** to the test's own `_HOLD_KEYS` tuple;
- `durable_resume_pending_acceptance` →
  `durable_resume_implemented = "PENDING_OPERATOR_ACCEPTANCE"`,
  `recovery_scanner_implemented = false`;
- `next_checkpoint_not_authorized` → `next_checkpoint_authorized = false`.

Every original assertion survives with equal strength; only the *source* changed
from a mutable dashboard to an immutable measured artifact.

### I10R2 governance truth

**Source: `BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.md`, exact `## Governance`
section.**  `implementation_ledger_current_state_parity` keeps its committed row
key — deliberately, so `BLOC_04_I10R2_MEASUREMENT_PARITY_MATRIX.json` still
regenerates byte-for-byte — but the predicate now reads the microseal's eight
proposed verdicts, plus the negative that I10R2 never self-ratified
(`... = OPERATOR_ACCEPTED`, `G4-09 ... = OPERATOR_ACCEPTED`,
`next_checkpoint_authorized = TRUE` must all be absent).

### The superseding verdict, still pinned

`test_i07r1i_ratification_is_recorded` binds to the ledger's exact
`## SENSOR-B4-I07R1I-RATIFY — ...` section and requires `OPERATOR_ACCEPTED`,
all five hold keys, `DURABLE_RESUME_IMPLEMENTED = TRUE`,
`RECOVERY_SCANNER_IMPLEMENTED = FALSE`, `next_checkpoint_authorized = TRUE`
authorizing `SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY`, `I09+ NOT` authorized,
and that the ratification was governance-only (`no test delta`).

### The dashboard, held to its own job

`test_current_state_is_a_dashboard_not_a_historical_checkpoint` requires the live
table to name the present `SENSOR-B4-I11` chain, keep
`next_checkpoint_authorized=FALSE`, state research frozen and I12 unauthorized,
and **not** be re-pinned to `SENSOR-B4-I07R1I` or to
`DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE`.

### Proof that no live dependency remains

The matrix does not take "no longer reads the dashboard" on trust.  It
**instruments the call**: `_files_read_by` replaces `Path.read_text` and
`Path.read_bytes` for the duration of each repaired binding and records every
file actually opened.

- `i07r1i_binding_never_reads_the_ledger` — the ledger's resolved path is
  **absent** from the recorded read set.
- `i07r1i_binding_reads_its_immutable_source` — the I07R1I matrix **is** in it.
- the same pair for I10R2 and its microseal.
- `old_i07r1i_binding_flips_with_dashboard` / `old_i10r2_binding_flips_with_dashboard`
  — the pre-I11R2 bindings, re-implemented verbatim in substance, **do** change
  their verdict when the dashboard is replaced by an arbitrary one, proving the
  measurement has teeth.

---

## 4. Measured closure

### Production

`quant-lab/src` diff: **zero files.**  Checked four ways — unstaged diff,
staged diff, `git diff ccc6a726 -- quant-lab/src` against the I11R1 accepted
HEAD, and untracked-file enumeration.  `postgres_metadata.py` specifically is
asserted untouched.

### Historical evidence

All **131** pre-existing `bloc_04` artifacts re-hashed against a baseline
captured at the mandatory start, before anything was edited:

- 0 byte mismatches
- 0 added, 0 removed
- the six original I11 blocked-runtime artifacts and every I07/I08/I09/I10/I11R1
  artifact are byte-identical to `ccc6a726`

`BLOC_04_I10R2_MEASUREMENT_PARITY_MATRIX.json` regenerates byte-for-byte, which
is the strongest available statement that I10R2's own evidence is undisturbed.

### Regression

| Scope | Passed | Skipped | Failed |
|---|---|---|---|
| focused — the two originally failing tests | 2 | 0 | **0** |
| storage suite | 1488 | 25 | **0** |
| non-storage suite | 1379 | 1 | **0** |
| full project tree | 2867 | 26 | **0** |

`full_totals_reconcile` proves the full-project figure is exactly the sum of the
two complete disjoint halves, so the report is arithmetic, not assertion.

#### Every skip explained (26 total)

- **21** — real-PostgreSQL I11/I11R1 guards, self-declaring, because no
  `SENSOR_POSTGRES_TEST_DSN` was set for these runs:
  `test_i11_postgres_metadata.py:83,100`;
  `test_i11r1_evidence.py:129,140`;
  `test_i11r1_postgres_integration.py` ×17.
- **4** — POSIX-only platform semantics, unreachable on this Windows host:
  `test_blob_store.py:498` (mode bits), `test_blob_store_namespace.py:231`
  (`os.pathconf`), `test_json_catalog.py:215` (permission semantics),
  `test_recovery.py:607` (symlink semantics).
- **1** — deliberate live-network opt-in:
  `providers/test_network_smoke_live.py:59` (`SENSOR_NETWORK_SMOKE` not set).

`test_atomic.py:185` is **not** skipped on this host — the Windows
`fsync_directory` implementation exists and its tests pass — and is correctly
absent from the ledger.

#### Transient environment failures observed and cleared

Two full storage runs initially failed, and neither was a code regression:

1. **12 failures** in `test_projection_lineage.py` / `test_projections.py` /
   `test_i05r1_evidence.py`.  Those modules use hard-coded **process-global**
   roots (`C:/tmp_r2a_lin`, `C:/tmp_proj`, `C:/tmp_r1f_proj`) rather than
   `tmp_path`, so a crashed or aborted earlier run leaves a poisoned directory
   that the next run inherits (`WinError 145` not-empty, `WinError 32` in-use,
   `FileNotFoundError` after a mid-test `rmtree`).  With the roots clean the
   same files pass in isolation **and** in the full suite.  Recorded as an
   environment/isolation finding; **not** patched here, per the no-opportunistic-
   patch rule.
2. One machine slowdown that pushed runs past the 600 s per-command cap, caused
   by eight orphaned `pytest` processes left behind by the capped-out runs.
   After terminating them the suite returned to its normal ~467 s.

---

## 5. Tooling truth

- **Ruff** — changed scope: `All checks passed!`  Storage-tree baseline:
  unchanged at exactly the two known pre-existing findings
  (`test_i08_evidence.py:33:55 F401`, `786:59 F811`).
- **compileall** — changed scope clean.
- **mypy** — repository baseline unchanged at exactly
  `Found 15 errors in 9 files (checked 114 source files)`.
  `_sibling_import.py` alone: `Success: no issues found`.
  `test_job_state_r1i.py`: clean.
  One finding appears inside a changed file —
  `test_i10r2_evidence.py` `fetchone()[0]` — and is **pre-existing**: the line
  is byte-identical at the start HEAD (line 361 there, 403 now after
  insertions) and lies outside every hunk of this checkpoint's diff.  It was
  simply never before type-checked with `MYPYPATH` configured.  No new finding
  was introduced.

## 6. Line-ending verification method

Machine-wide `core.autocrlf=true` (from `C:/Program Files/Git/etc/gitconfig`,
**not** this repository) rewrites committed LF blobs to CRLF at checkout.  This
worktree is scoped to `core.autocrlf=false` via `extensions.worktreeConfig`, so
the tree under test is byte-faithful.  No repo-wide `.gitattributes` was added —
explicitly a separate infrastructure-hygiene task.

Verified for this checkpoint:

- `git status --porcelain` on the evidence tree is **empty** after the repair;
- SHA-256 of all 131 pre-existing artifacts, captured before and re-compared
  after, are byte-identical;
- the 7 I03R1/I04-era JSON artifacts that `Path.write_text` re-CRLF's on every
  run showed a pure line-ending delta (`git diff --numstat` non-zero,
  `git diff --numstat --ignore-cr-at-eol` **empty**) and were restored to their
  committed blobs with `CR = 0`; no committed byte was rewritten;
- the governance ledger is 2321 lines with `CR = 0`, and
  `test_ledger_is_utf8_lf` continues to pass.

**The I04 `write_text` defect is recorded, not fixed.**  It is out of scope
here.  Because this checkpoint's own immutability predicate has to survive a
full suite run in which those 7 artifacts are rewritten mid-run, the predicate
classifies rather than ignores: a rewrite is tolerated **only** when the content
is byte-identical after undoing the line-ending rewrite **and** the artifact is
in the closed `I04_CRLF_CHURN_ALLOWLIST`.  Any other byte change is a real
historical rewrite and fails closed.  The published matrix is byte-identical
whether the churn is present or absent, which was verified in both states.

## 7. PostgreSQL runtime

`POSTGRES_RERUN = BLOCKED_ENVIRONMENT`.

`initdb` (PostgreSQL 16.15) succeeded, and the disposable cluster reached
`database system is ready to accept connections` on **three** separate starts.
On each attempt a server process was then terminated by the identical Windows
failure already recorded at I11R1:

```
LOG:  server process (PID 5284)  was terminated by exception 0xC0000142
LOG:  server process (PID 20100) was terminated by exception 0xC0000142
LOG:  server process (PID 13936) was terminated by exception 0xC0000142
LOG:  shutting down due to startup process failure
```

every occurrence immediately following a time-based checkpoint.  This is a
host-level Windows process-initialisation fault, not a code defect.

Because **no production change was made in SENSOR-B4-I11R2**, no new PostgreSQL
proof is required by this checkpoint's own success law.  The committed I11R1
measured evidence — including the completed real-PostgreSQL run recorded in
`BLOC_04_I11R1_POSTGRES_RUNTIME_MICROSEAL.md` — is **not** invalidated.  The
disposable cluster was destroyed; no credential reached Git.

## 8. External CI

No external CI result is claimed.  All evidence here is local and
repository-verifiable.

---

## 9. Governance

```text
PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED  = OPERATOR_HOLD
PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED          = OPERATOR_HOLD
PASS_SENSOR_B4_I11R2_GOVERNANCE_REGRESSION_SEALED        = PENDING_OPERATOR_REVIEW
G4-10_OPERATIONAL_METADATA_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized    = FALSE
recommended_next = OPERATOR REVIEW OF COMPLETE I11 -> I11R1 -> I11R2 CHAIN
I12+ = UNAUTHORIZED
research = FROZEN
```

This checkpoint does not self-ratify.
