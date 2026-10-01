# CSIA — BOOK 7 ACTION LADDER v0.2

> **Status:** PLANNING DOCUMENT — DRAFT (successor). Not ratified. No implementation.
> **Supersedes (on ratification of the Book 7 plan):**
> `CSIA_BOOK_7_ACTION_LADDER_AND_CAUSALITY_v0.1.md` (v0.1 preserved unmodified
> as history; its response semantics were found too weak — see
> `CSIA_BOOK_7_RESPONSE_SEMANTICS_RECONCILIATION_v0.1.md` §1).
> **Date:** 2026-10-01 · **Authority:** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Scope:** Bloc 7C — the constitutional ladder with repaired response rungs,
> response-absence semantics, lag/window governance. Causality → v0.2.

---

## 1. The canonical ladder

```text
CLAIM → DECLARED ACTION → DEPLOYED ACTION → USAGE RESPONSE → CAPITAL RESPONSE → MARKET_RESPONSE_REF
```

Each arrow is a **linked observation**, never an implication. The v0.1 leak
(`TEMPORAL ORDER → RESPONSE`) is closed here: rungs 4–6 may only be occupied by
a `ResponseLink` whose `response_change_ref` points at a valid
`ObservedChange` (Reconciliation §2.2–2.3).

## 2. Rungs 1–3 (unchanged from v0.1; re-affirmed)

| Rung | Occupied when | Evidence bar | Never satisfied by |
|---|---|---|---|
| CLAIM | a Book 2-class claim exists (may be E4) | Book 2 claim record | — |
| DECLARED ACTION | a responsible actor declared (roadmap/proposal/announcement/commitment) | declaration record + source class (family-typed) | its own truth (DECLARED ≠ EXECUTED) |
| DEPLOYED ACTION | Book 2-backed structural truth through the owning book | E0/E1 + owning-book record (contract deployed / feature active / integration live / migration complete / governance executed) | announcement, press release, roadmap, social post (§20.1; D2-5 spirit) |

A ladder that cannot occupy rung 3 **stops**; it does not skip to rung 4.

## 3. Rung 4 — USAGE RESPONSE (repaired)

```text
USAGE_RESPONSE_LINKED requires ALL SEVEN GATES:
  G1 valid deployed-action effective time (Book 2-backed, owning-book resolved)
  G2 valid ResponseBaseline with cited selection methodology — or an explicitly
     named baseline-free comparison methodology where genuinely meaningful
  G3 one or more PostActionObservations (Book 6 refs; refs, never copies)
  G4 Book 6-compatible comparability (all 9 Reconciliation §4 gates)
  G5 versioned comparison/change methodology cited
  G6 an ObservedChange result (CHANGE_OBSERVED or NO_CHANGE_OBSERVED)
  G7 the assessed change falls within a declared response window (cited)
```

Forbidden: `USAGE RESPONSE OBSERVED` from a post-action observation alone;
unchanged values counted as response; missingness read as zero; health,
adoption-success, materiality, or investment readings (`USAGE RESPONSE
OBSERVED != USAGE HEALTH` — D6M-5 OPEN_DEFERRED, untouched).

Book 7 records `USAGE_RESPONSE_LINKED` with `causal_status <= ASSOCIATION_ONLY`.

## 4. Rung 5 — CAPITAL RESPONSE (repaired)

Identical gate structure (G1–G7) with Book 5 economic records / Book 6
measurements as the canonical capital source. **No Book 5 write-back**; capital
topology, principal vectors, and liability obligations remain Book 5's. A
narrative-claimed capital flow without Book 5/6 records is `CHANGE_CLAIMED`,
never a capital response.

## 5. Rung 6 — MARKET_RESPONSE_REF (unchanged ceiling)

Typed forward reference only; no semantics. Sensor retains market observation;
Book 8 owns the bridge; D8 undecided and untouched; binding confirmation
surfaced as `D7N-5`.

## 6. Response-absence semantics (repaired; supersedes v0.1 §4)

Nine outcomes (Reconciliation §7): `CHANGE_OBSERVED`, `NO_CHANGE_OBSERVED`,
`CHANGE_NOT_MEASURABLE`, `BASELINE_UNAVAILABLE`, `POST_DATA_UNAVAILABLE`,
`NOT_COMPARABLE`, `TOO_EARLY_TO_ASSESS`, `NOT_APPLICABLE`, `UNKNOWN`.

`NO_RESPONSE_OBSERVED` (v0.1) is **withdrawn as a standalone outcome** and
re-expressed as `NO_CHANGE_OBSERVED`, which may be asserted only with: an
applicable cited response methodology, a closed assessment window, a valid
baseline, existing post-action observations, valid comparability, and a response
predicate that is not satisfied. "Window elapsed, nothing recorded" is now
`UNKNOWN` or a specific missingness state — **silence is not evidence**
(Reconciliation §8).

Non-collapsions (testable): `NO CHANGE != NO DATA`; `NO CHANGE != NEGATIVE
RESPONSE`; `ZERO VALUE != ZERO CHANGE`; `BASELINE_UNAVAILABLE != POST_DATA_UNAVAILABLE`.

## 7. Link contract

```text
NarrativeActionLink = narrative_ref? · claim_ref? · declared_action_ref? ·
                     deployed_action_ref? · usage_response_links[]
                     capital_response_links[] · market_response_ref (REF only)
                     link_type (descriptive sequence relation)
                     methodology_ref · valid_time/observed_at · evidence_refs[]
                     causal_status (closed, <= ASSOCIATION_ONLY in Book 7)
```

Every stage is optional and every absence carries a §6 outcome; a ladder may
stop anywhere; rungs are independently evidence-bound.

## 8. Lag / window governance (unchanged, now load-bearing)

No universal windows (24h/7d/30d/90d rejected as event-response defaults). A
`ResponseWindowMethodology` (versioned, operator-ratified at implementation
authorization) is required for gate G7; family-typed ranges keyed to Book 6
window classes (usage), Book 5 record cadence (capital), and governance stage
timing. No numeric default chosen here — choosing one would be an unauthorized
empirical parameter. Book 8 may later own market-specific alignment.

## 9. Verdict

```text
LADDER_V0.2          = PLANNED (rungs 4–5 gated by ResponseLink+ObservedChange)
TEMPORAL_ORDER_TO_RESPONSE_LEAK = CLOSED
NO_RESPONSE_OBSERVED = WITHDRAWN (-> NO_CHANGE_OBSERVED with 6 conditions)
OUTCOMES             = 9 states, non-collapsible
WINDOW_GOVERNANCE    = load-bearing for G7; no default
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
