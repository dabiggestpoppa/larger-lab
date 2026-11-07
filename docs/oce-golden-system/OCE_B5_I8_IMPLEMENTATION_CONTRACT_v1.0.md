# OCE Golden System
## B5-I8 — Implementation Contract (P0) — v1.0

**Document ID:** OCE-B5-I8-CONTRACT-001
**Version:** 1.0
**Status:** `P0_OPERATOR_ACCEPTED — PLANNING FROZEN` (ratified 2026-11-05; see `OCE_B5_I8_OPERATOR_RATIFICATION_v1.0.md`) — **planning only. No implementation gate has passed.**
**Stage:** `AUTHORIZED_STAGE=B5-I8-P0-RATIFICATION`
**Base SHA (authoring):** `7393228dd4b21be9440785204ea9e640800d5d95` (= `origin/main` when the packet was written)
**Ratification base (corrected main):** `74fee0f086f9215bf6b93a1b3adbf1d69406da39` (= live `origin/main` at acceptance)
**Registry:** `OCE_B5_I8_REQUIREMENT_TEST_REGISTRY_v1.0.json` (`OCE-B5-I8-REGISTRY-001`, 55 entries)
**Merge authority:** `MERGE_AUTHORIZED=true` **for the P0 ratification PR only**; the implementation rung and every later rung remain `MERGE_AUTHORIZED=false` until separately authorized.
**Accounting:** recurring cost `$0` · `capital.authority = none` · Freebuff untouched · `B5-I9 = LOCKED` · Book 6 `UNAUTHORIZED`

---

## 1. Stage identity (source-backed, not inferred)

| Field | Governing source | Exact text | Meaning frozen here |
|---|---|---|---|
| Official stage name | Block 5 plan §7, row `B5-I8` | *"Independent E2E, adversarial, usability and evidence audit"* | An **audit increment**, not a build increment |
| Stage gate | Block 5 plan §7, same row | *"Zero critical bypass or false claim"* | The stage's own exit gate is a verdict about absence of bypass and absence of false claim |
| Registry entry owned | B5-I3 construction plan §5 (`### B5-I8 — independent audit`); B5-I3 registry `G16` | *"Registry entries owned: G16 (usability protocol/results)"* | B5-I8 closes exactly one inherited gate, `G16` |
| Frozen planned node | B5-I3 construction plan §8; B5-I3 registry `G16.deferred.planned_node` | `infrastructure/control-plane/tests/test_b5_i8_independent_audit.py::TestUsabilityProtocol::test_accessibility_and_usability_verified` | This exact node id is inherited and must be created verbatim |
| Inherited deferral | B5-I7 contract §20 `B5I7-DF02` | owner **B5-I8**, future stage `B5-I8`, reason: plan §7 assigns usability to the independent audit increment | The `G16` obligation is received, not re-derived |
| Human-evidence basis | Block 5 plan §4 `B5.C2.S5`; B5-I3 contract §2 | *"Every requirement has executable or explicit human evidence"* | Usability may carry explicit human evidence; it may not be replaced by a self-assessment |

### 1.1 Cross-numbering, stated explicitly

The three numbering systems in this program diverge, and B5-I8 is where the divergence is easiest to get wrong.

| Number | What it actually is | Where it was executed | Relation to B5-I8 |
|---|---|---|---|
| Charter `I-7` (optional) | Loopback **web view**, only if the operator directs it | Anchored to plan `B5-I6`; **never executed**; owner = Operator | **Not** B5-I8 work. Carried as `B5I7-DF01`; remains operator-directable, unscheduled |
| Charter `I-8` (optional) | **Governed change + observability demonstration** | Executed as stage `B5-I7` (ratified, merged) | **Already consumed.** B5-I8 does not inherit it and must not restate it |
| Plan `B5-I8` | **Independent E2E, adversarial, usability and evidence audit** | This stage | The stage under this contract; **has no charter increment row of its own** |

Consequences frozen here:

1. `B5-I8 ≠ "build the web dashboard"`. Nothing in the corpus authorizes B5-I8 to create a web surface.
2. B5-I8 has **no** charter increment; the registry therefore records `charter_increment: null` with an explicit note, rather than inventing `I-8`.
3. The charter's increment ceiling (6 required + up to 2 optional = never more than 8) is already fully accounted for: `I-1…I-6` required, `I-7` and `I-8` optional. B5-I8 adds **no** increment and cannot raise the ceiling (Gate `G17`).
4. B5-I8's only inherited registry obligation is `G16`. Its audit obligations are the plan §7 row's four audit axes, which are not charter gates.

## 2. Source-to-claim audit (dispositions)

Every scope claim in this packet traces to one row below. Where two sources could be read as conflicting, the resolution is recorded here rather than decided by preference.

| # | Proposed claim | Governing document and row | Literal supported meaning | Inferred meaning | Conflict / cross-numbering | Disposition |
|---|---|---|---|---|---|---|
| S1 | B5-I8 is an audit stage | Block 5 plan §7 | "Independent E2E, adversarial, usability and evidence audit" | none needed | charter `I-8` is a different, already-executed increment | **ADOPTED** |
| S2 | B5-I8 is not the web view | Charter §12 row `I-7`; §8.2; B5-I7 contract §4.1; B5-I6 gap contract §5 | web view is optional, operator-directed, anchored to `B5-I6` | none | `test_b5_i7_web_view.py` prefix looks like a B5-I7 deliverable; it is not | **ADOPTED** — web view refused |
| S3 | B5-I8 closes `G16` | B5-I3 plan §5; B5-I3 registry; B5-I3 ratification | owner `B5-I8`, one planned node | none | none | **ADOPTED** |
| S4 | B5-I8 audits E2E | plan §7 row `B5-I8` | "Independent E2E … audit" | re-execution of the governed end-to-end path | none | **ADOPTED** |
| S5 | B5-I8 audits adversarially | plan §7 row `B5-I8`; charter §11 `G15` | "adversarial … audit"; negative controls prove bypass detection | none | none | **ADOPTED** |
| S6 | B5-I8 audits evidence | plan §7 row `B5-I8`; charter §11 `G9`; B5-I6 X1 lessons (ledger §17.12–§17.13) | "evidence audit"; identities bind to the correct operation and commit | citation resolution over prior stages | none | **ADOPTED** |
| S7 | Usability = comprehension evidence, not a UI | plan §6 `C5.S3` (*"Test operator comprehension of state, approval, failure, evidence and recovery"*); charter §11 `G16` | a protocol plus recorded results | a scripted operator task set over existing surfaces | `G16`'s own wording says "accessibility and operator usability", which could be read as demanding a browser UI | **ADOPTED with limit** — accessibility is verified over the surfaces that exist (CLI text + read-only panel document), never over a surface B5-I8 may not create |
| S8 | No production code may change | plan §7 row `B5-I8` gate; charter §5 authority law; B5-I7 contract §4.3 | the audit must not become a repair or a build | new tests + evidence docs only | none | **ADOPTED** |
| S9 | No new endpoint / contract-pack change | charter §8.4; B5-I7 contract §3 non-goals; `contracts/console-contract.json` byte-frozen | prohibited without a fresh operator-ratified scope change | none | none | **ADOPTED** |
| S10 | No `oce/frontend` modification | charter §6 (*"`oce/frontend` remains internally owned and is not modified at B5-I1"*) and §8.2 deferral; B5-I4/I-5/I-6/I-7 scope contracts | no frontend change has ever been authorized | a future increment might | none | **ADOPTED** — prohibited |
| S11 | No external hosting / telemetry / cloud | charter §6; `A003_LOCAL_FIRST_CLOUD_DEFERRAL`; plan §9 | local-only, no paid provider, no telemetry without separate authorization | none | none | **ADOPTED** |
| S12 | No browser-side canonical state | charter §5 rules 5–9 | UI state is never canonical state | none | none | **ADOPTED** |
| S13 | `B5-I9` is out of scope | plan §7 row `B5-I9`; plan §6 `C5.S5`; B5-I7 contract §4.2, §20 `B5I7-DF03` | factory gate + B6 reusable-extraction contract, operator-only completion | none | none | **ADOPTED** — deferred to `B5-I9` |
| S14 | Book 6 is out of scope | Block 6 plan §1, §7 | extraction of B5-proven reuse; build locked | none | none | **ADOPTED** — `UNAUTHORIZED` |
| S15 | Post-Book-6 evaluation is a separate future phase | Block 6 plan §3 `B6.C3.S5` (evaluation service) | an evaluation service is a Book 6 shared service | blind/organizational evaluation is not a Book 5 stage | none | **ADOPTED as future phase**, not B5-I8 acceptance |
| S16 | Same-agent audit is not independence | B5-I7 evidence law `EL13`; B5-I7 ratification §6 | same-agent audits must be labelled | none | plan §7 calls the audit "independent" | **RESOLVED**: "independent" is satisfied only by an audit **operator-distinct** from the implementer; this P0 packet cannot supply that and says so (see §11.7) |

No material conflict was found that requires a stop. The one genuinely ambiguous word — *independent* in plan §7 — is resolved by disclosure rather than by relabelling: organizational independence is carried as a deferred obligation (`B5I8-DF05`), and every score in this packet is explicitly `SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`.

## 3. Scope freeze

| Field | Frozen value |
|---|---|
| Stage purpose | Independently audit the B5 reference application across four axes — end-to-end, adversarial, usability (`G16`), evidence — and record a verdict of *zero critical bypass or false claim* |
| Operator outcome | One legible audit verdict, recomputable from committed evidence, plus a recorded usability/comprehension result and a list of residual risks — with no production surface changed |
| Allowed surfaces | new files `infrastructure/control-plane/tests/test_b5_i8_*.py` (exactly five planned files, §8); new documents under `docs/oce-golden-system/`; one **additive** CI selection step at the implementation stage; append-only ledger sections |
| Prohibited surfaces | `infrastructure/control-plane/src/**`; `infrastructure/control-plane/contracts/**`; `infrastructure/console/**`; `oce/frontend`; any existing test file; `.github/workflows/**` before the authorized implementation rung; provider/cloud/hosting/telemetry config; `test_b5_i7_web_view.py`; any B5-I9 or Book 6 artifact |
| Canonical state owner | the control-plane engine alone (charter §5; unchanged by this stage) |
| Read/write authority | audit reads only; the audit may **not** write canonical state, and no audit artifact is canonical |
| Transport boundary | in-process calls to existing console/control-plane read interfaces; no new route, no new endpoint, no listening socket introduced by B5-I8 |
| Local-only boundary | loopback literals only (`127.0.0.1`, `[::1]`); no external network, no CDN, no provider |
| Deterministic kernel boundary | the eleven charter §7 kernel functions stay deterministic and LLM-free; the audit adds no kernel behavior |
| Usability evidence required | scripted operator task protocol + recorded comprehension results + explicit limitation labels (§11) |
| Accessibility evidence required | deterministic accessibility checks over the surfaces that exist (text rendering, refusal legibility, state labels), recorded as `G16` evidence; **no** browser-surface accessibility is claimed |
| Recovery behavior | the audit is restartable and additive; a crashed audit run leaves no canonical change; re-running produces byte-identical verdict inputs |
| Failure behavior | every audit refusal is explicit; unknown ≠ zero, partial ≠ success, denied observable, unreachable fails closed (§9 failure matrix) |
| Evidence requirements | registry-bound nodes, exact-head CI artifact, parsed JUnit/collect, manifest, cleanup proof, verdict recomputation |
| Cost boundary | recurring cost `$0`; no paid provider; no cloud mutation |
| Stop conditions | contract §18 (nine stops) |
| Deferred items | `B5I8-DF01`…`DF05` (§19) |
| Future-stage owners | Operator (web view), `B5-I9` (factory gate + B6 extraction contract), Book 6 (`UNAUTHORIZED`), post-Book-6 evaluation phase, organizationally independent audit |

## 4. Web-view disposition (explicit)

**Disposition: C — B5-I8 proves usability without implementing the web view; the web view itself remains option B (separately operator-directable).**

| Question | Frozen answer | Source |
|---|---|---|
| Is the web view authorized inside B5-I8? | **No.** No document anchors `I-7` to `B5-I8`; plan §7's B5-I8 row names audit axes only | charter §12 row `I-7`; plan §7 |
| Who owns it? | **Operator** | charter §12; B5I7-DF01 |
| Future stage | *operator-directable, not scheduled* | B5-I7 contract §20 |
| Authorized filename, if ever directed | `infrastructure/control-plane/tests/test_b5_i7_web_view.py` — the frozen planned node string | B5-I3 plan §8; B5-I3 registry `G1`/`G2` |
| Reserved-prefix treatment | The prefix stays **reserved and unused**. B5-I8 asserts its absence, exactly as B5-I7 did | B5-I7 contract §4.1 |
| Collision/debt treatment | The prefix is a permanent naming debt of the frozen B5-I3 text; it is disclosed, not renamed | B5-I3 plan §8 (frozen) |
| Do existing frozen B5-I3 references constrain the name? | **Yes** — the planned-node string is frozen and `TestDeferredOwners` asserts registry↔plan agreement, so the name cannot be changed without editing frozen B5-I3 artifacts | B5-I3 contract §5 `TestDeferredOwners` |
| Must a future implementation use another filename? | **No.** The operator-directed stage must create exactly the frozen file, which is precisely why B5-I8 must not create it | B5-I3 plan §8 |
| Can the prefix be repaired without editing frozen history? | **No.** Repair would require editing frozen B5-I3 plan/registry text; it is therefore impossible under append-only law and is recorded as permanent debit | B5-I7 contract §4.1, §18.8 |

Consequence for this packet: `B5I8-R03` is a **static** requirement asserting the file's absence, and `B5I8-DF01` carries the obligation. B5-I8 does not create the web view, its tests, a mock of it, or a "preview" of it.

## 5. Boundaries

| Boundary | Frozen statement |
|---|---|
| `B5-I9` | Factory gate + B6 reusable-extraction contract (`C5.S5`), operator-only completion. B5-I8 may **not** decide reusable extraction, author correction ADRs, or draft the B6 contract. Deferred as `B5I8-DF02` |
| Book 6 | Reusable platform surfaces (API/SDK/templates/shared services). `UNAUTHORIZED`; no Book 6 document may be authored here. Deferred as `B5I8-DF03` |
| Post-Book-6 evaluation | A separate future phase (Book 6 `B6.C3.S5` evaluation service + blind/organizational evaluation). **Not begun.** Deferred as `B5I8-DF04` |
| Organizationally independent audit | Not supplied by B5-I8's own author. Deferred as `B5I8-DF05` |

## 6. Inherited laws (preserved, not restated as new)

frontend/console is a client and never a second authority · canonical state stays engine-owned · browser/client storage is non-authoritative · no silent success · unknown is not zero · partial is not success · denied is observable · unreachable fails closed · no external hosting · no external telemetry · loopback/local-only · no capital authority · no broker authority · no execution authority · no platform extraction · cost `$0`.

B5-I8 **verifies** these; it does not re-implement, re-declare, or relax them. A finding that any of them is already violated is a defect for the implementation stage to report, not a license to change production code inside B5-I8.

## 7. Registry law and arithmetic

- Registry id `OCE-B5-I8-REGISTRY-001`, version 1.0, **55 entries**.
- Allowed states: `PLANNED`, `MAPPED`, `DEFERRED_WITH_OWNER`, `BLOCKED`. Allowed binding types: `test`, `static`, `runner`, `attestation`, `deferred`.
- Every requirement is bound exactly once; ids are unique; no `PASS` claim exists at P0.
- Frozen distribution: kinds — identity 3, boundary 4, e2e 4, adversarial 10, usability 7, evidence_audit 6, measurement 4, gate 4, evidence_law 8, deferred 5 (= 55). Bindings — test 40, attestation 7, static 3, deferred 5 (= 55). States — `PLANNED` 40, `MAPPED` 10, `DEFERRED_WITH_OWNER` 5, `BLOCKED` 0 (= 55).
- The count was **not** chosen to resemble B5-I7's 44; it is the count the four audit axes plus `G16`, the inherited laws, eight audit evidence laws and five deferred obligations actually produce.

## 8. Planned test inventory (40 nodes, 5 files)

| File | Nodes | Axis |
|---|---|---|
| `test_b5_i8_e2e.py` | 4 | end-to-end re-execution |
| `test_b5_i8_adversarial.py` | 10 | adversarial / hostile / negative controls |
| `test_b5_i8_independent_audit.py` | 8 | `G16` node, evidence audit, gate closure |
| `test_b5_i8_usability_measurements.py` | 10 | usability protocol + measurements |
| `test_b5_i8_evidence_laws.py` | 8 | evidence laws `EL01`–`EL08` |

The exact node list is frozen in the registry (`requirement_set.planned_test_nodes`) and reproduced in the acceptance matrix. Laws:

- zero skip / xfail
- collection == execution
- node ids unique
- no orphan B5-I8 test file
- no orphan registry node
- focused floor **40**

`test_b5_i8_independent_audit.py` must contain the inherited `G16` node id **verbatim**: `TestUsabilityProtocol::test_accessibility_and_usability_verified`.

## 9. Failure taxonomy

Closed taxonomy of **18** classes, frozen in `OCE_B5_I8_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md` §2 with trigger, affected requirement, expected state, observable output, forbidden response, recovery owner and planned proof per class. No class is invented beyond the authorized audit scope; no authorized hostile trigger is left uncovered.

## 10. Mutation plan

Floor **12** mutations, each weakening a load-bearing law (client authority, truth collapse, redaction, bounds, determinism, loopback, accessibility semantics, evidence self-reference). Frozen in the failure/recovery plan §4. **Not implemented at P0.**

## 11. Usability and measurement contract

| Layer | What it is | Evidence class |
|---|---|---|
| Executable correctness gates | the 40 planned nodes | deterministic test |
| Observable operator-task measurements | completion, error, time-to-first-useful-state, navigation steps, refusal/recovery comprehension | measured (`OBSERVED` only after execution) |
| Accessibility checks | deterministic text/legibility/state-label checks over existing surfaces | deterministic test |
| Subjective operator review | free-text operator impressions | `SUBJECTIVE` — never a gate |
| Same-agent audit | this packet's §21-style audit | `SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT` |
| Organizationally independent evaluation | an auditor distinct from the implementer | **not available in B5-I8** (`B5I8-DF05`) |
| Post-Book-6 blind evaluation | blinded instrument, Book 6+ | **not begun** (`B5I8-DF04`) |

P0 labels only: `EXPECTED`, `FLOOR`, `CEILING`, `NOT_YET_OBSERVED`. Two values in this packet are genuinely `OBSERVED` because this mission measured them: the adjacent population (**189** nodes, recomputed) and the base SHA. No usability metric is `OBSERVED` — none has been executed.

## 12. Validation architecture (frozen)

Implementation head and evidence head are separate and named explicitly; merge-ref identity and post-merge truth are recorded only after observation; exact-head CI binding, artifact schema, JUnit schema, registry proof schema, manifest schema, cleanup schema, mutation schema and usability/accessibility evidence schema are frozen in `OCE_B5_I8_CONSTRUCTION_PLAN_v1.0.md` §6. Adjacent floor **189** (`OBSERVED`, this mission) replaces the inherited 186 (which was a different, 9-file selection); `common_nodes == 0 => FAIL`.

## 13. Carry-forward B5-I7 limitations

Frozen in `OCE_B5_I8_CONSTRUCTION_PLAN_v1.0.md` §7, with one disposition per limitation. No frozen B5-I7 artifact is edited to address any of them.

## 14. Deferred obligations

`B5I8-DF01` web view → Operator · `B5I8-DF02` factory corrections / B6 extraction → `B5-I9` · `B5I8-DF03` Book 6 → Book 6 · `B5I8-DF04` post-Book-6 blind evaluation → future phase · `B5I8-DF05` organizationally independent audit → Operator.

## 15. Stop conditions

`STOP-1` a production/frontend/contract file must change to make the audit pass · `STOP-2` the web view is required to satisfy `G16` · `STOP-3` a B5-I9 or Book 6 decision is needed · `STOP-4` a new endpoint or contract-pack change is needed · `STOP-5` the frozen `G16` node id cannot be created verbatim · `STOP-6` an audit finding is a critical bypass of authority (report, do not repair) · `STOP-7` an evidence value is untraceable to a raw source · `STOP-8` an external/paid dependency is required · `STOP-9` scope exceeds the charter ceiling or this contract.

## 16. P0 validation

Deterministic local validation proved: all five artifacts present; JSON canonical and parseable; 55 unique ids; binding and state closure; zero `PASS` claims; deferred-owner closure; 40 unique nodes; file/node arithmetic; category arithmetic; failure-class coverage; acceptance cross-references resolve to real registry ids; LF line endings; no implementation/test/workflow/provider file changed; `git diff --check` clean; exact changed-file boundary. The validator was **ephemeral** (not committed), therefore this packet makes **no** claim that it is retained reproduction tooling; the concrete results are recorded in ledger §19.

## 17. Locks and accounting

`B5-I8 = P0_OPERATOR_ACCEPTED — PLANNING_FROZEN` · `B5-I9 = LOCKED` · Book 6 `UNAUTHORIZED` · post-Book-6 evaluation not begun · `MERGE_AUTHORIZED=true` (scope: P0 ratification PR only) · recurring cost `$0` · `capital.authority = none` · no broker/execution authority · Freebuff untouched · no external hosting or telemetry · no history rewrite.

## 18. Exit state

```
B5_I8_STAGE_IDENTITY = plan §7 "Independent E2E, adversarial, usability and evidence audit"
B5_I8_CHARTER_INCREMENT = NONE (charter I-8 was consumed by B5-I7; charter I-7 is the operator-owned web view)
B5_I8_WEB_VIEW_DISPOSITION = C (usability proven without the web view; web view remains operator-directable, unscheduled)
B5_I8_P0 = OPERATOR_ACCEPTED_PLANNING_FROZEN
B5_I8_IMPLEMENTATION_AUTHORIZED = FALSE
B5_I9 = LOCKED
BOOK_6 = UNAUTHORIZED
POST_BOOK_6_EVALUATION = NOT_BEGUN
MERGE_AUTHORIZED = TRUE_FOR_P0_RATIFICATION_PR_ONLY
CAPITAL_AUTHORITY = NONE
RECURRING_COST = $0
```

---

## 16. Amendment 001 — CI selection surface (operator-ratified 2026-11-06)

Superseded clause: plan §1 rung **R6**'s allowed-file column
(`.github/workflows/b1-i1r-validation.yml`, additive only) and its artifact name.
Reason: B5-I7's EL09 superseding manifest pins that file as a **whole-file** immutable
row, so adding the selection step changes its bytes and turns
`TestEL09::test_manifest_rows_recomputed_hash_and_size` red (reproduced: 26/27).

Disposition: `SUPERSEDED`, not satisfied. The selection surface is the dedicated
additive workflow `.github/workflows/b5-i8-audit-validation.yml`, which triggers on the
same `pull_request → main` event class as the pinned workflow, runs on the same head and
merge context, holds `permissions: contents: read` only, and performs the identical
fail-closed selection (five files, floor 40, collection == execution, zero
fail/error/skip, unique ids, registry node closure, orphan refusal). The pinned workflow
stays byte-identical and continues to emit `b1-i1r-evidence-<run_id>` on the same head;
the dedicated workflow emits `b5-i8-evidence-<run_id>`.

Not changed by this amendment: the 55 requirements, 40 nodes, 18 failure classes, 12
mutation floor, floors 40/189, triggers, identity rules, artifact retention, cleanup
rules, authority boundaries, `G16` disposition and every limitation label.

Full text: `OCE_B5_I8_AMEND_001_CI_SELECTION_SURFACE_v1.0.md`.
