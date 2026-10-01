# CSIA — BOOK 7: NARRATIVE, EVENTS, AND ECOSYSTEM EVOLUTION — PLAN v0.2 (DRAFT)

> **Status:** **DRAFT_PENDING_OPERATOR_RATIFICATION.**
> **This plan is NOT implementation-authorized.** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Predecessor:** Book 6 `FROZEN_ACCEPTED` (anchor `3919fb8052e216e94034a753fb258d338c5fa0dc`;
> acceptance commit `5f94c3f40cea4441470c57671f51454da7377361`; gate
> `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL`).
> **Relationship to v0.1:** v0.2 supersedes v0.1 **only upon operator ratification**.
> v0.1 is preserved unmodified as historical evidence of the pre-repair planning
> state. **v0.1 is NOT ratifiable in its current state** — its Bloc 7C response
> semantics were found too weak (`POST_ACTION_OBSERVATION != OBSERVED_CHANGE`;
> see `CSIA_BOOK_7_RESPONSE_SEMANTICS_RECONCILIATION_v0.1.md`), and its
> event lifecycle was not mechanically unambiguous about being non-sequential.
>
> **Companion set (current):** Boundary Review v0.1 · Event Grammar **v0.2** ·
> Narrative Model v0.1 · Narrative State Governance v0.1 · Action Ladder
> **v0.2** · Causality Doctrine **v0.2** · Ecosystem Evolution v0.1 ·
> **Response Semantics Reconciliation v0.1** · False-Positive Corpus **v0.2** ·
> Event Candidate Matrix v0.1 · Narrative Candidate Matrix v0.1 · Seams and
> Firewall v0.1 · D7N Packet **v0.2** · Decision Readiness Review **v0.1** ·
> Pre-Ratification Review **v0.2**.

---

## 0. Goal and constitutional posture

Connect what the market is talking about to what actually changes — as
**descriptive linkage**, never as truth creation (Axiom 3; §20–21; §5.3a; §25).
v0.2 differs from v0.1 in exactly one structural respect, and it is the whole
point of this revision:

```text
v0.1 allowed:  a post-action observation  ->  "usage response"
v0.2 requires: an OBSERVED CHANGE (baseline + comparable post observation +
               cited comparison methodology, inside a cited window)
               ->  a response LINK (descriptive, non-causal)
```

## 1. Governing doctrine (non-negotiable)

```text
Axiom 1   native architecture before normalization (Book 6 owns measurement)
Axiom 3   EVIDENCE OUTRANKS NARRATIVE
Axiom 5   time is part of truth (bitemporal; late discovery; no rewrite)
Axiom 6   missing is not false (missingness vocabulary; NOT_SUPPORTED != 0)
Axiom 7   discovery does not imply promotion
Axiom 8   descriptive before predictive
§5.3a     no ranking/score/target/buy-sell
§20/20.1  E4 may raise a narrative's state, never a structural claim's state
§21       the ladder is constitutional
§23.1     CONFIRMED_* = "response observed on the named axis", never causal
§25       sequence does not prove causality
§12.2     bitemporal axes; replay machinery ownership = Book 7 Bloc 7D [→MA-13]
D2-6      ANNOUNCED != DEPLOYED != USED (D6M-5 OPEN_DEFERRED)
Anti-bleed AB-1 no structural write · AB-2 no narrative promotion · AB-3 no count-to-truth
Response   POST_ACTION_OBSERVATION != OBSERVED_CHANGE; OBSERVED_CHANGE != CAUSAL_RESPONSE;
           RESPONSE_LINK != CAUSAL_CLAIM  (Reconciliation v0.1)
```

## 2. Bloc 7A — Event ontology (Event Grammar v0.2)

Six-way separation; 8 planned contracts (adding EventSeries, EventOutcomeSet);
`REPORT_COUNT != EVENT_COUNT` with family-defined occurrence signatures;
identity contested-state preserved; **lifecycle = set-valued occurrence statuses,
family-declared applicability, non-normative ordering, no scalar lifecycle
field** (v0.2 repair); event-status and response-outcome vocabularies never
merge; ten-field temporal model; structural seam `CHANGED / CHANGE_CLAIMED /
NO_CHANGE_FOUND / NOT_APPLICABLE` (reference-only); family evidence bars
(security/governance/regulatory/institutional/tokenomics).

## 3. Bloc 7B — Narrative objects (Narrative Model v0.1 + State Governance v0.1)

Seven-term grammar; identity `(narrative_core, subject_scope, temporal_lineage)`
with recorded split/merge/relapse; descriptive propagation only (zero scores);
firewall FW-1..FW-4 (`NARRATIVE EXISTENCE != NARRATIVE CLAIM TRUTH`, type-level);
seven typed contradiction forms with preserve-both-lines; state governance with
`STATE NAME != DERIVATION RULE`, three classes, **zero rules ratified**, Book 7
contract pattern (D7N-3).

## 4. Bloc 7C — Narrative-to-action (Action Ladder v0.2 + Causality v0.2 + Reconciliation v0.1)

```text
CLAIM → DECLARED ACTION → DEPLOYED ACTION → USAGE RESPONSE → CAPITAL RESPONSE → MARKET_RESPONSE_REF
```

- Arrows are linked observations, never causation; ladders stop at any rung.
- Rungs 1–3 unchanged; **rungs 4–5 require the seven gates** (G1 effective time;
  G2 valid baseline or named baseline-free methodology; G3 post-action Book 6/5
  observations; G4 Book 6-compatible comparability; G5 versioned comparison
  methodology; G6 an `ObservedChange`; G7 declared response window).
- Three distinct objects: `PostActionObservation` ≠ `ObservedChange` ≠
  `ResponseLink`; `ResponseLink` non-causal (`causal_status <= ASSOCIATION_ONLY`).
- Baseline selection is itself methodology (four candidate models; **no default**).
- Nine response outcomes with six non-collapsions (`NO CHANGE != NO DATA`,
  `!= NEGATIVE RESPONSE`; `ZERO VALUE != ZERO CHANGE`, etc.).
- `NO_RESPONSE_OBSERVED` withdrawn as a standalone outcome; `NO_CHANGE_OBSERVED`
  requires six conditions; silence is not evidence.
- Response predicate: P1 existence selected; P2 only where Book 6 defines it;
  P3 materiality DEFERRED (no materiality concept exists in Book 7).
- Methodology sensitivity: outcomes under declared alternatives preserved
  side-by-side, never averaged.
- Incentives/confounders: contextual annotation only; never adjustment,
  never attribution.
- Ownership seam: **D7N-7 OPEN**; interim posture fail-closed
  (`CHANGE_NOT_MEASURABLE`); no change product until the owner is assigned.
- Lag/windows: no universal numerals; `ResponseWindowMethodology` cited per
  response (load-bearing for G7).

## 5. Bloc 7D — Ecosystem evolution (Ecosystem Evolution v0.1)

Graph diffs between accepted states only (6 objects, 9 row types, no valence);
migrations via Book 3 identity doctrine; dependency gain/loss via Book 4
records; **generic EXPANSION/CONTRACTION rejected** (dimension-specific states);
`PRESERVED_GRAPH_HISTORY != REVALIDATED_HISTORICAL_TOPOLOGY` (D7N-6); full
bitemporality with late-discovery and no rewrite.

## 6. Seams and firewall (Seams and Firewall v0.1, extended by v0.2)

Book 6 consumed by **typed reference only** — including the new response layer
(no recomputation, no thresholds, no health, no missingness override); Book 8
`MARKET_RESPONSE_REF` ceiling; anti-prescription firewall extended to response
surfaces (no "material response," no "successful response," no score/rank/
catalyst/conviction fields; quoted-source language never aggregated).

## 7. False-positive corpus (v0.2): 30 cases

20 carried forward by reference (4 ALLOWED conclusions tightened), 10 new
response-semantics cases (post-action-no-change, unchanged-as-response, missing
baseline, missing post data, incomparable, silence-as-no-response, capital-axis
leak, methodology-dependent change, incentive attribution, window-elapsed fill).
Becomes the adversarial exit-evidence core for 7A/7B/7C.

## 8. Exit evidence requirements (future, unauthorized)

- **7A:** identity never inflates with reports; lifecycle set-valued and
  family-declared (no scalar); event-status/response-outcome non-merger; corpus
  1–4, 10–12, 16–19, 21–30 pass.
- **7B:** FW-1..FW-4 type-enforced; propagation descriptive; contradiction
  preserved; zero emissions without ratified rules; corpus 9/15 pass.
- **7C:** seven-gate enforcement; **no rung occupiable by temporal order alone**;
  nine-outcome vocabulary honored; `NO_CHANGE_OBSERVED` basis required;
  market rung a typed ref; corpus 5–8, 13–14, 18, 20–30 pass.
- **7D:** accepted-state diffs only; dimension-specific evolution; corpus 19.
- **Firewall:** anti-prescription tests green; no response/health/materiality
  field expressible.
- **D2-6 / D6M-5:** deferral intact at exit.

## 9. Open operator decisions (D7N Packet v0.2)

`D7N-1` event identity authority · `D7N-2` narrative identity methodology ·
`D7N-3` state-rule governance + vocabulary timing · `D7N-4` causal-claim
governance · `D7N-5` market-seam binding · `D7N-6` replay semantics ·
**`D7N-7` change-comparison authority (new; requires operator; option A would
amend the frozen Book 6)**. **None decided. `OPEN_D7N_DECISIONS = 7`.**

## 10. Amendment audit (v0.2)

```text
BOOK_1_AMENDMENT_REQUIRED = FALSE
BOOK_2_AMENDMENT_REQUIRED = FALSE
BOOK_3_AMENDMENT_REQUIRED = FALSE
BOOK_4_AMENDMENT_REQUIRED = FALSE
BOOK_5_AMENDMENT_REQUIRED = FALSE
BOOK_6_AMENDMENT_REQUIRED = FALSE   (only D7N-7 option A would open Book 6;
                                     that is the operator's call, not planning's)
CONSTITUTION_AMENDMENT_REQUIRED = FALSE
```

## 11. Plan status

```text
BOOK_7_PLAN = v0.2 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_7_PLAN_v0.1 = SUPERSEDED (not ratifiable — response-semantics defect)
BOOK_7_GOVERNANCE_REVIEW = COMPLETE
BOOK_7_RESPONSE_SEMANTICS_RECONCILIATION = COMPLETE
PRE_RATIFICATION_REVIEW = v0.2 45 / 45 PASS
D7N_PACKET = v0.2
OPEN_BLOCKING_D7N_DECISIONS = 0 (all 7 classified; see Decision Readiness v0.1)
OPEN_DEFERRED_D7N_DECISIONS = see Decision Readiness v0.1
D2_6 = IN_FORCE
D6M_5 = OPEN_DEFERRED
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
NEXT = operator review of Book 7 v0.2 + D7N packet v0.2
```

Ratification of this plan ratifies planning structure and doctrine only. It
grants **no** implementation authority, ratifies **no** state rule, event
family beyond planning disposition, or D7N decision implicitly, and authorizes
**no** acquisition, crawler, network, database, dashboard, score, ranking, or
research execution.
