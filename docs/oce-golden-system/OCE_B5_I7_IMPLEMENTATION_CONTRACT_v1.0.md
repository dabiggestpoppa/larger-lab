# OCE Golden System
## B5-I7 — Implementation Contract (P0) — v1.0

**Document ID:** OCE-B5-I7-CONTRACT-001
**Version:** 1.0
**Status:** **P0 FROZEN — PLANNING ONLY. IMPLEMENTATION NOT AUTHORIZED.**
**Stage:** `AUTHORIZED_STAGE=B5-I7-P0`
**Base SHA (observed):** `c6a6479da427ddfe6af06622fc80b2221a4cdc5c` (merged `main`, PR #18 merge commit)
**Branch:** `oce-book-5-i7`
**Governing plan gate:** *Governed change demonstrated* (Block 5 plan §7, row `B5-I7`)
**Charter increment:** `I-8` (charter §12, the only increment row anchored to `B5-I7`)
**`MERGE_AUTHORIZED` = `false`**
**Recurring cost** `$0`; **`capital.authority = none`**

---

## 0. How to read this contract

1. Every normative statement carries a stable identifier `B5I7-Rnn` (requirement),
   `B5I7-ELnn` (evidence law) or `B5I7-DFnn` (deferred obligation). Identifiers are
   never reused, never renumbered, and never deleted — supersession is append-only.
2. Every identifier appears **exactly once** in
   `OCE_B5_I7_REQUIREMENT_TEST_REGISTRY_v1.0.json` and is bound **exactly once** to one
   execution surface: `test`, `static`, `runner`, `attestation`, or `deferred`.
3. Allowed registry states: `PLANNED`, `MAPPED`, `DEFERRED_WITH_OWNER`, `BLOCKED`.
   No implementation gate may read `PASS` during P0.
4. `MAPPED` = the binding target already exists in this tree today. `PLANNED` = the
   binding target (test node, workflow step, evidence artifact) is named here and is
   created by a later authorized rung of this stage.
5. Requirements are statements of fact about the *future* implementation; this P0
   commit contains **no** production code, no test file, no workflow edit.

## 1. Stage identity

**B5I7-R01** — This stage IS the Block 5 plan §7 increment `B5-I7`, quoted verbatim:
*"C4 change cycle plus C5 measurements/learning"*, gate *"Governed change demonstrated"*.
Its charter increment is exactly `I-8` — charter §12 row `I-8 (optional) | B5-I7 |
governed change demonstration + observability panel (packet section 11 pattern)`.
No other charter increment is anchored to `B5-I7`. B5-I7 does **not** include charter
increment `I-7` (see §4.1) and does not include B5-I8 or B5-I9 work (see §20).

**Authority:** `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` §7;
`OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` §12 row `I-8`, §11.

## 2. Governing authorities (read from merged `main` at the base SHA)

| # | Authority | Sections used |
|---|---|---|
| A1 | `OCE_GOLDEN_SYSTEM_ARCHITECTURE_CONSTITUTION_v1.1.md` | authority law, local-first, evidence law |
| A2 | `OCE_ARCHITECTURE_AMENDMENT_A003_LOCAL_FIRST_CLOUD_DEFERRAL_v1.0.md` | cloud/telemetry deferral |
| A3 | `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` | §5 C4.S1–S5, §6 Chapter 5 (C5.S1–S5), §7 increments, §9 non-goals |
| A4 | `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` | §5 authority law, §6 topology, §7 deterministic kernel, §8 bounded scope, §9 lifecycle, §10 security, §11 gates, §12 increment ceiling, §13 change control, §15 accounting |
| A5 | `OCE_B5_I1_CAND-004_EVIDENCE_PACKET_v1.0.md` | §10 recovery scenario, §11 governed change-cycle scenario, §12 reuse vs platform-extraction risk |
| A6 | `OCE_B5_I3_IMPLEMENTATION_CONTRACT_v1.0.md` + `OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json` | frozen 28-entry registry, deferred owners, planned-node law |
| A7 | `OCE_B5_I3_CONSTRUCTION_PLAN_v1.0.md` | §6 staged commit discipline, §7 traceability, §8 planned-node inventory, §9 limits |
| A8 | `OCE_B5_I6_GAP_AND_SCOPE_CONTRACT_v1.0.md` + `OCE_B5_I6_ACCEPTANCE_MATRIX_v1.0.md` | I-7 disposition, I-6 completion, B5-I7 lock wording |
| A9 | `OCE_B5_I6_DEPLOYMENT_OBSERVABILITY_RUNBOOK_v1.0.md` | operator path, drill procedure, command→node binding |
| A10 | `OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` | §1 increment status, §16.4 locks, §17 build evidence, §17.11–§17.13 X1 closure and corrected audit 8.75/10 |
| A11 | `.github/workflows/b1-i1r-validation.yml` | triggers, shared authoritative runner step, per-stage whole-file selection, orphan detection, gate check, artifact upload |
| A12 | `infrastructure/control-plane/contracts/console-contract.json` (frozen, blob hash `45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa`) and `contracts/evidence-manifest.schema.json` | declared read surfaces; evidence manifest schema |

## 3. Scope table (source-backed)

| Question | Governing source | Exact answer |
|---|---|---|
| Official B5-I7 stage name | A3 §7 | *C4 change cycle plus C5 measurements/learning* |
| Corresponding charter increment | A4 §12 | `I-8` (optional) — governed change + observability demonstration |
| Operator outcome | A3 §5 C4.S5, A4 §12 I-8, A5 §11 | one meaningful requirement change applied through the governed change cycle, proven by the control-plane suite passing **unchanged**, with a governed change record and learning entries |
| Required inputs | A5 §11, A3 §5 C4.S5, A9 | existing local loopback stack; frozen contract pack; B5-I6 drill playbook and its recorded report; prior stage evidence; the packet §11 change specification ("add a queue-depth observability panel") |
| Required outputs | A3 §5 C4.S5 (`change dossier`), A4 §12 I-8 evidence column, A3 §6 C5.S1/C5.S2/C5.S4 | change dossier (intent → plan → tests → release/rollback); governed change record; learning ledger entries; cost/time ledger with estimate-vs-observation labels; reuse inventory verified against import/runtime paths |
| Production surfaces allowed | A4 §12 I-8 stop column, A5 §11 | read-only console/client change only. Packet §11 verbatim: *"No control-plane modification is required (read-only client change), which is itself verified by the control-plane test suite passing unchanged."* |
| Test/evidence surfaces allowed | A3 C3.S3, A4 §11 G14, A7 §6 | new test files `infrastructure/control-plane/tests/test_b5_i7_*.py` (never `test_b5_i7_web_view.py`, see §4.1); new evidence artifacts under `docs/oce-golden-system/`; one additive workflow selection step at rung R4 (A11 pattern) |
| Explicit non-goals | A4 §12 I-8 non-goals, A3 §9 | no scope creep; no platform extraction; no new server endpoint; no contract-pack change; no new job type; no UI/web view; no LLM, hosting, cloud, provider, telemetry, broker, capital or execution surface |
| Deferred owners | A3 §7, A6 registry, A8 §5 | usability/accessibility protocol `G16` → **B5-I8**; factory corrections / B6 extraction contract (C5.S5) → **B5-I9**; charter increment `I-7` web view (`G1`, `G2`, node `test_b5_i7_web_view.py`) → **Operator, operator-directable, not scheduled** |
| Security boundary | A4 §5, §6, §10 | loopback-only topology; read-only panel; no secrets in output; refusal before I/O on undeclared or non-loopback targets; existing authorization enforced unchanged |
| Canonical-state owner | A4 §5 (authority law), A5 §11 | the control-plane engine alone. The console never owns, writes, or reconciles canonical state |
| Recovery owner | A4 §9, A6 `G8` | engine-owned (`recover_abandoned_leases()`); the console reports recovery, never enacts it |
| UI authority limitations | A4 §5 rule 9, §8.4 | presentation only; verbatim denial rendering; fail closed rather than render stale green |
| Local-only constraint | A4 §6, A2 | `127.0.0.1` only; no external network, no cloud, no provider |
| Cost ceiling | A4 §13/§15, A3 §9 | recurring cost `$0`; `capital.authority = none`; within the charter §12 increment ceiling |
| Exit gate | A3 §7, A4 §11 G14, A4 §12 I-8 | *Governed change demonstrated*: Gate `G14` green **plus** the regression-drill identical-report check, with the control-plane suite passing unchanged |

## 4. Contradiction resolutions (explicit, never silent)

**4.1 — Charter increment `I-7` (loopback web view) is NOT part of B5-I7.**
Charter §12 anchors row `I-7 (optional)` to stage `B5-I6`; construction plan §5 labels it
*"OPTIONAL loopback web view (plan anchor `B5-I6`)"*. B5-I6 completed without operator
direction and recorded (A8 §5): *"No `test_b5_i7_web_view.py` exists or is created;
registry entries G1/G2 stay with owner I-7, operator-directable at a later stage."*
Neither authority anchors `I-7` to `B5-I7`. Consequence: the frozen planned-node string
`infrastructure/control-plane/tests/test_b5_i7_web_view.py::…` (A6 registry, A7 §8) keeps
its `test_b5_i7_` file prefix although it is **not** a B5-I7 stage deliverable. This is an
append-only prefix reservation: B5-I7 must never create that file, and B5-I7's own test
files use the distinct names listed in the construction plan §5. The `I-7` obligation
travels as `B5I7-DF01`.

**4.2 — "C5 measurements/learning" is delimited by plan §7's own sibling rows.**
Plan §7 assigns `B5-I8` = *independent E2E, adversarial, **usability** and evidence audit*
and `B5-I9` = *factory gate and **B6 reusable-extraction contract***. Therefore C5.S3
(human clarity / usability, A4 gate `G16`) and C5.S5 (factory corrections, "Operator
ratifies reusable extraction scope") are excluded from B5-I7 even though both sit in
Chapter 5. B5-I7 carries C5.S1 (time/effort), C5.S2 (reuse achieved) and C5.S4 (learning
captured) — the "measurements/learning" clause of its own plan row. Carried as
`B5I7-DF02` and `B5I7-DF03`.

**4.3 — "read-only client change" vs the charter stop condition.**
Charter §12 I-8 requires *"one governed read-only change … verified by the control-plane
suite passing unchanged"* and stops the stage if *"change requires control-plane
modification beyond governed interfaces"*. Packet §11 states no control-plane
modification is required at all. Read together: the intended instantiation is a
client-side read-only change over **already declared** surfaces; any need to modify
`infrastructure/control-plane/src/**`, `contracts/**` (byte-frozen by A6), or any existing
test file triggers the stop condition `B5I7-STOP-3` — it is not a judgement call.

**4.4 — The queue-depth panel must not add a status section.**
`STATUS_SECTIONS` is frozen to `("health","readiness","system","workers","schedules")`
(`oce_console/kernel.py:49`) and section→surface mapping is fail-closed against the
frozen pack (`section_route`, matrix X6). Because the pack is byte-frozen (A12), no sixth
section can be declared. The panel is therefore a **separate read-only document** derived
from already declared surfaces (`health.read` → `GET /api/health` already carries
`pending_jobs`, `active_jobs`, `failed_jobs`, `quarantined_jobs`, `workers`; plus
`workers.list`, `jobs.schedules`), never a new section of `oce-console-status`.

**4.5 — Evidence law of the previous stage.** B5-I6's corrected disposition
`B5_I6_POST_MERGE_PROOF_CLOSURE_X1_RESTORED` (ledger §17.13, corrected audit 8.75/10) is
accepted input. B5-I7 does not restate, re-prove, or amend it, and opens no B5-I6 PR.

## 5. Allowed production scope

**B5I7-R02** — This stage applies **exactly one** governed change: *add a queue-depth
observability panel*, the packet §11 specification, as a read-only console/client change.
No second change may enter this stage.

**B5I7-R03** — At every rung of this stage the following paths are byte-unmodified
relative to the base SHA: `infrastructure/control-plane/src/**`,
`infrastructure/control-plane/contracts/**`, and **every existing** file under
`infrastructure/control-plane/tests/**`.

**B5I7-R04** — No scope creep and no platform extraction: no new server endpoint, no new
job type, no schema change, no SDK/library extraction, nothing belonging to B6.

**B5I7-R09** — Prior evidence is not corrupted: every `docs/oce-golden-system/OCE_B5_I0*`
through `OCE_B5_I6*` artifact and every prior ledger section (§1–§17) remains
byte-identical; ledger changes are append-only plus the single §1 status-row update.

Allowed surfaces, enumerated exhaustively:

| Surface | Path | Condition |
|---|---|---|
| Console client module(s) | `infrastructure/console/src/oce_console/**` | read-only; additive; existing exported behavior preserved |
| Packaging declaration | `infrastructure/console/packaging/make_release_manifest.py` | only to register a new console module in `DECLARED_INSTALL_SET` (so clean-install and manifest hash coverage stay complete) |
| New tests | `infrastructure/control-plane/tests/test_b5_i7_governed_change.py`, `.../test_b5_i7_evidence_laws.py` | never `test_b5_i7_web_view.py` |
| P0 documents | `docs/oce-golden-system/OCE_B5_I7_*` | this rung only |
| Evidence artifacts | `docs/oce-golden-system/OCE_B5_I7_GOVERNED_CHANGE_RECORD_v1.0.md`, `…_REUSE_INVENTORY_v1.0.md`, `…_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` | R/EVIDENCE rungs only |
| Workflow | `.github/workflows/b1-i1r-validation.yml` | one additive selection step, rung R4 only; triggers, permissions, shared runner, existing steps and gate check untouched |

## 6. Prohibited scope (enumerate, never infer)

No control-plane source, contract pack, schema or existing test change; no frontend /
`oce/frontend`; no Book 4, no Sensor Fabric; no B5-I0–I6 frozen artifact edit; no LLM,
model, provider, cloud, hosting, telemetry, or external network call; no broker, capital
or execution surface; no new write surface of any kind; no non-loopback bind; no merge,
no ratification, no B5-I8/I9 work.

## 7. Public interfaces (frozen before implementation)

**B5I7-R15** — The panel requests **only** surface ids declared in the frozen contract
pack. An undeclared, embedded or malformed surface is refused **before** any I/O.

**B5I7-R16** — The panel issues `GET` requests only: no `POST`/`PUT`/`PATCH`/`DELETE`,
no `invokes` entry, no canonical-state write of any kind.

Interface sketch (binding at R1): a read-only entry point
`oce_console.<panel module>.build_panel_document(read) -> dict` that accepts the same
injected read callable the status kernel uses, plus
`render_panel(document) -> str` emitting canonical JSON (sorted keys, ASCII, trailing
newline), and one additive CLI surface `python -m oce_console panel …`.

## 8. Canonical state ownership

The control-plane engine owns all canonical state (jobs, leases, evidence, audit). The
panel is a **projection of reads**; it never writes, never reconciles, never retries
silently, and never becomes a second state owner (`B5I7-R16`, `B5I7-R18`).

## 9. Deterministic / non-LLM law

No model, prompt, or inference in the path. Identical inputs produce byte-identical
output (`B5I7-R19`); randomness, wall-clock rendering and locale must not affect output;
`G10` (no LLM required) remains satisfied by import closure.

## 10. Local-only topology

Base URL defaults to and is validated as loopback (`127.0.0.1`/`localhost`/`[::1]`);
any other target is refused fail-closed (`B5I7-R20`). Zero outbound network, zero
telemetry, zero cloud dependency (`A2`).

## 11. Input bounds

**B5I7-R22** — bounded inputs: CLI arguments bounded (≤ 512 bytes each, ≤ 32 arguments),
rendered field values bounded (≤ 4096 bytes per string, ≤ 64 KiB per document), malformed
JSON or unexpected field types refused fail-closed with the existing denial vocabulary.
Oversize and malformed inputs are hostile test cases, not edge cases.

## 12. Output schema

The panel document is canonical JSON with at least: `kind` (`oce-console-panel`),
`state` (`OK` | `STACK_UNREACHABLE` | `DENIED` | `UNVERIFIABLE`), `queue` (declared
surface ids used, `pending`, `active`, `failed`, `quarantined`, `workers`), `provenance`
(exact head SHA **observed after** the commit exists, contract pack blob hash, run id
**recorded only after** the run exists). Unknown values render as JSON `null` with an
explicit `unknown_reason` — never as `0`, never as green (`B5I7-R18`).

## 13. Transition/state laws

Only the console's existing four document states may appear. No new state machine, no
side-effecting transition: rendering a panel never moves a job, lease, or session
(`B5I7-R16`). Unreachable → `STACK_UNREACHABLE`; denied → `DENIED` verbatim;
partial/unverifiable evidence → `UNVERIFIABLE` (`B5I7-R17`, `B5I7-R18`).

## 14. Denial and refusal behavior

Denials reuse the frozen refusal vocabulary (`unsupported_surface`,
`payload_too_large`, `malformed_request`, `non_loopback_refused`, …), are rendered
verbatim in the panel, and never trigger an automatic retry (`B5I7-R18`). Every refusal
has an observable expected result: a refusal class + a nonzero CLI exit code + no output
mutation toward green.

## 15. Recovery behavior

Recovery remains engine-owned. The panel reports recovery-related facts read from
declared surfaces only; it performs no lease, requeue, replay, or reconciliation action
(charter §9, `G8`). Interrupted panel runs leave no partial artifact presented as
complete (`B5I7-EL11`).

## 16. Observability requirements

The change record must expose, for a reviewer without code access: what changed, which
declared surfaces it reads, which gates ran, which artifacts carry which SHA/tree, and
which numbers are `EXPECTED` vs `OBSERVED` (`B5I7-EL04`, `B5I7-EL05`).

## 17. Security and privacy

No secrets, tokens, or authorization material in panel output or artifacts
(`B5I7-R21`); no credentials in files, logs, or the browser; loopback-only; the
existing authorization path is used unchanged — no auth bypass, no widened origin.

## 18. Compatibility rules

**B5I7-R23** — the documented invocation `python -m oce_console status --base-url …
--grant … --actor …` and every documented exit code keep their exact current behavior;
the panel is strictly additive (`X3` regression node must stay green unchanged).

## 19. Failure taxonomy

Failure classes, hostile cases, detection, owner and stop behavior are frozen in
`OCE_B5_I7_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md` §2–§4. Classes: `MALFORMED_INPUT`,
`OVERSIZED_INPUT`, `UNKNOWN_FIELD`, `DUPLICATE_ID`, `STALE_IDENTITY`,
`UNAUTHORIZED_TRANSITION`, `FORGED_CLIENT_STATE`, `NON_LOOPBACK_ACCESS`,
`MISSING_DEPENDENCY`, `INTERRUPTED_OPERATION`, `REPLAY`, `PARTIAL_EVIDENCE`,
`RECOVERY_DISAGREEMENT`, `UNVERIFIABLE_OUTPUT`, `SCOPE_ESCALATION`, `EVIDENCE_FRAUD`.

## 20. Deferred obligations (named owners — never absorbed)

**B5I7-DF01** — charter increment `I-7` loopback web view (registry entries `G1`,
`G2`, planned node `test_b5_i7_web_view.py::…`): owner **Operator**, future stage
*operator-directable, not scheduled*; reason: optional surface requires explicit
operator direction, which has not been given (A8 §5, A4 §12 row I-7).

**B5I7-DF02** — accessibility/usability protocol and results (gate `G16`, C5.S3): owner
**B5-I8**, future stage `B5-I8`; reason: plan §7 assigns usability to the independent
audit increment (A3 §7, A6 registry `G16` deferred owner).

**B5I7-DF03** — factory corrections, reusable-extraction scope and the B6 contract
(C5.S5): owner **B5-I9**, future stage `B5-I9`; reason: plan §7 assigns the factory gate
and B6 extraction contract to operator-only completion (A3 §6 C5.S5, §7 row `B5-I9`).

## 21. Testability requirements

Two-sided proofs only: every behavioral claim names a positive proof, a refusal proof, a
weakened-implementation control that must be executed red, and a cleanup assertion
(`OCE_B5_I7_ACCEPTANCE_MATRIX_v1.0.md`). Runtime or structural behavior is exercised;
source-string tests are used only for documentary laws whose subject *is* text
(`B5I7-EL*`). Frozen floor and node inventory: construction plan §5.

## 22. Evidence schema

Evidence JSON validates against `infrastructure/control-plane/contracts/evidence-manifest.schema.json`
(`manifest_id`, `run_id`, `produced_at`, `artifacts[].{name,path,sha256,size_bytes,required}`,
`outer_digest`). Laws `B5I7-EL01`–`B5I7-EL15` govern how any number, SHA, run id, badge,
manifest row, mutation claim, cleanup claim, audit label, or ratification statement may
enter the record.

## 23. Cleanup law

Every rung that mutates working state (mutation battery, negative-control executions,
temporary evidence directories) records machine-readable residual state: file list with
hash and size before/after, process/port list, and `git status --porcelain` output,
proving restoration to the pristine tree (`B5I7-EL11`).

## 24. Stop conditions (any one halts the stage)

| ID | Condition | Action |
|---|---|---|
| `B5I7-STOP-1` | The change cannot be made without modifying `infrastructure/control-plane/src/**`, `contracts/**`, or an existing test file | stop and report; do not weaken the gate |
| `B5I7-STOP-2` | The control-plane suite passes only after modifying an existing test | stop; the suite must pass **unchanged** |
| `B5I7-STOP-3` | Any required surface is not already declared in the frozen pack | stop; no pack edit is permitted |
| `B5I7-STOP-4` | Any non-loopback-reachable path appears in the panel path | stop and withdraw the surface |
| `B5I7-STOP-5` | A gate would be reported passed while skipped, substituted, pending or inferred | stop; report the gate as not executed |
| `B5I7-STOP-6` | Scope pressure to extract platform/SDK surface, add endpoints, or touch B5-I8/I9 work | stop; record as scope escalation |
| `B5I7-STOP-7` | Any evidence value cannot be traced to a raw artifact parsed after the fact | stop; discard the claim |

## 25. Requirement index (44 identifiers, bound exactly once)

Every normative statement in this contract carries one of these identifiers; each appears
in the registry exactly once and is bound to exactly one execution surface.

| ID | Kind | Normative statement (verbatim from the registry) | Binding | Clause |
|---|---|---|---|---|
| `B5I7-DF01` | deferred | Charter increment I-7 (loopback web view) is NOT B5-I7 work; B5-I7 creates no web view and never creates test_b5_i7_web_view.py. | `deferred` | §20 Deferred obligations |
| `B5I7-DF02` | deferred | Accessibility/usability protocol and results (gate G16, C5.S3) are not B5-I7 work. | `deferred` | §20 Deferred obligations |
| `B5I7-DF03` | deferred | Factory corrections, reusable-extraction scope and the B6 contract (C5.S5) are not B5-I7 work. | `deferred` | §20 Deferred obligations |
| `B5I7-EL01` | evidence_law | No predicted commit SHA may be written as fact; a SHA enters the record only after the object exists. | `test` | §22 Evidence schema |
| `B5I7-EL02` | evidence_law | No run, check or artifact id may be recorded before that id exists. | `test` | §22 Evidence schema |
| `B5I7-EL03` | evidence_law | No manually authored JSON may be called execution evidence. | `test` | §22 Evidence schema |
| `B5I7-EL04` | evidence_law | Planned totals are labelled EXPECTED, never OBSERVED. | `test` | §22 Evidence schema |
| `B5I7-EL05` | evidence_law | Observed totals may enter the ledger only after parsing raw artifacts. | `test` | §22 Evidence schema |
| `B5I7-EL06` | evidence_law | A green badge is not evidence without SHA and tree binding. | `test` | §22 Evidence schema |
| `B5I7-EL07` | evidence_law | New-test-only execution cannot prove regression absence. | `test` | §22 Evidence schema |
| `B5I7-EL08` | evidence_law | Common regression populations must be nonzero and meet the frozen floor. | `test` | §22 Evidence schema |
| `B5I7-EL09` | evidence_law | Manifest claims require independently recomputed hash and size. | `test` | §22 Evidence schema |
| `B5I7-EL10` | evidence_law | Mutation claims require actual discriminating failures and pristine restoration. | `test` | §22 Evidence schema |
| `B5I7-EL11` | evidence_law | Cleanup claims require machine-readable residual-state proof. | `test` | §22 Evidence schema |
| `B5I7-EL12` | evidence_law | Historical process defects remain visible after technical repair. | `test` | §22 Evidence schema |
| `B5I7-EL13` | evidence_law | A same-agent audit must never be labeled organizationally independent. | `test` | §22 Evidence schema |
| `B5I7-EL14` | evidence_law | Ratification cannot occur before every mandatory gate executes. | `test` | §22 Evidence schema |
| `B5I7-EL15` | evidence_law | No 'all gates passed' language is allowed while any gate is skipped, substituted, pending or inferred. | `test` | §22 Evidence schema |
| `B5I7-R01` | identity | B5-I7 is exactly the plan §7 increment 'C4 change cycle plus C5 measurements/learning' and charter increment I-8; no other charter increment is anchor... | `attestation` | §1 Stage identity |
| `B5I7-R02` | change_cycle | Exactly one governed change is applied in this stage - 'add a queue-depth observability panel' - and a second change is a violation. | `test` | §5 Allowed production scope |
| `B5I7-R03` | boundary | infrastructure/control-plane/src/**, infrastructure/control-plane/contracts/** and every pre-existing file under infrastructure/control-plane/tests/**... | `static` | §5 Allowed production scope |
| `B5I7-R04` | boundary | No scope creep and no platform extraction: no new server endpoint, no new job type, no schema change, no SDK/library extraction, no B6 work. | `attestation` | §6 Prohibited scope |
| `B5I7-R05` | change_cycle | The change dossier records the intent (the requirement being changed) before implementation begins. | `attestation` | §5 Allowed production scope |
| `B5I7-R06` | change_cycle | The change dossier records the plan and the bounded list of affected surfaces. | `attestation` | §5 Allowed production scope |
| `B5I7-R07` | change_cycle | The change ships with both a positive proof and an executed negative (weakened-implementation) proof. | `test` | §21 Testability requirements |
| `B5I7-R08` | change_cycle | Release and rollback for the change are documented and executable: the release manifest is regenerated deterministically and rollback metadata stays c... | `attestation` | §5 Allowed production scope |
| `B5I7-R09` | boundary | Frozen B5-I0..B5-I6 documents and every prior ledger section stay byte-identical; ledger edits are append-only plus the single §1 status-row update. | `static` | §5 Allowed production scope |
| `B5I7-R10` | gate | The control-plane suite passes with a node population identical to the base: zero added, zero removed, zero skipped, zero failed. | `runner` | §3 Scope table (exit gate) |
| `B5I7-R11` | gate | The shared authoritative validation runner is green at the exact observed head SHA (no badge inference). | `runner` | §3 Scope table (exit gate) |
| `B5I7-R12` | gate | The regression drill on an unchanged stack produces a byte-identical report to the base-tree reference report. | `test` | §3 Scope table (exit gate) |
| `B5I7-R13` | change_cycle | The governed change record is bound to the observed head SHA, run id and pack blob hash, each recorded only after it exists. | `attestation` | §22 Evidence schema |
| `B5I7-R14` | learning | Learning ledger entries exist with observation, disposition and owner; no observation is silently discarded. | `attestation` | §16 Observability requirements |
| `B5I7-R15` | panel | The panel requests only surface ids declared in the frozen contract pack; an undeclared, embedded or malformed surface is refused before any I/O. | `test` | §7 Public interfaces |
| `B5I7-R16` | panel | The panel issues GET requests only and performs no canonical-state write, invoke, lease, requeue or reconciliation action. | `test` | §8 Canonical state ownership |
| `B5I7-R17` | panel | When the stack is unreachable the panel renders STACK_UNREACHABLE and never a healthy, stale or green value. | `test` | §13 Transition/state laws |
| `B5I7-R18` | panel | Unknown or unverifiable queue values render as null with an explicit unknown_reason (never 0, never green); denials render verbatim; no silent retry. | `test` | §14 Denial and refusal behavior |
| `B5I7-R19` | panel | Identical inputs produce byte-identical canonical panel JSON (sorted keys, ASCII, trailing newline). | `test` | §12 Output schema |
| `B5I7-R20` | panel | A non-loopback base URL is refused fail-closed before any connection attempt. | `test` | §10 Local-only topology |
| `B5I7-R21` | panel | Panel output and evidence artifacts contain no secret, token or authorization material. | `test` | §17 Security and privacy |
| `B5I7-R22` | panel | CLI and document inputs are bounded; oversized or malformed input is refused fail-closed with the frozen refusal vocabulary. | `test` | §11 Input bounds |
| `B5I7-R23` | panel | The documented 'python -m oce_console status ...' invocation and every documented exit code are unchanged; the panel is strictly additive. | `test` | §18 Compatibility rules |
| `B5I7-R24` | measurement | Every cost/time figure in the change record carries the label ESTIMATE or OBSERVED, and no unmeasured figure is labelled OBSERVED. | `attestation` | §16 Observability requirements |
| `B5I7-R25` | measurement | Recurring cost stays $0 and capital.authority stays none for this stage. | `attestation` | §3 Scope table (cost ceiling) |
| `B5I7-R26` | measurement | Each reuse claim in the reuse inventory is verified against a real import or executed runtime path; unverified claims are removed. | `attestation` | §3 Scope table (required outputs) |

Counts: `26` requirements (`R01`-`R26`), `15` evidence laws (`EL01`-`EL15`), `3` deferred obligations (`DF01`-`DF03`) = **44**.

Binding distribution (frozen at P0): `test` 27 · `static` 2 · `runner` 2 · `attestation` 10 ·
`deferred` 3 = 44. State distribution: `PLANNED` 35 · `MAPPED` 6 · `DEFERRED_WITH_OWNER` 3 ·
`BLOCKED` 0 = 44.

---
## 26. Known limitations carried into implementation

1. No test file, workflow step, or evidence artifact exists at P0 — every `PLANNED`
   binding is a promise, not a proof. Nothing here may be reported as passing.
2. `test_b5_i7_web_view.py` prefix collision (§4.1) is permanent while the frozen B5-I3
   registry text stands; resolved by reservation, not by editing frozen text.
3. The identical-report regression check (R12) needs a reference report captured from the
   base tree at R1; until then R12 is `PLANNED`, not green.
4. Cost/time figures (R24) are `ESTIMATE` until measured; the record must not pre-fill
   `OBSERVED` values (`B5I7-EL04`).
5. This audit and this contract are **same-agent** artifacts; they are not organizationally
   independent review (`B5I7-EL13`).

---

**P0 boundary.** This document freezes scope and proof obligations only. It grants no
authority beyond `AUTHORIZED_STAGE=B5-I7-P0`. Implementation rungs (R1–R4, EVIDENCE)
each require a fresh operator authorization. `MERGE_AUTHORIZED=false`;
**B5-I7 IMPLEMENTATION NOT AUTHORIZED by this artifact**; `B5-I8`–`B5-I9` remain `LOCKED`.
