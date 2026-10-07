# OCE Golden System
## B5-I1 — Reviewer Brief (frozen procedure for both independent reviewers)

**Document ID:** OCE-B5-I1-REVIEWER-BRIEF-001
**Version:** 1.0
**Status:** FROZEN_INTAKE_INPUT — restates ratified rules; alters nothing
**Governing authorities:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` §§5–§7 (OPERATOR_RATIFIED — FROZEN); `OCE_B5_I0_EVALUATION_AND_INDEPENDENT_REVIEW_PROCEDURE_v1.0.md`; `OCE_B5_I0_CANDIDATE_SCORECARD_TEMPLATE_v1.0.md`
**Intake commit:** the commit on `oce-book-5-i1` that contains `OCE_B5_I1_INTAKE_REGISTER_v1.0.md` and packets CAND-001…CAND-005 (recorded in the reconciliation record)

---

> **AMEND-001 BANNER (2026-10-07, OPERATOR_RATIFIED):** `OCE_B5_I0_AMEND-001_SEQUENTIAL_DUAL_PASS_REVIEW_v1.0.md` supersedes §1 (isolation rules) for the B5-I1 evaluation: one agent performs two ordered, separately sealed passes — Pass A (evidence/compliance) and Pass B (adversarial/red-team). The passes are NOT independent and NOT blind and must never be described as such; the reviewer/builder COI is recorded on both scorecards. §2–§4 scoring/sealing obligations apply to both passes unchanged. §1 below is preserved verbatim as historical evidence.

## 1. Independence rules (verbatim requirements, unaltered)

- Two reviewers, Reviewer A and Reviewer B, execute in isolated contexts created from the same frozen intake commit.
- Neither reviewer may see the other's scores, rationale, confidence, or branch before both submissions are sealed.
- Neither reviewer may modify candidate evidence. Errors or gaps are recorded as observations, never edited.
- The intake author may not be any candidate's sole reviewer.
- Each reviewer declares conflicts of interest (advocacy, authorship, involvement, operator-stated preference) before scoring; recusal where impartiality is impossible.
- Reviewer artifacts use distinct filenames and distinct commit identities.

## 2. Scoring inputs (identical for both reviewers)

- The five evidence packets `OCE_B5_I1_CAND-00X_EVIDENCE_PACKET_v1.0.md` (X = 1..5) at the frozen intake commit.
- The frozen protocol, register, and scorecard template.
- The neutral identifiers CAND-001…CAND-005 are used on all scoring sheets. Working names appear only in the intake register.

## 3. Scoring obligations (per candidate, per protocol)

- Score C1–C10 with integer 0–4; every score ≥ 2 requires a cited evidence reference (packet section); missing criterion evidence caps the criterion at 1 with an `EVIDENCE-MISSING` flag.
- Execute the D1–D14 screen from packet §14 before scoring; any triggered disqualifier → `DISQUALIFIED`; any unevidenced/unknown disqualifier answer → `INSUFFICIENT_EVIDENCE` for that candidate.
- Record LOW/MEDIUM/HIGH confidence per criterion; record verbatim dissent; declare COI on the scorecard header.
- Do not converge, coordinate, or discuss with the other reviewer.

## 4. Output artifact and sealing

Each reviewer produces one scorecard file, instantiated from the blank template:

- Reviewer A: `OCE_B5_I1_SCORECARD_REVIEWER-A_v1.0.md`
- Reviewer B: `OCE_B5_I1_SCORECARD_REVIEWER-B_v1.0.md`

Sealing procedure (each reviewer, independently):

1. Complete the scorecard for all admitted candidates (or record recusal/disqualification rows).
2. Compute SHA-256 of the completed file.
3. Commit the file alone with a commit message in the form `B5-I1-REVIEW: scorecard <REVIEWER> (sealed)` on the review branch/workspace.
4. Record: commit SHA, file SHA-256, timestamp, and COI declaration — this quadruple is the seal.

A sealed scorecard is never edited. Corrections require a new sealed artifact; the superseded seal remains recorded.

## 5. Handoff to reconciliation

Only after both seals exist may the artifacts be revealed to the reconciler, who imports both unchanged, computes divergence, and follows `OCE_B5_I0_EVALUATION_AND_INDEPENDENT_REVIEW_PROCEDURE_v1.0.md` §3 steps 8–11 and §4 rules (no forced convergence; dual-record preserved where applicable).

## 6. Prohibitions (restated)

No reviewer selects an application, freezes product scope, implements code, or produces selection language. Output is a scored instrument for the reconciler and the operator decision packet only.
