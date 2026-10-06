# OCE Golden System
## B5-I0 — Reference-Application Selection Protocol

**Document ID:** OCE-B5-I0-PROTOCOL-001
**Version:** 1.0
**Status:** OPERATOR_RATIFIED — FROZEN
**Authorized stage:** `AUTHORIZED_STAGE=B5-I0` (exclusive)
**Parent authorities:** OCE Constitution 1.1; Amendment A-002; Master Program Atlas 1.0; Full Program Build Roadmap 1.0; Block 00/01/02/03/04/05 plans; Full Planning Index 1.0; final Book 4 evidence and acceptance records (immutable historical evidence)
**Build authorization:** None. Documentation only.
**Owner and final authority:** Operator

---

## 1. Purpose and freeze statement

This document freezes the *process* by which the Block 5 reference application will be selected at B5-I1, before any application is scored, favored, named, or eliminated.

Freeze statement:

1. The candidate criteria, weights, disqualifiers, evidence requirements, scoring scale, tie-break rules, dissent rules, conflict-of-interest guard, independent-review procedure, minimum passing score, operator decision boundary, and amendment lock in this document are **frozen as of this version**.
2. No candidate has been named, scored, ranked, favored, or eliminated by this document or by any B5-I0 artifact.
3. Scoring may not begin before the operator ratifies this protocol version.
4. Any change to these rules after any candidate result becomes visible requires a versioned amendment under §7.11; scores are never edited in place.

## 2. Scope and explicit distinction from Sensor Fabric `bloc_05`

This is **OCE Golden System Block 5 — Reference Application Factory** (planning unit `B5`, chapters `B5.C1`–`B5.C5`, increments `B5-I0`–`B5-I9`), whose purpose is to prove that OCE and PO can produce a complete governed application.

It is **not** the unrelated Sensor Fabric `bloc_05` material located under `quant-lab/research/crypto_foundry/sensor_fabric/bloc_05/` (crypto sensor-fabric research blocks). That material:

- is a different program with its own numbering;
- is not an input to, gate for, or dependency of this protocol;
- is not edited, executed, advanced, or referenced as authority by any B5-I0 artifact.

No Sensor Fabric stage is executed or modified by this mission.

## 3. Authority and doctrine carry-forward

This protocol inherits, without modification, the final Book 4 governance decision and the constitutional baseline:

- Deployment topology = **local-only**; external hosting authority = **none**.
- `oce/frontend` is internally owned, remains untouched during B5-I0, and is not a candidate criterion subject to modification.
- SonarQubeCloud, Kilo Code Bot, Vercel, and Railway remain **outside the governance boundary** for `larger-lab`; they are neither available to nor classified by this protocol.
- Freebuff remains **outside scope** and untouched.
- Cloud mutations = 0; broker mutations = 0; capital mutations = 0; execution mutations = 0; recurring cost = `$0`; `capital.authority = none`.
- GitHub Actions may validate repository work; it does not constitute application hosting authority.
- Deterministic non-LLM kernels are mandatory (Constitution Article V); an LLM may never be canonical state.
- Deny by default (Constitution Principle 7): unknown, unevidenced, or ambiguous entries never count as passing.

## 4. Candidate criteria (frozen)

A reference-application candidate is assessed against exactly these ten criteria. No criterion may be added, removed, renamed, or redefined without a versioned amendment under §7.11.

| ID | Criterion | Definition |
|---|---|---|
| C1 | Meaningful operator outcome | The application solves a real, stated operator problem with an observable success measure a human can judge without reading code. |
| C2 | Broad OCE lifecycle coverage | The application exercises a broad span of the OCE lifecycle end to end rather than a single isolated capability. |
| C3 | Deterministic non-LLM kernel | Correctness-critical logic is deterministic code with tests; LLMs may propose inputs or interpret outputs but are never the source of truth. |
| C4 | Bounded inputs and canonical state | Inputs are enumerable and bounded; state is canonical, schema-defined, and replayable; no unbounded data ingestion. |
| C5 | Local operation | The application runs and is demonstrable entirely on local infrastructure under the local-only topology. |
| C6 | Explainable outputs | Outputs are human-legible: the operator can see why a result was produced from recorded inputs and rules. |
| C7 | Bounded completion window | The work fits a bounded, stated completion window appropriate to a single reference build. |
| C8 | Recovery and change-cycle coverage | The application meaningfully exercises restore, restart, failure containment, and at least one governed change cycle. |
| C9 | Reuse potential without premature platform extraction | The application would exercise reusable Golden System surfaces, without becoming a disguised general platform rewrite. |
| C10 | Governed-path exercise breadth | The application can exercise identity, intent, planning, grants, workers, artifacts, evidence, review, packaging, observability, and recovery. |

Criterion C10 is assessed against the full enumerated path list: identity, intent, planning, grants, workers, artifacts, evidence, review, packaging, observability, recovery. Partial coverage is scored proportionally under §5.

## 5. Weighted scoring model (frozen)

### 5.1 Exact weights

| Criterion | Weight |
|---|---:|
| C1 Meaningful operator outcome | 15 |
| C2 Broad OCE lifecycle coverage | 15 |
| C3 Deterministic non-LLM kernel | 12 |
| C4 Bounded inputs and canonical state | 10 |
| C5 Local operation | 10 |
| C6 Explainable outputs | 8 |
| C7 Bounded completion window | 8 |
| C8 Recovery and change-cycle coverage | 8 |
| C9 Reuse potential without premature platform extraction | 6 |
| C10 Governed-path exercise breadth | 8 |
| **Total** | **100** |

### 5.2 Scoring scale (frozen)

Integer scores only, per criterion:

| Score | Meaning |
|---|---|
| 0 | Absent, contradicted by evidence, or disqualified at this criterion. |
| 1 | Minimal: partially present, or present but unevidenced (missing evidence caps a criterion at 1). |
| 2 | Adequate: meets the criterion with cited evidence. |
| 3 | Strong: meets the criterion with cited evidence and margin. |
| 4 | Exemplary: meets the criterion with cited, corroborated evidence. |

No fractional scores. No scores outside 0–4. Every score ≥ 2 requires a cited evidence reference; an unevidenced score of 2 or higher is invalid and must be corrected to 1 or justified by evidence before submission.

### 5.3 Weighted total (frozen)

`W = Σ (weight_i × score_i / 4)` for i = C1..C10, with Σ weights = 100. `W` ranges 0–100 and is reported to two decimal places.

### 5.4 Minimum passing score (frozen)

A candidate may be *recommended* only if **all** of the following hold:

1. `W ≥ 70.00`;
2. each of C1, C2, C3, and C5 scores ≥ 2;
3. zero mandatory disqualifiers triggered (see §6 and the Risk-Ceiling Register);
4. every disqualifier question answered with cited evidence (no unknowns);
5. both independent reviewers completed a full scoring pass (§7.9);
6. the operator decision boundary in §7.10 is respected (recommendation only — the operator selects).

A candidate failing any condition is recorded as NOT-PASSED with its evidence; it is never re-scored upward to reach the threshold.

## 6. Mandatory risk ceiling (summary; full register is authoritative)

A candidate is **disqualified** — regardless of weighted score — if it requires any of the following (frozen list, complete for this protocol version):

1. capital or execution authority;
2. live trading or broker credentials;
3. irreversible external effects;
4. regulated submissions;
5. public write access;
6. sensitive mass data;
7. paid external hosting;
8. cloud-only operation;
9. Vercel, Railway, SonarCloud, or Kilo;
10. external hosting authority;
11. public SaaS;
12. an LLM as canonical state;
13. a general platform rewrite disguised as an application;
14. recurring cost above `$0` for this stage.

Disqualifiers are absolute: no weighted score can offset them, and no reviewer may waive them. The full disqualifier register with detection methods, evidence requirements, and verdict fields lives in `OCE_B5_I0_RISK_CEILING_AND_DISQUALIFIER_REGISTER_v1.0.md` and is incorporated here by reference.

Quant-adjacent candidates may be considered **later only**, and only when they have zero capital authority and remain local, bounded, and reversible; they are not exempt from any item above.

## 7. Evaluation protocol (frozen before scoring)

### 7.1 Freeze order

Ratify this protocol → open candidate intake (B5-I1) → disqualifier screen → evidence collection → independent scoring → reconciliation → recommendation packet → operator decision. Scoring never precedes ratification of this protocol version.

### 7.2 Required evidence

Per criterion, the minimum evidence classes are:

| Criterion | Required evidence (minimum) |
|---|---|
| C1 | Written outcome statement + operator-testable acceptance scenarios |
| C2 | Coverage matrix mapping the candidate to OCE lifecycle stages |
| C3 | Kernel specification identifying deterministic core vs LLM-permitted surfaces |
| C4 | Bounded input inventory + canonical state schema draft |
| C5 | Local-run requirement statement showing no external service dependency |
| C6 | Sample output format demonstrating human-explainable results |
| C7 | Completion-window estimate with stated basis |
| C8 | Recovery scenario + one governed change-cycle scenario |
| C9 | Reuse inventory distinguishing reuse from platform extraction |
| C10 | Governed-path mapping across all eleven enumerated paths |

Disqualifier questions additionally require positive evidence for each "does not require" answer (deny by default: absence of evidence is not evidence of absence).

### 7.3 Missing-evidence treatment (frozen)

- Missing evidence on a scored criterion caps that criterion at score 1 and is flagged `EVIDENCE-MISSING`.
- Missing or unknown evidence on any disqualifier question sets candidate status to `INSUFFICIENT_EVIDENCE`: the candidate cannot be recommended until the evidence is supplied.
- Unknown never counts as pass. Absence of a disqualifier must be evidenced, not assumed.

### 7.4 Disqualifiers (frozen)

The fourteen items in §6, executed as a screen *before* scoring. A triggered disqualifier terminates assessment for that candidate; the record preserves what was found.

### 7.5 Tie-break rules (frozen)

Applied strictly in order, only among candidates satisfying §5.4:

1. higher C2 score;
2. then higher C1 score;
3. then higher C10 score;
4. then fewer `EVIDENCE-MISSING` flags;
5. then the operator decides between the remaining tied candidates.

No randomization, no reviewer preference, no agent discretion beyond the recorded order.

### 7.6 Dissent and uncertainty recording (frozen)

- Every reviewer records, per criterion, a confidence level: LOW / MEDIUM / HIGH.
- Any reviewer dissent is recorded **verbatim** in the decision packet and is never summarized away, edited, or deleted.
- A reconciliation that fails to converge preserves both scores, both rationales, and the unresolved divergence for the operator.

### 7.7 Conflict-of-interest and favored-candidate guard (frozen)

- Candidates enter the process under operator-assigned identifiers; the protocol and scorecard contain no candidate names.
- Every reviewer declares, before scoring, any prior advocacy, authorship, involvement, or operator-stated preference regarding any candidate; declarations are recorded in the scorecard.
- A reviewer who cannot score a candidate impartially recuses for that candidate; recusal is recorded.
- Prohibited for all actors: tailoring criteria, weights, evidence requirements, or timing to advantage any candidate; adding or removing candidates to change an outcome; suppressing a candidate's evidence.

### 7.8 Score immutability and amendment lock (frozen)

Any change to criteria, weights, disqualifiers, evidence requirements, scale, tie-breaks, minimum score, or process after **any** candidate result is visible requires a versioned amendment (`B5-I0-AMEND-001`, `-002`, …) containing: trigger, current clause, proposed text, rationale, affected scores, and operator ratification. Prior results remain recorded under the prior version; superseded results are preserved, never edited in place. If weights or scale change, every candidate is re-scored from scratch under the new version and both versions are retained.

### 7.9 Independent review procedure (frozen)

1. Two scoring passes are required, executed independently (separate sessions/agents) under this frozen protocol.
2. Each reviewer scores blind to the other's numbers until both are submitted.
3. Divergence greater than 1 point on any single criterion, or greater than 5.00 on `W`, triggers a reconciliation record.
4. Reconciliation produces either agreed scores with rationale, or a preserved dual-record of both scores plus dissent for the operator.
5. The builder of any candidate artifact may not be its sole independent reviewer.
6. The full procedural sequence, roles, and records are specified in `OCE_B5_I0_EVALUATION_AND_INDEPENDENT_REVIEW_PROCEDURE_v1.0.md`, which implements but may not alter this protocol.

### 7.10 Operator decision boundary (frozen)

Scoring and review produce a **recommendation packet only**. Selection of the reference application — and the Product Charter it produces — is the operator's decision at B5-I1. Agents may not select, may not treat a score as approval, and may not begin product scope, implementation, or code before operator selection is recorded.

### 7.11 Amendment procedure

As specified in §7.8: versioned amendments, operator-ratified, append-only, never silent, never retroactive over recorded results.

## 8. Scorecard

The blank scorecard for B5-I1 is `OCE_B5_I0_CANDIDATE_SCORECARD_TEMPLATE_v1.0.md`. It defines candidate identifiers and required fields only. It contains no winner, no scores, no selection, no product scope, and no code.

## 9. Roles

| Role | May do | May not do |
|---|---|---|
| Operator | Ratify protocol, assign candidate identifiers, receive packet, select | — (final authority) |
| Intake recorder | Enter candidates and evidence references | Score, select, alter protocol |
| Independent reviewer A / B | Score under frozen protocol, declare COI, record dissent | See others' scores before submission; alter protocol |
| Reconciler | Produce reconciliation records | Delete dissent, force convergence |
| Builder | Create candidate artifacts later at B5-I1+ | Be sole reviewer of own artifact |

## 10. Ratification block

| Field | Value |
|---|---|
| Protocol version | 1.0 |
| Frozen on | 2026-10-06 |
| Ratified by | Operator |
| Status before ratification | READY_FOR_OPERATOR_REVIEW |
| Status after ratification | OPERATOR_RATIFIED — FROZEN — selection rules frozen exactly as approved; scoring may begin at B5-I1 only under a fresh `AUTHORIZED_STAGE=B5-I1` |
| Amendments applied | none |

## 11. Prohibitions of this stage

B5-I0 does not: name a winner; score any candidate; select the application; freeze product scope; implement code; modify `oce/frontend`; edit Book 4 evidence records; touch Sensor Fabric `bloc_05` material; or authorize any cloud, broker, capital, execution, or hosting action.

## 12. Accounting

Documentation only. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. `main` unchanged. Book 4 records unchanged. B5-I1–I9 remain LOCKED.
