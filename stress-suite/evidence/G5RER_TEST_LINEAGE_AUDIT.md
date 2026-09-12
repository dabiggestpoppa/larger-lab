# G5RER TEST LINEAGE AUDIT — reconciliation of the 599/599 vs 766/766 vs 764/777 contradiction

**Audit ID:** G5RER-TLA-2026-02
**Authoritative branch:** `agent/oce-institutional-stress-suite-build`
**Current head (audit start):** `7ba17112e7521be700255188d36d15f63a951b3e`
**Method:** every number below is reproduced by an actual pytest run at the named
commit on a materialized tree; nothing is asserted from prose. All runs used
`PYTHONIOENCODING=utf-8`. No file was modified to produce this audit.

---

## 1. The contradiction, stated precisely

| Claim source | Claim |
|---|---|
| `G4R_RESULT.md` (gate at G4R artifacts head `9d8840b6`, archived `463495c3`) | 599 / 599 PASS |
| `G5R_RESULT.md` / `G5R_EVIDENCE_RECEIPT.json` (artifacts head `181b2589`, archived `b8a152e8`) | 766 / 766 PASS — "684 preserved + 82 G5R", "all prior 684 tests remain green" |
| `G5R_EXTERNAL_REVIEW_ADDENDUM.md` (current head `7ba17112`) | full suite 764 / 777 at base `b8a152e8` — "13 failures, all pre-existing G4R failures" |

If the same 13 tests existed at the G4R and G5R gates and failed, neither 599/599
nor 766/766 could be true. The resolution below shows the contradiction is an
artifact of an **undefined pytest invocation surface**, not of the tests.

---

## 2. Measured collection + pass/fail at every relevant head

All full-suite runs below collect every file under `stress-suite/tests`.

| Head | Commit | Collected | Run A: `cd stress-suite && python -m pytest tests -q` | Run B: `pytest stress-suite/tests -q` (repo root, plain) | Run C: `python -m pytest stress-suite/tests -q` (repo root) |
|---|---|---|---|---|---|
| G4R archive head | `463495c3` | **599** | **599 passed** | (see A/B equivalence below) | 586 passed, **13 failed** |
| G5 archive head | `56c0605d` | **684** | **684 passed** | — | — |
| G5R archive head ("base" in addendum) | `b8a152e8` | **766** | **766 passed** | 766 passed | 753 passed, **13 failed** |
| Current head | `7ba17112` | **777** | **777 passed** | 777 passed | 764 passed, **13 failed** |

Run A and Run B are equivalent surfaces (neither puts the repo root on
`sys.path`); Run C is the only surface on which any test fails, at every head,
and the failing set is identical at every head.

Result: **the G4R 599/599, G5 684/684 and G5R 766/766 gate numbers are each
reproduced exactly on the canonical surfaces (Run A / Run B).** The addendum's
"764 / 777 at base" is doubly wrong: (a) at base `b8a152e8` the collection is
766, not 777 — 777 is only reached at the current head after 11 later tests were
added; (b) the 13 are not failing tests on any surface the gates used.

---

## 3. The 13 failing names (Run C only) and when each entered

All 13 live in `stress-suite/tests/test_g4r.py`; all 13 fail in Run C with the
identical error:

```
ModuleNotFoundError: No module named 'tests.test_g4'
```

raised by the fixture-reuse import `from tests.test_g4 import _s13_epoch[, _s13_artifacts]`
executed inside the test body.

1. `test_manifest_only_reconstruction_fails_when_external_surfaces_required`
2. `test_evaluation_contract_ref_must_resolve`
3. `test_lifecycle_contract_ref_must_resolve`
4. `test_negative_knowledge_ref_must_resolve`
5. `test_operator_ratification_ref_must_resolve`
6. `test_transformation_evidence_ref_must_resolve`
7. `test_wrong_version_artifact_fails`
8. `test_wrong_epoch_knowledge_projection_fails`
9. `test_wrong_authority_snapshot_fails`
10. `test_artifact_with_correct_id_wrong_fingerprint_fails`
11. `test_evaluation_and_lifecycle_contracts_are_separate`
12. `test_reconstruction_validates_content_not_emptiness`
13. `test_reconstruction_conflicts_are_missing_surfaces`

**When each entered:** `test_g4r.py` was created in `9d8840b6`
(STRESS-G4RX, G4R's own final artifacts commit). All 13 test functions — and the
`from tests.test_g4 import ...` reuse imports inside them — are present in the
file at `9d8840b6` (verified per-name). The file was touched once more, in
`8a1568f2` (STRESS-G5P0), which upgraded the shared S13 helper wiring
(`_s13_pack_and_registry` gained evidence/registry binding); that change did not
introduce or remove any of these 13 functions and did not introduce the import
pattern (it predates the change).

---

## 4. Root cause — import shadowing under one invocation surface

Why Run C fails while Runs A/B pass:

* `stress-suite/tests/` has **no `__init__.py`** — it is a namespace package
  importable as `tests` only when `stress-suite/` is on `sys.path` (which
  `stress-suite/conftest.py` arranges) **and** no regular `tests` package shadows
  it.
* The **repo root also contains a `tests/` package with `__init__.py`**
  (added in `0c5e79c4`, an ancestor of every head in this audit; verified
  ancestor of `9d8840b6`). A regular package beats a namespace package in
  Python's import resolution regardless of `sys.path` order.
* `python -m pytest` puts the current directory (repo root) on `sys.path[0]`, so
  `import tests` binds to the root `tests/` package; `tests.test_g4` does not
  exist there → `ModuleNotFoundError` at test-run time.
* Plain `pytest` (Run B) and any run whose cwd is `stress-suite/` (Run A) do not
  put the repo root on `sys.path`, so `tests` resolves to `stress-suite/tests/`
  and the imports succeed.

Because the shadowing condition (root `tests/__init__.py`) predates the 13
tests, Run C fails these 13 at **every** head where `test_g4r.py` exists —
including G4R's own archive head `463495c3` (measured: 586 passed / 13 failed).
That is the decisive proof for question 7: **no 599/599 or 766/766 measurement
was ever made on the Run C surface.**

The failure is an import-resolution artifact, not an assertion or logic failure:
on the canonical surfaces all 74 `test_g4r.py` tests (61 + these 13) pass at
every head.

---

## 5. Question-by-question answers

1. **Exact collection at G4R archive head (`463495c3`): 599 tests.** Reproduced
   by Run A (599 passed) and Run C collect (599 collected). Per-file breakdown
   unchanged from the G4R accounting audit (pre-G4 456 + G4 68 + G4R 75 = 599).
2. **Exact collection at G5R archive head (`b8a152e8`): 766 tests.** Reproduced
   by Run A (766 passed). The 766 = 684 preserved + 82 G5R per
   `G5R_EVIDENCE_RECEIPT.json`; the G5 head (`56c0605d`) reproduces the 684
   baseline exactly.
3. **Exact collection at current head (`7ba17112`): 777 tests.** Reproduced by
   Run A (777 passed). Delta from base: +11, all in `tests/test_g5r.py`
   (82 → 93 functions), added by commit `7efa6bb6` (STRESS-G5RER). Verified by
   `git diff b8a152e8..HEAD -- stress-suite/tests/` = exactly
   `test_g5r.py | 313 insertions, 5 deletions`, 11 new `def test_` functions,
   zero deletions of test functions.
4. **Names of the 13 Run-C failures:** listed in §3.
5. **When each entered the repository:** all in `9d8840b6` (STRESS-G4RX),
   Sep 1 2026, as part of `test_g4r.py` creation (see §3).
6. **Classification of each of the 13:** **AUTHORITATIVE** — never superseded,
   never obsolete, never accidentally collected, no logic regression. They are
   live S13 reconstruction/registry regressions that pass on the canonical
   surface at every head. The only condition under which they error is the
   non-canonical Run C surface (`python -m pytest` from the repo root), via the
   namespace-shadowing mechanism in §4. The addendum's label "pre-existing G4R
   failures" is **superseded**: they were never counted as failures by any gate
   and are not failing tests in the authoritative suite. (Their presence since
   `9d8840b6` does mean the Run C failure mode is old — it is "pre-existing" as
   a surface artifact, but it is not a G4R *test* failure and is not evidence of
   any regression.)
7. **Why G4R could say 599/599 and G5R 766/766 if those tests existed:** because
   both gates measured on the canonical surfaces (Run A / Run B), on which all
   tests pass. Deterministic proof: Run C fails the identical 13 at G4R's own
   archive head (586/599 measured), so the recorded 599/599 cannot have come from
   a Run-C-style invocation. No test needed to change between gates for the
   numbers to be simultaneously true.
8. **Exact commands used by each historical receipt, if reconstructable:** the
   gate receipts do **not** record their pytest command (verified: no receipt or
   audit under `stress-suite/evidence/` contains a command string). The per-scenario
   receipts are generated by `stress-suite/scenarios/g{4,5,5r}_run_evidence.py`,
   whose docstrings state they are "run from the stress-suite root". The gate
   totals are reconstructable exactly by Run A
   (`cd stress-suite && python -m pytest tests -q`) or Run B
   (`pytest stress-suite/tests -q` from the repo root), which reproduce 599/599,
   684/684, 766/766 and 777/777 at the respective heads — and are **not**
   reproducible by Run C. This audit therefore defines Run A as the
   **authoritative full-suite command** going forward (it is cwd-independent,
   i.e. robust to the root-`tests` shadowing).

---

## 6. Per-file collection (for arithmetic audits)

`test_g4r.py` = 74 at every head (G4R, G5, G5R, current). The only per-file
delta between `b8a152e8` and `7ba17112` is `test_g5r.py` 82 → 93. 766 + 11 = 777.

Related accounting corrections superseded by this audit:

* Addendum table row "Full stress-suite | 764 | 777" conflated two heads: base
  collection is 766; 777 is the current-head collection. The 13 "failures" do
  not exist on the authoritative surface at any head.
* Addendum/`G5R_EXTERNAL_REVIEW_RECEIPT.json` regression arithmetic ("9 new
  regression tests" vs enumerated 4+2+2+3=11): the true delta since base is
  **11 new collected tests**, all in `test_g5r.py` at `7efa6bb6` (see TC-07's
  superseding receipt for the recomputed accounting from collected names).

---

## 7. Terminal state

**A) FULL SUITE GREEN.**

* Authoritative command: `cd stress-suite && python -m pytest tests -q`.
* Current head `7ba17112`: **777 / 777 passed** (measured).
* G5R archive head `b8a152e8`: **766 / 766 passed** (measured) — reproduces the
  G5R gate receipt exactly.
* G5 archive head `56c0605d`: **684 / 684 passed** (measured).
* G4R archive head `463495c3`: **599 / 599 passed** (measured).

No test-contract change was required and no coverage is weakened; no test was
deleted or disabled. The lineage contradiction is resolved by fixing the
invocation surface, not by editing history or suppressing tests.
