# OCE B5-I2 Operator Ratification — v1.0

**Artifact class:** operator ratification record (documentation only)
**Stage:** `AUTHORIZED_STAGE=B5-I2-AUDIT_REPAIR_AND_RATIFICATION`
**Date:** 2026-10-08
**Supersedes no prior artifact; complements the Book 5 ledger §9 audit section (commit `0fa18d695…`).**

---

## 1. Identity (base, implementation, repair, evidence SHAs)

| Role | SHA | Commit subject |
|---|---|---|
| Base (`origin/main` at authorization) | `882835dac27c04712fe4a59c2cf0bc975e419724` | Merge PR #9 (B5-I1) |
| P0 | `66a185186…` | `B5-I2-P0: freeze first implementation increment` |
| R1 | `5ce24e4c4…` | `B5-I2-R1: add console-control-plane contract pack and binding module` |
| R2 (original implementation head) | `77bccf860307ca3b9bee6939ab2fe3a8f848eabd` | `B5-I2-R2: add two-sided contract tests with adversarial negative controls` |
| Historical evidence head | `5b3db4445771f160f1e0b0d6b3105ac5c2817ea1` | `B5-I2-EVIDENCE: record B5-I2 execution evidence in Book 5 ledger` |
| Repair X1 (CI-exposed selection) | `835fc644342b17acabfe65ef465359c58a6fe5a2` | `B5-I2-X1: execute console-contract proofs in authoritative validation` |
| Repair X2 (proof strictness) = **implementation head** | `d5801e104b4ee4178e2145bfb4189e7b21169267` | `B5-I2-X2: make authority-owner, route, schema and import-closure proofs strict` |
| Audit evidence head | `0fa18d695716c82a7ccef386d36e26967308bcdd` | `B5-I2-EVIDENCE-AUDIT: append superseding B5-I2 audit section to Book 5 ledger` |

History is append-only: no amend, squash, rebase, reset or force-push at any point. Branch changed only through work in this authorized stage; the branch touches exactly six files versus base (workflow, ledger, implementation contract, and the three new B5-I2 files); the three pre-existing schemas are untouched.

## 2. Exact authoritative CI run IDs

| Run | Head tested | Conclusion | Role |
|---|---|---|---|
| `37708674982` | `77bccf860…` | SUCCESS | **Historical** — aggregate workflow only; 0 of 24 B5-I2 nodes selected (ledger §9.1). Not node-level evidence. |
| `37709881210` | `5b3db4445…` | SUCCESS | **Historical** — same, 0 of 24 selected. |
| `37788106183` | `835fc6443…` (X1) | SUCCESS | **Proving** — B5-I2 selection live: 24/24 executed (artifact `b1-i1r-evidence-e7ac8552318d`). |
| `37791367627` | `d5801e104…` (X2, implementation head) | SUCCESS | **Proving** — exact-head implementation proof (artifact `b1-i1r-evidence-5b14ebb60d9d`). |
| `37795129886` | `0fa18d695…` (audit evidence head) | SUCCESS | **Proving** — exact-head evidence proof (artifact `b1-i1r-evidence-fa707ba2da2f`, verdict PASS, 24/0/0/0, `pr_head_sha=0fa18d695…`). |
| ratification-head run | this commit | verified post-push before merge | Cannot self-contain its own run id; recorded in the final merge report. |

Workflow: `B1-I1R Validation`, event `pull_request` → `main`, PR #10; identity gate binds repository, observed branch, tested commit and tree; gate status `READY_FOR_OPERATOR_REVIEW` on every proving run.

## 3. JUnit totals (both proving runs, artifact-level)

| Run | tests | passed | failed | errors | skipped | collected | duplicate full node IDs |
|---|---|---|---|---|---|---|---|
| `37788106183` | 24 | 24 | 0 | 0 | 0 | 24 = executed | 0 |
| `37791367627` | 24 | 24 | 0 | 0 | 0 | 24 = executed | 0 |

Selection is whole-file on `infrastructure/control-plane/tests/test_console_contracts.py` (floor 24); registry proof JSON in each artifact binds `pr_head_sha` to the exact head, the tested checkout to the PR merge ref (base `882835dac…` + head), and `executed_equals_collected = true`.

## 4. All 24 named-node execution proof (from the run-`37791367627` registry proof)

Every node below was collected, selected, executed, passed, not skipped, unique, and bound to the tested head `d5801e104b4ee4178e2145bfb4189e7b21169267`. Full prefix `infrastructure/control-plane/tests/test_console_contracts.py::`:

1. `TestContractPack::test_pack_is_structurally_valid`
2. `TestContractPack::test_every_declared_operation_exists_on_the_governed_module`
3. `TestContractPack::test_invoke_routes_match_http_api_registrations`
4. `TestContractPack::test_pack_identity_is_pinned_in_this_test_file`
5. `TestUnsupportedOperationRefusal::test_unknown_read_surface_refused_before_side_effects`
6. `TestUnsupportedOperationRefusal::test_unknown_invoke_surface_refused_before_side_effects`
7. `TestUnsupportedOperationRefusal::test_read_surface_id_used_as_invoke_is_refused`
8. `TestUnsupportedOperationRefusal::test_non_vacuous_negative_control_weakened_guard_admits`
9. `TestMalformedInputRefusal::test_unknown_job_type_refused_before_admission`
10. `TestMalformedInputRefusal::test_oversize_payload_refused`
11. `TestMalformedInputRefusal::test_missing_required_field_refused`
12. `TestMalformedInputRefusal::test_unexpected_field_refused`
13. `TestMalformedInputRefusal::test_cancel_with_missing_job_id_refused`
14. `TestGovernedInvokeSurfaces::test_submit_through_pack_is_the_governed_operation`
15. `TestGovernedInvokeSurfaces::test_submit_without_authority_yields_schema_valid_denial`
16. `TestGovernedInvokeSurfaces::test_cancel_and_retry_are_single_governed_operations`
17. `TestCanonicalStateAgreement::test_projected_job_agrees_verbatim_with_governed_state`
18. `TestCanonicalStateAgreement::test_reads_render_governed_responses_verbatim`
19. `TestCanonicalStateAgreement::test_stale_or_unknown_job_inspect_is_not_fabricated`
20. `TestDeterminism::test_identical_inputs_produce_byte_identical_projections`
21. `TestDeterminism::test_module_import_closure_has_no_llm_hosting_or_broker_dependencies`
22. `TestDeterminism::test_refusal_law_operates_without_any_model`
23. `TestEvidenceIdentityBinding::test_evidence_manifest_binds_to_schema_and_operation`
24. `TestEvidenceIdentityBinding::test_denial_envelope_from_governed_authority_is_rendered_verbatim`

Class distribution: 4 + 4 + 5 + 3 + 3 + 3 + 2 = 24. Zero skips in authoritative Linux CI.

## 5. Two-sided contract proof

**Serialized side:** `console-contract.json`, `contract_version 1.0.0`, SHA-256 `45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa`, pinned by node 4 (pack-changed-only mutation M1 fails node 4). **Runtime side:** `console_contracts.py` loads and re-validates the pack on every call (kind + `oce_control.*` prefix), enforces exact request field sets, payload bound 65536 (pack == module), pinned 21-field projection (subset of the schema's pinned 23), and fail-closed refusals before side effects. Both sides agree on version, operation names (12/12 resolved live), request/response fields, status vocabulary (schema enum; fabricated status fails M6), bounds, authority owner, and read/invoke classification (kind confusion fails M4).

**Negative controls discriminate (11/11):** pack-changed, guard-weakened, wrong-owner, read-as-invoke, submit-bypass, fabricated-status, schema added/removed/renamed, static forbidden import, dynamic import escape — each fails ≥1 node; restore returns 24/24 (ledger §9.5).

**Three existing schemas:** `job-envelope.schema.json`, `denial-envelope.schema.json`, `evidence-manifest.schema.json` — created `B2-C1` (`dbf128368`, 2026-08-30), present at base, untouched by this branch; compatibility proven by validating real governed documents in nodes 15/17/23/24.

## 6. Authority mapping (every declared operation → existing governed owner)

| Surface | Existing owner (module.callable → route) | Class |
|---|---|---|
| `health.read` | `api.ControlPlaneAPI.health` → `GET /api/health` | read |
| `readiness.read` | `api.ControlPlaneAPI.readiness` → `GET /api/readiness` | read |
| `jobs.inspect` | `api.ControlPlaneAPI.inspect_job` → `GET /api/jobs/{job_id}` | read |
| `jobs.schedules` | `api.ControlPlaneAPI.list_schedules` → `GET /api/schedules` | read |
| `workers.list` | `api.ControlPlaneAPI.list_workers` → `GET /api/workers` | read |
| `system.read` | `api.ControlPlaneAPI.system_state` → `GET /api/system` | read |
| `audit.read` | `api.ControlPlaneAPI.audit_history` → `GET /api/audit` | read |
| `denial.read` | `authority.AuthorityEngine.record_denial` → embedded in denied `APIResponse.data.denial` | read |
| `evidence.read` | `evidence.EvidenceBuilder.build_manifest` → embedded in evidence records | read |
| `jobs.submit` | `api.ControlPlaneAPI.submit_job` → `POST /api/jobs` | mutation |
| `jobs.cancel` | `api.ControlPlaneAPI.cancel_job` → `POST /api/jobs/{job_id}/cancel` | mutation |
| `jobs.retry` | `api.ControlPlaneAPI.retry_job` → `POST /api/jobs/{job_id}/retry` | mutation |

- 12/12 resolved through live import + attribute chain to a callable; 10/10 HTTP routes present in `http_api.py` source (2 embedded declare none, pinned to that form); zero placeholder, future-route or invented capabilities.
- Invokes are exactly the three governed mutations; leases have **no** console surface (observed via job envelopes/worker listings); `leases.read/list/release/renew` refused `unsupported_surface` fail-closed (demonstrated for read and invoke kinds); health cannot mutate; denials cause zero governed side effects (node 15); cancellation/retry legality is owned by the existing lifecycle (node 16); not-found is never fabricated (node 19); no second lifecycle state machine and no duplicated recovery law exist in the module.

## 7. Limitations

Recorded in ledger §9.8: local full-suite greenness is impossible on this Windows host (environment-conditional failures, 0 HEAD-only failure sites, `/proc` failure reproduced at base with the same command); `denial.read`/`evidence.read` are embedded bindings not routed through the generic read dispatcher; `jobs.schedules`/`audit.read` lack a dedicated CI node (positive proof = strict binding/route nodes + audit runtime demonstration); ruff findings are pre-existing R2 debt (no project lint gate); the ratification commit's own CI run id cannot be contained in this artifact and is verified before merge.

## 8. Scope confirmation

This stage implements **only charter increment I-1** (`B5-I2`): versioned contract pack + deterministic binding module + its 24 tests, plus CI-selection/proof repairs confined to the existing workflow. No UI, no console code, no new API endpoints, no hosting, no LLM dependence, no broker/capital/trading/execution authority, no unrelated workflow changes, no branch-protection changes. Cloud mutations 0; recurring cost `$0`; `capital.authority = none`.

**B5-I3 requires a fresh `AUTHORIZED_STAGE=B5-I3` and has NOT begun.**

## 9. Status transitions recorded by this artifact

- **B5-I2 → `OPERATOR_ACCEPTED`** (Book 5 ledger §1 updated in the same commit)
- **B5-I3–I9 → `LOCKED`** (already `LOCKED` in ledger §1; reconfirmed here)

Ratified under `AUTHORIZED_STAGE=B5-I2-AUDIT_REPAIR_AND_RATIFICATION` once: all 24 nodes executed in authoritative Linux CI with zero failures/errors/skips/duplicates; two-sided agreement and 11/11 negative controls proven; implementation and evidence heads each have exact-head CI success; PR head equals the verified evidence head; local equals live remote; tracked tree clean; B5-I3+ absent; PR mergeable.
