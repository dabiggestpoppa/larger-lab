# OCE Golden System
## B5-I8 — Failure Matrix and Recovery Plan (P0) — v1.0

**Document ID:** OCE-B5-I8-FAILURE-001
**Version:** 1.0
**Status:** `P0_DRAFT_FOR_OPERATOR_REVIEW` — planning only; no failure class has been executed.
**Stage:** `AUTHORIZED_STAGE=B5-I8-P0` · Base `7393228dd4b21be9440785204ea9e640800d5d95`
**Contract:** `OCE_B5_I8_IMPLEMENTATION_CONTRACT_v1.0.md` · **Registry:** `OCE-B5-I8-REGISTRY-001`

---

## 1. Taxonomy law

The taxonomy is **closed at 18 classes**. Each class is either (a) a hostile condition the audit must *provoke* against existing surfaces, or (b) a failure mode of the audit itself. A class exists only if a planned node discriminates it. Every authorized hostile trigger named in the stage contract is covered; no class is added for a surface B5-I8 may not touch (no web-view class, no endpoint class beyond refusal, no multi-tenant class).

## 2. Failure classes

| ID | Trigger | Affected requirement | Expected state on trigger | Observable output | Forbidden response | Recovery owner | Planned proof | Stop |
|---|---|---|---|---|---|---|---|---|
| `F01` | local stack unreachable | `B5I8-R08`, `B5I8-R17`, `B5I8-R40` | `STACK_UNREACHABLE` (fail closed) | explicit unreachable state, exit code non-zero, no rendered truth | render stale green; retry silently; fall back to cached state | engine (unchanged); audit reports | `TestEndToEndPath::test_full_governed_path_reexecuted_from_frozen_message` | — |
| `F02` | authorization denial on a governed read | `B5I8-R11`, `B5I8-R13` | `DENIED` rendered verbatim | full denial envelope preserved, no reinterpretation | swallow denial; convert to empty success; retry without consent | engine | `TestEndToEndPath::test_denial_path_rendered_verbatim_end_to_end` | — |
| `F03` | malformed payload | `B5I8-R13`, `B5I8-R18` | `MALFORMED_INPUT` refusal before side effect | refusal reason + zero side effects | partial parse; silent default; best-effort rendering | engine | `TestForgedState::test_forged_client_state_refused_before_effect` | — |
| `F04` | partial response | `B5I8-R15` | `PARTIAL` presented as partial | partial marker distinct from success | complete-looking success; drop the missing half silently | audit reports; engine unchanged | `TestTruthCollapse::test_partial_never_renders_success` | — |
| `F05` | inconsistent response across surfaces | `B5I8-R09`, `B5I8-R10`, `B5I8-R31` | `INCONSISTENT` recorded as a finding | disagreement surfaced with both values | pick the convenient value; average; suppress | audit owner (report only) | `TestEvidenceAudit::test_no_all_green_claim_while_gate_pending` | `STOP-6` if critical |
| `F06` | stale state | `B5I8-R16` | `STALE` state labelled | age/label visible, never green | render stale as current; refresh silently as if live | engine | `TestTruthCollapse::test_stale_state_never_renders_green` | — |
| `F07` | unknown / unverifiable value | `B5I8-R14`, `B5I8-R26` | `UNKNOWN` preserved | unknown token distinct from `0` and from empty | coerce to zero; coerce to empty; infer | audit reports | `TestTruthCollapse::test_unknown_never_renders_zero` | — |
| `F08` | oversized payload | `B5I8-R20` | bounded refusal or bounded truncation with a marker | explicit size refusal / truncation flag | unbounded read; silent truncation presented as complete | audit reports | `TestBounds::test_oversized_input_refused_within_bounds` | — |
| `F09` | excessive collection width | `B5I8-R20`, `B5I8-R21` | bounded, deterministic subset with a wide-collection flag | width flag + deterministic order | unbounded expansion; unstable order | audit reports | `TestBounds::test_oversized_input_refused_within_bounds` | — |
| `F10` | nondeterministic ordering | `B5I8-R21`, `B5I8-R38` | identical output for permuted equivalent input | byte-identical artifacts across permutations | order-dependent output; hash drift | audit owner | `TestDeterminism::test_adversarial_case_ordering_deterministic` | — |
| `F11` | secret leakage | `B5I8-R19` | redaction before output | no token/cookie/key values in any audit artifact | marker-only redaction; value with key retained; nested value surviving | audit owner | `TestRedaction::test_secret_material_absent_from_audit_output` | `STOP-6` if real credential |
| `F12` | non-loopback request / bind attempt | `B5I8-R17` | refused before I/O | explicit loopback-only refusal | accept `0.0.0.0`; accept LAN origin; "localhost only" ambiguity accepted silently | engine (unchanged); audit reports | `TestTransport::test_non_loopback_request_fail_closed` | `STOP-1` if enforcement missing |
| `F13` | attempted write authority from client | `B5I8-R12`, `B5I8-R13` | refused; authority not minted | refusal + no canonical change | mint intent/grant; write through a read path; console-owned recovery | engine | `TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | `STOP-6` if bypass succeeds |
| `F14` | unsupported route / operation | `B5I8-R18` | refused before side effect | explicit unsupported refusal | generic 500; silent no-op; hidden success | engine | `TestTransport::test_unsupported_route_refused_before_side_effect` | — |
| `F15` | client-side state divergence | `B5I8-R13`, `B5I8-R16` | client state treated as non-authoritative | divergence recorded, engine value wins | client value adopted as truth; reconciliation in the client | engine | `TestForgedState::test_forged_client_state_refused_before_effect` | — |
| `F16` | accessibility / comprehension failure | `B5I8-R22`, `B5I8-R23`, `B5I8-R24`, `B5I8-R25`, `B5I8-R26`, `B5I8-R27`, `B5I8-R39`, `B5I8-R41` | finding recorded; `G16` remains open | named accessibility/comprehension finding with the task that failed | declare `G16` met by assertion; omit the failed task | audit owner (report only) | `TestAccessibility::test_accessibility_semantics_verified` | `STOP-6` if critical |
| `F17` | false claim / self-referential evidence | `B5I8-R29`, `B5I8-R30`, `B5I8-R31`, `B5I8-R33`, `B5I8-R34`, `B5I8-R35`, `B5I8-R36`, `B5I8-R37`, `B5I8-EL01`, `B5I8-EL02`, `B5I8-EL03`, `B5I8-EL04`, `B5I8-EL05`, `B5I8-EL06`, `B5I8-EL07`, `B5I8-EL08` | claim rejected; verdict recomputed | failing citation or unrecomputable verdict | accept a narrative verdict; accept an `OBSERVED` label without a parsed source; "all gates passed" while any gate is held | audit owner | `TestAuditVerdict::test_verdict_recomputable_from_committed_evidence` | `STOP-7` |
| `F18` | external dependency / telemetry / cost-producing attempt | `B5I8-R05`, `B5I8-R06`, `B5I8-R19` | refused; none introduced | dependency audit shows none | import a provider SDK; enable analytics; billable call | operator | `TestRedaction::test_secret_material_absent_from_audit_output` + static dependency audit | `STOP-8` |

Coverage: every class names at least one planned node, and all 40 planned nodes appear in at least one class (40/40). Classes `F01`–`F18` are exactly the triggers named in contract §9 and the stage contract's failure surface.

## 3. Recovery plan

| Situation | Required behavior | Owner |
|---|---|---|
| Audit run crashes mid-protocol | no canonical state changed; session/audit record marked `PARTIAL`; re-run permitted | audit operator |
| Audit finds a production defect | record it as a **finding**, do not repair inside B5-I8; escalate to operator for a fresh stage | operator |
| Audit finds a critical authority bypass | `STOP-6`: halt the audit, publish the finding, do not proceed to a verdict of acceptance | operator |
| Usability task cannot be completed | record the failure and the comprehension gap; do **not** delete the task from the protocol | audit operator |
| Evidence citation does not resolve | `EL01`/`EL07` red; verdict is `NOT_RECOMPUTABLE`; no acceptance | audit owner |
| Adjacent population changes between ends | recompute common population; `common_nodes == 0` ⇒ FAIL; do not substitute the focused suite | audit owner |
| CI reveals a defect in the audit's own artifacts | repair narrowly in a new append-only commit; never edit the prior rung | stage owner |

No recovery action in B5-I8 may write canonical control-plane state, modify production code, or amend a prior stage's evidence.

## 4. Mutation plan (floor 12; not implemented at P0)

| ID | Weakened law | Target anchor (future) | Expected discriminating node | Acceptable failure mode | Restoration proof | Pristine rerun |
|---|---|---|---|---|---|---|
| `M01` | client is not an authority | introduce client-side canonical state in the audit harness | `TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | assertion failure or explicit refusal | byte-exact restore + `git status` clean | required |
| `M02` | unknown ≠ zero | coerce unknown to `0` in the renderer | `TestTruthCollapse::test_unknown_never_renders_zero` | assertion failure | byte-exact restore | required |
| `M03` | partial ≠ success | map `PARTIAL` to success | `TestTruthCollapse::test_partial_never_renders_success` | assertion failure | byte-exact restore | required |
| `M04` | denied is observable | suppress the denial envelope | `TestEndToEndPath::test_denial_path_rendered_verbatim_end_to_end` | assertion failure | byte-exact restore | required |
| `M05` | loopback-only | widen the accepted host set | `TestTransport::test_non_loopback_request_fail_closed` | assertion failure | byte-exact restore | required |
| `M06` | no write controls | add a write path to the audited surface | `TestAuthorityMinting::test_client_cannot_mint_identity_or_grant` | assertion failure | byte-exact restore | required |
| `M07` | unsupported refused pre-side-effect | allow an unsupported route | `TestTransport::test_unsupported_route_refused_before_side_effect` | assertion failure | byte-exact restore | required |
| `M08` | recursive redaction | restrict redaction to top-level keys | `TestRedaction::test_secret_material_absent_from_audit_output` | assertion failure | byte-exact restore | required |
| `M09` | bounded output | remove the bound | `TestBounds::test_oversized_input_refused_within_bounds` | assertion failure | byte-exact restore | required |
| `M10` | deterministic ordering | shuffle iteration order | `TestDeterminism::test_adversarial_case_ordering_deterministic` | assertion failure | byte-exact restore | required |
| `M11` | evidence is not self-referential | make the verdict a free-text constant | `TestAuditVerdict::test_verdict_recomputable_from_committed_evidence` | assertion failure | byte-exact restore | required |
| `M12` | accessibility semantics are checked | drop the semantics assertion | `TestAccessibility::test_accessibility_semantics_verified` | assertion failure | byte-exact restore | required |

Law for the future battery: every mutation must turn a **named** node red; a mutation that turns nothing red is a non-discriminating mutation and FAILS the stage. Restoration must be byte-exact and the pristine rerun must be green in the same run.

## 5. Stop conditions

Identical to contract §15 (`STOP-1`…`STOP-9`). `STOP-6` (critical bypass) and `STOP-7` (untraceable evidence value) are the two that most plausibly trigger in an audit stage; both end the stage with a reported finding rather than a repair.
