# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## OPERATOR RATIFICATION BALLOT v0.1

**Document ID:** CSIA-BALLOT-001
**Version:** 0.1
**Status:** OPEN — NO DECISIONS RECORDED
**Source of truth for options:** `CSIA_OPERATOR_DECISION_PACKET_BOOK0_BOOK1_v0.1.md` (no new options are created here)
**Purpose:** Let the operator decide D1–D6 + R-1A-5 without reading the planning corpus. Each item: question, default, meaning, alternative, unlock, reversibility.
**Rules:** This ballot decides nothing by itself. Decisions bind only when recorded in the Operator Decision Log (Constitution v0.2 §5.4). Silence is not ratification.

---

## D1 — Constitution v0.2 ratification

- **Question:** Do you ratify `CSIA_CONSTITUTION_v0.2.md` as the governing doctrine of CSIA?
- **Recommended default: RATIFY AS WRITTEN** — every correction in v0.2 closes a defect the review found (authority gaps, missing epistemic rules); nothing was loosened.
- **Accepting the default means:** CSIA has a real constitution; all downstream planning binds to its rules.
- **Meaningful alternative:** RATIFY WITH NAMED OBJECTIONS (list which corrections you reject → those become v0.3 items) or RETURN FOR REVISION (name the defects).
- **Unlocks:** Book 0 closure, and every Book 1 bloc freeze (all four are gated on D1).
- **Reversibility:** Yes, via constitutional amendment — but ratify-then-amend is costlier than objecting now.
- **Choices: RATIFY AS WRITTEN / RATIFY WITH NAMED OBJECTIONS / RETURN FOR REVISION**

## D2 — Claim-state machine

- **Question:** Is the claim-state machine (9 states, legal/illegal transitions, dependent-claim propagation) accepted as fixed?
- **Recommended default: ACCEPT**
- **Accepting means:** in plain terms — every claim in CSIA carries an honest label (observed / declared / inferred / contested…), inference can never silently masquerade as observation, and if a claim collapses, everything depending on it is flagged for re-check instead of quietly staying "true."
- **Meaningful alternative:** AMEND — change specific transitions (e.g., stricter independence rules) before anything is built.
- **Unlocks:** Book 2 promotion design and Book 6 state vectors inherit a fixed epistemic spine.
- **Reversibility:** Amendable later, but the transitions become load-bearing in Book 2 — cheapest to fix now.
- **Choices: ACCEPT / AMEND (specify)**

## D3 — Evidence-tier → claim-state promotion matrix

- **Question:** Is the matrix (which evidence tier can promote a claim to which state) accepted as fixed?
- **Recommended default: ACCEPT**
- **Accepting means:** in plain terms — official docs and on-chain state (E0) can establish facts; first-party declarations (E1) establish only "they say so"; press and social posts (E4) can prove a *narrative exists* but can never establish that a claimed change is *true*.
- **Meaningful alternative:** AMEND — e.g., require two independent sources everywhere (more rigorous, slower) or relax some bars (faster, riskier).
- **Unlocks:** Book 2 evidence thresholds and all chain/protocol promotion rules.
- **Reversibility:** Amendable; it's a table, so changes are cheap before population and expensive after.
- **Choices: ACCEPT / AMEND (specify)**

## D4 — Descriptive vs prescriptive boundary

- **Question:** Is the §5.3a wording confirmed (no rankings, scores, targets, timing, or advice — and no smuggling such intent through state names)?
- **Recommended default: CONFIRM**
- **Accepting means:** in plain terms — CSIA may describe, infer, and research states ("stablecoin inflows doubled while integrations grew"), but it never silently becomes an investment recommendation or execution authority. It cannot tell you what to buy, rank ecosystems as opportunities, or frame states as attractive/undervalued.
- **Meaningful alternative:** TIGHTEN (add more forbidden constructs) or LOOSEN (not recommended — erodes the "no recommender" commitment).
- **Unlocks:** Safe naming conventions for Books 6/8/9 surfaces.
- **Reversibility:** Amendable, but vocabulary crystallizes early — earliest confirmation is cheapest.
- **Choices: CONFIRM / TIGHTEN / LOOSEN**

## D5 — Anti-drift audit cadence

- **Question:** Is the audit cadence confirmed — the 13 standing drift questions answered in a recorded audit at every book ratification and program-phase boundary?
- **Recommended default: CONFIRM (per-book + per-phase)**
- **Accepting means:** in practice — roughly one short recorded audit per book (~10 total). It's the mechanism that catches drift like "we've quietly become a news feed" or "native modeling is atrophying."
- **Meaningful alternative:** LIGHTER (phase boundaries only — risks a whole book drifting unchecked) or HEAVIER (per bloc — ~20 extra audits for marginal benefit).
- **Unlocks:** Nothing by itself; it protects everything.
- **Reversibility:** Fully — it's procedural.
- **Choices: CONFIRM / LIGHTER / HEAVIER**

## D6 — Program Ledger authority

- **Question:** Upon D1 ratification, is `CSIA_PLANNING_PROGRESS.md` confirmed as the canonical current-state / next-authorized-step record?
- **Recommended default: CONFIRM**
- **Accepting means:** one file is the single place any future session reads to know what's authorized; historical planning docs stay preserved but their old "NEXT" fields do not override the ledger.
- **Dependency note:** D6 only becomes meaningful if D1 ratifies the Constitution — §G is what grants the ledger its role. If D1 fails, D6 has no object and the ledger remains bookkeeping-only.
- **Meaningful alternative:** REJECT (each doc keeps its own NEXT — recreates the CR-01 conflict) or CONFIRM with a different ledger location.
- **Unlocks:** Clean governance handoffs between sessions; no more conflicting "next step" claims.
- **Reversibility:** Amendable; ledger can move with a recorded decision.
- **Choices: CONFIRM / REJECT / CONFIRM ELSEWHERE**

## R-1A-5 — IBC voucher / chain-local asset representation

- **Question:** How are channel-bound asset forms (e.g., IBC vouchers like USDC-on-Osmosis) represented in the identity model?
- **Recommended default: OPTION C**

- **OPTION A — deployment-like identity:** each channel/path form is treated as a deployment of the asset. Workable fallback; stretches the "deployment" concept (which so far means *how an asset comes to exist on a chain*, not *how it travels*).

- **OPTION B — attribute-only:** the asset has one entry per chain, with channel details as attributes. **Found structurally inadequate:** when one channel closes, you'd need per-attribute timestamps — which breaks the Book 1D rule that history lives at record level. Also loses multi-channel and multi-hop truth. Adopting it would require a constitutional amendment.

- **OPTION C — canonical + REALIZATION (recommended):** one economic asset, many chain-local realization identities:

  ```text
  ONE ECONOMIC ASSET  (e.g., USDC)
          |
          +--> REALIZATION ON CHAIN A / PATH 1
          |
          +--> REALIZATION ON CHAIN A / PATH 2
          |
          +--> REALIZATION ON CHAIN B
          |
          +--> etc.
  ```

  Each realization preserves: local denomination; chain; channel/path; multi-hop route; valid-from/valid-to; closure; migration; provenance; capital flow — while all realizations still aggregate back to the SAME canonical asset. Keeps "deployment" (issuance) and "realization" (travel) semantically pure.

- **Unlocks:** Bloc 1A freeze (then 1C folds its edge consequences). Book 0 ratification does NOT wait on this.
- **Reversibility:** A ↔ C are mechanically interconvertible later. B is effectively irreversible without data loss once populated.
- **Choices: A / B / C** — Recommended: **C**

---

## Recording

Reply in any clear form, e.g.:

```text
D1 accept, D2 accept, D3 accept, D4 accept, D5 accept, D6 accept, R-1A-5 C
```

or with named objections/alternatives. Decisions take effect when recorded in the Operator Decision Log.

End of ballot.
