# OCE Golden System
## B5-I0 — Risk Ceiling and Disqualifier Register

**Document ID:** OCE-B5-I0-RISK-REGISTER-001
**Version:** 1.0
**Status:** READY_FOR_OPERATOR_REVIEW — FROZEN BEFORE ANY CANDIDATE IS SCORED
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (§6, §7.4)
**Stage scope:** `AUTHORIZED_STAGE=B5-I0` only
**Build authorization:** None. Documentation only.

---

## 1. Purpose

This register is the authoritative, frozen enumeration of the mandatory risk ceiling for Block 5 reference-application selection. It is incorporated into the selection protocol by reference. Disqualifiers are absolute: they are evaluated *before* scoring, no weighted score can offset them, and no reviewer, agent, or builder may waive, soften, re-interpret, or batch-remove them.

## 2. Operating doctrine

- **Screen before score.** The disqualifier screen runs first (protocol §7.4). A triggered disqualifier terminates assessment; the record preserves what was found.
- **Deny by default.** UNKNOWN or unevidenced answers to any disqualifier question set status `INSUFFICIENT_EVIDENCE` (protocol §7.3); the candidate cannot be recommended until evidence is supplied. Absence of evidence is not evidence of absence.
- **No offset.** `W ≥ 70.00` is meaningless when any disqualifier triggers (protocol §5.4).
- **Local-only baseline.** The Book 4 local-only topology decision carries forward: local operation is the default; external hosting authority = none; recurring cost for this stage = `$0`.
- **Frozen list.** Adding, removing, or rewording any item requires a versioned amendment under protocol §7.8 with operator ratification, visible before any candidate result exists or with full re-score afterward.

## 3. Mandatory disqualifiers (frozen list)

| ID | Disqualifier | Rationale | Evidence required to clear |
|---|---|---|---|
| D1 | Capital or execution authority | Capital boundary (Constitution Art. XV / B0.C2.S4); `capital.authority = none` | Statement that the candidate routes no capital and grants no execution authority |
| D2 | Live trading or broker credentials | Book 9 gates; no credential path in reference build | No broker integration, no credential storage, no live/paper routing claims |
| D3 | Irreversible external effects | Constitution Principle 9 (reversible first) | Description of effects showing full local reversibility |
| D4 | Regulated submissions | External regulatory exposure outside program scope | No submission, filing, or regulated-data pathway |
| D5 | Public write access | Private by default (Constitution Principle 11 / Art. XIII) | No unauthenticated or public write surface |
| D6 | Sensitive mass data | Data minimization; retention doctrine (B0.C5.S4) | Input inventory bounded, non-sensitive, enumerated |
| D7 | Paid external hosting | Recurring cost ceiling `$0` for this stage | Runs on local infrastructure; no paid hosting dependency |
| D8 | Cloud-only operation | Local-only topology (Book 4 final decision) | Local run path proven without cloud dependency |
| D9 | Vercel, Railway, SonarCloud, or Kilo | Outside the governance boundary (Book 4 §24) | No dependency on, integration with, or configuration for any of the four |
| D10 | External hosting authority | External hosting authority = none (Book 4 §24) | Candidate requires no external deployment authority |
| D11 | Public SaaS | Block 5 non-goals; private by default | No public SaaS dependency for core operation |
| D12 | LLM as canonical state | Constitution Article V; deterministic kernel requirement | Kernel spec shows deterministic canonical state; LLM limited to input proposal/output interpretation |
| D13 | General platform rewrite disguised as an application | Block 5 block contract; C9 anti-extraction rule | Scope is one application, not a platform; no premature SDK/framework extraction |
| D14 | Recurring cost above `$0` for this stage | Cost ceiling for B5-I0/I1 stage | No recurring paid dependency of any kind |

## 4. Quant-adjacent candidates (conditional rule)

Quant-adjacent candidates may be considered **later only**, and only when all of the following hold simultaneously:

1. zero capital authority (D1 cleared with evidence);
2. operation remains local (D8 cleared);
3. inputs and state remain bounded (C4 evidence present);
4. effects remain reversible (D3 cleared);
5. no item in §3 triggers.

Being quant-adjacent is not itself a disqualifier and not itself a merit; the same screen and the same evidence rules apply. This stage does not evaluate, rank, or pre-commit to any quant-adjacent candidate.

## 5. Standing exclusions carried from Book 4 (context, not candidate evaluation)

Recorded for boundary clarity; these are not candidates and not subject to scoring:

- SonarQubeCloud, Kilo Code Bot, Vercel, Railway — detached from `larger-lab`, outside the governance boundary, **not classified as passing** by this register.
- Freebuff — outside scope, untouched.
- `oce/frontend` — internally owned, untouched during B5-I0.
- Sensor Fabric `bloc_05` material — unrelated program; not edited, executed, or referenced as authority.
- Book 4 evidence records (`B4-EVIDENCE-RECORD.md`, `B4-ACCEPTANCE-MATRIX.md`) — immutable historical evidence; not appended to.

## 6. Screen execution record (blank — completed per candidate at B5-I1)

| Field | Entry |
|---|---|
| Candidate identifier | `CAND-___` |
| Screen date | |
| Screened by | |
| D1..D14 verdicts (each PASS/DISQUALIFIED + evidence ref) | |
| UNKNOWN count (must be 0 to proceed) | |
| Overall: PASS / DISQUALIFIED / INSUFFICIENT_EVIDENCE | |
| Amendment refs (should be none) | |

## 7. Accounting

Documentation only. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. No candidate scored, favored, or selected by this register.
