# OCE Golden System
## B5-I0 — Evaluation and Independent-Review Procedure

**Document ID:** OCE-B5-I0-EVAL-PROC-001
**Version:** 1.0
**Status:** OPERATOR_RATIFIED — FROZEN BEFORE ANY CANDIDATE IS SCORED
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OCE-B5-I0-PROTOCOL-001 v1.0)
**Companion register:** `OCE_B5_I0_RISK_CEILING_AND_DISQUALIFIER_REGISTER_v1.0.md`
**Stage scope:** `AUTHORIZED_STAGE=B5-I0` only; execution of scoring occurs at B5-I1
**Build authorization:** None. Documentation only.

---

## 1. Purpose

This procedure specifies *how* the frozen selection protocol is executed, reviewed, and audited at B5-I1. It implements the protocol; it may not alter criteria, weights, disqualifiers, scale, thresholds, tie-breaks, or the operator decision boundary. Any conflict resolves in favor of the protocol, and the conflict itself is recorded as a contradiction.

## 2. Preconditions (all must hold before scoring begins)

1. Protocol v1.0 ratified and frozen by the operator (ratification block completed).
2. Risk register v1.0 frozen; disqualifier screen tooling ready.
3. Scorecard template v1.0 instantiated as blank copies per candidate identifier.
4. Two independent reviewers appointed; neither is the builder of any candidate artifact (protocol §7.9.5).
5. Candidate identifiers assigned by operator/intake recorder; no candidate identity embedded in scoring sheets beyond the identifier.
6. Amendment log empty or fully ratified (no silent rule drift).
7. `main`, Book 4 records, `oce/frontend`, and Sensor Fabric material are untouched by B5-I0 (validated in the B5-I0 acceptance matrix).

If any precondition fails, scoring does not start; status remains READY_FOR_OPERATOR_REVIEW.

## 3. Sequence

| Step | Action | Actor | Record produced |
|---|---|---|---|
| 1 | Ratify + freeze protocol | Operator | Ratification block (protocol §10) |
| 2 | Assign candidate identifiers | Operator / intake recorder | Scorecard §1 copies |
| 3 | Disqualifier screen (D1–D14) | Screened by one reviewer + verification by second | Scorecard §2 |
| 4 | Evidence collection against §7.2 classes | Intake recorder | Scorecard §3 |
| 5 | Unknown-resolution loop: any UNKNOWN → request evidence; unresolved ⇒ `INSUFFICIENT_EVIDENCE` | Intake recorder | Evidence requests, scorecard §2/§3 |
| 6 | Reviewer A scoring, blind to B | Reviewer A | Scorecard §4A |
| 7 | Reviewer B scoring, blind to A | Reviewer B | Scorecard §4B |
| 8 | Unlock comparison; check divergence triggers | Reconciler | Scorecard §5 |
| 9 | Reconciliation: agreed scores OR dual-record with verbatim dissent | Reconciler | Scorecard §5 |
| 10 | Threshold evaluation (§5.4 conditions 1–6) | Reconciler | Scorecard §6 |
| 11 | Tie-break only if tied among threshold-passers (strict order C2→C1→C10→fewer flags→operator) | Reconciler | Scorecard §7 |
| 12 | Assemble recommendation packet (recommendation only) | Packet assembler | Scorecard §8 |
| 13 | Operator decision at B5-I1; Product Charter if selecting | **Operator only** | Scorecard §9 + Product Charter |
| 14 | Close-out: immutability attestation, amendment log check | Reconciler | Scorecard §§10–11 |

Steps may not be reordered; steps 6–7 may not begin before steps 3–5 close; step 13 may not occur before step 12.

## 4. Independent-review rules

1. **Blind dual scoring.** Each reviewer submits before seeing the other's numbers. Blindness is attested in the scorecard.
2. **COI declaration first.** Every reviewer declares advocacy, authorship, involvement, or operator-stated preference before touching a scorecard (protocol §7.7); recusal when impartiality cannot be maintained.
3. **Divergence triggers.** >1 point on any criterion, or >5.00 on `W`, mandates a reconciliation record.
4. **No forced convergence.** Reconciliation ends in AGREED (with rationale) or DUAL-RECORD PRESERVED (both scores, both rationales, unresolved divergence verbatim for the operator). Pressure to converge is itself a recorded observation.
5. **Dissent is append-only.** Verbatim preservation; never summarized away, edited, or deleted.
6. **Confidence capture.** LOW/MED/HIGH per criterion feeds the packet's uncertainty section; LOW confidence on a threshold-critical criterion (C1, C2, C3, C5) is flagged explicitly for the operator.
7. **Re-review prohibited after result visibility** unless triggered by a ratified versioned amendment (protocol §7.8), which forces full re-scoring of *all* candidates under the new version with prior results retained.

## 5. Missing-evidence handling (operational)

| Situation | Action | Status |
|---|---|---|
| Criterion evidence absent | Cap criterion at 1; flag `EVIDENCE-MISSING` | Scoring continues |
| Disqualifier evidence absent/UNKNOWN | Request evidence; block recommendation | `INSUFFICIENT_EVIDENCE` |
| Evidence arrives after scoring (pre-decision) | Attach; reviewer may update only if no candidate result has been made visible to anyone outside the review pair; otherwise versioned amendment path | Recorded |
| Evidence arrives after any result is visible | Amendment path only (protocol §7.8); never in-place score edits | Recorded |

## 6. Recommendation packet contents (recommendation only — never a selection)

- candidate identifier(s), threshold status, reconciled or dual `W` values;
- disqualifier screen outcomes with evidence refs;
- per-criterion scores with confidence levels;
- verbatim dissent and uncertainty sections;
- tie-break record if applied;
- explicit statement: "This packet recommends; only the operator selects (protocol §7.10).";
- amendment log state (expected: none).

## 7. Anti-favored-candidate controls (audit checklist)

| Control | Verification |
|---|---|
| Criteria/weights match protocol exactly | Diff scorecard header weights vs protocol §5.1 |
| No criterion added/removed/renamed | Section 4 tables match C1–C10 |
| Disqualifier screen precedes scoring | Timestamps in scorecard §2 < §4 |
| Two blind passes attested | Scorecard §4A/§4B attestations |
| COI declarations present | Scorecard §4 headers |
| Dissent preserved verbatim | Scorecard §5/§4 notes |
| No score edited post-submission | Scorecard §11 attestation |
| No selection language in packet | Packet §8 review |
| Amendment log consistent | Scorecard §10 |

Any control failure ⇒ status `BLOCKED` for that candidate's packet until corrected; the failure itself is recorded.

## 8. Stopping rules

Stop and report `BLOCKED` (do not improvise) when: a disqualifier answer cannot be evidenced; reviewers diverge irreconcilably on facts (not just preference); an amendment is needed mid-process; or any actor attempts score edits, criterion tailoring, candidate add/remove to change an outcome, or selection language before operator decision.

## 9. Explicit non-authority

This procedure does not select an application, freeze product scope, implement code, authorize merges, rerun workflows, modify Book 4 records, touch `oce/frontend`, edit Sensor Fabric `bloc_05` material, or authorize any cloud, broker, capital, execution, or hosting action.

## 10. Accounting

Documentation only. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. No candidate scored, favored, or selected by this procedure.
