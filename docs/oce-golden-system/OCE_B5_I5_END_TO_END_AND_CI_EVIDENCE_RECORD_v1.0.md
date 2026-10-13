# OCE B5-I5 End-to-End and CI Evidence Record — v1.0

**Document ID:** OCE-B5-I5-E2E-CI-EVIDENCE-001
**Version:** 1.0 — append-only evidence record for `AUTHORIZED_STAGE=B5-I5`
**Authorized base:** `43720843b2f4c9a59044fd9d462edb0fe3b338b6` (B5-I4 merge of PR #14)
**Implementation head:** `ffccf5c3d9b5dabffaf9f8037cf168dd14ea3825` (tree `2ab70be70e745c7e3150759f298bf289a723c691`)
**PR:** #15 (draft, `NOT MERGE AUTHORIZED`; B5-I6–I9 remain `LOCKED`; `MERGE_AUTHORIZED=false`)

---

## 1. Commit ladder (complete, append-only, no rewrites)

| Rung | Commit (full) | Tree (full) | Subject |
|---|---|---|---|
| P0 | `aeda12deece94d50fb6ed98f8500d45b681a175f` | `3404d68e3bec3f293c5d68a8c48a78ccbb79b922` | B5-I5-P0: freeze governed submission + dual-clock timeline + evidence-bound drill scope |
| R1 | `c9e6afae7ebbcce4eab146bb8b433a98e9de83d4` | `26c6467ce82a9a15850e5721eb3d0499b6759d87` | governed catalog-bounded submission and contract-mediated job read (+ Amendment A1) |
| R2 | `bfacf1d9c07f5081f2b8134131a0a6f111dcc9e0` | `f317e959b2eed1e6a10da880a2138402ba12062f` | dual-clock timeline with F-3 failure envelope and evidence binding |
| R3 | `2c8cdaa8815ec9a3a1dff3883d98cd8dbb4c8354` | `3b02671ae77f3ed3c7b08dc67e68b4aafe902c1e` | versioned drill session, engine-owned recovery view, duplicate-effect |
| R4 | `ffccf5c3d9b5dabffaf9f8037cf168dd14ea3825` | `2ab70be70e745c7e3150759f298bf289a723c691` | executable proof suite (24 nodes) and authoritative selection |

**Identifier correction (disclosed):** the PR body §4 table (created before this record)
mistyped the P0 tree as `5877be485881b6b8c0dcf2931a43e869f284476a`. The true P0 tree is
`3404d68e3bec3f293c5d68a8c48a78ccbb79b922` (verified by `git log --format=%T` on the
committed object). The PR body is append-only; a correction note was appended to it.
No commit, history, or proof depends on the mistyped value.

## 2. End-to-end evidence (real operator path, three processes, zero mocks)

Topology: one orchestrating driver process; the **real engine stack** as a subprocess
(`ControlPlane` = JobStore/Authority/Scheduler/WorkerProtocol/EvidenceBuilder/
RecoveryCoordinator + the frozen FastAPI app over a real loopback socket, uvicorn,
ephemeral port); the **console operator** as a separate subprocess using ONLY the
`oce_console` package over governed HTTP. The driver↔stack engine-harness channel is
stdin/stdout JSON process control (NOT an HTTP surface; the console cannot see it).
Grant minting is engine-owned (`plane.authority.issue_grant` in the harness); the
console only ever receives authority.

Harness artifacts (uncommitted temp artifacts; hashes recorded for reproducibility):

| Artifact | SHA-256 |
|---|---|
| `stack.py` (engine stack subprocess) | `b1bbf004b6b786f1135f2eb89ecf57c41e2cc001c9599e8451aebda43a49bc16` |
| `console_op.py` (console operator subprocess) | `e159fb7d841bdc5f3a75d05949655e86ec80e2b2dab97d8dfd360353ced9ab2b` |
| `driver.py` (orchestrator) | `32a91db6c0318b0c29f40027d7c90cb0299a09ed8c403928c6da378987a48d04` |
| `b5i5-e2e-evidence.json` (captured evidence, 6210 bytes) | `69b33bd479d44981a7802a70a2be222c16fa26b70aec6f78918117a0462fe548` |

Command: `python driver.py <worktree-root>` (Windows host, Python 3.11.9,
fastapi 0.136.1, uvicorn, pytest 9.0.3).

### 2.1 Scenario results (all 17 checks PASS; deterministic payload hash reproduced across separate runs)

| # | §11 scenario | Exact result |
|---|---|---|
| 1 | Primary successful outcome | Governed submit → job created; engine-minted `payload_hash` `33d62e9cb39a664c33629e3265b8dc4725ed14a08303bb7034d73f89db22a29e`; console POST count after first submit = 1 |
| 2 | Deterministic repeated execution | Second identical submit → identical engine-minted `payload_hash` (`identical_engine_minted_hash: true`); timeline render byte-deterministic (`render_deterministic: true`) |
| 3 | Denied authority | Tampered grant → `status: denied`, full denial envelope rendered verbatim (`reason_code: missing_authority`, `denial_id: bb4ee1892d1f3d7fb48be21a2d70ba76`, `denied_at` from engine clock), exactly **1** POST for the denied attempt, zero store traces |
| 4 | Malformed input | Out-of-catalog `job_type` → `ConsoleRefusal(reason=unsupported_job_type)` before any I/O |
| 5 | Unavailable dependency | Engine stack killed mid-session → console read collapsed to `StackUnreachable` (`collapsed: true`), never false success |
| 6 | Mid-operation failure + recovery | Engine-side: worker loss (heartbeat stale, lease past 60s TTL) → `recover_abandoned_leases()` requeued **1** job (engine-owned, G8); console observed `leased → running → pending → succeeded` and enacted nothing |
| 7 | Restart/recovery | Console-process restart (fresh clients): authoritative view **byte-identical** (`identical_authoritative_view: true`, state `succeeded`, attempt 1). Engine restart (fresh stack process): stale job read **refused fail-closed** (`read: false, refusal: not_found`) — never empty success, never guess |
| 8 | Hostile negative control | Weakened implementations executed red in the suite (§4); E2E denial envelope proves forged grants cannot become degraded success |
| 9 | Zero unauthorized mutation | Total console POSTs = **3** (2 governed submits + 1 denied attempt); engine store at end = exactly **2** jobs (`9f571498…` succeeded, `cfba33c5…` pending); denied + malformed left zero traces |
| 10 | Zero external network | Socket-audited `connect()` in the console process: 7/7 connects to `127.0.0.1` (fresh processes likewise); any non-loopback connect is blocked and would fail the run |

Drill report: `disposition: DRILL_PASS`, `duplicate_effect_check: true`,
`engine_payload_hash_matches_binding: true` (G9 two-sided agreement), session record
schema-validated before emission.

## 3. Implementation-head CI (§10) — parsed artifact, not the badge

- Run `38453887983` (`b1-i1r-validation`, event `pull_request`, ref `15/merge`);
  terminal status **completed | success**; validate job `115491489488` ✓ in 6m52s.
- Head identity: run head SHA `ffccf5c3d9b5dabffaf9f8037cf168dd14ea3825` == implementation head;
  the tested checkout was the PR merge-ref (`26f94a587762b03fa88a42518149402fe6366087`)
  whose **tree `2ab70be70e745c7e3150759f298bf289a723c691` == R4 tree** (verified
  independently: `git rev-parse ffccf5c3d^{tree}` == `2ab70be7…`; and in-CI
  SOURCE-IDENTITY check recorded `tree=2ab70be70e74`).
- Artifact `b1-i1r-evidence-b90ca1c84e7b` downloaded and parsed:

| Gate | Parsed result |
|---|---|
| B5-I5 selection (`b5-i5-timeline-proof.json`) | verdict **PASS**; collected == executed == junit tests == **24**; failures 0; errors 0; skipped 0; duplicate node ids 0; duplicate junit ids 0; orphan `test_b5_i5_*.py` 0; floor 22 met |
| B5-I4 kernel (`b5-i4-kernel-proof.json`) | PASS; 23 tests, 0/0/0 (frozen suite unchanged) |
| B5-I3 registry (`b5-i3-registry-proof.json`) | PASS; 51 tests, 0/0/0 |
| B5-I2 contracts (`b5-i2-registry-proof.json`) | PASS; 24 tests, 0/0/0; reproducibility battery `control_green: true` |
| Shared regression (`regression-output.txt`) | **67 PASS, 0 FAIL** |
| Adversarial gate (`adversarial-results.json`) | **49/49 PASS** (25 meta + 24 negative), 0 fail |
| Static validation (`initial-validation-summary.md`) | **31/31 PASS**, 0 BLOCKED/SKIPPED; gate `READY_FOR_OPERATOR_REVIEW` |
| Manifest (`evidence-manifest.json`) | 7/7 artifacts **independently recomputed** (SHA-256 + size): 0 mismatches |
| Cleanup (`worktree-cleanup.json`) | `pruned: true, removed: true`; per-suite worktree checks clean |
| Stage gate (`stage-status.json`) | `READY_FOR_OPERATOR_REVIEW` |

Benign annotation disclosed: a `git exit 128` runner annotation from PR merge-ref
checkout mechanics; the job succeeded and every proof step passed (same pattern as
prior Book 5 runs).

## 4. Same-agent four-dimension audit (§12) — NOT organizationally independent

| Dimension | Score | Evidence |
|---|---|---|
| SPEC | **9.5/10** | Increment identity derived exactly from frozen authorities (plan §7, charter §12, ledger §12.1/§13, B5-I3 registry); every registry entry mapped with no orphan and no silent expansion; floor 22 and acceptance matrix frozen before results. −0.5: the P0 ceiling miscount (defect D1 below). |
| DESIGN | **10/10** | Reuse over parallel authority throughout (frozen pack binding, engine clock fields as event-time, engine `payload_hash` as evidence identity, engine-owned recovery); one canonical-state owner, one mutation boundary, one recovery law; the design audit (mission §5) ran BEFORE production code and surfaced the read-path necessity, which R1 solved additively with zero changes to frozen B5-I4 methods. |
| CORRECTNESS | **10/10** | 24/24 green in authoritative Linux CI with collected==executed==24, zero mandatory skips; adjacent B5-I2/I3/I4 suites unchanged-green (24/51/23); 17-scenario real end-to-end pass; executed negative controls; deterministic payload hash reproduced across independent runs; manifest independently verified. |
| QUALITY | **10/10** | Ruff clean, compile clean, client-only AST closure (stdlib-only, no `oce_control`), append-only ladder with no rewrites, documentation-only evidence commit. Pre-commit iteration (4 test-helper fixes, 15 lint findings, 6 E2E-harness fixes in uncommitted temp scripts) never entered a commit and required no repair rung. |

**Arithmetic:** (9.5 + 10 + 10 + 10) / 4 = **9.875 / 10**.

### 4.1 Defect register

| ID | Distinct defect/event | First bad rung | Repair rung | Residual consequence | Non-double-count |
|---|---|---|---|---|---|
| D1 | P0 scope contract froze "previously-existing files edited ≤ 2" while the increment's own S-2 requirement necessarily needed a third existing-file edit (additive `transport.py read_job`); caught by the mandated §5 design audit before any implementation commit | P0 (`aeda12dee`) | R1 (`c9e6afae7`, Amendment A1 + additive implementation) | None functional; ceiling corrected append-only to ≤3 with full disclosure | One event, deducted once (SPEC); DESIGN receives no second deduction for the same root cause |

**TRUE_DEFECTs in shipped repository code: none.** E2E-harness iteration (JobEnvelope
field shape, stdlib `operator` shadowing, action-scoped grant pairing, missing harness
keys, loopback-audit tuple parsing, restart-read `ok` check) occurred entirely in
uncommitted temp scripts before evidence capture and is disclosed here for
transparency; none reached a commit.

## 5. Limitations (permanent and stage-scoped)

1. **Same-agent audit** — not organizationally independent (stated on every Book 5 artifact).
2. **Local environmental failures** — 32 Book-4 control-plane tests fail on this Windows
   host; they reproduce **byte-identically at the exact base** `43720843` with the
   identical command/environment (failure-set diff: identical). Zero caused by B5-I5.
   Authoritative Linux CI: zero mandatory skips.
3. **Engine canonical store is in-memory** in the local topology; an engine restart
   starts empty and the console refuses stale reads fail-closed (`not_found`). Durable
   engine restart/recovery is the B4/Postgres domain, outside B5-I5 scope.
4. **`read_job` returns the raw governed response** (frozen B5-I4 transport convention):
   callers must check `ok` before feeding envelopes to `build_timeline`/`bind_evidence`.
   `bind_evidence` refuses envelopes without `job_id` fail-closed (demonstrated in E2E).
5. **Plain HTTP inside the literal loopback boundary**; mid-read failures collapse to
   `STACK_UNREACHABLE` (carried B5-I4 limitations, unchanged).
6. **E2E harness channel** is engine-test process control only — not an HTTP surface,
   not shipped in the repository; hashes recorded in §2.
7. **PR body identifier correction** — P0 tree mistyped in PR body §4; corrected
   append-only there and authoritatively in §1 of this record.

## 6. Accounting

Cloud mutations: 0. External hosting: none. External network: zero (socket-audited).
Recurring cost: `$0`. `capital.authority = none`. Broker/execution/order-routing: none.
LLM required/authoritative/state-owning: none. Freebuff untouched. Book 4, Sensor
Fabric, providers, hosting config: 0-line diff. B5-I6–I9 remain `LOCKED`;
`MERGE_AUTHORIZED=false`; no self-ratification; PR 15 stays draft and unmerged.
