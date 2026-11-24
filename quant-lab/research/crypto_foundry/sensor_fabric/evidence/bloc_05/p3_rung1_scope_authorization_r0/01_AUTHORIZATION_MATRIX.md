# PATH-SPECIFIC AUTHORIZATION MATRIX

Evaluated against the **committed** audits at `295acb52`, not an interpretation. All paths below are `quant-lab/`-relative because that is how the audits normalise (`removeprefix("quant-lab/")`).

## 0. The refusing laws (measured)

| Audit | Mechanism | Entries | Effect on proposed paths |
|---|---|---|---|
| `test_b5_i05_scope_audit.py::test_only_the_authorized_paths_were_added_since_the_i05_base` | `allowed_prefixes` tuple + `path.startswith(...)`, asserted over **staged**, **unstaged** and **untracked** | 18 | all proposed paths REJECTED |
| `test_b5_i10_scope_audit.py::test_only_the_i10_authorized_prefixes_carry_tracked_changes` | `allowed` tuple + `path.startswith(...)`, same three sets | 25 | all proposed paths REJECTED |
| `test_b5_i09_scope_audit.py::test_sem_a04_sealed_trees_are_untouched_relative_to_the_i09_base` | git diff over a **named** sealed list: `identity/`, `terms/`, `time/`, `normalization/__init__.py`, `models.py`, `enums.py`, `registry/`, `config/…` | — | `consumer/` is **not sealed → I09 does not block** |
| `test_i11r2_binding_audit.py:477` | `payload["python_files_scanned"] == len(_scanned_paths())` | 1 pin | new `.py` ⇒ 1,102 → 1,105 mismatch |
| `test_b5_i05_scope_audit.py::test_the_governance_audit_republish_is_mechanical_only` | staged diff of the I11R2 artifact must be **exactly one removed + one added line**, both naming `python_files_scanned` | 1 | sanctions the republish *only* for authorized additions |

Admitted `src/` families today: `normalization/time/`, `normalization/common/`, `normalization/authority/`, `normalization/sensors/`. There is no `normalization/` catch-all, so a new sibling package cannot slip in.

---

## Path 1 — `src/crypto_sensor_fabric/normalization/consumer/models.py` (Rung 1, REQUIRED)

| Field | Answer |
|---|---|
| 1. Rule that refuses it | I05 `allowed_prefixes` (18 entries) and I10 `allowed` (25 entries) — neither contains `…/normalization/consumer/`; both assert on untracked paths too, so the file cannot even exist pre-commit |
| 2. Why required | Rung 1's entire deliverable: `ConsumerRequest`, `ConsumerVerdict`, `ConsumerDecision`, `ConsumerRefusalReason`, `CustodyAuthorityBasis` with their laws (A1.1–A1.5). It has no home in any admitted package |
| 3. Exact authorization | one named entry: `"src/crypto_sensor_fabric/normalization/consumer/models.py"` |
| 4. Why no admitted location works | `sensors/` is frozen as "exactly the modules" by I10's `FROZEN_MODULES` (a fifth module is an explicit unapproved surface) and holds verifier logic, not contracts; `authority/` is the trust-root loader and is sealed by I09's custody diff; `models.py`/`enums.py` at the normalization top level are **byte-sealed** by I09 a04; `common/` is date/number helpers. Dropping contracts into any of them would breach a *stronger* law than the one being amended |
| 5. Risk of broadening | Medium if granted as a directory prefix (a future file lands silently); **low if granted as exact files** — the grant dies at that path and every later file needs its own decision |
| 6. New governance tests | assert `consumer/` contains exactly the authorized files; assert no module in `consumer/` imports `sensors/verification.py` at runtime; assert `ConsumerDecision` has exactly 3 members and basis has exactly 3 with no `SYNTHETIC_TEST_ONLY`; assert no callable/verdict field on `ConsumerRequest` |
| 7. Rollback | revert the entry + delete the files; inventory republish back to 1,102; no other artefact depends on it |

## Path 2 — `src/crypto_sensor_fabric/normalization/consumer/__init__.py` (conditional)

| Field | Answer |
|---|---|
| 1. Rule | same two allowlists |
| 2. Why required | **only** if namespace-package import proves unreliable under `PYTHONPATH=quant-lab/src`; the design's C1 does not require exports |
| 3. Exact authorization | `"src/crypto_sensor_fabric/normalization/consumer/__init__.py"` |
| 4. Alternatives | Python 3.12 implicit namespace packages work without it; the honest default is *no `__init__.py`* unless a test proves otherwise |
| 5. Risk | very low (empty file) but it is still a tracked `.py` and moves the inventory |
| 6. Tests | import-safety test does `import crypto_sensor_fabric.normalization.consumer.models` |
| 7. Rollback | delete; inventory −1 |

**Recommendation:** do not request it in Rung 1. Request it only with evidence of a real import failure.

## Path 3 — `tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py` (Rung 1, REQUIRED)

| Field | Answer |
|---|---|
| 1. Rule | both allowlists; admitted test families are `test_b5_i05_`, `test_b5_i08…i11`, `test_b5_i11r1_`, `test_b5_i11f1_`, `test_b5_i09p2a…e` — `test_b5_p3_consumer_` matches none |
| 2. Why required | A1.1–A1.5 are only meaningful as executed assertions; the contract exists to be tested |
| 3. Exact authorization | `"tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py"` |
| 4. Alternatives | the `test_b5_i10_` / `test_b5_i09p2e_` prefixes are *other checkpoints'* named suites; adding consumer contract tests there would misattribute ownership and expand a checkpoint's scope retroactively |
| 5. Risk | low; exact-file entry |
| 6. Tests | the file itself is the test; governance meta-test asserts it exists and is imported by the suite |
| 7. Rollback | delete file + entry |

## Path 4 — `tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py` (Rung 5; **already exists elsewhere**)

| Field | Answer |
|---|---|
| 1. Rule | both allowlists |
| 2. Why required | Rung 5 (attacks A01–A20) |
| 3. Exact authorization | `"tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py"` |
| 4. Alternatives | none; a security suite must not live inside another checkpoint's file |
| 5. Risk | **coordination risk, not permission risk** — see below |
| 6. Tests | mutation-checked controls (removing a control must fail a test) |
| 7. Rollback | delete file + entry |

**Collision found in Phase 0.** Remote branch `agent/crypto-sensor-fabric-p3-consumer-security-r1` (`16b4a0b2`, a **direct child of `295acb52`**, 777 lines) already creates this exact path, self-declared `STATUS: RED / PENDING` because `consumer/` does not exist. It is a sibling workstream: not merged here, not modified here. Any authorization for this path must name that branch as the current claimant and must not re-create the file; the Rung 5 work becomes *reconcile and green* it, not author it.

## Path 5 — future Rung 2–4 source (marked FUTURE SCOPE ONLY)

| Path | Rule | Exact authorization | Notes |
|---|---|---|---|
| `…/consumer/policy.py` | both allowlists | own exact entry at Rung 2 | verification derivation + inspection |
| `…/consumer/custody_authority.py` | both allowlists | own exact entry at Rung 3 | authority derivation from pinned bytes |
| `…/consumer/rebinding.py` *(optional)* | both allowlists | only if it outlives a private function | design keeps rebinding private inside `policy.py` |

**Not requested now.** Each rung's directive requests its own entries; nothing here pre-authorizes them.

## Inventory impact

| State | Tracked `.py` | I11R2 pin | Action |
|---|---|---|---|
| now | 1,102 | 1,102 | none |
| Rung 1 (models + contracts test, no `__init__.py`) | **1,104** | 1,102 | mechanical republish ⇒ 1,104 |
| Rung 1 with `__init__.py` | 1,105 | 1,102 | republish ⇒ 1,105 |
| + sibling security test merged | 1,105 / 1,106 | — | republish once, after the final merge |

The republish writes only the `python_files_scanned` line (`UPDATE_I11R2_EVIDENCE=1`), and the I05 audit already proves mechanically that no other line may move.

## Rollback conditions (global)

1. Any new file lands outside the named entries ⇒ revert.
2. Any `consumer/` module imports `sensors/verification.py` at runtime ⇒ revert (A1.5).
3. A republish changes anything but `python_files_scanned` ⇒ revert (I05 a-mechanical law).
4. `INTEGRATION_STATE` or the approval manifest changes ⇒ revert immediately; those are not in scope at any rung.
5. The sibling security branch is merged into the consumer branch ⇒ stop and re-run the matrix; two checkpoints would then share one test path.
