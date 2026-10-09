# OCE B5-I3 Implementation Contract — v1.0

**Document ID:** OCE-B5-I3-CONTRACT-001
**Version:** 1.0
**Status:** FROZEN — B5-I3 scope/evidence artifact (scope only; not a ratification)
**Authorized stage:** `AUTHORIZED_STAGE=B5-I3`
**Base (merged main):** `c60e07456559431e560ac4d69141063dd89a9325` (merge of PR #11; parents `e3e38e83866fd6b1897531b0149c568a16b80177`, `bcaa76dc91d4b3e08530a9982a7fbde90495dfdc`)
**Branch:** `oce-book-5-i3` (fresh dedicated worktree `larger-lab-book5-i3`, created from the exact base above; HEAD equals base, 0/0 relation, clean tracked tree at creation)
**Governing charter:** `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` (`OPERATOR_RATIFIED — FROZEN`, 2026-10-07)
**Governing plan:** `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` sections 4, 5 and 7
**Precedent derivation:** `OCE_B5_I2_IMPLEMENTATION_CONTRACT_v1.0.md` section 1 (plan §7 + charter §12 co-derived as one increment)

---

## 1. Official B5-I3 stage identity (derived from frozen authorities, in order)

| Authority | Provision |
|---|---|
| Block 5 plan §7 (row `B5-I3`) | `B5-I3 \| C2 failures/acceptance and construction plan \| Requirement-test registry complete` |
| Block 5 plan §4 `B5.C2.S4` | Failure behavior: define dependency outage, invalid data, partial task, crash, stale state, retry and cancellation behavior → deliverable **failure matrix and recovery plan**; evidence/gate: *"No failure returns false success or loses canonical state."* |
| Block 5 plan §4 `B5.C2.S5` | Acceptance protocol: bind requirements to unit, integration, E2E, adversarial, restart, usability and evidence checks → deliverable **acceptance registry**; evidence/gate: *"Every requirement has executable or explicit human evidence."* |
| Block 5 plan §5 `B5.C3.S1` | Plan generation: bounded dependency plan with grants, budgets, gates and staged commits → deliverable **construction plan**; gate: *"Plan traceable to every acceptance requirement."* (the "construction plan" named in plan §7's B5-I3 row) |
| Charter §12 table 1, row `I-2` | `I-2 \| B5-I3 \| requirement-test registry and acceptance plan` |
| Charter §12 table 2, row `I-2` | Purpose: *"Make acceptance executable before building"*; exact scope: *"requirement-test registry mapping every charter gate (section 11) and scenario (S-1..S-4) to a concrete runnable test"*; executable acceptance gate: *"registry complete; every gate has an executable test or an explicitly deferred owner"*; evidence output: *"requirement-test registry"*; explicit non-goals: *"no tests for unproposed features"*; stop condition: *"a gate with no executable form: stop, ask operator"* |
| Charter §11 | Seventeen acceptance gates G1–G17 (frozen) |
| CAND-004 evidence packet §2 | Four operator-testable scenarios S-1…S-4 (frozen) |
| Ledger §1 row `B5-I3` | `B5-I3 \| C2 failures/acceptance and construction plan \| LOCKED \| Requires B5-I2 complete` — B5-I2 is now `OPERATOR_ACCEPTED` (ledger §9/§10), so the predecessor gate is satisfied |

**Official stage title:** *C2 failures/acceptance and construction plan — requirement-test registry and acceptance plan (charter increment I-2)*.

The plan anchor (B5-I3 = C2 failures/acceptance **and construction plan**) and the charter increment map (B5-I3 = I-2, requirement-test registry and acceptance plan) agree on one and the same increment: make acceptance executable **before** building — every charter gate and scenario bound to a concrete runnable test or an explicitly deferred owner, the C2.S4 failure matrix that the registry's failure-class entries materialize, and the bounded construction plan that must be traceable to every acceptance requirement. C2.S1/S2/S3 are already frozen inside the ratified charter (sections 2/4/5/7) and delivered in executable form by B5-I2 (charter increment I-1); this increment delivers C2.S4 and C2.S5 plus the §5 plan-generation artifact. The mapping is **unambiguous — one increment, not several**. No `BLOCKED_B5_I3_AUTHORITY_CONFLICT` condition exists.

**Stop-condition pre-check (charter §12 I-2):** every one of the 17 gates, 4 scenarios and 7 plan-named failure classes has an executable form or an explicitly authorized deferred owner at this base — gates G4/G5/G7/G9/G10 bind to existing, CI-selected B5-I2 nodes; G14 binds to the authoritative shared runner; G12/G13 bind to ledger attestations plus dependency audits; G16 binds to a usability protocol whose *explicit human evidence* plan §4 (C2.S5) admits, deferred to B5-I8; S-1…S-4 bind to increments I-3…I-6 exactly as charter §12 table 2 assigns them. No gate lacks an executable form; the stop condition does not trigger.

## 2. Exact objective and non-objectives

**Objective (one sentence):** Make CAND-004 acceptance executable before construction by publishing a machine-validated requirement-test registry that maps every charter gate (G1–G17), every scenario (S-1–S-4) and every plan-defined failure class (7) to a concrete runnable test or an explicitly deferred owner — accompanied by the C2.S4 failure matrix/recovery plan and the bounded construction plan for B5-I4+ — proven by executable closure/refusal/negative-control tests in authoritative CI.

**Non-objectives (exact, frozen):**

- no production/runtime code of any kind (`infrastructure/control-plane/src/**` untouched; B5-I3 introduces zero new runtime behavior, zero new endpoints, zero new schemas);
- no modification of the frozen B5-I2 instruments (`console-contract.json`, `console_contracts.py`, `test_console_contracts.py`, `test_b5_i2_mutation_harness.py`, the three existing schemas — all byte-identical at exit);
- no console/CLI/UI/web-view code (charter increments I-3…I-8 own those; `oce/frontend` untouched);
- no tests for unproposed features (charter §12 I-2 non-goal verbatim): no test may exercise a console surface that no ratified increment has built;
- no modification of any workflow except the single added selection step in `b1-i1r-validation.yml` (triggers, shared runner, identity gates, evidence upload, gate check, cleanup and both B5-I2 steps untouched);
- no cloud/hosting/telemetry/LLM/broker/capital/execution surface of any kind; recurring cost stays `$0`;
- no merge, no ratification, no self-acceptance: the mission ends at a draft PR with exact-head evidence;
- B5-I4–I9 remain `LOCKED` and unauthorized.

## 3. Authority ownership

| Concern | Owner (existing, untouched) |
|---|---|
| Canonical job/lease/worker/evidence state | `job_store`, `worker_leases`, `worker_fabric`, `evidence` (B2–B4) |
| Console↔control-plane interface truth | B5-I2 `console-contract.json` + `console_contracts.py` (frozen) |
| Charter gates and scenarios | `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` §11/§2 (frozen; this stage never edits them) |
| Acceptance mapping (this stage) | New registry `OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json` — a **client-side mapping artifact**; it confers no authority, mints no state, and can never make a gate pass by declaring it |
| Gate status transitions | Operator only, via this ledger (plan §7; protocol §7.10 carry-forward) |
| Authoritative execution | Existing `B1-I1R Validation` workflow (`b1-i1r-validation.yml`) |

## 4. Input and output contracts

**Inputs (read-only):** charter §11 (G1–G17), CAND-004 packet §2 (S-1–S-4), plan §4 `B5.C2.S4` failure-class list (dependency outage, invalid data, partial task, crash, stale state, retry, cancellation), the B5-I2 contract pack + its 24 frozen test nodes, the harness-integrity file's 16 nodes, existing control-plane test nodes referenced by registry bindings, and ledger attestations.

**Outputs (exactly four new files + two edited files):**

| Path | Class | Change |
|---|---|---|
| `docs/oce-golden-system/OCE_B5_I3_IMPLEMENTATION_CONTRACT_v1.0.md` | P0 scope contract | NEW |
| `docs/oce-golden-system/OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json` | R1 requirement-test registry (the charter's named evidence output) | NEW |
| `docs/oce-golden-system/OCE_B5_I3_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md` | R1 C2.S4 failure matrix + recovery plan | NEW |
| `docs/oce-golden-system/OCE_B5_I3_CONSTRUCTION_PLAN_v1.0.md` | R1 bounded construction plan, traceable to every requirement id | NEW |
| `infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py` | R2/R3 executable proofs + negative controls | NEW |
| `docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` | Ledger: §1 row `LOCKED → IN_PROGRESS` (this P0 commit); §11 evidence append (EVIDENCE commit only) | EDIT (append-only history preserved; prior sections byte-stable; CRLF preserved) |
| `.github/workflows/b1-i1r-validation.yml` | R4: one added whole-file selection step for the new test file | EDIT (minimal; see §3.14) |

**Registry input/output contract (machine-validated):** UTF-8 JSON, canonical serialization (sorted keys, two-space indent, trailing newline, byte-identical to `json.dumps(obj, indent=2, sort_keys=True) + "\n"`), top-level keys exactly `{registry_id, registry_version, charter, charter_increment, plan_anchor, base_sha, requirement_set, entries}` (closed set — any added/removed key is a refusal), `entries` sorted by `id`, every `id` unique, entry fields closed per binding type (§3.5/§3.13 below), no absolute paths, no timestamps, no durations, no host/user names anywhere in the document.

## 5. State transitions

B5-I3 introduces **no runtime state**. The only state transitions in this increment are governance states on the ledger, executed append-only:

1. `B5-I3: LOCKED → IN_PROGRESS` — this P0 commit (predecessor gate satisfied: B5-I2 `OPERATOR_ACCEPTED`);
2. `B5-I3: IN_PROGRESS → READY_FOR_OPERATOR_REVIEW_B5_I3` — reported at mission exit (never `OPERATOR_ACCEPTED`; only the operator may transition further);
3. every registry entry `mapping_status` starts `NOT_YET_PROVEN` and becomes `MAPPED` only when its binding is proven by an executed B5-I3 node (a mapping claim only — **no charter gate status is transitioned by this stage**).

Unknown states, unknown ids, unknown binding types fail closed (test refusal, not acceptance).

## 6. Failure/refusal semantics

| Condition | Required behavior (fail-closed, testable) |
|---|---|
| Registry file absent, unparseable, or wrong encoding | All structure tests fail; no test skips |
| Missing/extra top-level or entry key | Structure/closure validator refuses with a named problem code |
| Missing/duplicate/out-of-set requirement id | Closure validator refuses (set equality, both directions) |
| Entry binding to a test node that does not collect | Binding validator refuses (collection-equality proof) |
| `deferred` entry without an authorized owner, planned node id, or reason | Deferred validator refuses |
| Unknown `binding.type`, `execution_surface`, or `mapping_status` | Vocabulary validator refuses (closed enums) |
| Oversized field (> 4096 chars per text field) | Size-bound validator refuses before any further processing |
| Absolute path, URL, secret-shaped string, timestamp in registry | Forbidden-content validator refuses |
| Any B5-I3 test failing, erroring, skipping, or duplicating | CI selection step exits nonzero; run fails |
| New `tests/test_b5_i3_*.py` file not selected by the workflow step | Orphan-detection assertion in the step fails the run |
| Emitted artifact ≠ committed registry bytes (where byte-compared) | Mismatch fails (see §3.15) |

No failure returns false success: every refusal above raises/asserts with an explicit problem code, never a silent pass.

## 7. Determinism requirements

- Registry bytes are canonical (sorted keys, pinned indentation, trailing newline); identical logical content ⇒ identical bytes; a determinism test re-serializes and byte-compares.
- Entry ordering is the sorted `id` order (observable ordering is deterministic).
- Collection-based proofs parse `pytest --collect-only -q` output and compare as **sets** (order-independent), so collection-order variance cannot flip a result.
- No LLM participates in any load-bearing check; validators are plain Python in the test module.

## 8. Local-only and loopback boundary

This stage adds no listener, no socket, no host/port, no provider SDK, no telemetry call and no network read. The registry declares no endpoint. Local-only topology (charter §6; A-003) is untouched; loopback law remains owned by the existing `http_api` bind (B4-R3R2) and the B5-I2 pack's `law.loopback_only`.

## 9. Persistence and canonical-state boundary

The registry, failure matrix and construction plan are documentation artifacts under `docs/`; they persist nothing at runtime, open no database, and write no file during test execution except pytest's own cache/junit outputs (which are untracked or evidence-dir-local). Canonical state remains exclusively in the control-plane stores. Tests must leave the tracked worktree byte-clean (verified by an in-suite cleanliness assertion and by the CI step's `git diff` check).

## 10. Recovery/retry behavior

Not applicable to runtime (none exists). Governance-level retry law: CI reruns are ordinary new runs bound to their own head; no run may be reinterpreted as another head's evidence. The construction plan (R1) must state B5-I4+ recovery expectations by *referencing* existing engine-owned recovery (`recovery.py`, lease expiry, re-queue) — never by re-specifying it (G8: recovery remains engine-owned).

## 11. Security/privacy boundary

- No secrets, tokens, keys or credential-shaped strings in any output (secret-pattern scan at evidence time).
- No absolute machine paths in committed artifacts (root-relative POSIX paths only).
- Field-size bounds enforced before content validation (§3.6/§3.13).
- Outputs contain no host names, user names, timestamps or durations (determinism + privacy).
- GitHub Actions remains validation-only; no workflow token permission is widened; `permissions` untouched.

## 12. Compatibility with frozen B5-I2 contracts

- The registry may *reference* B5-I2 surfaces (e.g. `contract_surface` entries) only with ids that exist in `console-contract.json` today; a validator asserts every such reference resolves (12-surface closed vocabulary: 9 reads + 3 invokes).
- Registry node bindings into `test_console_contracts.py` must be members of the 24 actually-collected nodes, and into `test_b5_i2_mutation_harness.py` members of the 16 collected nodes (collection-equality proof, not string presence).
- No B5-I2 file is modified; SHA-256 of `console-contract.json` at exit equals the frozen `45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa`.
- The existing B5-I2 CI steps (floor 24, integrity floor 16, harness battery) must pass unchanged after the R4 insertion.

## 13. Test architecture

Single new file `infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py`, whole-file selected in CI. Structure:

| Class | Concern |
|---|---|
| `TestRegistryStructure` | JSON parses; canonical bytes; closed top-level key set; types; determinism re-serialization; forbidden-content/size bounds |
| `TestRequirementClosure` | Requirement set is exactly `{G1..G17} ∪ {S-1..S-4} ∪ {F-1..F-7}` (28 ids, kinds cross-checked); unique ids; every entry has authority citation + non-empty requirement text; closed status/type vocabularies; entries sorted |
| `TestExecutableBindings` | Every `test` binding's file exists, node id prefixes match, and the node is in that file's `pytest --collect-only` set (set-equality; per-distinct-file subprocess collection); every `runner` binding names the existing authoritative runner path; `contract_surface` references resolve against the live pack (12 surfaces) |
| `TestDeferredOwners` | Every `deferred` entry carries an owner from the closed set `{I-3, I-4, I-5, I-6, I-7, I-8, B5-I8}` (charter §12 assignments + plan §7 B5-I8), a planned node id matching the repo's node-id grammar rooted under `infrastructure/control-plane/tests/`, and a non-empty reason; no deferred owner exists for an id outside the deferred-eligible set |
| `TestFailureMatrixConsistency` | The C2.S4 document exists, declares exactly the 7 plan failure classes, and each `F-*` registry entry cross-references the document section (and vice versa: every document class has a registry entry) |
| `TestConstructionPlanTraceability` | The construction plan exists and cites **every** one of the 28 requirement ids (set containment both ways against the registry's id set) |
| `TestB5I2Compatibility` | Pack SHA-256 frozen; 12/12 surfaces resolve; the 24-node file still collects exactly 24; no B5-I2 file modified (hash assertions) |
| `TestNegativeControls` | In-memory mutation controls: each validator refuses its mutated input with the named problem code (drop gate, duplicate id, forge node, defer-without-owner, unknown enum, oversize, forbidden content, extra key); **non-vacuity node**: a deliberately weakened validator admits a mutated registry that the real validator refuses, proving the check — not silence — discriminates |
| `TestStageBoundaries` | Registry contains no hosting/telemetry/URL/model strings; no production module was added (the `src/oce_control` module list is asserted unchanged for B5-I3 additions); test file itself imports no network/LLM module |

Helper validators live in this same test module (production code is out of scope by §2), so positive tests (`problems == []` on the real registry) and negative controls (same validator on mutated input `problems != []`) exercise the identical code path — no mock bypasses the validator.

## 14. Negative controls (each must be able to turn red; demonstrated before EVIDENCE)

| # | Mutation (one weakened control) | Expected discriminating proof |
|---|---|---|
| N1 | Registry entry `G5` removed | Closure set-equality test fails |
| N2 | Duplicate id (`G1` twice) | Uniqueness/sorted test fails |
| N3 | `test` binding forged to nonexistent node | Collection-equality test fails |
| N4 | `deferred` entry stripped of owner | Deferred validator fails |
| N5 | Unknown `binding.type` value | Vocabulary test fails |
| N6 | Text field oversized (4097+ chars) | Size-bound test fails |
| N7 | Absolute path / URL injected into registry | Forbidden-content test fails |
| N8 | Extra top-level key added | Closed-key test fails |
| N9 | Non-vacuity: weakened validator (checks removed) run against N1–N8 inputs | Weakened validator passes while the real one refuses — demonstrates the proof discriminates rather than being silent |
| N10 | Registry absent (pre-R1 tree) | Whole structure/closure suite red — the committed-red-adjacent demonstration executed in the working tree before R1 and recorded in ledger §11 |

Controls N1–N9 are executed **in CI on every run** (in-memory mutations inside `TestNegativeControls`); N10 is the pre-R1 working-tree red run recorded at EVIDENCE.

## 15. Authoritative CI selection

Smallest possible change to the **existing** `b1-i1r-validation.yml` (one added step, mirroring the B5-I2 X1 pattern):

- whole-file selection of `infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py`;
- frozen node floor = the exact collected count at the R4 head (recorded in the step and in evidence);
- fail-closed registry proof: pytest-reported collected == parsed node ids == JUnit tests; zero duplicate full node IDs; zero failures/errors/skips; every junit classname inside the B5-I3 module; floor met;
- **orphan detection:** any `infrastructure/control-plane/tests/test_b5_i3_*.py` present in the tree but not executed by this step fails the run;
- JUnit + machine-readable registry proof JSON written into the existing evidence artifact (same run id, bound to `pr_head_sha` and the tested checkout head/tree);
- triggers, permissions, shared runner, both B5-I2 steps, upload condition, cleanup and gate check untouched; workflow YAML parse-verified;
- no manually dispatched runs: evidence comes from natural `pull_request` triggers only.

## 16. Evidence artifact format

The existing evidence artifact (`b1-i1r-evidence-<run id>`) gains: `b5-i3-collect.txt`, `b5-i3-pytest-output.txt`, `b5-i3-registry-junit.xml`, `b5-i3-registry-proof.json` (same schema family as the B5-I2 proof: verdict, floor, collected/executed/duplicates, junit totals, `pr_head_sha`, `tested_checkout_head`, `tested_checkout_tree`). Ledger §11 (EVIDENCE commit) records: ladder SHAs, base/implementation/evidence heads, changed-file inventory by category, local parsed totals, base-vs-head comparison classification, N1–N10 results, exact-head run/check/artifact ids (appended append-only after the runs are proven), mandatory node count, duplicate count, manifest verification, cleanup result, limitations, prohibited-authority accounting, `B5_I4_THROUGH_I9 = LOCKED`, and `PR_NOT_MERGE_AUTHORIZED`.

## 17. Cleanup behavior

- Tests write only to pytest cache (untracked/ignored) and the CI evidence dir (outside the repo).
- CI step ends with `git diff --exit-code` plus a tracked-cleanliness check (pattern: B5-I2 repro step).
- Local validation runs end with a tracked-tree-clean assertion; the two transient P0-phase expectations (none beyond git's own state) leave no scratch file named as authoritative tooling.

## 18. Commit ladder

| Rung | Subject | Contents |
|---|---|---|
| P0 | `B5-I3-P0: freeze C2 failures/acceptance and construction plan (charter increment I-2)` | This contract + acceptance matrix (§2 below) + ledger §1 row `LOCKED → IN_PROGRESS` — documentation only; pushed before any implementation |
| R1 | `B5-I3-R1: add requirement-test registry, failure matrix and construction plan` | The three R1 artifacts |
| R2 | `B5-I3-R2: add registry closure, binding and compatibility proofs` | Test file (structure/closure/binding/deferred/compat/boundary classes) |
| R3 | `B5-I3-R3: add adversarial registry negative controls` | `TestNegativeControls` + non-vacuity node (or full file if co-evolved; concern separation preserved in the message) |
| R4 | `B5-I3-R4: execute registry proofs in authoritative validation` | The single workflow selection step |
| EVIDENCE | `B5-I3-EVIDENCE: record B5-I3 execution evidence in Book 5 ledger` | Ledger §11 append + acceptance-matrix status updates |
| Xn | `B5-I3-Xn: …` | Only if CI exposes defects; each repair is its own commit; chronology never hidden by amendment |

No amend, squash, rebase, reset, force-push or branch deletion at any point. Pushes are ordinary fast-forward. Red chronology: the structure/closure tests are authored and executed against the pre-R1 (registry-absent) tree **before** R1 lands — red captured in the working tree; git history contains no committed failing-test rung, and ledger §11 states this explicitly with the red transcript summary (the same disclosure discipline as ledger §9.6).

## 19. Final exit gate and stage boundary

Mission §16 defines the exit gate; the stage succeeds only as `READY_FOR_OPERATOR_REVIEW_B5_I3` with the draft PR open and unmerged. This contract freezes scope only: it grants no authority beyond the slice above, is not a ratification, and does not authorize implementation of any later increment.

```
B5_I4_THROUGH_B5_I9 = LOCKED
IMPLEMENTATION_MERGE_AUTHORIZED = FALSE
CAPITAL_AUTHORITY = NONE
EXECUTION_AUTHORITY = NONE
EXTERNAL_HOSTING_AUTHORITY = NONE
RECURRING_COST = $0
```

---

## Acceptance matrix (B5-I3 requirements → proofs; all statuses initially `NOT YET PROVEN`)

Artifact keys: **C** = this contract; **R** = `OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json`; **FM** = `OCE_B5_I3_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md`; **CP** = `OCE_B5_I3_CONSTRUCTION_PLAN_v1.0.md`; **T** = `infrastructure/control-plane/tests/test_b5_i3_requirement_registry.py`; **L** = Book 5 ledger; **W** = `b1-i1r-validation.yml`.

| # | Requirement | Authority source | Implementation surface | Executable proof | Expected refusal proof | CI node / artifact | Evidence location | Status |
|---|---|---|---|---|---|---|---|---|
| A1 | Scope frozen from plan §7 + charter §12 I-2 as one increment | Plan §7; charter §12 I-2 | C §1 | Authority-provision table literal-match audit (manual + doc review) | Conflicting authority would trigger `BLOCKED_B5_I3_AUTHORITY_CONFLICT` (none exists) | — (documentation) | C §1 | PROVEN — contract §1 authority table; no conflict emitted (ledger §11.1) |
| A2 | Zero production code added | Charter §12 I-2 non-goals; C §2 | None (`src/**` untouched) | `TestStageBoundaries::test_no_production_module_added` | Diff-path assertion refuses `src/` additions | T node + `git diff` in evidence | L §11; PR body | PROVEN — nodes `TestStageBoundaries::test_no_production_module_added` + `test_production_tree_unchanged_since_base`, run `37869921075` |
| A3 | Registry exists, machine-readable, canonical bytes | Charter §12 I-2 evidence output | R | `TestRegistryStructure` (parse, closed keys, re-serialization byte-equality) | Unparseable/extra-key/oversize → named refusal | T nodes | R; L §11 | PROVEN — `TestRegistryStructure` 9 nodes, run `37869921075` (proof `b5-i3-registry-proof.json` PASS) |
| A4 | Complete requirement set: 17 gates + 4 scenarios + 7 failure classes, unique ids | Charter §11; packet §2; plan §4 C2.S4 | R | `TestRequirementClosure` (two-directional set equality + uniqueness + kind cross-check) | Missing/extra/duplicate id → refusal | T nodes | R; L §11 | PROVEN — `TestRequirementClosure` 5 nodes, run `37869921075` |
| A5 | Every entry has an executable test binding or an explicitly deferred owner | Charter §12 I-2 gate | R | `TestExecutableBindings` + `TestDeferredOwners` | Forged node / ownerless deferral → refusal (N3, N4) | T nodes | L §11 §N1–N10 | PROVEN — `TestExecutableBindings` 7 + `TestDeferredOwners` 3, run `37869921075` |
| A6 | Every `test` binding is a real collectible node (no fabricated proof) | Charter §12 I-2 *"concrete runnable test"* | R + T | Collection set-equality per referenced file | Node absent from collection → refusal | T nodes | L §11 | PROVEN — `test_every_bound_node_collects` collection equality, run `37869921075` |
| A7 | Failure matrix declares exactly the 7 plan classes and cross-binds to registry `F-*` entries; no false success, no canonical loss | Plan §4 C2.S4 gate | FM + R | `TestFailureMatrixConsistency` | Class missing/extra or cross-ref break → refusal | T nodes | FM; L §11 | PROVEN — `TestFailureMatrixConsistency` 3 nodes, run `37869921075` |
| A8 | Construction plan traceable to every acceptance requirement | Plan §5 C3.S1 gate | CP | `TestConstructionPlanTraceability` (id containment both directions) | Any requirement id uncited → refusal | T nodes | CP; L §11 | PROVEN — `TestConstructionPlanTraceability` 3 nodes, run `37869921075` |
| A9 | B5-I2 compatibility: pack/schemas/tests byte-identical; references resolve to the 12 surfaces / 24 nodes / 16 nodes | B5-I2 contract §3/§12; charter §13 change control | R (references only) | `TestB5I2Compatibility` (SHA-256 + collection counts + surface resolution) | Reference to unknown surface/node → refusal | T nodes; full B5-I2 steps stay green | L §11 | PROVEN — `TestB5I2Compatibility` 5 nodes + B5-I2 steps 24/0/0/0 and 16/0/0/0, run `37869921075` |
| A10 | Determinism: canonical serialization, stable ordering, no timestamps/hosts/paths | Charter §7 (deterministic kernel); C §7 | R | `TestRegistryStructure` determinism nodes | Byte drift / forbidden content → refusal (N7) | T nodes | L §11 | PROVEN — `TestRegistryStructure` canonical/determinism nodes, run `37869921075` |
| A11 | Local-only: no listener, endpoint, provider, telemetry introduced | Charter §6; A-003; C §8 | All new files | `TestStageBoundaries` forbidden-surface assertions (URL/hosting/model strings) | Forbidden string present → refusal | T nodes | L §11 accounting | PROVEN — `TestStageBoundaries` forbidden-content + import-closure nodes, run `37869921075` |
| A12 | No secrets/credentials in outputs; bounded fields | Charter §10; C §11 | R, FM, CP | Secret-pattern scan + `TestRegistryStructure` size bounds | Secret-shaped or oversize content → refusal (N6) | T nodes + evidence scan | L §11 | PROVEN — size/content nodes + local secret scan clean; CI static 35/35, artifact `b1-i1r-evidence-88e278820556` |
| A13 | Authoritative CI executes every mandatory B5-I3 node with floor, zero dups/failures/errors/skips, orphan detection | Mission §11; B5-I2 X1 precedent | W (one step) | Step's registry-proof JSON (`executed == collected == junit`, floor, orphan glob) | Any violation → step exits nonzero | Run + `b5-i3-registry-proof.json` + junit | L §11 (exact-head ids) | PROVEN — `b5-i3-registry-proof.json` PASS: floor 51, 51==51==51, 0 dups/failures/errors/skips, 0 orphans, run `37869921075` |
| A14 | Negative controls N1–N9 discriminate in CI; non-vacuity demonstrated | Mission §9; charter G15 analog | T | `TestNegativeControls` (real validator refuses each mutation; weakened validator admits them) | Mutation admitted → node red | T nodes | L §11 (N1–N10 table) | PROVEN — `TestNegativeControls` 10 nodes (N1–N9 discriminate; weakened admits), run `37869921075` |
| A15 | Red chronology honest: pre-R1 red captured, history contains no failing-test rung (stated) | Mission §6; ledger §9.6 precedent | Working tree + L | Pre-R1 pytest transcript summarized in §11 | False test-first claim would contradict §11 wording | — | L §11 | PROVEN — pre-R1 red 21F/2P recorded in ledger §11.2; no failing-test rung in history |
| A16 | Base-vs-head regression: no B5-I3-only failure, error or mandatory skip | Mission §12 | Full suites | Same command on `c60e0745…` and final head; failure-site set comparison | Head-only failure → classification `genuine B5-I3 regression` blocks exit | Evidence comparison in L §11 | L §11 | PROVEN — base `c60e0745` vs head `39fd324e3`: identical 32-failure sets, +51 passed, skips 103=103 (ledger §11.3) |
| A17 | Ledger append-only; prior sections byte-stable; CRLF preserved | Mission §13; plan lineage | L | `git diff` shows only §1 row edit (P0) + §11 append (EVIDENCE); prefix byte-compare | Any prior-line deletion → diff assertion red | Evidence `git diff` | L §11 | PROVEN — ledger diff vs base = §1 status row (P0 + EVIDENCE transitions, one line) + §11 append only; prior sections byte-stable, CRLF pure (verified at EVIDENCE) |
| A18 | Draft PR open, unmerged, title ends `(NOT MERGE AUTHORIZED)`, body append-only with exact SHAs/runs | Mission §14 | PR metadata | PR state assertions at exit | Premature merge-authorized language → exit gate fails | — | PR body | PROVEN — PR #12 draft/OPEN/unmerged; title ends `(NOT MERGE AUTHORIZED)`; body append-only (ledger §11.8, PR #12) |
| A19 | B5-I4–I9 locked; prohibited authorities zero (cloud/broker/capital/execution/LLM/hosting) | Charter §16; plan §7; A-003 | L + all outputs | Ledger lock rows + accounting attestation + boundary tests | Any lock/authority drift → exit gate fails | Evidence | L §1/§11 | PROVEN — ledger §1 LOCKED rows + §11.1 accounting + `TestStageBoundaries`, run `37869921075` |
| A20 | Evidence bound to exact final head; wording matches execution; artifact parsed, not badge-inferred | Mission §13/§15 | Evidence artifact | Download + parse junit/proof JSON; `pr_head_sha == head`; manifest hash/size verification | Head mismatch → L §11 records defect, exit blocked | Run/check/artifact ids | L §11 | NOT YET PROVEN |

**Matrix law:** a row may only transition from `NOT YET PROVEN` to `PROVEN` in the EVIDENCE commit, citing the exact executable proof (node id or run/artifact id) that produced it; rows without executed proof remain `NOT YET PROVEN` and block the exit gate rather than being silently dropped.

---

**FROZEN under `AUTHORIZED_STAGE=B5-I3`.** This contract freezes scope only; it is not a ratification of B5-I3, grants no authority beyond the slice above, and B5-I4–I9 remain `LOCKED`.
