# OCE Golden System
## B5-I0 — Candidate Scorecard Template (BLANK — for B5-I1)

**Document ID:** OCE-B5-I0-SCORECARD-001
**Version:** 1.0
**Status:** BLANK TEMPLATE — READY_FOR_OPERATOR_REVIEW
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OCE-B5-I0-PROTOCOL-001 v1.0)
**Used at:** B5-I1 (candidate comparison), only after the protocol is ratified/frozen
**Build authorization:** None

---

## 0. Template declaration

This scorecard is intentionally blank. It defines candidate identifiers and required fields only. It does **not**:

- name a winner;
- score any candidate;
- select the application;
- freeze product scope;
- implement code.

B5-I1 remains responsible for comparing candidates and producing the operator-approved Product Charter. One copy of this template is instantiated per candidate identifier; identifiers are assigned by the operator or intake recorder without favor.

## 1. Candidate identification

| Field | Entry |
|---|---|
| Candidate identifier | `CAND-___` |
| Candidate working name (internal label only) | |
| Intake recorder | |
| Date entered | |
| Source of candidate proposal | |
| Operator-stated preference, if any (recorded, not weighted) | |

> An internal working name is a record label, not a ranking, endorsement, or selection.

## 2. Disqualifier screen (before scoring — §7.4)

Rule: any YES in the "Required?" column where the risk ceiling applies = **DISQUALIFIED**; scoring does not proceed.

| # | Disqualifier | Required by this candidate? (Y/N/UNKNOWN) | Evidence reference | Verdict |
|---|---|---|---|---|
| D1 | Capital or execution authority | | | |
| D2 | Live trading or broker credentials | | | |
| D3 | Irreversible external effects | | | |
| D4 | Regulated submissions | | | |
| D5 | Public write access | | | |
| D6 | Sensitive mass data | | | |
| D7 | Paid external hosting | | | |
| D8 | Cloud-only operation | | | |
| D9 | Vercel, Railway, SonarCloud, or Kilo | | | |
| D10 | External hosting authority | | | |
| D11 | Public SaaS | | | |
| D12 | LLM as canonical state | | | |
| D13 | General platform rewrite disguised as an application | | | |
| D14 | Recurring cost above `$0` for this stage | | | |

Screen status: `____` (PASS / DISQUALIFIED / INSUFFICIENT_EVIDENCE)
Unknown on any row ⇒ `INSUFFICIENT_EVIDENCE` (§7.3): candidate cannot be recommended until evidence is supplied.

## 3. Required evidence checklist (§7.2)

| Criterion | Required evidence class | Provided? (Y/N) | Evidence reference | `EVIDENCE-MISSING` flag |
|---|---|---|---|---|
| C1 | Outcome statement + operator-testable acceptance scenarios | | | |
| C2 | Coverage matrix across OCE lifecycle stages | | | |
| C3 | Kernel spec: deterministic core vs LLM-permitted surface | | | |
| C4 | Bounded input inventory + canonical state schema draft | | | |
| C5 | Local-run statement, no external service dependency | | | |
| C6 | Sample output format showing explainability | | | |
| C7 | Completion-window estimate with basis | | | |
| C8 | Recovery scenario + one governed change cycle | | | |
| C9 | Reuse inventory vs platform-extraction boundary | | | |
| C10 | Mapping across: identity, intent, planning, grants, workers, artifacts, evidence, review, packaging, observability, recovery | | | |

## 4. Independent scoring sheets (two passes — §7.9)

Scoring scale (0–4 integers only; ≥2 requires cited evidence; missing evidence caps at 1):

| Score | Meaning |
|---|---|
| 0 | Absent / contradicted by evidence |
| 1 | Minimal or unevidenced |
| 2 | Adequate with cited evidence |
| 3 | Strong with cited evidence |
| 4 | Exemplary with cited, corroborated evidence |

Weighted total: `W = Σ (weight_i × score_i / 4)`; `Σ weights = 100`; report to two decimals.

### 4A. Reviewer A

COI declaration (§7.7): ______________________ (DECLARE / RECUSE per candidate: ____)
Reviewed blind to Reviewer B: ☐ confirmed

| Criterion | Weight | Score (0–4) | Evidence ref | Confidence (LOW/MED/HIGH) |
|---|---:|---|---|---|
| C1 Meaningful operator outcome | 15 | | | |
| C2 Broad OCE lifecycle coverage | 15 | | | |
| C3 Deterministic non-LLM kernel | 12 | | | |
| C4 Bounded inputs and canonical state | 10 | | | |
| C5 Local operation | 10 | | | |
| C6 Explainable outputs | 8 | | | |
| C7 Bounded completion window | 8 | | | |
| C8 Recovery and change-cycle coverage | 8 | | | |
| C9 Reuse potential without premature platform extraction | 6 | | | |
| C10 Governed-path exercise breadth | 8 | | | |
| **Total** | **100** | | **W = ____.__** | |

Dissent / uncertainty notes (verbatim-preserved): ______________________

### 4B. Reviewer B

COI declaration (§7.7): ______________________ (DECLARE / RECUSE per candidate: ____)
Reviewed blind to Reviewer A: ☐ confirmed

| Criterion | Weight | Score (0–4) | Evidence ref | Confidence (LOW/MED/HIGH) |
|---|---:|---|---|---|
| C1 Meaningful operator outcome | 15 | | | |
| C2 Broad OCE lifecycle coverage | 15 | | | |
| C3 Deterministic non-LLM kernel | 12 | | | |
| C4 Bounded inputs and canonical state | 10 | | | |
| C5 Local operation | 10 | | | |
| C6 Explainable outputs | 8 | | | |
| C7 Bounded completion window | 8 | | | |
| C8 Recovery and change-cycle coverage | 8 | | | |
| C9 Reuse potential without premature platform extraction | 6 | | | |
| C10 Governed-path exercise breadth | 8 | | | |
| **Total** | **100** | | **W = ____.__** | |

Dissent / uncertainty notes (verbatim-preserved): ______________________

## 5. Reconciliation record (§7.9)

| Field | Entry |
|---|---|
| Divergence > 1 point on any criterion? (Y/N; which) | |
| Divergence on W > 5.00? (Y/N) | |
| Reconciliation outcome (AGREED / DUAL-RECORD PRESERVED) | |
| Agreed scores / rationale | |
| Unresolved dissent (verbatim, both positions) | |
| Reconciler | |

## 6. Threshold evaluation (§5.4)

| Condition | Result (PASS/FAIL) |
|---|---|
| `W ≥ 70.00` (which W: ____.__) | |
| C1 ≥ 2, C2 ≥ 2, C3 ≥ 2, C5 ≥ 2 | |
| Zero disqualifiers triggered | |
| Every disqualifier question answered with cited evidence | |
| Two independent scoring passes completed | |
| Operator decision boundary respected | |

Threshold status: `____` (RECOMMENDED / NOT-PASSED / INSUFFICIENT_EVIDENCE / DISQUALIFIED)

> NOT-PASSED and DISQUALIFIED results are recorded with evidence and never re-scored upward to reach the threshold.

## 7. Tie-break record (§7.5) — only if tied among threshold-passing candidates

| Order | Rule | Applied? | Result |
|---|---|---|---|
| 1 | Higher C2 score | | |
| 2 | Higher C1 score | | |
| 3 | Higher C10 score | | |
| 4 | Fewer `EVIDENCE-MISSING` flags | | |
| 5 | Operator decides | | |

## 8. Recommendation packet fields (recommendation ONLY — §7.10)

| Field | Entry |
|---|---|
| Candidate identifier | `CAND-___` |
| Threshold status | |
| W (Reviewer A / B / reconciled) | |
| Dissent carried forward (verbatim) | |
| Uncertainty carried forward | |
| Recommendation statement (no selection language) | |
| Packet assembled by / date | |

## 9. Operator decision (B5-I1 — only the operator may complete)

| Field | Entry |
|---|---|
| Selected candidate identifier | |
| Operator decision statement | |
| Decision date | |
| Product Charter reference (created at B5-I1) | |
| If a non-selected or below-threshold candidate chosen: recorded rationale + versioned amendment ref | |

## 10. Amendment log (§7.8)

| Amendment ID | Clause changed | Trigger | Candidate results visible at change? | Operator ratified? | Re-scored under new version? |
|---|---|---|---|---|---|
| | | | | | |

## 11. Score-change immutability attestation

| Field | Entry |
|---|---|
| Scores edited after submission? (must be NO, or amendment ref) | |
| Attested by | |

---

*End of blank template. Contains no winner, no scores, no selection, no product scope, no code.*
