# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 0 — CONSTITUTION, EPISTEMICS, AND PROGRAM GOVERNANCE
## Ratification Packet v0.2 (Reconciled)

**Document ID:** CSIA-B0-PACKET-001
**Version:** 0.2
**Status:** FROZEN_FOR_REVIEW — AWAITING OPERATOR RATIFICATION — **NOT RATIFIED**
**Supersedes:** `CSIA_BOOK_0_RATIFICATION_PACKET.md` (v0.1, preserved unmodified)
**Depends on:** `CSIA_CONSTITUTION_v0.2.md` (unratified), `CSIA_CONSTITUTION_REVIEW_v0.1.md`, `CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md`
**Planning branch:** `agent/crypto-systems-intelligence-atlas-plan`
**Implementation authority:** NONE

---

# 0. Why a v0.2 packet

v0.1 was sound on substance but contained three reconciliation defects found in session 2:

1. Its verdict language ("no critical blockers remain") preceded the bootstrap-authority repair: it referenced Program Ledger authority derived from an **unratified** Constitution v0.2 without flagging the dependency (session-2 Phase 1B finding).
2. It did not surface R-1A-5 (IBC voucher representation) as a Book-1-linked decision the operator would face immediately after D1–D6, leaving the decision surface fragmented across documents.
3. It stated `READY_FOR_OPERATOR_RATIFICATION = TRUE` without the explicit "ready ≠ ratified" distinction this v0.2 makes normative.

v0.2 repairs these without changing the ratified-text content of v0.1 (mission, authority, epistemics, claim states, contradiction, causality, uncertainty, sources, amendment, anti-drift — all carried forward unchanged; see v0.1 for the full text of sections 1–10, which remain the operative contract).

**v0.1 → v0.2 changelog:**

| Change | Reason |
|---|---|
| Added readiness counters (§12) with exact N values | Session-2 Phase 5 requirement |
| Explicit "ready ≠ ratified" rule (§13) | Session-2 Phase 5 requirement |
| R-1A-5 surfaced as immediately-following decision (§11.1) | Decision-surface completeness |
| Bootstrap-authority caveat on D6 (§11, D6 entry) | Session-2 Phase 1B finding |
| Decision references now point to the decision packet as the canonical options analysis | Single source for options |

---

# 1–10. Operative contract sections

Sections 1–10 of v0.1 (Mission; Authority; Epistemic hierarchy + tier-promotion matrix; Claim states; Contradiction handling; Causality language; Uncertainty; Source hierarchy; Amendment procedure; Anti-drift rules) are carried forward **unchanged** as the operative contract of Book 0. `CSIA_BOOK_0_RATIFICATION_PACKET.md` (v0.1) remains preserved and readable; ratification of this v0.2 adopts those sections as written.

No section content changed between v0.1 and v0.2; only the decision surface and readiness accounting below were reconciled.

---

# 11. Explicit operator decisions required

## 11.1 The blocking set: D1–D6

Full options analysis, consequences, reversibility, and recommended defaults for each decision live in `CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md` (Part I). Summary:

| ID | Exact question | Artifact affected | Reversibility |
|---|---|---|---|
| D1 | Ratify Constitution v0.2 as governing doctrine (with/without per-correction objections to CR-01..CR-07)? | Entire Constitution v0.2; every downstream status block | Via amendment (§36) |
| D2 | Accept the claim-state machine (§7.1) as fixed? | Constitution §7.1; Book 2 2D; Book 6 6C | Via amendment; cheap now |
| D3 | Accept the tier-to-claim-state promotion matrix (§6.1) as fixed? | Constitution §6.1; Book 2 2D | Via amendment; cheap now |
| D4 | Confirm the descriptive/prescriptive boundary wording (§5.3a)? | Constitution §5.3a; Books 6/8/9 surfaces | Via amendment; vocabulary crystallizes early |
| D5 | Confirm anti-drift audit cadence (per-book + per-phase)? | Constitution §37; Book 0 0C.4; Book 9E | Fully reversible (procedural) |
| D6 | Confirm the Program Ledger as sole next-step authority upon this ratification? *(Bootstrap caveat: this decision is what converts the ledger's PROPOSED_NEXT_STEP_AUTHORITY into actual authority — until D6 is recorded, the ledger binds nothing.)* | Constitution §G; CSIA_PLANNING_PROGRESS.md | Via amendment |

**Bootstrap note (session-2 repair):** D6's effect is conditional on D1. If D1 is rejected/returned, D6 has no object to confirm — the ledger remains bookkeeping-only regardless.

## 11.2 The immediately-following Book 1 decision: R-1A-5

- **Exact question:** How are IBC vouchers (channel-bound, non-custodial asset representations) represented in Book 1 identity? Options A (channel deployments), B (attribute-level — rejected as violating Bloc 1D record rules), C (separate REALIZATION class — recommended).
- **Full stress-test analysis:** `CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md` Part II.
- **Blocking:** Bloc 1A freeze only (not Book 0 ratification).
- **Timing:** decide immediately after D1–D6, before any Bloc 1A ratification record is completed.

## 11.3 Deferred decisions (not blocking)

| ID | Decision | Gate |
|---|---|---|
| D7 | Capital Field reconciliation | Before Book 5 planning |
| D8 | CSIA↔Sensor shared-seam ownership | Before Book 8 planning |

---

# 12. Readiness accounting

```text
CONSTITUTION_TEXT_DEFECTS_REMAINING = 0

    Basis: the v0.1 constitutional review found 7 critical + 13 major +
    10 minor issues. All 7 critical issues are addressed in v0.2 text
    (CR-01..CR-07, each traceable inline). No new constitutional-text
    defects were found in session 2 (the defects found were in the
    ledger, the stress-matrix verdict wording, and the session report —
    all repaired outside the Constitution). MAJOR/MINOR items were
    addressed or consciously accepted as reviewed; they do not block
    ratification.

OPERATOR_DECISIONS_REMAINING = 7

    D1, D2, D3, D4, D5, D6  (Book 0 blocking set)
    R-1A-5                  (Book 1 Bloc 1A freeze; decided immediately after)

    (D7, D8 are deferred by design and not counted as remaining for
    ratification purposes.)

BOOK_0_READY_FOR_OPERATOR_RATIFICATION = TRUE
```

# 13. Ratification rule

**"Ready for ratification" does NOT mean "ratified."**

```text
READY_FOR_OPERATOR_RATIFICATION = TRUE     (readiness assessment)
OPERATOR_RATIFIED               = FALSE    (no decision has been provided
                                            by the operator in any session)
```

`OPERATOR_RATIFIED = TRUE` may be set **only** when the operator explicitly provides decisions D1–D6 (accepting, objecting to, or returning the underlying texts), recorded per Constitution §5.4 in the Operator Decision Log. No agent session may set it. Silence is not ratification (Constitution §0).

**If the operator ratifies:** the exact decisions to make are D1–D6 per §11.1 (options in the decision packet), then R-1A-5 per §11.2, each recorded in the Operator Decision Log in the format specified by the decision packet.

**If any decision is objected/returned:** the affected text returns to revision; this packet's readiness counters are recomputed in a v0.3; no partial ratification shortcuts.

End of Book 0 ratification packet v0.2.
