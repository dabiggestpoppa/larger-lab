# OCE Golden System
## B5-I0 — Amendment AMEND-001: Sequential Dual-Pass Review (B5-I1 evaluation)

**Document ID:** OCE-B5-I0-AMEND-001
**Version:** 1.0
**Status:** OPERATOR_RATIFIED — ACTIVE
**Amendment type:** Process amendment under protocol §7.8 / §7.11 (versioned amendment; append-only; prior results — none exist — would have been preserved under the prior version)
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)
**Ratified by:** Operator, via `AUTHORIZED_STAGE=B5-I1-SEQUENTIAL-DUAL-PASS` (2026-10-07)
**Amendment log (scorecard template §10):** this amendment is the sole entry

---

## 1. Trigger

The B5-I1 authorization (`AUTHORIZED_STAGE=B5-I1-EVALUATION`) requires two genuinely independent reviewers (protocol §7.9; reviewer brief §1; launch procedure §1). The frozen mechanism required two isolated agent threads. The operator has declined to open additional chats, spawn additional agents, or supply external reviewer threads, and has instead authorized — by explicit ratification through this amendment — a replacement mechanism executed inside the existing conversation.

## 2. Current clause (superseded for this evaluation)

Protocol §7.9: "Two scoring passes are required, executed independently (separate sessions/agents) under this frozen protocol. Each reviewer scores blind to the other's numbers until both are submitted." Reviewer brief §1 and launch procedure §1–§3 specify the two-isolated-thread mechanics, absolute blindness, and the `BLOCKED_REVIEWER_ISOLATION_FAILED` failure token.

## 3. Amended text (replacement mechanism)

For the B5-I1 evaluation only, the two-pass requirement is executed as follows:

1. **One agent performs two ordered, separately sealed passes** in this same conversation:
   - **Pass A — evidence/compliance pass:** executes the D1–D14 screen and scores C1–C10 for every candidate per the frozen protocol, treating the packet evidence at face value and auditing compliance of each packet against the frozen evidence classes.
   - **Pass B — adversarial/red-team pass:** re-runs D1–D14 from scratch and re-scores C1–C10 with an explicit falsification mandate: challenging Pass A's assumptions, citations, missing evidence, feasibility judgments, hidden coupling, boundedness, reversibility, local-only operation, and risk classification, and attacking every qualifying claim.
2. Pass A is sealed (SHA-256 + dedicated commit + push) before Pass B begins authoring; Pass B is sealed before reconciliation begins. Both seals are recorded in the reconciliation record.
3. Both passes independently execute D1–D14 and score C1–C10 for every candidate. All frozen scoring rules apply to both passes unchanged: weights 15/15/12/10/10/8/8/8/6/8; integer 0–4; ≥2 requires cited evidence; missing criterion evidence caps at 1 with `EVIDENCE-MISSING`; D1–D14 screen before scoring; threshold `W ≥ 70.00` with floors C1/C2/C3/C5 ≥ 2; tie-break C2→C1→C10→fewer flags→operator; no score changed to reach threshold; dissent preserved verbatim.
4. Divergence handling is unchanged: criterion divergence greater than 1 point or weighted-total divergence greater than 5.00 requires an explicit reconciliation record with cited evidence; unresolved disagreements remain preserved verbatim in the decision packet; no forced convergence; no averaging.

## 4. Honest limitations (must be restated on every derived artifact)

- **Pass A and Pass B are NOT independent.** They are performed by the same agent in the same context.
- **Pass A and Pass B are NOT blind to each other.** Pass B is performed after Pass A is sealed and may legitimately build on it; its integrity derives solely from its explicitly different adversarial mandate, not from ignorance.
- **No result may ever be described as independently reviewed, blind-scored, or dual-reviewer verified.** The decision packet must state the sequential dual-pass mechanism and its limitations verbatim.
- **Conflict of interest:** the reviewing agent is also the author of the intake register and evidence packets (protocol §7.9.5 builder-not-sole-reviewer rule is NOT satisfied in its original form). The operator has accepted this trade-off explicitly by ratifying this amendment. This COI is recorded in both scorecard headers.

## 5. What this amendment does NOT change

- All B5-I0 criteria (C1–C10), definitions, weights, scale, thresholds, floors, disqualifiers D1–D14, tie-break order, anti-drift requirements, dissent rules, missing-evidence rules, and the operator decision boundary (protocol §7.10) remain frozen and unchanged.
- Candidate packets remain frozen until both passes are sealed; no packet is edited during or after review (reviewer observations are recorded on scorecards only).
- The prior two-isolated-reviewer procedure (`OCE_B5_I1_REVIEWER_LAUNCH_v1.0.md`, reviewer brief §1) is **preserved as historical evidence**, superseded for this evaluation, not deleted or rewritten.
- The replacement satisfies the operator's requirement for **two analytical lenses**; it does **not** satisfy, and must never be claimed to satisfy, external reviewer independence.
- **No candidate result existed before this amendment.** No scorecard, score, ranking, or recommendation existed in any artifact at ratification time (verified: no `OCE_B5_I1_SCORECARD_*` file exists at commit `6d1d6f0a…`).

## 6. Reference updates applied (necessary only)

| Artifact | Update | Rationale |
|---|---|---|
| `OCE_B5_I1_REVIEWER_BRIEF_v1.0.md` | New §1a banner referencing this amendment | Supersedes §1 isolation clauses for this evaluation; obligations restated |
| `OCE_B5_I1_REVIEWER_LAUNCH_v1.0.md` | Banner before §1 referencing this amendment | Supersedes §1–§3 isolation mechanics; §4 handoff applies after both sequential seals |
| `OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` | B5-I1 status row + decision-history entry | Records the ratified mechanism change truthfully |
| `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` | **Unchanged** (frozen-ratified body; amendment incorporated by reference per §7.8) | §7.8 amendments are external versioned documents |
| `OCE_B5_I0_ACCEPTANCE-MATRIX_v1.0.md` | **Unchanged** (proves B5-I0 representation, which is not altered) | No B5-I0 requirement changed |

## 7. Ratification block

| Field | Value |
|---|---|
| Amendment ID | B5-I0-AMEND-001 |
| Version | 1.0 |
| Trigger | Operator declined additional chats/agents/external reviewer threads for B5-I1 review capacity |
| Clause(s) changed | Protocol §7.9 execution mechanism (two isolated reviewers → sequential dual pass); reviewer brief §1; launch procedure §1–§3 |
| Affected scores | None — no candidate result existed before this amendment |
| Candidate results visible at change? | NO |
| Operator ratified? | YES — via `AUTHORIZED_STAGE=B5-I1-SEQUENTIAL-DUAL-PASS`, 2026-10-07 |
| Re-score required? | N/A — scoring begins under this amendment |
| Status | OPERATOR_RATIFIED — ACTIVE |

## 8. Accounting

Documentation only. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. No candidate scored, favored, or selected by this amendment. Append-only commit; no amend, squash, rebase, reset, or force-push.
