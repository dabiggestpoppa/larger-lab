# OCE B5-I5 Operator Ratification — v1.0

**Document ID:** OCE-B5-I5-OPERATOR-RATIFICATION-001
**Version:** 1.0 — ratification artifact for `AUTHORIZED_STAGE=B5-I5-RATIFY`
**Date:** 2026-10-14
**Authorized base:** `43720843b2f4c9a59044fd9d462edb0fe3b338b6` (B5-I4 merge of PR #14)
**PR:** #15 — merged only under `MERGE_AUTHORIZED=CONDITIONAL` after every ratification gate passes

> **Disposition set in this commit:** `B5_I5 = OPERATOR_ACCEPTED` (Book 5 ledger
> §1 row and §16 updated in this same commit; acceptance matrix status recorded).
> This artifact grants no other authority: `B5_I6_THROUGH_B5_I9 = LOCKED`;
> no B5-I6 work exists or begins; recurring cost `$0`; `capital.authority = none`;
> Freebuff untouched; no frontend/hosting/provider/cloud/telemetry/LLM-authority/
> broker/capital/execution expansion; canonical state remains engine-owned.

Ratification is by the operator under `AUTHORIZED_STAGE=B5-I5-RATIFY`; the
technical audit, repairs and evidence were executed by the same agent that
built the increment and are therefore **same-agent, NOT organizationally
independent** (stated on every Book 5 artifact).

---

## 1. Authority reconstruction and requirement map

Governing sources read in full: Block 5 plan (`OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md`
§7 row `B5-I5`); ratified CAND-004 Product Charter (§12 increments I-4/I-5/I-6);
Book 5 ledger (§12.1/§13 deferral record, §14 build evidence); B5-I2 contract
pack (`console-contract.json`, `job-envelope.schema.json`); B5-I3 requirement
registry + failure/recovery matrix + construction plan; B5-I4 contract,
implementation, evidence and ratification; B5-I5 P0 scope contract; B5-I5
acceptance matrix; B5-I5 requirement-execution addendum; Amendment A1; B5-I5
evidence record; PR #15 body.

**Scope legitimacy verdict:** B5-I5 legitimately includes exactly
**(a) the complete I-4 slice, (b) I-5, and (c) only the explicitly assigned
B5-I5 half of I-6** — proven by literal citations:

| Increment | Literal authority | Charter gate text | Owner |
|---|---|---|---|
| I-4 (entire) | Charter §12 row: `I-4 \| B5-I4/B5-I5 \| submission and representative-job timeline (S-2)`; B5-I4 deferral (ledger §12.1/§13, B5-I4 matrix/contract) defers the **entire** I-4 console half to B5-I5 | *Invoke governed paths for submission → catalog-bounded job submission; dual-clock timeline (S-2); gate: S-2 tests pass; timeline reproducible* | B5-I5 |
| I-5 | Charter §12 row: `I-5 \| B5-I5 \| evidence/artifact binding + drill playbook execution (S-3 core)` | *timeline-to-evidence binding (G9); versioned drill playbook execution (G5); gate: G9 binding audit passes; playbook runs bounded* | B5-I5 |
| I-6 (B5-I5 half only) | Charter §12 row: `I-6 \| B5-I5/B5-I6`; plan §7 row `B5-I5` explicitly assigns *S-4 denial verbatim on submit, restart-identity G6, engine-owned recovery G8, duplicate-effect S-3, negative controls G15* to B5-I5, leaving the remainder to B5-I6 | *S-3/S-4 completion … gate: recovery-drill end-to-end passes; negative controls recorded* | B5-I5 (half) / **B5-I6 (remainder — LOCKED)** |

Requirement map (each governed requirement → authority → implementation owner
→ executable proof → evidence output → future owner), the acceptance-matrix
rows and requirement-execution addendum entries all map 1:1 with **no orphan
requirement and no requirement silently pulled forward from B5-I6**:

| Requirement | Authority | Implementation owner | Executable proof (B5-I5 suite) | Evidence output | Future owner |
|---|---|---|---|---|---|
| S-2 dual-clock timeline, event-time sorted, reproducible | charter §12 I-4; B5-I3 registry S-2 | `oce_console/timeline.py` | `TestDualClockTimeline::*` + §7 ordering controls | timeline doc; E2E S1–S2, S6 | — |
| F-3 failure envelope, no false success | B5-I3 registry F-3 (deferred to I-4) | `timeline.py` `_summary_state` | `TestPartialTask::*` | timeline `failure_envelope` verbatim | — |
| Catalog-bounded governed submission (ONE write) | charter §12 I-4; P0 §6 | `oce_console/submit.py` + frozen pack `jobs.submit` | `TestGovernedSubmit::*` | engine job envelope; E2E S1/S9 | — |
| Refusals before I/O (catalog/oversize/malformed/loopback/identity) | P0 §6 refusal law | `submit.py`, `transport.py` | `TestRefusals::*`, `TestSubmitIdentityAuthority::*` | refusal records | — |
| S-4 denial rendered verbatim, no retry | charter §12 I-6; plan §7 B5-I5 | `submit.py` (engine decides) | `test_denied_submit_rendered_verbatim_not_retried` | denial envelope; E2E S3 | — |
| G9 timeline→evidence binding to engine identity | charter §12 I-5 | `oce_console/drill.py` `bind_evidence` | `TestEvidenceBinding::*`, `TestEvidenceBindingGuards::*` | binding record; E2E DRILL | — |
| G5 versioned bounded playbook | charter §12 I-5 | `drill.py` `Playbook` | `TestDrillSession::test_playbook_runs_bounded` | session record | — |
| G6 restart-identity | charter §12 I-6 (B5-I5 half) | stateless console | `TestRestartIdentity::*` | identical-view proof; E2E S7 | — |
| G8 engine-owned recovery reporting (console enacts nothing) | charter §12 I-6 (B5-I5 half) | `drill.py` observation-only | `test_recovery_is_engine_owned_console_enacts_nothing` | requeue observation; E2E S6 | — |
| S-3 duplicate-effect check + `DRILL_PASS` | charter §12 I-6 (B5-I5 half) | `drill.py` `build_drill_report` | `TestDrillSession::*`, `TestDrillReportClaimGuard::*` | drill report; E2E DRILL | — |
| G15 negative controls | charter §12 I-6 (B5-I5 half) | `TestNegativeControls` + §5/§7/§8 controls | 12/12 mutation battery red demonstrations | evidence record §7.2 | — |
| B5-I6 remainder of I-6 (deeper recovery completion) | charter §12 I-6 | **nobody — LOCKED** | none | none | **B5-I6 (requires fresh `AUTHORIZED_STAGE`)** |

## 2. Amendment A1 disposition — **judgment A: legitimate bookkeeping correction**

Proven from authorities frozen **before** B5-I5 existed:

1. **The frozen requirement already implied job-specific governed reads.**
   Charter §12 I-4 requires the dual-clock timeline (S-2) over a
   representative job's lifecycle, and Gate G3 makes the console client-only
   (it may not import/read `job_store`), so the console must read one job
   through the governed boundary.
2. **The interface already existed.** The B5-I2 contract pack (frozen,
   `OPERATOR_ACCEPTED`) declares `jobs.inspect` — kind `read`, bound to
   `GET /api/jobs/{job_id}` → `ControlPlaneAPI.inspect_job`, projection
   `job_envelope_projected`, governing schema `job-envelope.schema.json`.
   No new endpoint, schema, or pack change was needed or made.
3. **A new parallel transport module was inferior and effectively
   prohibited.** The loopback/proxy-free/redirect/identity laws are a
   security boundary implemented once in `transport.py`; a second module
   would either duplicate those laws (two sources of truth for the same
   boundary — contrary to the charter's reuse-over-parallel-authority
   design law) or reimplement them additively anyway. The chosen change
   was the minimal additive `LoopbackTransport.read_job` in the existing
   module — **zero changes to any existing B5-I4 method** (verified: frozen
   B5-I4 suite stays 23/23 green in every CI run).
4. **The amendment changed only the file ceiling** (≤ 2 → ≤ 3 existing
   files): A1 §3 explicitly leaves behavior, authority, acceptance
   conditions, write surface, floors, non-goals and locks untouched.
5. **Timing:** A1 was authored from the §5 design audit that ran **before
   any implementation commit**, and entered in the **same rung (R1,
   `c9e6afae7`) as the transport change** — it was not retrofitted after
   implementation was observed working. Combining amendment and code in
   one rung reduced temporal separation of review; that is recorded as a
   minor process observation **within D1's single deduction** (the ceiling
   miscount), not a second defect: the delta is mechanically verifiable
   (one ceiling number + one additive method) and was independently
   re-derived from pre-B5-I5 authorities by this ratification audit.

**Disposition: A1 preserved as a legitimate correction; no authority expansion
occurred.** Had the judgment been B, ratification would have stopped for an
operator decision; it is not.

## 3. `read_job` disposition (§5) — TRUE_DEFECT D2, repaired at R5

The untyped success-or-denial dictionary was a misuse-prone public seam and
was demonstrated to be consumable as success (§7.1 of the evidence record).
**Repair:** typed fail-closed result boundary — `project_job_read()` central
validator + `read_job()` returning the validated envelope or raising
`JobReadRefusal` (verbatim response attached); timeline renders denial and
incomplete envelopes as explicit `UNVERIFIABLE` gaps; `bind_evidence` refuses
denial/incomplete/cross-job inputs. All eight mandated negative controls are
executable nodes (`TestJobReadFailClosedBoundary`), plus the 12/12 external
mutation battery. Frozen contract compatibility: `read_job` remains a read on
the declared `jobs.inspect` route with unchanged loopback/GET-only/identity
laws; denials remain renderable verbatim through the refusal object (S-4
spirit preserved).

## 4. Timeline / dual-clock disposition (§7)

Event-time owner: **engine** (envelope fields only — `created_at`,
`lease.leased_at/heartbeat_at`, `result.completed_at`,
`failure_envelope.failed_at`). Knowledge-time owner: **console** (observation
instant, annotated beside each transition). Ordering key: `(event_time,
sequence)` with observation sequence as the declared tie-break; clock-domain
labels are the `event_time`/`knowledge_time` field names, asserted present on
every transition. Missing timestamps → explicit gap (never fabricated);
regressing timestamps → sorted, never rewritten; denial/failure envelopes →
gap / F-3 `failed`, never a successful lifecycle event; restart boundaries →
stale reads refuse fail-closed (no fabricated monotonic sequence);
serialization deterministic (`render_timeline` byte-identical). Every
load-bearing ordering rule now has a discriminating executable control
(`TestTimelineOrderingControls`, proven red under mutation M2a/M2b/M2c).

## 5. Drill / recovery / evidence-binding disposition (§8)

The console observes recovery and never performs it (structural verb audit +
POST-count proof); `DRILL_PASS` requires the engine-owned duplicate-effect
check **and** this session's own `check_duplicate_effect` observation;
binding anchors to engine `job_id` + `payload_hash` + `evidence_refs` and
refuses denial, missing-hash, missing-refs and cross-job inputs; session
records are append-only, schema-validated and version-bound; reports cannot be
reused across sessions/jobs (session validation + binding/job agreement +
two-sided engine cross-check). Restart boundaries are recorded truthfully: the
local engine store is **in-memory**, an engine restart starts empty, and the
console reports the stale-read refusal honestly — durable engine restart
parity remains the Book 4/Postgres domain and is **not** claimed.

## 6. Submission authority disposition (§6)

Out-of-catalog operation, malformed/oversize payload, missing/malformed
identity and non-loopback base URL all refuse **before any I/O** (exploding-
opener proofs). Engine-undecidable validity (well-formed but unauthorized
grant) is decided by the engine and rendered verbatim as a denial; one
invocation issues exactly one POST (counting client proofs + E2E totals);
no implicit retry exists anywhere; the client mints no grant, actor, job ID,
payload hash, evidence identity or recovery state (payload hashes verified
equal to the engine's own `job_store` values); duplicate-effect claims measure
engine-owned facts (`plane.recovery.verify_no_duplicate_effects`, engine store
counts), never client-local counters; no denial creates a timeline or drill
success record.

## 7. Complete ladder, rungs, and file boundaries (append-only)

| Rung | Commit | Tree | Kind |
|---|---|---|---|
| P0 | `aeda12deece94d50fb6ed98f8500d45b681a175f` | `3404d68e3bec3f293c5d68a8c48a78ccbb79b922` | scope freeze (docs) |
| R1 | `c9e6afae7ebbcce4eab146bb8b433a98e9de83d4` | `26c6467ce82a9a15850e5721eb3d0499b6759d87` | production + A1 |
| R2 | `bfacf1d9c07f5081f2b8134131a0a6f111dcc9e0` | `f317e959b2eed1e6a10da880a2138402ba12062f` | production |
| R3 | `2c8cdaa8815ec9a3a1dff3883d98cd8dbb4c8354` | `3b02671ae77f3ed3c7b08dc67e68b4aafe902c1e` | production |
| R4 | `ffccf5c3d9b5dabffaf9f8037cf168dd14ea3825` | `2ab70be70e745c7e3150759f298bf289a723c691` | test suite + workflow step |
| EVIDENCE | `07215cf41ea2ab22c6bc28dbfb700dd90145628f` | `ff0f8d4e021234572964ed68d69a5ba70f8dfa3f` | evidence doc only |
| **R5 (repair)** | `57cb37cf3b9d36ee8fd2d266b1d46533cab1ad30` | `86ca12046fbfb06006f39cd3b01a36a9a137bdff` | production fix + 21 new nodes |
| **R6 (correction)** | `f1e33cf8ea65b7c7ae7a24e0f7f236293eb4ea54` | `1efd687538974e38dd86396ef4c2406694c9edeb` | evidence/governance docs only |
| **RATIFY (this commit)** | *see §11* | *see §11* | ratification docs only |

- Linear, first-parent, append-only: `git rev-list --first-parent` from the
  authorized base reaches every rung; `git rev-list --merges` inside the
  branch = 0; the P0 parent equals the exact authorized base.
- Ladder SHAs/trees above were verified from git objects (`git log
  --format='%H %T'`); the P0 **tree** mistype in the PR body survives only as
  explicitly superseded history (evidence record §1 correction, PR §17.1).
- Changed paths at R6 = **exactly 12** (workflow, 6 governance docs, 4 console
  modules, 1 test file); this ratification commit adds exactly 1 new path →
  **13 ≤ the P0 ceiling of 16**; previously-existing files edited = 3
  (ledger, workflow, transport) ≤ A1's corrected ceiling of 3.
- Workflow diff vs base is exactly **one additive selection step** for
  `test_b5_i5_*.py` (mirrors B5-I2-X1/B5-I3-R4/B5-I4-R3); triggers,
  permissions, shared gates, uploads and prior-stage selections unchanged.
- Zero-line diff: control-plane `src/`, contracts/schemas, frozen B5-I2/I3/I4
  tests, frontend, Book 4, Sensor Fabric, providers, B5-I6+.

## 8. CI evidence — exact IDs and parsed totals (all live-confirmed)

| Purpose | Run | Head / merge-ref | Check-run | Artifact (id) | Parsed totals |
|---|---|---|---|---|---|
| Implementation head | `38453887983` (SUCCESS) | head `ffccf5c3d…` / merge-ref `26f94a58…`, tree `2ab70be7…` == R4 tree | `115491489488` | `b1-i1r-evidence-b90ca1c84e7b` (`11841404115`, 33797 B) | B5-I5 24/24, 0/0/0, floor 22; I4 23, I3 51, I2 24; regression 67/0; adversarial 49/49; static final 35/35; manifest 7/7 recomputed; cleanup PASS; blockers [] |
| Evidence head | `38458622212` (SUCCESS) | head `07215cf4…` / merge-ref `5cddfc0e…` parents `[43720843…, 07215cf4…]`, tree `ff0f8d4e…` == EVIDENCE tree | `115507683282` | `b1-i1r-evidence-8a6a6b1c1c68` (`11843854782`, 33759 B) | B5-I5 24/24, 0/0/0, floor 22; I4 23, I3 51, I2 24; regression 67/0; adversarial 49/49; static final 35/35; manifest 7/7 recomputed; cleanup PASS; blockers [] |
| R5 repair head | `38581001417` (SUCCESS) | head `57cb37cf3…` / merge-ref `c1ccc9e4…` parents `[43720843…, 57cb37cf3…]`, tree `86ca1204…` == R5 tree | `115910565848` | `b1-i1r-evidence-1a5935484d53` (`11903980928`, 35117 B) | B5-I5 **45/45**, 0/0/0, floor 22, dups 0, orphans 0, problems []; I4 23, I3 51, I2 24 (repro battery ALL_DISCRIMINATED 11/11); regression 67/0; adversarial 49/49; static initial 31/31 + final 35/35; manifest 7/7 recomputed; cleanup PASS; blockers []; gate READY_FOR_OPERATOR_REVIEW; cost $0 |
| R6 correction head | `38582520500` | head `f1e33cf8…` | (see PR) | (see PR) | verified before ratification commit (recorded in PR §RATIFY) |
| Ratification head | *this commit's CI — cannot be contained in this artifact (same limitation recorded by B5-I2/B5-I3 artifacts); run/check-run/artifact IDs recorded append-only in PR #15 `B5-I5 RATIFICATION` and re-verified pre-merge* | | | | |

Merge-ref second-parent and tree bindings above were proven live from git
objects (GitHub git-commit API) and match each rung's exact head/tree; every
manifest was recomputed from independently downloaded bytes (SHA-256 + size),
7/7 exact, 0 mismatches.

## 9. Exact scenario/check table and reproducibility disposition

| Metric | Value |
|---|---|
| §11 scenarios executed | **10** (not 17; "17 checks"/"17-scenario" superseded — evidence record §7.3) |
| Enumerated conditions | **35** (34 recorded-JSON + 1 committed-suite external); **35/35 true** in the witness run and again in the post-repair witnessed re-run |
| Harness hard assertions | 4 statements (6 atoms) in `driver.py`; none in the other harness files |
| Process roles / instances | 3 roles; 6 instances (1 driver, 2 stack, 3 console) |
| Submit POSTs / jobs / denials / malformed refusals | 3 (2 governed + 1 denied) / 2 / 1 / 1 (0 POST) |
| Restart events / recovery transitions | 2 (1 console-process, 1 engine) / 1 engine requeue, `leased → running → pending → succeeded` |
| Reproducibility classification | **B — witnessed, non-reproducible local demonstration.** The harness is uncommitted scratch and is never named as a reproduction vehicle; every load-bearing claim maps to committed test nodes (evidence record §7.4) or is marked witness-only (socket audit, 3-process topology) |

## 10. Final audit scores (same-agent, NOT independent)

SPEC **9.5** (D1 −0.5) / DESIGN **9.5** (D2 −0.5) / CORRECTNESS **8.5**
(D3 −0.5, D4 −0.5, D5 −0.5) / QUALITY **9.5** (D6 −0.5);
**(9.5 + 9.5 + 8.5 + 9.5) / 4 = 37 / 4 = 9.25 / 10**.
One root cause = one deduction; no double-count; no deduction merely for the
existence of repair rungs; no restoration for repaired defects. Full register
and arithmetic: evidence record §7.1/§7.7; supersedes the earlier 9.875.

## 11. Exact heads

- **Authorized base:** `43720843b2f4c9a59044fd9d462edb0fe3b338b6`
- **Final implementation head (last production rung):** `57cb37cf3b9d36ee8fd2d266b1d46533cab1ad30` (R5, tree `86ca12046fbfb06006f39cd3b01a36a9a137bdff`)
- **Evidence head:** `07215cf41ea2ab22c6bc28dbfb700dd90145628f` (tree `ff0f8d4e021234572964ed68d69a5ba70f8dfa3f`)
- **Evidence-correction head:** `f1e33cf8ea65b7c7ae7a24e0f7f236293eb4ea54` (tree `1efd687538974e38dd86396ef4c2406694c9edeb`)
- **Ratification head:** this commit (parent = R6 head; SHA not self-embeddable — recorded append-only in PR #15 `B5-I5 RATIFICATION` with its exact-head CI run/check-run/artifact IDs, and re-verified as merge parent 2 at §18 post-merge)

## 12. Local validation summary (Windows host, §11 of the mission)

B5-I5 suite 45/45 green; B5 selection (I2+I3+I4+I5+contracts) 159 passed;
full suite `32 failed, 998 passed, 103 skipped` with the 32-failure node-ID
set **byte-identical at the exact authorized base and at R5/R6** (`diff`
empty — all 32 are pre-existing Book-4 environmental failures); Ruff clean on
all touched Python; compile clean; JSON/YAML parse clean (CI re-proves 11/11
and 30/30); `git diff --check` clean; secret scan clean; B5-I2 mutation
harness `ALL_DISCRIMINATED` in CI; 12/12 B5-I5 weakened controls executed
independently with red demonstrations and byte-identical restore.

## 13. Limitations

1. Same-agent audit — not organizationally independent.
2. 32 Book-4 Windows-environmental failures, byte-identical at base/head;
   authoritative Linux CI has zero mandatory skips.
3. Engine canonical store is in-memory at this stage; restart starts empty
   and stale reads refuse fail-closed; durable restart = B4/Postgres domain.
4. Plain HTTP inside the literal loopback boundary; mid-read collapse to
   `STACK_UNREACHABLE` (carried B5-I4 limitation).
5. E2E is a witnessed, non-reproducible local demonstration (classification B).
6. PR body identifier corrections (P0 tree mistype; P0 commit SHA mistype;
   "17 checks" phrasing; 11-paths count) are superseded append-only there and
   authoritatively here / in evidence record §7.8.
7. This ratification commit's own CI run ID cannot be contained in this
   artifact; it is recorded in PR #15 and verified before merge.

## 14. Accounting

Cloud mutations: 0. External hosting: none. External network: zero.
Recurring cost: `$0`. `capital.authority = none`. Broker/execution: none.
LLM authority: none. Freebuff untouched. Frontend/Book 4/Sensor Fabric/
providers: 0-line diff. PR #15 merged only as a normal two-parent merge
commit (no squash, no rebase, no force; branch retained).
**B5-I6–I9 remain `LOCKED`; this artifact does not unlock them.**
