# OCE B5-I3 Construction Plan — v1.0

> **Book 5 increment:** B5-I3 (charter increment I-2, plan anchor `B5-I3`)
> **Derived from:** Block 5 plan §5 `B5.C3.S1` pattern — *bounded dependency plan (grants,
> budgets, gates, staged commits)*; named in plan §7 row `B5-I3` as the construction plan half
> of *C2 failures/acceptance and construction plan*.
> **Gate:** *Plan traceable to every acceptance requirement.*
> **Status:** planning only. **No increment I-3+ is authorized by this document.** Each stage
> below requires a fresh `AUTHORIZED_STAGE` from the operator before any line of it is built.

---

## 1. Objective and boundary

Carry every requirement in `OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json` (17 charter gates,
4 operator scenarios, 7 plan failure classes — 28 total) to executable completion through the
charter §12 increment rows, without ever exceeding the frozen increment ceiling or the ratified
CAND-004 charter. This plan is the staged route from *"registry complete"* (B5-I3's own gate)
to *"every gate executed with recorded evidence"* (charter §11 release condition).

**Stop rule (global):** if any stage discovers that its work requires authority the charter has
not granted (new job type, non-governed write path, non-loopback bind, external hosting, cloud,
broker, capital, execution, LLM-required behavior), the stage stops and the operator decides —
scope never expands by drift (charter §12 stop conditions; gate G17).

## 2. Grants (all stages)

- **New grants: NONE.** Every stage consumes the frozen B5-I2 contract pack and existing
  governed control-plane operations. No new authority-bearing role, no new write path, no new
  endpoint outside governed change (plan C1.S5 change control).
- **Capital / broker / execution authority:** NONE (ledger §6; charter exit states).
- **External hosting / cloud / provider:** NONE — local-only topology, loopback-only binding.
- **LLM:** never required for deterministic behavior; any LLM surface would be optional,
  replaceable, removable and non-authoritative (charter §8).
- **Reuse law:** the console remains a client; canonical state stays in the control plane;
  B5-I2 contracts are consumed, never duplicated.

## 3. Budgets (all stages)

- Recurring cost: **$0** (charter `RECURRING_COST = $0`; gate G13).
- Increment ceiling: **6 required (I-1..I-6) + up to 2 optional (I-7, I-8) = never more than 8**
  (charter §12 ceiling accounting; gate G17). I-1 (B5-I2) and I-2 (B5-I3) are spent;
  6 remain within the ceiling.
- Test budget: every stage lands with its planned nodes selected by the authoritative workflow
  in the same pattern as B5-I3 R4 (whole-file selection, node floor, zero skips/failures/errors,
  zero duplicate node ids) — a stage's tests that CI does not select do not count as proven.

## 4. Dependency graph

```
B5-I2 contract pack (frozen, OPERATOR_ACCEPTED)
        │
B5-I3 registry + failure matrix + this plan (this increment)
        │
        ├─► I-3  deterministic read path (S-1, G3/G7 read half, F-1/F-5 console half)
        │        │
        │        ├─► I-4  governed submission + dual-clock timeline (S-2, F-3 console half)
        │        │        │
        │        │        └─► I-5  evidence/artifact binding + drill session records (G9, F-4 console half)
        │        │                  │
        │        └──────────────────┴─► I-6  fail-closed + recovery drill completion (S-3/S-4, G5/G6/G8/G15, F-6 consent)
        │
        ├─► I-7  OPTIONAL loopback web view (only if operator directs; gates G1/G2 web surface)
        └─► I-8  OPTIONAL governed change demonstration
                                 │
                                 └─► B5-I8 independent E2E/adversarial/usability audit (G16)
```

Stage inputs are exactly: the B5-I2 pack, the B5-I3 registry entries owned by that stage, and
the charter §12 contract row for that stage. Nothing else may be pulled forward.

## 5. Stage plans

### I-3 — deterministic read path (plan anchor `B5-I4`)

- **Purpose (charter §12):** CLI status view over contract-validated reads (S-1); fail-closed
  `STACK_UNREACHABLE`.
- **Registry entries owned:** G3 (UI half), G7 (UI half), S-1 (console half), F-1 (console
  half), F-5 (console half).
- **Planned tests:**
  `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestClientOnlyReads::test_no_direct_store_read`
  `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStatusAgreement::test_status_view_matches_api_verbatim`
  `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStatusView::test_s1_lists_match_api_verbatim`
  `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStackUnreachable::test_stack_unreachable_renders_fail_closed`
  `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestNoStaleGreen::test_unverifiable_gap_never_renders_green`
- **Executable acceptance gate (charter §12):** I-2 registry's S-1/G7 tests pass.
- **Evidence output:** first vertical-slice demo record.
- **Non-goals:** no writes, no drills, no web view.
- **Stop condition:** any direct store read — stop, client-only, contract-mediated (gate G3).

### I-4 — governed submission and dual-clock timeline (plan anchors `B5-I4`/`B5-I5`)

- **Purpose (charter §12):** catalog-bounded job submission; dual-clock timeline (S-2).
- **Registry entries owned:** S-2 (console half), F-3 (console half).
- **Planned tests:**
  `infrastructure/control-plane/tests/test_b5_i4_timeline.py::TestDualClockTimeline::test_s2_transitions_rendered_with_both_clocks`
  `infrastructure/control-plane/tests/test_b5_i4_timeline.py::TestPartialTask::test_failure_envelope_rendered_without_false_success`
- **Executable acceptance gate:** S-2 tests pass; timeline reproducible.
- **Evidence output:** submit/complete session records.
- **Non-goals:** no new job types; no bypass of admission (gate G4).
- **Stop condition:** submission needs a non-governed path — stop.

### I-5 — evidence/artifact binding and drill session records (plan anchor `B5-I5`)

- **Purpose (charter §12):** timeline-to-evidence binding (G9); versioned drill playbook
  execution for S-3 beginnings (G5).
- **Registry entries owned:** G9 (audit half), F-4 (console half).
- **Planned tests:**
  `infrastructure/control-plane/tests/test_b5_i5_evidence_binding.py::TestArtifactBinding::test_timeline_binds_to_operation_and_commit`
  `infrastructure/control-plane/tests/test_b5_i5_drills.py::TestConsoleCrash::test_session_record_marked_partial_on_crash`
- **Executable acceptance gate:** G9 binding audit passes; playbook runs bounded.
- **Evidence output:** drill session records + reports as digest-referenced artifacts.
- **Non-goals:** no drill logic outside playbooks; no recovery enactment (gate G8).
- **Stop condition:** evidence binding cannot anchor to the correct operation/commit — stop.

### I-6 — fail-closed and recovery completion (plan anchors `B5-I5`/`B5-I6`)

- **Purpose (charter §12):** S-3/S-4 completion — denial rendering verbatim, restart-identity
  (G6), engine-owned recovery reporting, duplicate-effect check (S-3), gates G5/G8/G15.
- **Registry entries owned:** G5 (drill half), G6 (console half), G8 (reporting half), G15
  (drill half), S-3 (console half), S-4 (console half), F-6 (consent half).
- **Planned tests:**
  `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestFailClosed::test_unsupported_drill_operation_refused`
  `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting`
  `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestAdversarialControls::test_bypassed_authority_detected`
  `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestDrillReport::test_s3_lease_requeue_completion_no_duplicate_effect`
  `infrastructure/control-plane/tests/test_b5_i6_console_restart.py::TestRestartIdentity::test_restart_preserves_session_record`
  `infrastructure/control-plane/tests/test_b5_i6_fail_closed.py::TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry`
- **Executable acceptance gate:** recovery-drill end-to-end passes; negative controls recorded.
- **Evidence output:** drill report with disposition `DRILL_PASS` after worker loss.
- **Non-goals:** no console-owned recovery; no retry without consent.
- **Stop condition:** a bypass trace or forged-agreement risk found — stop, adversarial review.

### I-7 — OPTIONAL loopback web view (plan anchor `B5-I6`)

- **Registry entries owned:** G1 (web surface), G2 (web surface).
- **Planned tests:**
  `infrastructure/control-plane/tests/test_b5_i7_web_view.py::TestLoopbackOnly::test_non_loopback_bind_and_request_refused`
  `infrastructure/control-plane/tests/test_b5_i7_web_view.py::TestLoopbackOnly::test_non_loopback_origin_request_fail_closed`
- **Gate condition:** only if the operator directs it; gates G1, G2, G7, G16 executed and
  negative tests recorded (charter §12 row I-7).
- **Non-goals:** no non-loopback bind; no secrets in browser; no browser mutations beyond
  charter §5 rule 9.
- **Stop condition:** any non-loopback reachable path — stop and withdraw the surface.

### I-8 — OPTIONAL governed change demonstration (plan anchor `B5-I7`)

- **Registry entries owned:** none (no B5-I3 requirement defers to I-8; listed for ceiling
  accounting completeness).
- **Gate condition (charter §12):** gate G14 plus regression-drill identical-report check.
- **Non-goals:** no scope creep; no platform extraction.

### B5-I8 — independent audit (plan §7 anchor `B5-I8`)

- **Registry entries owned:** G16 (usability protocol/results).
- **Planned tests:**
  `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestUsabilityProtocol::test_accessibility_and_usability_verified`
- **Gate (plan §7):** zero critical bypass or false claim; usability verified without weakening
  authority (charter gate G16 test class: usability protocol/results).

## 6. Staged commit discipline (every stage)

Each stage, when authorized, follows the ladder proven in B5-I2 and B5-I3 itself:

1. **P0** — documentation-only implementation contract + acceptance matrix, pushed before any
   implementation, draft PR titled `...(NOT MERGE AUTHORIZED)`.
2. **R1** — core deterministic artifacts for that stage.
3. **R2** — boundary/refusal behavior and compatibility binding, with tests.
4. **R3** — executable positive, negative and adversarial proofs (every negative control able
   to turn red, demonstrated).
5. **R4** — authoritative CI selection: whole-file selection, mandatory-node floor, zero
   duplicate node ids, zero failed/errors/skipped, evidence bound to exact head.
6. **EVIDENCE** — documentation-only ledger append with exact SHAs, run ids, totals.

No amend, no rebase, no force-push, no committed-red false green; CI defects are repaired in
separate `Xn` commits, append-only.

## 7. Traceability matrix (all 28 registry requirements)

| ID | Requirement (abbrev.) | Executable today | Owning stage for remaining surface |
|---|---|---|---|
| G1 | Loopback-only executable + negative | binding tests (config spine) | I-7 (web surface) |
| G2 | Non-loopback binding/request fail closed | binding tests (config spine + pack) | I-7 (web surface) |
| G3 | UI cannot mutate canonical state | pack refusal (B5-I2) | I-3 (read path) |
| G4 | Mutation = one governed operation | pack trace (B5-I2) | — (closed now) |
| G5 | Unsupported ops refused pre-side-effect | pack refusal (B5-I2) | I-6 (drill surface) |
| G6 | Frontend loss/restart safe | engine restart test | I-6 (restart identity) |
| G7 | UI lifecycle agrees with authority | verbatim-agreement (B5-I2) | I-3 (status view) |
| G8 | Recovery/reconciliation engine-owned | engine recovery test + pack closure | I-6 (reporting) |
| G9 | Evidence/artifact identity binding | manifest binding (B5-I2) | I-5 (timeline binding) |
| G10 | No LLM required | import-closure audit (B5-I2) | — (closed now) |
| G11 | No external hosting/paid provider | import-closure audit (B5-I2) | — (closed now) |
| G12 | Cloud/broker/capital/execution zero | dependency audit + ledger attestation | — (closed now) |
| G13 | Recurring cost $0 | ledger attestation | — (closed now) |
| G14 | Existing OCE validation green | shared runner (workflow) | — (closed now) |
| G15 | Negative controls detect bypass | mutation harness (B5-I2) | I-6 (drill controls) |
| G16 | Accessibility/usability verified | — (deferred owner) | B5-I8 |
| G17 | Within frozen increment ceiling | charter attestation + B5-I3 audit | — (closed now) |
| S-1 | Visibility matches API verbatim | verbatim reads (B5-I2) | I-3 |
| S-2 | Submit + dual-clock timeline | governed submit (B5-I2) | I-4 |
| S-3 | Recovery drill, no duplicate effect | engine recovery + duplicate proof | I-6 (I-5 begins) |
| S-4 | Denial rendered verbatim, no silent retry | denial envelope (B5-I2) | I-6 |
| F-1 | Dependency outage | engine fail-closed tests | I-3 |
| F-2 | Invalid data | pack refusal (B5-I2) | — (closed at contract boundary) |
| F-3 | Partial task | engine atomicity tests | I-4 |
| F-4 | Crash | engine restart/crash tests | I-5 (I-6 identity) |
| F-5 | Stale state | engine stale-cleanup tests | I-3 |
| F-6 | Retry | governed retry + engine durability | — (consent half at I-6) |
| F-7 | Cancellation | governed cancel + refusal | — (closed now) |

Every registry id appears exactly once above; every remaining surface maps to exactly one
owning stage; every owning stage exists as a charter §12 row (or plan §7 stage for B5-I8).

## 8. Planned node inventory (18 planned nodes, deferred owners)

Each planned node is the concrete future test the owning stage must add; the registry carries
the same strings, and the B5-I3 suite asserts they appear here verbatim.

| Owner | Planned node |
|---|---|
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestClientOnlyReads::test_no_direct_store_read` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStatusAgreement::test_status_view_matches_api_verbatim` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStatusView::test_s1_lists_match_api_verbatim` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestStackUnreachable::test_stack_unreachable_renders_fail_closed` |
| I-3 | `infrastructure/control-plane/tests/test_b5_i4_console_kernel.py::TestNoStaleGreen::test_unverifiable_gap_never_renders_green` |
| I-4 | `infrastructure/control-plane/tests/test_b5_i4_timeline.py::TestDualClockTimeline::test_s2_transitions_rendered_with_both_clocks` |
| I-4 | `infrastructure/control-plane/tests/test_b5_i4_timeline.py::TestPartialTask::test_failure_envelope_rendered_without_false_success` |
| I-5 | `infrastructure/control-plane/tests/test_b5_i5_evidence_binding.py::TestArtifactBinding::test_timeline_binds_to_operation_and_commit` |
| I-5 | `infrastructure/control-plane/tests/test_b5_i5_drills.py::TestConsoleCrash::test_session_record_marked_partial_on_crash` |
| I-6 | `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestFailClosed::test_unsupported_drill_operation_refused` |
| I-6 | `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting` |
| I-6 | `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestAdversarialControls::test_bypassed_authority_detected` |
| I-6 | `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py::TestDrillReport::test_s3_lease_requeue_completion_no_duplicate_effect` |
| I-6 | `infrastructure/control-plane/tests/test_b5_i6_console_restart.py::TestRestartIdentity::test_restart_preserves_session_record` |
| I-6 | `infrastructure/control-plane/tests/test_b5_i6_fail_closed.py::TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry` |
| I-7 | `infrastructure/control-plane/tests/test_b5_i7_web_view.py::TestLoopbackOnly::test_non_loopback_bind_and_request_refused` |
| I-7 | `infrastructure/control-plane/tests/test_b5_i7_web_view.py::TestLoopbackOnly::test_non_loopback_origin_request_fail_closed` |
| B5-I8 | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestUsabilityProtocol::test_accessibility_and_usability_verified` |

## 9. What this plan may not do

- May not authorize any stage (fresh `AUTHORIZED_STAGE` per stage, operator only).
- May not weaken, skip or reorder charter gates (charter §13: gates may be strengthened by
  amendment only).
- May not add requirements beyond the 28 registry ids (charter non-goal: no tests for
  unproposed features).
- May not merge B5-I3 itself (draft PR, `NOT MERGE AUTHORIZED`).
