# OCE Golden System
## B5-I1 — Reviewer Launch Procedure (two isolated threads)

**Document ID:** OCE-B5-I1-REVIEWER-LAUNCH-001
**Version:** 1.0
**Status:** FROZEN_LAUNCH_PROCEDURE
**Evidence base commit:** `52843ffc11ff97511ec7e7242f6adc7083290360` (`B5-I1-P1: record candidate intake and evidence packets`)
**Review base commit:** the head of `oce-book-5-i1` at the moment both reviewer threads start (this commit). Both reviewers must verify they are on the same HEAD SHA before scoring and record it on their scorecard.

---

> **AMEND-001 BANNER (2026-10-07, OPERATOR_RATIFIED):** `OCE_B5_I0_AMEND-001_SEQUENTIAL_DUAL_PASS_REVIEW_v1.0.md` supersedes §1–§3 (two-isolated-thread mechanics, absolute blindness, `BLOCKED_REVIEWER_ISOLATION_FAILED`) for the B5-I1 evaluation: one agent performs two ordered, separately sealed passes in one context (Pass A evidence/compliance, Pass B adversarial/red-team); the passes are NOT independent and NOT blind. §4 applies after both sequential seals. §1–§4 below are preserved verbatim as historical evidence.

## 1. Isolation mechanics

- Reviewer A and Reviewer B are separate agent threads (separate contexts, separate sessions). They never communicate.
- Each reviewer creates its **own worktree and branch** from the review base commit:
  - Reviewer A: branch `oce-book-5-i1-review-a`
  - Reviewer B: branch `oce-book-5-i1-review-b`
- Neither reviewer may fetch, log, read, or inspect the other's branch, files, or commits at any time. Blindness is absolute until both seals are recorded.
- Neither reviewer modifies any file under `docs/oce-golden-system/` except creating their own single new scorecard file.

## 2. Per-reviewer procedure (identical for A and B)

1. `git worktree add <dir> -b <review-branch> <review-base-sha>`; verify `git rev-parse HEAD` equals the review base; record it.
2. Read, in order: `OCE_B5_I1_REVIEWER_BRIEF_v1.0.md`, `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (§4–§7), `OCE_B5_I0_CANDIDATE_SCORECARD_TEMPLATE_v1.0.md`, and the five packets `OCE_B5_I1_CAND-00X_EVIDENCE_PACKET_v1.0.md` (X = 1..5).
3. Declare conflicts of interest on the scorecard header (advocacy, authorship, involvement, operator preference); recuse per candidate if impartiality is impossible.
4. For **each** candidate CAND-001…CAND-005: execute the D1–D14 screen from packet §14 (trigger → `DISQUALIFIED`; unevidenced/unknown → `INSUFFICIENT_EVIDENCE`), then score C1–C10 with integers 0–4. Every score ≥ 2 cites its packet section; missing criterion evidence caps that criterion at 1 with an `EVIDENCE-MISSING` flag. Record LOW/MEDIUM/HIGH confidence and verbatim reasoning per criterion.
5. Compute `W = Σ(weight × score / 4)` per candidate; apply the threshold rule `W ≥ 70.00` with floors (C1, C2, C3, C5 ≥ 2, zero disqualifiers, evidenced, full dual-pass context) only as a *recorded* per-candidate threshold result. Do NOT rank candidates against each other; do NOT write a recommendation.
6. Save exactly one file: `OCE_B5_I1_SCORECARD_REVIEWER-A_v1.0.md` (A) or `OCE_B5_I1_SCORECARD_REVIEWER-B_v1.0.md` (B), instantiated from the blank template, identifiers only.
7. Seal: compute SHA-256 of the file; commit it alone with message `B5-I1-REVIEW: scorecard <REVIEWER> (sealed)`; push the review branch; report to the operator: commit SHA, file SHA-256, timestamp, review base SHA, COI declaration. This quadruple is the seal.
8. Stop. No reconciliation, no comparison, no further commits on the review branch.

## 3. Failure handling

- If a reviewer cannot establish its own isolation (e.g., it can see the other reviewer's artifacts), it stops with `BLOCKED_REVIEWER_ISOLATION_FAILED` and reports.
- Reviewer errors are recorded as observations on the scorecard; evidence packets are never edited.

## 4. After both seals exist

The operator confirms both seals to the reconciliation context. Only then are both scorecards revealed, imported unchanged, and reconciled per `OCE_B5_I0_EVALUATION_AND_INDEPENDENT_REVIEW_PROCEDURE_v1.0.md` §3 steps 8–11 (divergence triggers >1 point per criterion or >5.00 on `W`; AGREED or DUAL-RECORD-PRESERVED; dissent preserved verbatim; no forced convergence).
