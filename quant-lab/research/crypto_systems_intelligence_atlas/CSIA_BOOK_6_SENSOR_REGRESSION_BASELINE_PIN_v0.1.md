# CSIA — Book 6 Sensor Regression Baseline Pin v0.1

**Status:** `PINNED — VERIFIED MEASUREMENT`
**Date:** 2026-10-04
**Decision id:** none. This artifact records a measurement and pins it to a
named commit. It ratifies no policy, opens no gap, and grants no authority.
**Grants implementation authority:** `FALSE`
**Changes any accepted source:** `FALSE`

```text
SENSOR_BASELINE_PINNED          = TRUE
SENSOR_BASELINE_FRAMING_CORRECTED = TRUE   (see section 1)
SENSOR_BASELINE_MEASURED       = TRUE   (reproduced this session, exactly)
SENSOR_BASELINE_VERIFIABLE     = TRUE   (named commit + tree fingerprints)

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 0. The pin

```text
PINNED_COMMIT   = 5f94c3f40cea4441470c57671f51454da7377361
PINNED_BRANCH   = agent/crypto-systems-intelligence-atlas-book6-build
PINNED_COMMIT_SUBJECT = "docs(csia): accept Book 6 fundamental measurement kernel"
PRESERVES_ANCHOR      = 3919fb8052e216e94034a753fb258d338c5fa0dc   (verified ancestor)
COMMAND        = python -m pytest tests/crypto_sensor_fabric -q
RUN_FROM       = quant-lab/
```

### 0.1 The measured profile, reproduced this session

```text
SENSOR_COLLECTED   = 2343
SENSOR_PASSED      = 2325
SENSOR_FAILED      =   14
SENSOR_SKIPPED     =    4
SENSOR_XFAILED     =    0
OBSERVED_DURATION  = 197.56s
```

```text
MATCHES_OPERATOR_SUPPLIED_BASELINE = TRUE   (exact, all four figures)
```

---

## 1. The framing correction — this is the substantive finding

The operator's request was to pin the baseline to "a named sensor commit".
That framing was wrong, and the investigation says so rather than forcing a fit.

**The sensor baseline was never a sensor-programme measurement.** It was measured
on the sensor suite **as it exists inside the CSIA lineage**.

| Reference point | Collected | Verdict |
|---|---|---|
| CSIA lineage at `5f94c3f40c` (`tests/crypto_sensor_fabric`) | **2343** | **MATCH** |
| CSIA planning lineage at `8433c73f` | **2343** | **MATCH** |
| sensor branch `a4ee26379` (2026-09-24) | 2850 | no match |
| sensor branch `e8d1384d9` (2026-10-04, tip) | 3353 | no match |

The sensor programme has advanced well past 2343: its branch tip collects **3353**
tests. Yet the CSIA figure has been reproduced exactly, twice this session, on
two independent CSIA lineages.

```text
SENSOR_BASELINE_IS_A_CSIA_LINEAGE_MEASUREMENT = TRUE
SENSOR_BASELINE_IS_A_SENSOR_BRANCH_MEASUREMENT = FALSE
```

Pinning to a sensor-programme commit would have been a category error: it would
have bound a CSIA freeze gate to a commit that the CSIA freeze has never
referenced, and it would have silently replaced 2343 with 3353.

The correct pin is a **CSIA-lineage commit** — and the only one that matters is
`5f94c3f40c`, which is also the base every future Book 6 implementation branch
must derive from. The pin and the implementation base are therefore the same
commit by construction, not by coincidence.

---

## 2. The correction of "14 xfailed" to "14 failed"

The CSIA corpus records the baseline as:

```text
G-3  Zero regressions: Sensor suite unchanged from its accepted baseline
     (2325 PASS / 14 FAIL / 4 SKIPPED; the 14 are the known canonical set)
```

The 14 are **failures**, not expected failures. They are a deliberate canonical
set of failing evidence-matrix regeneration checks that the sensor programme
carries as known-and-accepted at this point in its history.

```text
THE_14_ARE_XFAILURES = FALSE
THE_14_ARE_FAILURES  = TRUE
SENSOR_XFAILED       = 0
```

This matters mechanically, not cosmetically. An `xfail` is absorbed by a green
run. A **known failure** breaks a green run. A freeze gate written against
"2325 / 14 xfail" would pass on a run with 14 *unexpected* failures — it would
be a gate that cannot fail. Written against "2325 / 14 fail / 4 skip", it can.

A prior uncommitted draft of the consolidated authorization review stated
"14 xfailed" and carried the figure forward as operator-supplied and unverified.
That statement was wrong on both counts and is corrected by this artifact. The
review and the packet were never committed or ratified, so they are amended in
place; this section is the audit trail for the change.

```text
CORRECTION_MADE = 14 xfailed -> 14 failed
CORRECTION_ALSO = "not re-run / could not verify" -> re-run and reproduced exactly
TARGET_FILES_WERE_UNCOMMITTED = TRUE
RATIFIED_RECORD_EDITED = FALSE
```

---

## 3. The 14 canonical failures, pinned by identity

A count alone is a weak freeze gate: a different 14 failures would satisfy it.
These are pinned by name.

```text
tests/crypto_sensor_fabric/storage/test_i05r2_evidence.py::
    TestCrashBoundaryMatrix::test_deterministic_generation
    TestPhysicalSchemaMatrix::test_deterministic_generation
    TestPublicApiMatrix::test_deterministic_generation
tests/crypto_sensor_fabric/storage/test_i05r3_evidence.py::TestI05R3Evidence::
    test_lineage_identity_matrix_matches_committed
    test_time_contract_matrix_matches_committed
tests/crypto_sensor_fabric/storage/test_i05r4_evidence.py::TestI05R4Evidence::
    test_evidence_immutability_matrix_matches_committed
    test_service_retry_matrix_matches_committed
    test_verifier_interface_matrix_matches_committed
tests/crypto_sensor_fabric/storage/test_i06_evidence.py::test_generated_matches_committed[
    build_identity_matrix-BLOC_04_I06_IDENTITY_MATRIX.json]
    test_generated_matches_committed[
    build_mutation_matrix-BLOC_04_I06_MUTATION_MATRIX.json]
    test_generated_matches_committed[
    build_resolution_matrix-BLOC_04_I06_RESOLUTION_MATRIX.json]
tests/crypto_sensor_fabric/storage/test_i06r1_evidence.py::test_generated_matches_committed[
    build_canonical_contract_matrix-BLOC_04_I06R1_CANONICAL_CONTRACT_MATRIX.json]
    test_generated_matches_committed[
    build_declaration_durability_matrix-BLOC_04_I06R1_DECLARATION_DURABILITY_MATRIX.json]
    test_generated_matches_committed[
    build_identity_binding_matrix-BLOC_04_I06R1_IDENTITY_BINDING_MATRIX.json]
```

```text
ALL_14_ARE_EVIDENCE_MATRIX_REGENERATION_CHECKS = TRUE
ALL_14_ARE_IN_STORAGE_EVIDENCE_MODULES           = TRUE
```

Every one is an **evidence-matrix regeneration** check: the test regenerates a
committed evidence matrix and asserts it matches. They fail because the CSIA
lineage carries an older sensor evidence snapshot than the generators expect.
None is a Book 6 artefact.

```text
FAILURES_CAUSED_BY_BOOK_6 = 0
FAILURES_CAUSED_BY_THIS_SESSION = 0
```

**The freeze gate is therefore:** exactly these 14 fail; no others.

---

## 4. Machine-verifiable freeze fingerprints

A named commit tells you *where* the baseline was measured. It does not let you
verify it cheaply — the sensor suite takes ~200s. These fingerprints let any
future implementer confirm the freeze in under a second, without running pytest
at all.

Method: for every file under the tree, exclude `__pycache__`, normalise CRLF to
LF, take the MD5, then SHA-256 over the sorted `(relpath, md5)` pairs.

```text
SENSOR_TESTS_TREE_FILES  = 215
SENSOR_TESTS_TREE_SHA256 = a3a99657117c0238a0f635c19dde8a7f8e5ab3575c8bac6b334fa3e7254b0fd5

SENSOR_SRC_TREE_FILES    = 112
SENSOR_SRC_TREE_SHA256   = b16a148e5ac05ca148bf6bd60af4be6ff72b1fbc95e118dafdbcf7f24c6b2081
```

### 4.1 Both CSIA lineages carry the identical sensor tree

Verified this session, file by file, CRLF-normalised:

```text
PLANNING tests tree = 215 files, a3a99657117c0238a0f635c19dde8a7f8e5ab3575c8bac6b334fa3e7254b0fd5
BOOK6    tests tree = 215 files, a3a99657117c0238a0f635c19dde8a7f8e5ab3575c8bac6b334fa3e7254b0fd5

FILES_ONLY_IN_ONE_LINEAGE = 0
FILES_DIFFERING_IN_CONTENT = 0
```

So the freeze is not branch-local: it is identical on the planning branch and
on the accepted Book 6 build branch. Any implementation branch derived from
`5f94c3f40c` inherits it automatically.

> **CRLF normalisation is mandatory for this check.** A raw `diff -rq` between
> the two worktrees reports every sensor file as differing. That is a Windows
> checkout artefact, not a content change — 0 files actually differ once line
> endings are normalised. An un-normalised freeze check would be permanently red
> and would therefore be permanently ignored.

### 4.2 The verification procedure

```text
1. Confirm the implementation branch derives from 5f94c3f40c
     git merge-base --is-ancestor 5f94c3f40c HEAD
2. Confirm the sensor trees are untouched (fast path, ~1s)
     compare both SHA-256 fingerprints against section 4
   IF BOTH MATCH -> the sensor freeze gate is satisfied; pytest is not required
3. Optionally run the full sensor suite (~200s)
     cd quant-lab && python -m pytest tests/crypto_sensor_fabric -q
     EXPECT: 2325 passed, 14 failed, 4 skipped
   AND the 14 failures are exactly those named in section 3
```

```text
SENSOR_FREEZE_VERIFIABLE_WITHOUT_RUNNING_TESTS = TRUE
SENSOR_FREEZE_CHECK_COST          = ~1 second (fast path)
SENSOR_FULL_SUITE_COST           = ~200 seconds
```

---

## 5. Standing state

```text
SENSOR_REGRESSION_BASELINE_PINNED = TRUE
SENSOR_REGRESSION_BASELINE_PINNED_TO = 5f94c3f40cea4441470c57671f51454da7377361
SENSOR_REGRESSION_BASELINE_CANONICAL = 2325 passed / 14 failed / 4 skipped
SENSOR_BASELINE_REPIN_REQUIRED      = FALSE

CRITERION_12_SENSOR_FREEZE_PRESERVABLE = TRUE   (now verified, not asserted)
```

Criterion 12 of the consolidated authorization review was previously the only
one resting on an unverified operator-supplied figure. It now rests on a
reproduced measurement and a named commit.

---

## 6. What this pin did not do

```text
RATIFIED_ANYTHING          = FALSE
IMPLEMENTATION_AUTHORIZED  = FALSE
SOURCE_CHANGED             = FALSE
TEST_CODE_WRITTEN          = FALSE
BRANCH_CREATED             = FALSE
WORKTREE_CREATED           = FALSE
FROZEN_WORKTREE_MUTATED    = FALSE   (read-only pytest run; 0 drift, re-verified)
SENSOR_SOURCE_TOUCHED      = FALSE
RATIFIED_RECORD_EDITED     = FALSE
GAPS_REOPENED              = FALSE
```

The frozen Book 6 worktree was used **read-only**: the suite was collected and
run against the already-checked-out `5f94c3f40c`, which created no tracked
change and no drift.

---

## 7. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.1.md        (G-3, origin of the figures)
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.6.md        ("independently reproduced")
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md   (G-3)
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md  (criterion 12)
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.1.md  (section 7)
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
