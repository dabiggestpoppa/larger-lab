# OCE Golden System
## B5-I7 — Construction Plan (P0) — v1.0

**Document ID:** OCE-B5-I7-CONSTRUCTION-001
**Version:** 1.0
**Status:** **P0 FROZEN — PLANNING ONLY. IMPLEMENTATION NOT AUTHORIZED.**
**Stage:** `AUTHORIZED_STAGE=B5-I7-P0`
**Base SHA (observed):** `c6a6479da427ddfe6af06622fc80b2221a4cdc5c`
**Gate (plan §7 row `B5-I7`):** *Governed change demonstrated*
**Charter increment:** `I-8` (charter §12 row `I-8 (optional) | B5-I7`)
**Companions:** contract, registry (44), acceptance matrix (44 rows), failure matrix (16 classes).
**`MERGE_AUTHORIZED = false`** · recurring cost `$0` · `capital.authority = none`

---

## 1. What this stage builds

One governed change — *add a queue-depth observability panel* (packet §11) — applied
through the full C4.S5 change cycle as a **read-only console/client change over already
declared surfaces**, plus the C5.S1/C5.S2/C5.S4 measurement and learning artifacts.
Control-plane source, contract pack and every existing test stay byte-identical
(`B5I7-R03`), which *is* the charter §12 I-8 evidence that no control-plane modification
was required.

## 2. Rung ladder (construction plan §6 discipline, unchanged)

| Rung | Deliverables | Gate | Evidence |
|---|---|---|---|
| **P0** | this contract, registry, acceptance matrix, failure matrix, construction plan, ledger §1 + §18 | scope frozen; **no** implementation gate `PASS` | this commit |
| **R1** | panel read composition + reference drill report captured from the **base** tree; change record §1 intent, §2 plan | deterministic kernel renders from declared reads; reference sha256 recorded | raw bytes + sha256 |
| **R2** | refusal/boundary behavior (fail-closed, bounds, loopback, secret-scan) + compatibility binding | every refusal observable with frozen reason vocabulary | node output, request logs |
| **R3** | the 27 planned nodes green; mutation battery executed red then restored; rollback exercised; hostile cases F1–F16 | positive + negative + cleanup proofs all recorded | junit + battery raw output + cleanup record |
| **R4** | one additive CI selection step (`Execute B5-I7 governed-change proofs`), floor 27, zero skip, orphan/duplicate checks, exact-head binding | authoritative selection green at exact head; shared runner green | CI artifact `b1-i1r-evidence-<run_id>` |
| **EVIDENCE** | ledger append + `OCE_B5_I7_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` parsed from raw artifacts | no `OBSERVED` value without a parsed source | ledger §18.x |

Ladder laws: no amend, no rebase, no force-push, no committed-red false green; CI defects
are repaired in separate `Xn` commits, append-only. Every rung after P0 requires a **fresh
operator `AUTHORIZED_STAGE`**.

## 3. Rung constraints (what each rung may not do)

- **R1** may not touch `infrastructure/control-plane/**` (source, contracts, existing tests)
  and may not create `test_b5_i7_web_view.py` (`B5I7-DF01`).
- **R2** may not weaken any existing refusal or exit code (`B5I7-R23`); bounds are additive.
- **R3** may not weaken an assertion to make a mutation "pass"; a mutation that does not go
  red is recorded as **not discriminated** (`B5I7-EL10`).
- **R4** may not change triggers, permissions, the shared runner, existing steps, the upload
  step or the gate check — one additive step only (`A11`).
- **EVIDENCE** may not write a number that was not parsed from raw output (`B5I7-EL05`),
  may not write a SHA before the object exists (`B5I7-EL01`), and may not describe a
  skipped/pending gate as passed (`B5I7-EL15`).

## 4. Validation architecture (frozen before implementation)

**4.1 Focused test files (exact, exhaustive).**

| File | Nodes | Purpose |
|---|---|---|
| `infrastructure/control-plane/tests/test_b5_i7_governed_change.py` | 12 | change cycle, panel behavior, drill identity, compatibility |
| `infrastructure/control-plane/tests/test_b5_i7_evidence_laws.py` | 15 | `B5I7-EL01`–`EL15` structural/documentary proofs |

No other `test_b5_i7_*` file may exist. `test_b5_i7_web_view.py` **must not exist**
(`B5I7-DF01`); its absence is asserted by the selection step.

**4.2 Authoritative runner selection.**
CI selection is the additive step `Execute B5-I7 governed-change proofs` in
`.github/workflows/b1-i1r-validation.yml` (pattern: the B5-I6 step — whole-file array,
`--collect-only` into `b5-i7-collect.txt`, `--junitxml` into `b5-i7-junit.xml`, stdout into
`b5-i7-pytest-output.txt`, plus an inline python proof). The shared authoritative battery
remains `bash infrastructure/cloud-ground/scripts/run-validation.sh` (`B5I7-R11`), whose
exit code and `stage-status.json.gate_status == READY_FOR_OPERATOR_REVIEW` are parsed from
the raw artifact — never from a badge.

**4.3 Minimum node floor and zero-skip.**
Floor = **27** (`EXPECTED` at P0; re-derived at R4 from `pytest --collect-only` and recorded
as `OBSERVED` only then). Required in the step: `failed == 0`, `errored == 0`,
`skipped == 0`, `xfailed == 0`, `deselected == 0`, `collected == collected_at_base_of_step`,
duplicate node ids == 0.

**4.4 Adjacent-suite selection and shared regression (both SHAs).**
The adjacent B5 population is the nine whole-file selections
`test_console_contracts.py`, `test_b5_i2_mutation_harness.py`,
`test_b5_i3_requirement_registry.py`, `test_b5_i4_console_kernel.py`,
`test_b5_i5_timeline.py`, and the four `test_b5_i6_*.py` files — **186 nodes**, executed at
the base SHA *and* the implementation head (`B5I7-EL07`, `B5I7-EL08`). The common
regression population must be nonzero at both ends; new-test-only execution may never be
cited as regression absence. P0 baseline recorded below (§7) is `OBSERVED`, captured from
raw pytest output.

**4.5 Static checks (documentation/registry rungs and every later rung).**

| Check | Command | Expectation |
|---|---|---|
| boundary (control-plane untouched) | `git diff --name-only --diff-filter=M <base> -- infrastructure/control-plane/src infrastructure/control-plane/contracts infrastructure/control-plane/tests` | empty |
| boundary (frozen docs untouched) | `git diff --name-only <base> -- 'docs/oce-golden-system/OCE_B5_I[0-6]*'` | empty |
| whitespace | `git diff --check` | no output |
| secrets | gitleaks (installed by `sh infrastructure/cloud-ground/scripts/install-gitleaks.sh`) or equivalent pattern scan | no finding |
| line endings | `infrastructure/**/*.py|sh|yml|yaml` and `.github/**` blobs are LF per `.gitattributes`; new docs blobs LF | no CRLF blob in those paths |
| JSON validity | `json.load` on the registry + every cited JSON | parses; canonical serialization matches |
| ID uniqueness/binding | P0 validator (§5 of this plan) | 44 unique ids, 44 bindings, 0 orphans |

**4.6 Mutation battery (planned).**
`infrastructure/control-plane/scripts/b5_i7_mutation_battery.py` (R3) with a machine-readable
result JSON: for each mutation — target file, mutation description, **expected red node**,
observed result (`RED`/`NOT_DISCRIMINATED`), restored sha256 of the mutated file,
`git status --porcelain` after restoration. `EXPECTED` minimum = **12** mutations covering
F1–F14 detection paths plus the evidence-law claims that are structural; every row must show
an actual failing assertion, never an expected-failure annotation.

**4.7 Evidence manifest schema.**
`infrastructure/control-plane/contracts/evidence-manifest.schema.json` —
`manifest_id`, `run_id`, `produced_at`, `artifacts[].{name,path,sha256,size_bytes,required}`,
`outer_digest`. Manifest rows are recomputed from raw bytes at claim time
(`B5I7-EL09`); no manifest row may be typed in by hand.

**4.8 Cleanup record.**
Machine-readable residual state per mutation/negative-control execution: file list with
sha256+size before/after, `git status --porcelain`, listening ports, child processes.
A cleanup claim without this listing fails (`B5I7-EL11`).

**4.9 Exact-head binding method.**
At run time: `HEAD_SHA=$(git rev-parse HEAD)`, `git status --porcelain` must be empty, tree
id via `git rev-parse HEAD^{tree}`; the same CI job writes run id, head SHA, tree id,
junit and output into one artifact. A SHA is written only after `git cat-file -e` succeeds
(`B5I7-EL01`).

**4.10 Evidence-head rerun requirement.**
After the documentation/evidence commit exists, a **fresh** exact-head run of the B5-I7 step
and of `b1-i1r-validation.yml` must reach terminal state and be parsed. Citing an earlier
run of a different head is prohibited (`B5I7-EL06`).

**4.11 Base/head comparison method.**
Run the identical selection at base and head; compare parsed junit counters and node-id sets
(B5-I6 `b5_x1_compare.py` pattern; planned `b5_i7_compare.py` at R4). Deltas must be exactly
the 27 new nodes — every other node identical in id and status. Any other delta is a
regression and stops the stage.

**4.12 Duplicate/orphan detection.**
Zero duplicate node ids within the step; orphan rule: every `test_b5_i7_*.py` present in
`infrastructure/control-plane/tests/` must be listed in the step's file array, and
`test_b5_i7_web_view.py` must be absent; registry planned-node strings must match the
construction-plan §5 inventory verbatim, and no inventory entry may lack a registry binding.

**4.13 Artifact retention.**
CI evidence lives in the run's `b1-i1r-evidence-<run_id>` artifact (platform retention);
anything cited after retention expiry must be re-parsed, not quoted from memory
(`B5I7-EL03`).

**4.14 The four evidence identities (never conflated).**

| Identity | What it proves | Binding |
|---|---|---|
| implementation head | code + focused/adjacent suites green | head SHA recorded at run time |
| evidence head | the evidence-carrying commit's own runs | fresh rerun per §4.10 |
| PR merge ref | PR head/base identity, two parents, tree equality | `gh api`/`git cat-file` after push |
| post-merge truth | `origin/main` after merge | only post-merge runs count for merged claims |

A claim must name which identity it rests on. Placeholder or hand-authored JSON is
permanently disqualified from citation (`B5I7-EL03`).

## 5. Planned node inventory (27 nodes, verbatim from the registry)

| Requirement | Planned node (exact string) | Rung |
|---|---|---|
| `B5I7-EL01` | `TestEL01::test_no_unverified_sha_recorded_as_fact` | `R3` |
| `B5I7-EL02` | `TestEL02::test_no_run_or_artifact_id_recorded_before_existence` | `R3` |
| `B5I7-EL03` | `TestEL03::test_manually_authored_json_not_presented_as_execution_evidence` | `R3` |
| `B5I7-EL04` | `TestEL04::test_planned_totals_labeled_expected_not_observed` | `R3` |
| `B5I7-EL05` | `TestEL05::test_observed_totals_bound_to_parsed_raw_artifacts` | `R3` |
| `B5I7-EL06` | `TestEL06::test_green_claims_carry_sha_and_tree_binding` | `R3` |
| `B5I7-EL07` | `TestEL07::test_regression_absence_never_proven_by_new_tests_only` | `R3` |
| `B5I7-EL08` | `TestEL08::test_common_regression_population_nonzero_and_at_floor` | `R3` |
| `B5I7-EL09` | `TestEL09::test_manifest_rows_recomputed_hash_and_size` | `R3` |
| `B5I7-EL10` | `TestEL10::test_mutation_claims_require_discrimination_and_restoration` | `R3` |
| `B5I7-EL11` | `TestEL11::test_cleanup_claims_require_machine_readable_residual_state` | `R3` |
| `B5I7-EL12` | `TestEL12::test_historical_process_defects_remain_visible` | `R3` |
| `B5I7-EL13` | `TestEL13::test_same_agent_audit_not_labeled_independent` | `R3` |
| `B5I7-EL14` | `TestEL14::test_no_ratification_before_all_mandatory_gates` | `R3` |
| `B5I7-EL15` | `TestEL15::test_no_all_gates_passed_language_while_any_gate_pending` | `R3` |
| `B5I7-R02` | `TestSingleChange::test_exactly_one_governed_change_recorded` | `R3` |
| `B5I7-R07` | `TestChangeCycle::test_change_has_positive_and_negative_proofs` | `R3` |
| `B5I7-R12` | `TestRegressionDrill::test_unchanged_stack_drill_report_byte_identical` | `R3` |
| `B5I7-R15` | `TestPanelContract::test_undeclared_surface_refused_before_io` | `R3` |
| `B5I7-R16` | `TestPanelReadOnly::test_panel_issues_only_get_requests` | `R3` |
| `B5I7-R17` | `TestPanelFailClosed::test_unreachable_stack_never_renders_healthy` | `R3` |
| `B5I7-R18` | `TestPanelFailClosed::test_unknown_queue_depth_rendered_unknown_not_zero` | `R3` |
| `B5I7-R19` | `TestPanelDeterminism::test_identical_inputs_render_byte_identically` | `R3` |
| `B5I7-R20` | `TestPanelLoopback::test_non_loopback_base_url_refused` | `R3` |
| `B5I7-R21` | `TestPanelSecurity::test_panel_output_contains_no_secret_material` | `R3` |
| `B5I7-R22` | `TestPanelBounds::test_oversized_and_malformed_input_refused` | `R3` |
| `B5I7-R23` | `TestCompatibility::test_documented_status_command_and_exit_codes_unchanged` | `R3` |

Every string above appears verbatim in
`OCE_B5_I7_REQUIREMENT_TEST_REGISTRY_v1.0.json` (`requirement_set.planned_test_nodes`) and
in the acceptance matrix surface column. Count: 12 + 15 = **27** (`EXPECTED`).

## 6. Deferred owners (never absorbed into this stage)

| Obligation | Owner | Future stage |
|---|---|---|
| charter `I-7` loopback web view + `test_b5_i7_web_view.py` (`G1`, `G2`) | Operator | operator-directable, not scheduled |
| `G16` accessibility/usability protocol and results (C5.S3) | B5-I8 | `B5-I8` |
| C5.S5 factory corrections, extraction scope, B6 contract | B5-I9 | `B5-I9` (operator-only) |

## 7. P0 baseline actually executed (OBSERVED, raw pytest output)

| Population | Command | Result |
|---|---|---|
| focused + adjacent B5 selection (9 files) | `python -m pytest <9 files> -q` | **186 passed, 0 failed, 0 skipped** (87 s) |
| full `infrastructure/control-plane/tests` at this head | `python -m pytest infrastructure/control-plane/tests -q` | 1091 collected; **956 passed, 32 failed, 103 skipped** (265 s) |
| full suite at base SHA `c6a6479da` (separate detached worktree) | same command | see ledger §18.4 (recorded only after parsing) |

The 32 full-suite failures are confined to `test_b4_startup_gate.py` (26),
`test_b4_cxr7_trusted_program.py` (4), `test_b4_cxr6_activation_capability.py` (1) and
`test_local_lifecycle.py::test_cxr5r1_proc_cmdline_free_of_secrets` (1) — none is in the
B5 population, and none is in a file this P0 touches. They are recorded as
`OBSERVED` environment-dependent baseline failures pending the base-SHA comparison row; no
claim of "all green" is made for the full suite (`B5I7-EL15`).

## 8. What this plan may not do

- May not authorize any rung (fresh `AUTHORIZED_STAGE` per rung, operator only).
- May not weaken, skip or reorder charter gates (charter §13: gates strengthen only by
  amendment).
- May not add requirements beyond the 44 registry ids (charter non-goal: no tests for
  unproposed features).
- May not merge this P0 PR (`MERGE_AUTHORIZED=false`, `NOT IMPLEMENTATION AUTHORIZED`).
- May not begin `B5-I8`, `B5-I9`, Book 6, cloud/hosting/provider work.

## 9. Traceability (registry → rung)

| Rung | Registry ids |
|---|---|
| P0 | `B5I7-R01`, `B5I7-R04`, `B5I7-DF01`–`DF03` (contract/matrix attestations) |
| R1 | `B5I7-R05`, `B5I7-R06`, `B5I7-R12` (reference capture) |
| R2 | `B5I7-R15`–`B5I7-R23` (refusal/bounds/compatibility), `B5I7-R03`, `B5I7-R09` |
| R3 | `B5I7-R02`, `B5I7-R07`, `B5I7-R08`, `B5I7-R12`, `B5I7-EL01`–`EL15`, mutation battery |
| R4 | `B5I7-R10`, `B5I7-R11` (plus static checks §4.5 re-run at head) |
| EVIDENCE | `B5I7-R13`, `B5I7-R14`, `B5I7-R24`, `B5I7-R25`, `B5I7-R26` |

Every one of the 44 ids appears in exactly one primary rung; no id is unassigned.

---

**P0 boundary.** Planning and acceptance freeze only. `MERGE_AUTHORIZED=false`;
**B5-I7 IMPLEMENTATION NOT AUTHORIZED**; `B5-I8`–`B5-I9` remain `LOCKED`.
