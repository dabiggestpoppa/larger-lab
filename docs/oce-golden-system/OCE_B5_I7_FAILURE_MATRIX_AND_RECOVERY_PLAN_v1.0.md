# OCE Golden System
## B5-I7 — Failure Matrix and Recovery Plan (P0) — v1.0

**Document ID:** OCE-B5-I7-FAILURE-001
**Version:** 1.0
**Status:** **P0 FROZEN — PLANNING ONLY. IMPLEMENTATION NOT AUTHORIZED.**
**Stage:** `AUTHORIZED_STAGE=B5-I7-P0`
**Base SHA (observed):** `c6a6479da427ddfe6af06622fc80b2221a4cdc5c`
**Companions:** `OCE_B5_I7_IMPLEMENTATION_CONTRACT_v1.0.md` (§19 taxonomy, §24 stops),
`OCE_B5_I7_REQUIREMENT_TEST_REGISTRY_v1.0.json` (44 entries),
`OCE_B5_I7_ACCEPTANCE_MATRIX_v1.0.md` (44 rows, negative controls),
`OCE_B5_I7_CONSTRUCTION_PLAN_v1.0.md` (rungs, nodes, floors).
**`MERGE_AUTHORIZED = false`** · recurring cost `$0` · `capital.authority = none`

---

## 1. Purpose and law

Every hostile case named in the P0 mission maps to exactly one failure class below; every
failure class maps to at least one planned proof and one named recovery owner. No class is
detected only by prose. Recovery never means "retry until green": a recovery is a
**canonical transition performed by the owner of the state**, recorded in evidence, and
observable without reading the implementation.

Ownership rules (frozen by charter §5/§9 and carried unchanged):

| State | Owner | May recover? |
|---|---|---|
| Canonical job/lease/evidence/audit state | control-plane engine | yes — `recover_abandoned_leases()` and engine transitions only |
| Console session record | console `session_store` (append-only) | marks `partial`; never rewrites history |
| Rendered panel/status document | console kernel/panel (ephemeral) | re-render from reads; never caches a value as truth |
| Test/evidence artifacts | stage rung that produced them | re-derived from raw output; never hand-edited |
| Scope/authorization | operator only | no rung may grant itself authority |

## 2. Failure taxonomy (16 classes)

| # | Class | Hostile trigger | Planned detection (ID / node) | Observable expected result | Recovery owner | Stop? |
|---|---|---|---|---|---|---|
| F1 | `MALFORMED_INPUT` | truncated/invalid JSON, wrong types, non-string keys | `B5I7-R22` / `TestPanelBounds::test_oversized_and_malformed_input_refused` | refusal with frozen reason `malformed_request`, nonzero exit, no partial render | console (fail closed) | no |
| F2 | `OVERSIZED_INPUT` | >64 KiB document, >512-byte argument, >32 args | `B5I7-R22` / same node | refusal `payload_too_large`, no I/O | console | no |
| F3 | `UNKNOWN_FIELD` | undeclared surface id or unexpected response field | `B5I7-R15` / `TestPanelContract::test_undeclared_surface_refused_before_io` | `unsupported_surface` raised **before** any socket attempt (request log empty) | console | no |
| F4 | `DUPLICATE_ID` | repeated surface/section id in one request set | `B5I7-R15` / same node | second request suppressed or refusal; never double-counted queue depth | console | no |
| F5 | `STALE_IDENTITY` | evidence cited for the wrong SHA/tree, stale session id | `B5I7-EL06`, `B5I7-R13` / `TestEL06::test_green_claims_carry_sha_and_tree_binding` | claim rejected: head SHA and tree identity absent or mismatched | stage evidence owner | **yes — STOP-7** if already published |
| F6 | `UNAUTHORIZED_TRANSITION` | panel attempting a state change (submit/cancel/requeue) | `B5I7-R16` / `TestPanelReadOnly::test_panel_issues_only_get_requests` | GET-only assertion fails on any write verb; zero invoke-surface access | engine (only writer) | **yes — STOP-1** |
| F7 | `FORGED_CLIENT_STATE` | client-supplied "healthy/queued" values injected into the render | `B5I7-R17`, `B5I7-R18` / fail-closed nodes | forged value ignored; state rendered from reads or `STACK_UNREACHABLE`/`null` | console | no |
| F8 | `NON_LOOPBACK_ACCESS` | non-loopback base URL, redirect to foreign host | `B5I7-R20` / `TestPanelLoopback::test_non_loopback_base_url_refused` | `non_loopback_refused` before connect (blocked-connect control proves zero attempts) | console | **yes — STOP-4** |
| F9 | `MISSING_DEPENDENCY` | stack down, contract pack unreadable, module missing | `B5I7-R17` / fail-closed node | `STACK_UNREACHABLE`, never stale green; `G8` engine owns recovery | engine for state, console for render | no |
| F10 | `INTERRUPTED_OPERATION` | rung aborted mid-run, partial JSON/junit left behind | `B5I7-EL11` / `TestEL11::test_cleanup_claims_require_machine_readable_residual_state` | artifact marked partial and excluded from claims; cleanup listing shows residuals | rung owner | **yes — STOP-7** if cited as evidence |
| F11 | `REPLAY` | re-submitting a governed operation, re-using an old run id | `B5I7-EL02`, `B5I7-R16` / `TestEL02::test_no_run_or_artifact_id_recorded_before_existence` | duplicate id rejected or refusal; no second write attempt | engine | no |
| F12 | `PARTIAL_EVIDENCE` | totals without parsed raw source; hand-written JSON | `B5I7-EL03`, `B5I7-EL05` / corresponding `TestEL*` nodes | claim discarded; JSON without parser provenance fails the node | stage evidence owner | **yes — STOP-7** |
| F13 | `RECOVERY_DISAGREEMENT` | drill report differs between runs on an unchanged stack | `B5I7-R12` / `TestRegressionDrill::test_unchanged_stack_drill_report_byte_identical` | byte-difference fails identity comparison; drill not accepted | engine (drill authority) | **yes** until explained |
| F14 | `UNVERIFIABLE_OUTPUT` | queue depth unknown, unverifiable gap, evidence id unresolvable | `B5I7-R18`, `B5I7-EL01` / `TestPanelFailClosed::test_unknown_queue_depth_rendered_unknown_not_zero`, `TestEL01` | `null` + `unknown_reason`, **never** `0`/green; unresolvable SHA fails the node | console | no |
| F15 | `SCOPE_ESCALATION` | pressure to add endpoint, pack entry, web view, B5-I8/I9 work | `B5I7-R04`, `B5I7-DF01..DF03`, stops `STOP-1/3/6` | scope claim contradicts contract §6/§20 and is recorded as escalation | operator | **yes — STOP-6** |
| F16 | `EVIDENCE_FRAUD` | predicted SHA, pre-recorded run id, badge-as-proof, "all gates passed" while pending | `B5I7-EL01`–`EL15` (15 nodes) | the specific `TestEL*` node turns red | stage evidence owner | **yes — STOP-5/7** |

Class coverage check: hostile cases mandated by the P0 mission map as — malformed F1,
oversized F2, unknown fields F3, duplicate identifiers F4, stale identity F5,
unauthorized transition F6, client-side forged state F7, non-loopback F8,
missing dependency F9, interrupted operation F10, replay F11, partial evidence F12,
recovery disagreement F13, unverifiable output F14. F15/F16 are the two governance
classes added by the B5-I6 X1 lessons. **All 16 classes are covered; none is unowned.**

## 3. Recovery plan

**3.1 Failure during implementation rungs (R1–R3).**
Repair in a new rung or an `Xn` commit, append-only. Never amend, rebase, or force-push;
never commit a red test run; the working tree returns to pristine
(`git status --porcelain` empty) before any evidence claim (`B5I7-EL10`, `B5I7-EL11`).

**3.2 Failure during evidence runs (R4/EVIDENCE).**
The run is recorded as failed with its raw output preserved. A replacement run is a new
run id; the failed run is never deleted, and totals are re-derived by parsing raw artifacts
(`B5I7-EL02`, `B5I7-EL05`). If the exact-head run cannot reach terminal state, the gate
stays *not executed* — never *passed* (`B5I7-EL14`, `B5I7-EL15`).

**3.3 Failure of the governed change itself (the panel cannot be built read-only).**
If the change needs a control-plane source, contract-pack, or existing-test edit,
`STOP-1`/`STOP-2`/`STOP-3` fire. Recovery = withdraw the change and report; there is no
"just this once" pack edit, because the pack is byte-frozen
(`45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa`).

**3.4 Failure of a negative control (mutation never goes red).**
The mutation battery is not satisfied: record the mutation as **not discriminated**, do not
count it, and repair the *test*, never the *claim* (`B5I7-EL10`).

**3.5 Recovery-disagreement protocol (F13).**
Both reports are kept byte-for-byte; sha256 of each is recorded; the discrepancy is
diagnosed against stack identity (PID/port/SHAs) before any rerun is accepted. Divergence
without an identified stack-state difference halts the gate (`B5I7-R12`).

**3.6 Rollback of the change itself.**
The release manifest carries `rollback.base_commit` + procedure; rollback = restore the
base console tree, rebuild the manifest, verify with `verify_manifest` (existing B5-I6
instruments, unmodified). Rollback is exercised at R3, not merely documented (`B5I7-R08`).

## 4. Two-sided proof obligation per class

For every row in §2 the R3 record must contain: (a) the positive proof on the real
implementation; (b) an executed negative control showing the weakened implementation going
red; (c) the restored green run; (d) a cleanup record with residual state. A class with only
(a) is **not** proven. This mirrors the B5-I6 discipline (11/11 discriminated with
restoration) and raises it to the 15 evidence laws (`B5I7-EL01`–`EL15`).

## 5. Stop-condition index (cross-reference)

`STOP-1` control-plane edit required · `STOP-2` existing test would have to change ·
`STOP-3` undeclared surface · `STOP-4` non-loopback path · `STOP-5` skipped/substituted/
pending/inferred gate described as passed · `STOP-6` scope escalation into extraction or
B5-I8/I9 · `STOP-7` untraceable evidence value. Full text: contract §24. Any stop halts the
stage; resumption requires a fresh operator authorization.

## 6. Non-ownership check (no unowned obligation)

| Obligation | Owner | Where recorded |
|---|---|---|
| web view / `test_b5_i7_web_view.py` | Operator (charter §12 I-7) | `B5I7-DF01` |
| usability/accessibility protocol (`G16`) | B5-I8 | `B5I7-DF02` |
| factory corrections, B6 extraction contract | B5-I9 | `B5I7-DF03` |
| cloud/hosting/telemetry | deferred by Amendment A003, operator-gated | contract §6/§10 (prohibited) |
| canonical recovery transitions | engine | §1 above |

No failure class is owned by nobody; no deferred item lacks owner, reason and future stage.

## 7. P0 status of this document

Everything above is **PLANNED**. No failure class has been exercised under
`AUTHORIZED_STAGE=B5-I7-P0`; no mutation has been run; no rollback has been performed.
Reporting any row as detected, discriminated, or recovered at P0 would itself be
`EVIDENCE_FRAUD` (F16).

`MERGE_AUTHORIZED = false` · **B5-I7 IMPLEMENTATION NOT AUTHORIZED** ·
`B5-I8`–`B5-I9` remain `LOCKED`.
