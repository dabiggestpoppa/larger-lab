# OCE Golden System
## Book 5 — Progress and Evidence Ledger

**Document ID:** OCE-BOOK5-LEDGER-001
**Version:** 1.0
**Status:** ACTIVE LEDGER — initialized at B5-I0
**Governing authorities:** OCE Constitution 1.1; Master Program Atlas 1.0 (Block 5 — Reference Application Factory); Full Program Build Roadmap 1.0; Block 5 Reference Application Factory Plan 1.0 (`OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md`)
**Stage scope:** `AUTHORIZED_STAGE=B5-I1-CHARTER_RATIFICATION_AND_MERGE` (executed 2026-10-07; see decision history §4); the next stage requires a fresh `AUTHORIZED_STAGE=B5-I2`
**Build authorization:** None beyond documentation-only B5-I0/B5-I1 artifacts

---

## 1. Increment status

| Increment | Scope (per Block 5 plan §7) | Status | Gate / evidence |
|---|---|---|---|
| **B5-I0** | Freeze candidate criteria, risk ceiling and evaluation protocol | **OPERATOR_ACCEPTED** | Operator-ratified 2026-10-06 (protocol §10); this ledger's §2 evidence set; selection process frozen before any scoring |
| **B5-I1** | C1 compare/select/freeze application → operator-approved Product Charter | **OPERATOR_ACCEPTED** | Intake + evidence packets commit `52843ffc11ff97511ec7e7242f6adc7083290360`; AMEND-001 ratified (`f381ce0e…`) with both passes sealed (`b05c61d0…`, `8f5a06c9…`); reconciliation and decision packet published (`OCE_B5_I1_RECONCILIATION_v1.0.md`, `OCE_B5_I1_DECISION_PACKET_v1.0.md` — recommendation only); **operator selected CAND-004 (Local Job Console) 2026-10-07** on the adopted record (W 82.75; floors C1=3/C2=4/C3=3/C5=3; zero disqualifiers; zero UNKNOWN; reviews sequential, NOT independent, NOT blind per AMEND-001) — see decision packet §9; Product Charter drafted (`5b082164…`), audited (repairs `1534305778…`, `d4bb8e6064c3…`), and **ratified 2026-10-07** (`OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` → `OPERATOR_RATIFIED — FROZEN`; ratification artifact `OCE_B5_I1_OPERATOR_RATIFICATION_v1.0.md`). B5-I1 complete. B5-I2–I9 remain LOCKED; the next stage requires a fresh `AUTHORIZED_STAGE=B5-I2`; no implementation has begun
| B5-I2 | C2 outcome/domain/interfaces — charter increment I-1: console-control-plane deterministic interface contracts | **OPERATOR_ACCEPTED** — authorized 2026-10-07 under `AUTHORIZED_STAGE=B5-I2`; ratified 2026-10-08 under `AUTHORIZED_STAGE=B5-I2-AUDIT_REPAIR_AND_RATIFICATION` (§9; `OCE_B5_I2_OPERATOR_RATIFICATION_v1.0.md`) | Branch `oce-book-5-i2` created from exact merged main `882835dac…`; implementation contract frozen (`OCE_B5_I2_IMPLEMENTATION_CONTRACT_v1.0.md`): contract pack for every console-read/invoke surface (jobs, workers, leases, health, submit, denial) bound to existing governed control-plane operations and existing schemas (`job-envelope.schema.json`, `denial-envelope.schema.json`, `evidence-manifest.schema.json`); gate = contract tests pass on both sides; non-goals per charter section 12 I-1 (no console code, no UI, no new server endpoints) |
| B5-I3 | C2 failures/acceptance and construction plan | **LOCKED** | Requires B5-I2 complete |
| B5-I4 | C3 deterministic kernel and first vertical slice | **LOCKED** | Requires B5-I3 complete |
| B5-I5 | C3 complete build/tests/lineage/operator review | **LOCKED** | Requires B5-I4 complete |
| B5-I6 | C4 local deployment, observability and recovery | **LOCKED** | Requires B5-I5 complete |
| B5-I7 | C4 change cycle plus C5 measurements/learning | **LOCKED** | Requires B5-I6 complete |
| B5-I8 | Independent E2E, adversarial, usability and evidence audit | **LOCKED** | Requires B5-I7 complete |
| B5-I9 | Factory gate and B6 reusable-extraction contract | **LOCKED** | Operator-only completion; requires B5-I8 complete |

**Lock rule.** An increment may not begin without (a) the preceding increment's gate satisfied and (b) a fresh operator `AUTHORIZED_STAGE`. B5-I0 status changes only through operator review of this ledger. No increment above B5-I0 has been started, executed, or authorized by this mission.

## 2. B5-I0 evidence set

| # | Artifact | Document ID | Status | Role |
|---|---|---|---|---|
| 1 | Selection protocol (criteria, exact weights, freeze + amendment rules) | OCE-B5-I0-PROTOCOL-001 | OPERATOR_RATIFIED — FROZEN | Frozen selection process |
| 2 | Blank candidate scorecard template | OCE-B5-I0-SCORECARD-001 | OPERATOR_RATIFIED — FROZEN (BLANK) | B5-I1 instrument; no winner/score/selection |
| 3 | Risk ceiling and disqualifier register | OCE-B5-I0-RISK-REGISTER-001 | OPERATOR_RATIFIED — FROZEN | 14 mandatory disqualifiers, frozen |
| 4 | Evaluation and independent-review procedure | OCE-B5-I0-EVAL-PROC-001 | OPERATOR_RATIFIED — FROZEN | Blind dual scoring, dissent, COI controls |
| 5 | Book 5 progress/evidence ledger (this file) | OCE-BOOK5-LEDGER-001 | ACTIVE | B5-I0 OPERATOR_ACCEPTED; B5-I1–I9 LOCKED |
| 6 | B5-I0 acceptance matrix | OCE-B5-I0-ACCEPTANCE-MATRIX-001 | PASS — OPERATOR_RATIFIED | Requirement → artifact-section proof |

## 3. Stage integrity attestations (B5-I0)

| Attestation | Value |
|---|---|
| Selection rules frozen before any candidate scoring | YES — protocol v1.0 freeze statement; no candidate exists, named or unnamed |
| Candidates named / scored / selected in B5-I0 | 0 / 0 / 0 |
| Product scope frozen | NO — B5-I1 owns comparison + operator-approved Product Charter |
| Code implemented | NO — documentation only |
| `oce/frontend` modified | NO — internally owned, untouched |
| Book 4 evidence records appended/edited | NO — immutable historical evidence |
| Sensor Fabric `bloc_05` material edited/executed | NO — unrelated program, untouched |
| Deployment topology | local-only (Book 4 final decision carried forward) |
| External hosting authority | none |
| SonarQubeCloud / Kilo / Vercel / Railway | outside governance boundary; not classified as passing |
| Freebuff | outside scope; untouched |
| Cloud mutations / broker mutations / capital mutations / execution mutations | 0 / 0 / 0 / 0 |
| Recurring cost | `$0` |
| `capital.authority` | `none` |
| GitHub Actions | validation surface only; not application hosting authority |

## 4. Book 5 decision history

| Date | Event | Actor | Record |
|---|---|---|---|
| 2026-10-06 | Reality lock from merged `main` (`3bde6cb2c…`, PR #4 merge commit, parents `7c7816f38…`/`0e486f15c…`); branch `oce-book-5-build` created from exact merged `main` | Agent under `AUTHORIZED_STAGE=B5-I0` | B5-I0 acceptance matrix §G (G10) |
| 2026-10-06 | Required reading of 12 authorities completed; OCE Block 5 vs Sensor Fabric `bloc_05` distinction recorded | Agent | Protocol §2 |
| 2026-10-06 | Six B5-I0 artifacts authored, documentation-only, one commit | Agent | This ledger §2 |
| (pending) | Operator review of B5-I0 | **Operator** | Status decision on this ledger |
| 2026-10-06 | Operator ratification of B5-I0 at commit `bcbeacf88bd8d55e4bef1396c0ac50b3fc1b6334`: protocol accepted and frozen with no amendments; evidence map repaired (acceptance-matrix heading → `all ten candidate criteria`, E3 `L §11` → `L §3`); B5-I0 → OPERATOR_ACCEPTED; B5-I1–I9 remain LOCKED; normal merge of PR #8 authorized (`MERGE_AUTHORIZED=true` for PR #8 only) | **Operator** | `AUTHORIZED_STAGE=B5-I0-RATIFICATION`; protocol §10; this ledger §1 |
| 2026-10-07 | AMEND-001 ratified (`OCE_B5_I0_AMEND-001_SEQUENTIAL_DUAL_PASS_REVIEW_v1.0.md`): operator declined additional chats/agents/external reviewer threads; two-isolated-reviewer mechanism superseded for the B5-I1 evaluation by one agent performing two ordered, separately sealed passes (Pass A evidence/compliance; Pass B adversarial/red-team). The passes are NOT independent and NOT blind; no candidate result existed before the amendment. All frozen criteria/weights/thresholds/disqualifiers/tie-breaks unchanged; prior launch procedure preserved as historical evidence | **Operator** | `AUTHORIZED_STAGE=B5-I1-SEQUENTIAL-DUAL-PASS`; amendment §7 ratification block |
| 2026-10-07 | B5-I1 evaluation executed under AMEND-001: Pass A sealed `b05c61d0a547d3b9287eac55c7a0f1def7487fb7` (file SHA-256 `6a937706a42debda35b5d4e170c5c47b9745f80f26c307457f8a766878b6917c`), Pass B sealed `8f5a06c925b4ebd161ad1f8b6ad8cac02300373f` (file SHA-256 `95ca2c6f830185088bce17a65a12400b823abc94b0887475ad31e75f98fecf9b`); all five candidates screen PASS (0/14 disqualifiers triggered, 0 UNKNOWN each); W-weighted triggers reconciled (9.50, 19.00, 5.75, 5.75) with no per-criterion divergence exceeding 1 and tie-break never invoked; outcomes: DUAL-RECORD PRESERVED ×4 (CAND-001/002/003/005, adopted W 64.00/54.50/67.75/67.75, losing rows preserved verbatim) + AGREED (limited) ×1 (CAND-004, W 82.75); decision packet published as RECOMMENDATION ONLY recommending CAND-004; B5-I1 → AWAITING_OPERATOR_SELECTION; B5-I2–I9 LOCKED. Mechanism NOT independent and NOT blind per AMEND-001 | Agent under `AUTHORIZED_STAGE=B5-I1-EVALUATION` | Reconciliation §2–§5; decision packet §1–§8; this ledger §1 |
| 2026-10-07 | Operator selection of CAND-004 (Local Job Console) under `AUTHORIZED_STAGE=B5-I1-OPERATOR-SELECTION_AND_CHARTER_DRAFT` — the only candidate passing both sequential review lenses and every frozen threshold condition (adopted W 82.75; floors C1=3/C2=4/C3=3/C5=3; D1–D14 zero triggered/zero UNKNOWN; lenses agree; the three disclosed limitations become charter acceptance gates). Decision packet §9 completed by the operator (scorecard/seal commitments and hashes recorded there); decision packet status → RECOMMENDATION_ONLY — CAND-004 OPERATOR-SELECTED; Product Charter drafted, documentation-only, as `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` with product identity `OCE Local Job Console` and exit state `PRODUCT_CHARTER_STATUS = DRAFT_FOR_OPERATOR_RATIFICATION`; ledger B5-I1 row → SELECTED_AWAITING_CHARTER_RATIFICATION (B5-I1 NOT fully accepted); selection recorded at commit `0025aa1701c4c709b6344cec08f57bcdb184cd9a`, charter draft commit recorded under subject `B5-I1-CHARTER: draft selected CAND-004 product charter`; implementation remains unauthorized; B5-I2–I9 remain LOCKED. Reviews were sequential and NOT independent and NOT blind per AMEND-001 | **Operator** (agent scribe under `AUTHORIZED_STAGE=B5-I1-OPERATOR-SELECTION_AND_CHARTER_DRAFT`) | Decision packet §9; `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md`; this ledger §1 |
| 2026-10-07 | B5-I1 ratification under `AUTHORIZED_STAGE=B5-I1-CHARTER_RATIFICATION_AND_MERGE`: final adversarial ratification audit of the complete charter against the protocol, AMEND-001, evidence packet, both sealed scorecards (SHA-256 re-verified byte-identical), reconciliation, decision packet, plan, and this ledger — all literal checks pass; two demonstrated documentation defects repaired in narrow append-only commits (`1534305778…` stale predicted-SHA ledger references → real `0025aa1701c4…`/`5b082164…`; `d4bb8e6064c3…` charter §12 wording carries the literal "planning only" phrase); charter ratified: `PRODUCT_CHARTER_STATUS = OPERATOR_RATIFIED — FROZEN` with `IMPLEMENTATION_AUTHORIZED = FALSE`, `B5_I2_PLUS = LOCKED`, `CAPITAL_AUTHORITY = NONE`, `EXECUTION_AUTHORITY = NONE`, `RECURRING_COST = $0`; B5-I1 → OPERATOR_ACCEPTED; B5-I2–I9 remain LOCKED and require a fresh `AUTHORIZED_STAGE=B5-I2`; ratification does not authorize implementation and no implementation has begun; PR #9 merge authorized (normal two-parent merge, `MERGE_AUTHORIZED=true` for PR #9 only) | **Operator** (agent scribe under `AUTHORIZED_STAGE=B5-I1-CHARTER_RATIFICATION_AND_MERGE`) | `OCE_B5_I1_OPERATOR_RATIFICATION_v1.0.md`; charter exit state; this ledger §1 |

## 5. Downstream contract (what B5-I1 may rely on, only after ratification)

If the operator ratifies B5-I0, B5-I1 may rely exclusively on: the frozen protocol v1.0 (criteria, weights, disqualifiers, scale, thresholds, tie-breaks, dissent/COI/review rules, amendment lock), the blank scorecard v1.0, the frozen risk register v1.0, and the frozen evaluation procedure v1.0 — each as versioned in §2. B5-I1 still requires a fresh `AUTHORIZED_STAGE=B5-I1` and produces the comparison plus the operator-approved Product Charter. Planning completion grants no implementation authority.

## 6. Accounting

Documentation only; two append-only commits on `oce-book-5-build` (`B5-I0: freeze reference-application selection protocol`, `B5-I0-RATIFY: accept frozen selection protocol and repair evidence map`), no force push. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. `main` untouched by direct push; `oce-program-build` unchanged. PR #8 normal two-parent merge authorized by the operator (`MERGE_AUTHORIZED=true` for PR #8 only); no amend, squash, rebase, reset, or force-push.

B5-I1 evaluation phase A (this ledger §1/§4): six append-only commits on `oce-book-5-i1` (`52843ffc…` intake, `6d1d6f0a…` launch freeze, `f381ce0e…` AMEND-001, `b05c61d0…` Pass A seal, `8f5a06c9…` Pass B seal, and `20825493…` B5-I1-P2 reconciliation/decision-packet/ledger commit), ordinary fast-forward pushes only; `main` untouched by direct push; cloud/broker/capital/execution mutations 0; recurring cost `$0`; `capital.authority = none`.

B5-I1 selection and charter-drafting (this ledger §1/§4/§7): two further append-only commits on `oce-book-5-i1` (`0025aa17…` operator selection of CAND-004 recorded in decision packet §9 + ledger; `5b082164…` Product Charter CAND-004 draft + evidence updates), ordinary fast-forward pushes only; scorecards and reconciliation byte-identical (SHA-256 pins unchanged); documentation only — no implementation, no `oce/frontend` modification, no B5-I2 work; cloud/broker/capital/execution mutations 0; recurring cost `$0`; `capital.authority = none`.

B5-I1 ratification (this ledger §1/§4/§7): three further append-only commits on `oce-book-5-i1` (`1534305778…` stale-SHA ledger repair, `d4bb8e6064c3…` charter planning-only wording repair, and the `B5-I1-RATIFY` ratification commit — charter → `OPERATOR_RATIFIED — FROZEN`, ratification artifact added, ledger → B5-I1 `OPERATOR_ACCEPTED`), ordinary fast-forward pushes only; scorecards, reconciliation, and frozen packets byte-identical; documentation only; PR #9 merged into `main` as a normal two-parent merge commit (no squash, rebase, or force; merge SHA recorded on the merged PR); cloud/broker/capital/execution mutations 0; recurring cost `$0`; `capital.authority = none`; no implementation begun; B5-I2 requires a fresh `AUTHORIZED_STAGE`.
| 2026-10-07 | B5-I2 execution under `AUTHORIZED_STAGE=B5-I2`: branch `oce-book-5-i2` created from exact merged main `882835dac…` and pushed; 12 authorities read; B5-I2 derived unambiguously as charter increment I-1 (console-control-plane deterministic interface contracts; plan §7 anchor `C2 outcome/domain/interfaces`, gate `Deterministic product contracts pass`); implementation contract frozen at commit `66a185186…` (P0, documentation only); production slice implemented test-first — contract pack `console-contract.json` + deterministic binding module `console_contracts.py` (R1 `5ce24e4c4…`) and 24 two-sided contract tests with adversarial negative controls (R2 `77bccf860…`); red evidence recorded (weakened refusal guard → refusal tests fail; restored → green); full control-plane regression identical to clean-base baseline except one pre-existing Windows-only `/proc` test failure; exact-head CI: `B1-I1R Validation` run 37708674982 SUCCESS on `77bccf860307ca3b9bee6939ab2fe3a8f848eabd` (pull_request → main, PR #10); draft PR #10 opened with `NOT MERGE AUTHORIZED`; B5-I3–I9 remain LOCKED | Agent under `AUTHORIZED_STAGE=B5-I2` | `OCE_B5_I2_IMPLEMENTATION_CONTRACT_v1.0.md`; PR #10; this ledger §1/§8 |

B5-I2 (this ledger §1/§4/§8): four append-only commits on `oce-book-5-i2` (`66a185186…` P0 implementation-contract freeze, `5ce24e4c4…` R1 contract pack + binding module, `77bccf860…` R2 contract tests, and the EVIDENCE documentation commit), ordinary fast-forward pushes only; no existing control-plane module, schema, or workflow file modified; no console code, no UI, no new server endpoint; no LLM dependency; loopback-only; cloud/broker/capital/execution mutations 0; recurring cost `$0`; `capital.authority = none`; no merge performed; B5-I3+ not begun.

## 7. B5-I1 evidence set (as of ratification)

| # | Artifact | Document ID | Status | Role |
|---|---|---|---|---|
| 1 | Candidate intake register | OCE-B5-I1-INTAKE-001 | INTAKE_RECORDED | Census method; identifier→working-name mapping; 14-component parity; evidence-class discipline |
| 2 | Evidence packets CAND-001…CAND-005 | OCE-B5-I1-PACKET-CAND-00X | INTAKE_EVIDENCE — UNSCORED (frozen at both seals) | Identical 14-component requirement set; D1–D14 with positive evidence, no UNKNOWN |
| 3 | Reviewer brief + two-thread launch procedure | OCE-B5-I1-REVIEWER-BRIEF-001 / -LAUNCH-001 | Preserved verbatim as historical evidence (superseded for this evaluation by AMEND-001) | Prior frozen two-isolated-reviewer mechanism |
| 4 | AMEND-001 | OCE-B5-I0-AMEND-001 | OPERATOR_RATIFIED — ACTIVE | Sequential dual-pass mechanism; passes NOT independent and NOT blind |
| 5 | Scorecard PASS A | OCE-B5-I1-SCORECARD-PASS-A-001 | SEALED — commit `b05c61d0…`, SHA-256 `6a937706…78b6917c` | Evidence/compliance pass, all five candidates |
| 6 | Scorecard PASS B | OCE-B5-I1-SCORECARD-PASS-B-001 | SEALED — commit `8f5a06c9…`, SHA-256 `95ca2c6f…fecf9b` | Adversarial/red-team pass, all five candidates |
| 7 | Reconciliation record | OCE-B5-I1-RECONCILIATION-001 | RECONCILIATION_COMPLETE | Imports unchanged; divergence table; cited-evidence arbitration; dual records preserved ×4 |
| 8 | Operator decision packet | OCE-B5-I1-DECISION-PACKET-001 | RECOMMENDATION_ONLY — CAND-004 OPERATOR-SELECTED (2026-10-07) | Recommendation (CAND-004) with mechanism limitations, verbatim dissent; §9 completed by the operator — selection of CAND-004 recorded with rationale, seals, and scorecard SHA-256 pins |
| 9 | Product Charter CAND-004 | OCE-B5-I1-CHARTER-CAND-004 | OPERATOR_RATIFIED — FROZEN (2026-10-07) | Operator-selected Product Charter (OCE Local Job Console; `CAND-004` preserved); product identity, operator problem, users, outcome, authority law, deterministic kernel, local-only topology, bounded scope, lifecycle/recovery, security/privacy, 17 acceptance gates, 6–8 increment ceiling (planning only, not begun); exit states: `IMPLEMENTATION_AUTHORIZED = FALSE`, `B5_I2_PLUS = LOCKED`, `CAPITAL_AUTHORITY = NONE`, `EXECUTION_AUTHORITY = NONE`, `RECURRING_COST = $0` |
| 10 | Operator ratification record | OCE-B5-I1-RATIFICATION-001 | OPERATOR_RATIFIED — FROZEN | Final adversarial ratification audit findings; repair commits `1534305778…` / `d4bb8e6064c3…`; commit identities (selection `0025aa1701c4…`, charter `5b082164c747…`); scorecard seals re-verified; boundaries frozen; PR #9 merge authorized (two-parent, PR #9 only) |

## 8. B5-I2 evidence set

| # | Artifact | Identity | Status | Role |
|---|---|---|---|---|
| 1 | Implementation contract v1.0 | `OCE_B5_I2_IMPLEMENTATION_CONTRACT_v1.0.md` at commit `66a185186…` | FROZEN (scope only; not a B5-I2 ratification) | Exact B5-I2 scope = charter §12 I-1; non-goals; gates; surfaces; refusal/determinism/local-only law; test strategy; stop condition |
| 2 | Contract pack | `infrastructure/control-plane/contracts/console-contract.json` at commit `5ce24e4c4…`, SHA-256 `45bcb4f63fdb44c039e81fa51ac01a877bb05faee048efa8193ed7fc16af14aa` (committed blob) | COMMITTED | Versioned console↔control-plane interface contracts; every surface bound to one existing governed operation |
| 3 | Binding module | `infrastructure/control-plane/src/oce_control/console_contracts.py` at commit `5ce24e4c4…` | COMMITTED | Deterministic stdlib-only projection/validation/refusal layer |
| 4 | Contract tests | `infrastructure/control-plane/tests/test_console_contracts.py` at commit `77bccf860…` — 24 tests | GREEN 24/24 (two-sided I-1 gate) | Authority-owner binding; G5 refusal + zero side effects; G7 verbatim agreement; G9 evidence/denial schema validation; G10 no-LLM structural proof; weakened-control non-vacuity |
| 5 | Exact-head CI | `B1-I1R Validation` run `37708674982` — SUCCESS on `77bccf860307ca3b9bee6939ab2fe3a8f848eabd`, branch `oce-book-5-i2`, event `pull_request` (PR #10) | SUCCESS | Authoritative exact-implementation-head proof; identity gate binds repository, branch, commit, tree |
| 6 | Draft PR | PR #10 `oce-book-5-i2` → `main`, draft, `NOT MERGE AUTHORIZED` | OPEN — NOT MERGED | Operator review artifact |
## 9. B5-I2 audit, repair and superseding evidence (AUTHORIZED_STAGE=B5-I2-AUDIT_REPAIR_AND_RATIFICATION)

> This section is APPEND-ONLY and supersedes §4 (2026-10-07 B5-I2 execution row) and §8 rows 4–5 **where they conflict**, which remain published as history. Three corrections: (a) the historical exact-head CI runs did **not** execute the 24 B5-I2 test nodes; (b) "implemented test-first" was not the wall-clock reality (see §9.6); (c) the clean-base regression comparison is refined by an exact failure-site comparison (§9.7). No earlier text was rewritten or erased.

### 9.1 Authoritative-selection defect in the historical runs (evidence defect, established)

Artifact-and-log audit of both historical runs proved the B5-I2 file was never selected — the shared runner executes the cloud-ground regression battery only:

| Run | Head (tested) | Conclusion | B5-I2 nodes collected | B5-I2 JUnit | B5-I2 proof artifact |
|---|---|---|---|---|---|
| `37708674982` | `77bccf860307ca3b9bee6939ab2fe3a8f848eabd` (R2, historical implementation head) | SUCCESS | **0 of 24** | absent | absent |
| `37709881210` | `5b3db4445771f160f1e0b0d6b3105ac5c2817ea1` (historical evidence head) | SUCCESS | **0 of 24** | absent | absent |

Therefore §8 rows 4–5 stand only as: row 4 = local 24/24 green at publication time; row 5 = aggregate workflow/identity-gate success. Neither historical run is evidence that any B5-I2 node executed. A green workflow or aggregate "validation passed" is not node-level proof.

### 9.2 Repairs (CI-exposed, both pushed before this section)

| Commit | Subject | Scope |
|---|---|---|
| `835fc644342b17acabfe65ef465359c58a6fe5a2` | `B5-I2-X1: execute console-contract proofs in authoritative validation` | Two steps added to the **existing** `b1-i1r-validation.yml`: hash-locked control-plane pytest install (same form as `b2-control-plane.yml`) and whole-file selection of `test_console_contracts.py` with a fail-closed collection/registry proof + JUnit written into the existing evidence artifact. No new workflow, no trigger change, no branch-protection change, no bypass, no second runner; shared-runner identity/cleanup gates and exit-code capture untouched. |
| `d5801e104b4ee4178e2145bfb4189e7b21169267` | `B5-I2-X2: make authority-owner, route, schema and import-closure proofs strict` | Four proof repairs inside existing nodes (node count remains 24): authority-owner binding de-tautologised (`assert … or True` → full module import + attribute-chain resolve + callable); HTTP route matching extended from invokes-only to every declared read route (embedded denial/evidence bindings pinned to their declared form); exact 23-property pin of `job-envelope.schema.json` + projection-subset assertion (a silently **added** schema property previously passed every check); dynamic-import escape detection (`__import__` / `import_module` / `reload` call form) added to the import-closure proof. |

### 9.3 Proving runs (current, exact-head, node-level)

| Run | Head (tested) | Artifact / run id | JUnit (tests/failures/errors/skips) | Collected | Duplicate full node IDs | Gate |
|---|---|---|---|---|---|---|
| `37788106183` | `835fc644342b17acabfe65ef465359c58a6fe5a2` (X1) | `b1-i1r-evidence-e7ac8552318d` / `e7ac8552318d` | **24 / 0 / 0 / 0** | 24 (= executed) | 0 | READY_FOR_OPERATOR_REVIEW |
| `37791367627` | `d5801e104b4ee4178e2145bfb4189e7b21169267` (X2, implementation head) | `b1-i1r-evidence-5b14ebb60d9d` / `5b14ebb60d9d` | **24 / 0 / 0 / 0** | 24 (= executed) | 0 | READY_FOR_OPERATOR_REVIEW |

Identity binding per registry proof: `pr_head_sha` equals the exact head above; the tested checkout is the PR merge ref (`23e9a61db…` = merge of `882835dac…` + `835fc6443…`, tree `9a72b5cf…`; `50af447aea…` for the X2 run, tree `2fe89a61…`). All 24 full node IDs are unique, all prefixed `infrastructure/control-plane/tests/test_console_contracts.py::`, selection is whole-file (floor 24), `executed_equals_collected = true`, runner command recorded in the step log (`pytest infrastructure/control-plane/tests/test_console_contracts.py --collect-only -q` then full run with `--junitxml`). Class distribution: TestContractPack 4, TestUnsupportedOperationRefusal 4, TestMalformedInputRefusal 5, TestGovernedInvokeSurfaces 3, TestCanonicalStateAgreement 3, TestDeterminism 3, TestEvidenceIdentityBinding 2 = 24. Passed 24, skipped 0 (zero-skip law holds in authoritative Linux CI).

### 9.4 Two-sided contract mapping (JSON pack ↔ Python binding ↔ existing authority)

Proven by: strict binding test (all 12 resolved through live import + attribute chain, callable), route test (10 registered routes + 2 embedded), runtime demonstrations below, and the mutation battery (§9.5).

| Contract surface | Pack declaration | Python binding | Existing authority owner | Class | Positive proof | Refusal proof |
|---|---|---|---|---|---|---|
| `health.read` | read → `api.ControlPlaneAPI.health`, `GET /api/health` | `read_surface` → `getattr(api,"health")` | `api` + `health.HealthService` (existing) | read | node `test_reads_render_governed_responses_verbatim`; CI strict-binding node | health-as-invoke refused `unsupported_surface` (audit demo); kind-flip mutation M4 red |
| `readiness.read` | read → `api.readiness`, `GET /api/readiness` | `read_surface` | `api` (existing) | read | node `test_reads_render…` (verbatim governed verdict) | unknown/kind confusion refused (nodes) |
| `jobs.inspect` | read → `api.inspect_job`, `GET /api/jobs/{job_id}`, schema `job-envelope` | `read_job_envelope` → `read_surface` + pinned projection | `job_store.JobStore` (existing) | read | nodes `test_projected_job_agrees_verbatim…`, `test_stale_or_unknown_job_inspect_is_not_fabricated` | unknown job → governed `not_found`, never fabricated (node) |
| `jobs.schedules` | read → `api.list_schedules`, `GET /api/schedules` | `read_surface` | `scheduler.Scheduler` via `api` (existing) | read | audit live execution `ok=True status=success` + CI strict-binding/route nodes | unknown surface ids refused (nodes) |
| `workers.list` | read → `api.list_workers`, `GET /api/workers` | `read_surface` | `worker.WorkerProtocol` (existing) | read | node `test_reads_render…` | M4 kind-flip red |
| `system.read` | read → `api.system_state`, `GET /api/system` | `read_surface` | `api` (existing) | read | node `test_reads_render…` + negative-control node (weakened guard admits direct call with observable audit activity, real guard refuses) | node `test_non_vacuous_negative_control_weakened_guard_admits`; M2 red |
| `audit.read` | read → `api.audit_history`, `GET /api/audit` | `read_surface` | `api` audit log (existing) | read | audit live execution `ok=True status=success` + CI strict-binding/route nodes | unknown surface ids refused (nodes) |
| `denial.read` | read → `authority.AuthorityEngine.record_denial`, route `embedded in denied APIResponse.data.denial`, schema `denial-envelope` | governed denial path rendered verbatim; `validate_denial_envelope` | `authority.AuthorityEngine` — sole (pack `law.authority_owner`) | read | nodes `test_denial_envelope_from_governed_authority_is_rendered_verbatim` (key-set identity vs live `record_denial`), `test_submit_without_authority_yields_schema_valid_denial` | denial causes **zero** governed side effects (node asserts empty job store); authority failures never minted by console |
| `evidence.read` | read → `evidence.EvidenceBuilder.build_manifest`, route `embedded in job evidence_refs / evidence records`, schema `evidence-manifest` | `validate_evidence_manifest` over governed builder output | `evidence.EvidenceBuilder` (existing) | read | node `test_evidence_manifest_binds_to_schema_and_operation` (digest binds artifact bytes) | schema drift mutations M7b/M7c red |
| `jobs.submit` | invoke → `api.submit_job`, `POST /api/jobs`; request `job_type,payload,resource_scope?,environment?,priority?,grant_id,actor_id` (required `job_type,payload,grant_id,actor_id`); `max_payload_bytes` 65536; schema `job-envelope`; failure `denial-envelope` | `invoke_surface`: pack-validated, then the one governed call `api.submit_job` | `api.submit_job` (+ grant law) (existing) | mutation | node `test_submit_through_pack_is_the_governed_operation` (store owns state) | nodes unknown-job-type / oversize / missing / unexpected-field / missing-grant; wrong-owner M3 and dispatcher-bypass M5 red |
| `jobs.cancel` | invoke → `api.cancel_job`, `POST /api/jobs/{job_id}/cancel` | `invoke_surface` → `getattr(api,"cancel_job")` | `api.cancel_job` (existing) | mutation | node `test_cancel_and_retry_are_single_governed_operations` | node `test_cancel_with_missing_job_id_refused`; M3 red |
| `jobs.retry` | invoke → `api.retry_job`, `POST /api/jobs/{job_id}/retry` | `invoke_surface` → `getattr(api,"retry_job")` | `api.retry_job`; lifecycle transition law owns legality (existing) | mutation | node `test_cancel_and_retry…` (illegal transition refused by governed lifecycle; canonical state unchanged — no second state machine) | M3 red |

Charter six-coverage: **jobs** (inspect/schedules/submit/cancel/retry), **workers** (list), **leases** — no console surface is declared (lease state observed through job envelopes and worker listings per frozen contract §7); enforcement demo: `leases.read`, `leases.list`, `leases.release` (read) and `leases.renew`, `leases.release` (invoke) all refused `unsupported_surface` fail-closed with zero side effects; lease mutation remains worker-fabric-only. **health** (read/readiness, cannot mutate: invoke set is exactly `jobs.submit/jobs.cancel/jobs.retry`), **submit** (row 10), **denial** (row 8).

JSON/Python agreement (verified): version `contract_version=1.0.0` pinned by node; operation names = 12 `binds_to.callable`s, all resolved live; request fields validated exactly against pack entries (extra field → `malformed_request`, node); response fields = projection (21) = pinned module set, subset of the schema's 23, pinned both ways (X2); status vocabulary = the schema's 9-value enum produced only by the governed lifecycle (fabricated `completed` → M6 red); bounds: pack `max_payload_bytes` 65536 == module `MAX_PAYLOAD_BYTES`; authority owner: `law.authority_owner = oce_control.authority.AuthorityEngine`, and every `load_contract()` call re-validates kind (`read`/`invoke`) plus the `oce_control.*` module prefix; refusal vocabulary: 4 mechanical pack refusal keys == 4 module `REFUSAL_*` codes, plus `authority_denial` owned by `AuthorityEngine` (schema enum, rendered verbatim).

Three existing schemas identified precisely: `job-envelope.schema.json`, `denial-envelope.schema.json`, `evidence-manifest.schema.json` — all created by `B2-C1` (`dbf128368`, 2026-08-30), present at base `882835dac…`, and untouched by this branch (branch touches only the new pack under `contracts/`). Compatibility is proven by execution: real governed job projections, live denial envelopes and a real `EvidenceBuilder` manifest validate against them in nodes; pack `schemas` map names exactly these three.

### 9.5 Non-vacuity: 11-mutation battery (every negative control discriminates)

Baseline 24/24 green; each mutation applied to exactly one control; every mutation failed ≥ 1 node; sources restored; battery verdict ALL DISCRIMINATED (results JSON archived at `C:\tmp\b5i2_mutations.json`; runner `.b5i2_mutation_battery.py` retained untracked for reproduction):

| # | Mutation (one weakened control) | Nodes that failed |
|---|---|---|
| M1 | pack byte changed, Python untouched | 1 — `test_pack_identity_is_pinned_in_this_test_file` (SHA-256 pin) |
| M2 | Python weakened refusal guard, pack untouched | 2 — unknown-read-refusal + negative-control node |
| M3 | operation rebound to wrong authority owner (`submit`→`cancel_job`) | 7 |
| M4 | read surface declared as invoke (kind confusion) | 1 — `test_read_surface_id_used_as_invoke_is_refused` |
| M5 | submit bypasses the governed dispatcher (fabricated response) | 7 |
| M6 | fabricated unknown status `completed` in projection | 3 |
| M7a | schema field **added** | 1 — schema pin node (only detectable because of X2) |
| M7b | schema field removed | 3 |
| M7c | schema field renamed | 3 |
| M8 | forbidden static import (`import requests`) in module | 1 — import-closure node |
| M9 | dynamic import escape (`__import__` call form) in module | 1 — import-closure node (X2 check) |

### 9.6 Red/green chronology (corrected, precise)

Commit order on the branch: `66a185186` P0 (frozen implementation contract, docs) → `5ce24e4c4` R1 (pack + module, **no tests**) → `77bccf860` R2 (the 24 tests) → `5b3db4445` EVIDENCE → `835fc6443` X1 → `d5801e104` X2. **Git history contains no committed failing-test rung.** Working-tree reality recorded by this session: the pack and the production module were authored before the test file in the same working-tree session; the first test executions were red from implementation defects and were driven to 24/24 green while uncommitted; non-vacuity red evidence was produced out-of-band by mutation demonstrations (weakened refusal guard → refusal tests fail → restore → green), now systematised as the 11-mutation battery (§9.5). The frozen contract §9 sentence "tests are authored first and demonstrated failing against the unimplemented module" states the prescribed discipline, not a fact encoded in history; the §4/§8 phrase "implemented test-first" is superseded by this paragraph. R1/R2 were committed only after green. The published commit order therefore does not itself encode the red state.

### 9.7 Full regression verification (§6)

Command (identical at both ends): `python -m pytest infrastructure/control-plane/tests -q -o addopts= --tb=line -rf -rs`.

| Tree | Result | Failure-site set relation |
|---|---|---|
| HEAD `d5801e104` (branch + X1 + X2) | 29 failed, 797 passed, 103 skipped | **0 HEAD-only sites** — every HEAD failure also fails at base |
| base `882835dac` (detached worktree, same machine, same command) | 32 failed, 770 passed, 103 skipped | 3 base-only sites (`test_b4_startup_gate.py:1621/:1641` secret-provisioning state variance between runs) |

The Windows `/proc` failure is reproduced at base with the same command: `test_local_lifecycle.py:459 "could not read /proc cmdline"` — pre-existing, unrelated to B5-I2. B5-I2 nodes failing at HEAD: **0 of 24**. Skip classification at HEAD: all 103 skips are environmental — 99 `container runtime unavailable (Docker absent)` (marked container tests), 2 `symlinks unavailable on this platform`, 2 `POSIX permission/ chmod-000` (Windows); **B5-I2 skips = 0** (no marker applies; authoritative CI JUnit `skipped=0`). Shared OCE regression runner: 67/67 registered tests pass locally (and runs inside every proving CI run); workflow-constraint tests (`test_gate_regressions.py` -k ci_/workflow/branch: 12/12) and the line-ending rule test pass. Lint: no project lint config/gate exists; `ruff check` (defaults) on the changed files reports 6 findings on the test file, **all pre-existing at R2** (4× E402 path-bootstrap pattern used repo-wide, 1× F401, 1× F841 — zero new findings from X1/X2) and **0 findings on `console_contracts.py`**; `pyflakes` not installed locally. Compile: `py_compile` clean on both changed Python files. JSON: pack + 3 schemas parse. Schema/pack consistency: 12/12 bindings resolve callable, 10/10 registered routes present (+2 embedded), projection ⊂ schema, bounds equal. Secret scan over changed files: no hits. `git diff 882835dac..HEAD --check`: clean. Duplicate-node inspection: 0.

### 9.8 Limitations (honest record)

1. The local full control-plane suite cannot be green on this Windows host (Docker/`/proc`/POSIX-conditional tests); the authoritative gate is Linux CI, where the proving runs are green at node level for B5-I2 and the aggregate runner for everything else.
2. `denial.read` and `evidence.read` are *embedded* bindings (their routes ride governed responses/records); the generic `read_surface` dispatcher assumes `api`-module callables and is not their execution path — their proofs are the envelope-validation nodes. No test or claim asserts `read_surface("denial.read")` executes; a future console must render them from governed responses as the pack declares.
3. `jobs.schedules` and `audit.read` are positively exercised in this audit's local runtime demonstration plus CI strict-binding/route nodes; no dedicated CI node calls `read_surface` for them (all other read surfaces have one).
4. Ruff findings listed in §9.7 are pre-existing debt (R2), left unfixed to keep this stage's implementation head stable; they are recorded rather than suppressed.
5. Historical runs `37708674982`/`37709881210` remain green records of the aggregate workflow; they are explicitly **not** node-level B5-I2 evidence (§9.1).

### 9.9 Gate status at this section

24 nodes executed in authoritative Linux CI ✓; zero failures/errors/skips ✓; zero duplicate full node IDs ✓; JSON/Python two-sided agreement proven ✓; all 12 operations map to existing authority owners, no placeholder capability ✓; negative controls discriminate 11/11 ✓; implementation head `d5801e104…` exact-head CI success (`37791367627`) ✓. Evidence-head and ratification-head CI runs are recorded in the B5-I2 operator-ratification artifact when this section's commit and the ratification commit have each passed exact-head CI. This stage implements only charter increment I-1; B5-I3+ remains LOCKED and requires a fresh `AUTHORIZED_STAGE`.

---

## 10. B5-I2 post-merge reproducibility closure (AUTHORIZED_STAGE=B5-I2-POST-MERGE-REPRODUCIBILITY-REPAIR)

> Appended after the merge of PR #10 (merge `e3e38e83…`). Section 9.5 above is NOT edited or erased; this section supersedes only its reproduction-vehicle designation.

### 10.1 What §9.5 recorded correctly, and what is corrected here

- **Stands:** §9.5 truthfully recorded the local execution result — baseline 24/24 green, each of the 11 mutations failed at least one node, sources restored, verdict `ALL DISCRIMINATED`. The committed §9.5 table, the PR #10 body, the ratification artifact and commit messages remain accurate records of that historical execution.
- **Corrected:** §9.5 additionally stated “runner `.b5i2_mutation_battery.py` retained untracked for reproduction” and named `C:\tmp\b5i2_mutations.json` as the archived results JSON. That designation was wrong: both were unpublished local scratch paths outside the repository. Neither was ever committed, ever part of a CI artifact, or ever required by a passing gate. They are superseded and non-authoritative as reproduction vehicles.

### 10.2 The governed replacement (committed, CI-executed, deterministic)

| Item | Value |
|---|---|
| Governed harness path | `infrastructure/control-plane/scripts/b5_i2_mutation_battery.py` |
| Harness publish commit (R1) | `3af34c956…` |
| Harness integrity tests (16 nodes) | `infrastructure/control-plane/tests/test_b5_i2_mutation_harness.py` |
| Integrity + CI wiring commit (R2) | `7210df105…` |
| Harness hardening commit (R2b) | `c82fc18cd…` (fail-fast inventory gate + decode robustness) |
| Harness bytecode-purge fix (R2c) | `1814aa74f…` — FINAL harness content, git blob `865c75a8bce0341cdd8516ab17ec35489f4f7570` |
| Canonical result artifact | `docs/oce-golden-system/OCE_B5_I2_REPRODUCIBILITY_RESULT_v1.0.json` (schema `oce.b5-i2.reproducibility-result`, version `1.0.0`) |
| Tested implementation | merged B5-I2 `e3e38e83866fd6b1897531b0149c568a16b80177` |
| Test-file blob SHA | `85e1b17b79a1e06093619a5e1d604a9b753fb207` (unchanged) |
| Harness content SHA-256 | `1c05b0213dac…` (recorded inside the artifact; byte-bound by CI `--verify`) |
| Baseline | exactly 24 nodes — 24 passed / 0 failed / 0 errors / 0 skipped |
| Mutations | M1, M2, M3, M4, M5, M6, M7a, M7b, M7c, M8, M9 — **11/11 `DISCRIMINATED`**, verdict `ALL_DISCRIMINATED`, 0 unresolved, 0 skipped |

Harness law (executable, not aspirational): execution happens only in an isolated temporary copy — the caller’s tracked worktree is never written; the control is proven green before AND after the battery; every patch anchor must occur exactly once; no-op mutations are refused; the run exits nonzero on any incomplete, vacuous, duplicated, skipped or non-discriminating state; the canonical JSON is byte-deterministic (sorted keys; no timestamps, temp paths, host names, user names or durations). The authoritative workflow step additionally proves the tracked source is byte-identical after execution.

Honest chronology of this repair: the first two exact-head runs of the new CI step (`37826140353` on `7210df105…`, `37826223948` on `c82fc18cd…`) **failed** — the integrity fixture’s same-size mutation (`assert 1 + 1 == 2` → `== 3`) landed in the same second as the preceding compile, so timestamp+size `.pyc` validation reused stale assertion-rewritten bytecode and the mutated tree wrongly stayed green (`exit=0`). Root cause fixed in R2c by purging `__pycache__` under the isolated tree before every pytest invocation (the same latent exposure existed for real mutation M3, `api.submit_job` → `api.cancel_job`, identical byte length). No test, gate or assertion was weakened; the failing runs are recorded rather than hidden.

### 10.3 Authoritative CI (exact-head)

The exact-head run / check-run / artifact identifiers for this section’s evidence commit are appended in §10.4 below, append-only, once the run is proven green and its artifact has been downloaded and parsed (an artifact cannot contain its own CI run identity).

### 10.4 Supersession and invariants

- `.b5i2_mutation_battery.py` (untracked scratch runner) and `C:\tmp\b5i2_mutations.json` (untracked scratch results) are **superseded and non-authoritative**; after merge verification they are deleted from the local machine. The durable evidence package is now: §9.5 (historical result record), this §10 (correction), the canonical result artifact, the committed harness + integrity tests, and the CI evidence artifacts.
- B5-I2 production behavior, contract pack, schemas, frozen tests and the merged implementation remain **unchanged** by this stage — no production file is touched (`test_console_contracts.py` blob stays `85e1b17b…`; `console_contracts.py`, `console-contract.json` and the three schemas are byte-identical to the merged B5-I2).
- The Book 5 acceptance/ratification artifacts required no wording correction: they record mutation *results* (M1/M4/M6 citations) and never named the scratch paths.
- B5-I3–I9 remain **LOCKED**; a fresh `AUTHORIZED_STAGE=B5-I3` is required to begin them.

#### Exact-head CI proof (appended append-only after the runs completed)

| Run | Head | Conclusion |
|---|---|---|
| `37824894774` | `3af34c956…` (R1) | `success` (workflow step not yet present) |
| `37826140353` | `7210df105…` (R2) | `failure` — stale-bytecode incident, recorded in §10.2 chronology |
| `37826223948` | `c82fc18cd…` (R2b) | `failure` — stale-bytecode incident, recorded in §10.2 chronology |
| `37827592594` | `1814aa74f…` (R2c) | `success` (purge fix proven: integrity + battery step green) |
| `37827782039` | `018b2f98d…` (EVIDENCE) | `success` — authoritative proving run, identities below |

EVIDENCE-head exact binding: run `37827782039` conclusion `success`, `head_sha = 018b2f98de4d0cfce1097073eb8207e21b08d511`, check-suite `102489108183`, check-run `113484971259` (`validate`, `success`, same `head_sha`), artifact `11573010013` (`b1-i1r-evidence-5496a7937bdd`, not expired, 22453 bytes).

Artifact parse (downloaded and parsed, not badge-inferred): emitted `b5-i2-reproducibility-result.json` **byte-identical** to the committed canonical artifact (12546 bytes); baseline 24 nodes → **24/0/0/0**; **11/11 `DISCRIMINATED`** (raw observations all `matched_by: node`, zero via fallback class); integrity junit **16/0/0/0**; B5-I2 junit **24/0/0/0**; registry proof `PASS` (collected = executed = 24, zero duplicates); `b5-i2-repro-worktree-check.txt` empty (tracked source byte-identical after execution); gate `READY_FOR_OPERATOR_REVIEW`. The final head’s own run identity is recorded in PR #11 (an artifact cannot contain its own CI run identity).
