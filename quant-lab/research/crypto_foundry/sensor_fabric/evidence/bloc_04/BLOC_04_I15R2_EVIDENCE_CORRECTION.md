# BLOC_04_I15R2_EVIDENCE_CORRECTION

**Mandate:** SENSOR-B4-I15R2 — Windows concurrent publication stability + path-normalization consistency microseal
**Branch:** agent/crypto-sensor-fabric-build
**Base (start) HEAD:** `67fd2271a4137403d68c236e3e46dc2a97528389`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Scope:** I15R2 ONLY. I16+ UNAUTHORIZED. G4-13 NOT EARNED. Research FROZEN.

This document is **append-only correction evidence**. It does NOT rewrite the
I15 matrices, the I15R1 matrices, the I15 ledger section, or any historical
I03–I14 artifact. **I15 and I15R1 remain valid historical evidence.**

---

## 1. Operator review finding closed

I15R1 closed the security defects. Independent verification surfaced a
remaining **operational hardening** defect: concurrent identical writers
remained highly unstable on Windows. Under the accepted
`TestConcurrency::test_concurrent_identical_writers_one_final`, roughly half of
all trials failed. Both causes fail CLOSED, so no integrity property was
violated — but a ~50% failure rate on an ordinary safe write is not acceptable
for ratification, and §32 requires that benign concurrency reach deterministic
success.

This microseal closes **only** those two concurrency defects.

---

## 2. Defect A — the canonicalization AUTHORITY was split, and raw `Path.resolve()` is not one

### 2.1 What was wrong

Two modules held two different definitions of "real path":

- `atomic._real_path()` applied Windows extended-length (`\\?\`) prefix
  normalization (introduced by I15R1B);
- `paths.resolve_under_root()` compared a **raw** `Path(root).resolve()` and
  `path.resolve()`.

Raw `Path.resolve()` is not a canonicalization authority on Windows. CPython's
`ntpath.realpath` (`Lib/ntpath.py`) only strips the `\\?\` prefix when its own
post-strip re-resolution check succeeds, so the **same physical directory** is
returned spelled one way by one call and the other way by the next.

### 2.2 Deterministic reproduction (not a timing observation)

Measured on this host at the start head, with no concurrency at all:

```
root.resolve()                      = 'C:\...\i15r2A-tlgkrl2u'
Path('\\?\C:\...\i15r2A-tlgkrl2u\blobs\sha256\ab\cd').resolve()
                                    = '\\?\C:\...\i15r2A-tlgkrl2u\blobs\sha256\ab\cd'
raw `root not in target.parents`    = False   -> false refusal
```

The same physical directory, two spellings, one false "resolves outside the
storage root" refusal — surfaced to the writer as `UnsafeObjectKey`. Under
concurrent publication the two spellings interleave, which is why the observed
symptom was intermittent rather than constant.

### 2.3 The repair — ONE shared authority

`paths.canonical_real_path()` is now the single canonicalization authority, and
`paths.is_within_real_root()` the single containment predicate. Both
`resolve_under_root()` and `publish_no_replace()` compare through them;
`atomic._real_path()` is a **delegating alias**, not a second definition. A
test row scans every module in the storage package and requires the prefix
logic to be present in exactly one file (`paths.py`).

The pure string law (`strip_windows_extended_prefix`) is split out so the
extended-drive and `\\?\UNC\` forms are provable without a live network share.

### 2.4 The `normcase` audit (§7/§18) — result: NO explicit case folding

`os.path.normcase` was audited and **deliberately not applied**. `PureWindowsPath`
comparison is already case-insensitive and `PurePosixPath` is not, so
`Path`-based containment yields the correct per-platform law for free.
Explicitly lowercasing would merge two genuinely different POSIX directories
and *weaken* containment. Two rows assert this executably: no `normcase`/`lower`
appears in the comparison path, and a differently-cased POSIX sibling stays
outside the root.

---

## 3. Defect B — the `ensure_durable_directory` walk-up race

### 3.1 The exact interleaving

The entry guard probed the target and saw it ABSENT. The walk-up loop then
re-probed the same path. If another writer created the complete chain in that
window, the walk-up loop body never executed, `missing` collapsed to `[]`, and
`ensure_durable_directory_chain(target, [])` raised
`ValueError("components must be nonempty")` — for a perfectly legitimate
concurrent creation.

### 3.2 Deterministic reproduction

Driven through an injected `exists_probe` seam — **no sleeps**. The test
re-executes the *verbatim pre-repair walk-up* and asserts it raises, so the
seal is earned by the production repair rather than by a weak harness.

### 3.3 The repair — idempotent creation, not a retry

When the walk-up observes the target EXISTING after the entry guard saw it
ABSENT, the target is re-checked and returned **only** if it is an existing
plain directory. A symlink, a file or any other object appearing there still
fails closed and is left untouched. The chain builder is never called with an
empty component list.

Correctness comes from idempotent directory creation and atomic no-clobber
publication — **never** from a retry loop (§25), and **never** from catching
`ValueError` / `UnsafeObjectKey` / `AtomicPublishSecurityError` at
`LocalBlobStore.put` (§24). No such catch exists in the writer.

### 3.4 NAME-MAX probe race (§11)

The component-limit probe is a filesystem observation, so the directory it is
taken against is now revalidated as the **same** plain directory immediately
before and after. Replaced, turned into a link, or vanished, the reported limit
cannot be attributed to the parent about to receive the new name, and the
operation fails closed. **No guessed 255 fallback was introduced** — the I03
law (filesystem truth) is preserved.

---

## 4. Measured results

### 4.1 Baseline at the start head `67fd2271a`

15 trials x 8 barrier-started identical writers on one `LocalBlobStore` per
trial = 120 workers:

- **11 green / 4 red trials**
- failure class: `VALUE_ERROR_COMPONENTS_EMPTY` x4 (`ValueError: components
  must be nonempty`), `UNSAFE_OBJECT_KEY` x0 in this sample
- final-object count violations 0, hash violations 0 (the failures fail closed)

Defect A's `UnsafeObjectKey` symptom did not reproduce in this particular
sample; it is recorded as deterministically reproducible in §2.2 rather than
as a measured trial count.

### 4.2 After the repair

- **100 trials x 8 identical writers: 100 green / 0 red**, every trial exactly
  1 `COMMITTED_NEW` + 7 `REUSED_EXISTING`, 0 unexpected exceptions, 1 final
  immutable object, final hash verified.
- Distinct-payload stress: every expected SHA appears exactly once as a durable
  content identity, no crosstalk, all hashes verify — the repair is not overfit
  to the same-hash race.
- A benign same-hash publication-race loser still resolves through
  `AtomicPublishTargetExists` -> verify winner -> `REUSED_EXISTING`; it is
  never converted into a generic security refusal (§16).

### 4.3 Security regression (§15)

The I15R1 malicious TOCTOU matrix was re-run unchanged: **13 rows / 13 OK**,
**outside-root mutations = 0**, **foreign bytes published = 0**, and the two
synthetic counterfactuals still demonstrate the escape they exist to prove
(`check_use_seam_pre_repair_counterfactual_escape` still measures 1).

---

## 5. One I15R1 row re-measures differently — reported, NOT rewritten

Re-running the I15R1 suite on this host re-measures one informational field of
`final_name_preexisting_link`:

| field | committed I15R1 bytes | re-measured on this host |
|---|---|---|
| `measured.refusal` | `NotADirectoryError` | `UnsafeObjectKey` |

**Cause.** The planted object is a *broken* reparse point (a junction to a
file), so `Path(final).resolve()` raised `NotADirectoryError` — an untyped
`OSError` that escaped `resolve_under_root`, `_resolve` (which catches only
`ValueError`) and therefore `put()` itself.

**Why it changed.** `is_within_real_root()` catches `OSError` from
canonicalization and returns `False` — the fail-closed behaviour that
`atomic._is_within` already had in I15R1 and that is now the shared law. The
broken link is therefore refused EARLIER and TYPED as `UnsafeObjectKey`.

**Why the I15R1 matrix was NOT modified (§28).** The row's `result` is `OK`
before and after, `outside_file_untouched` is `true` before and after, and the
matrix-level counts are unchanged: outside-root mutations 0, foreign bytes 0.
Only an informational label moved, and it moved *toward* a stricter typed
refusal. Per §28 the committed I15R1 bytes are preserved as the historical
I15R1 record and this delta is recorded here instead. **Operational
consequence: re-running the I15R1 suite on this host leaves that one matrix
dirty; it must be reverted and never staged** — exactly as for the I15
informational timing rewrites.

---

## 6. Verification totals

Focused I15R2 (both new modules): 43 tests, 41 passed / 2 skipped, 0 failed.
I15R1 + I15 hardening re-run: 30 passed / 0 failed. I11R2 governance-binding
audit: 14 passed, artifact regenerated mechanically for the 2 new tracked test
filenames (`python_files_scanned` 995 -> 997, no new unexpected hits), and
byte-stable on the no-update re-run.

Full storage: **1832 passed / 13 skipped / 0 failed** (I15R1 baseline 1791 +
41 new). Full project `quant-lab/tests`: **3211 passed / 14 skipped / 0
failed** (baseline 3170 + 41 new). Ruff clean on the changed scope;
compileall clean; mypy 10 pre-existing errors in `providers/` and `probes/`,
**0** in `paths.py` or `atomic.py`; secret scan clean.

### 6.1 One long storage run showed 29 transient failures — reported, NOT hidden

The **first** full-storage run reported 29 failed / 1803 passed / 2 errors, all
inside three DuckDB-backed projection modules
(`test_projection_lineage.py`, `test_projections.py`, `test_writer_preconditions.py`),
all with Windows filesystem errors (`WinError 2/3` path-not-found,
`PermissionError`) against those modules' hard-coded `C:\tmp_*` roots.

This was investigated rather than dismissed:

- those three modules **pass 89/89 in isolation**;
- a full-storage run **excluding only the two new I15R2 test files** (production
  changes still applied) is **1791 passed / 11 skipped / 0 failed** — exactly
  the I15R1 baseline, proving the production repair introduces no failure;
- a full-storage run **including** them then re-ran **1832 passed / 13 skipped
  / 0 failed**.

Conclusion: the 29 failures were a transient Windows filesystem/handle window
in the long run, not a deterministic interaction with the repair and not
related to it. Per §13 this is NOT recorded as "a known flake": it was
reproduced-against, isolated and re-measured green. Disk headroom was checked
and unchanged (11 G free throughout).

---

## 7. What I15R2 does NOT do

No change to staged-source inode anchoring, destination-parent containment,
post-commit revert, the POSIX descriptor-relative `O_NOFOLLOW` parent walk, the
fresh-corruption matrix, secret safety or resource bounds — except where §11
revalidation was required at the name-max probe. No retry was added. No
security error was downgraded, swallowed or retried. No POSIX case folding.
No self-ratification. I16 not started.

---

## 8. Published I15R2 evidence

- `BLOC_04_I15R2_CONCURRENT_PUBLICATION_MATRIX.json`
- `BLOC_04_I15R2_PATH_CANONICALIZATION_MATRIX.json`
- `BLOC_04_I15R2_EVIDENCE_CORRECTION.md` (this file)

I03–I14, I15 and I15R1 matrices are unmodified. The only historical artifact
touched is `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`, regenerated
mechanically per §29 because two new tracked test filenames entered its scan.