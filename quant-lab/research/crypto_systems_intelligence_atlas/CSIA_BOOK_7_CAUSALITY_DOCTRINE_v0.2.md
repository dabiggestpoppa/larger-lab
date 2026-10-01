# CSIA — BOOK 7 CAUSALITY DOCTRINE v0.2

> **Status:** PLANNING DOCUMENT — GOVERNANCE DOCTRINE (successor). Not ratified.
> **Supersedes (on plan ratification):** `CSIA_BOOK_7_CAUSALITY_DOCTRINE_v0.1.md`
> (v0.1 preserved unmodified; v0.1 left the response layer under-specified —
> see Reconciliation §1.2).
> **Date:** 2026-10-01 · **Authority:** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Constitutional basis:** §25, §23.1, Axiom 3.

---

## 1. Four-level separation (unchanged)

```text
L1 TEMPORAL ORDER      "usage increased after event E"          (sequence only)
L2 ASSOCIATION         "usage increases co-occur with family F" (cited methodology)
L3 MECHANISTIC LINK    "the documented mechanism could carry E to Y" (attributed)
L4 CAUSAL CLAIM        "E caused Y"                             (reserved; D7N-4 gate)
```

## 2. What changed in v0.2: the response layer now sits strictly below L2

v0.1 defined a response as an observation that *followed* an action — which put
the response rung at L1 by another name while L4 stayed prohibited. v0.2 makes
the ladder consistent with the causality doctrine:

```text
RESPONSE_LINK (rung 4–5 content) is an OBSERVED_CHANGE under a cited
comparison methodology, linked within a cited window:

  change measured        => causal_status = ASSOCIATION_ONLY (max)
  no change measured     => NO_CHANGE_OBSERVED (not a negative, not a null claim)
  change unmeasurable    => CHANGE_NOT_MEASURABLE (+ missingness state)
```

Rules binding on every Book 7 surface:

- No rung may be occupied by temporal order alone (Reconciliation §3, G1–G7).
- `NO_CHANGE_OBSERVED` never inverts into an opposite-state claim.
- An incentive/concurrent-event annotation (Reconciliation §11) sharpens
  context and never rewrites the measurement or upgrades `causal_status`.
- Materiality thresholds (P3) remain DEFERRED; no "significant response" claim
  may be rendered as CSIA state.

## 3. Language rules (unchanged from v0.1)

Permitted: "usage increased after event E (comparison methodology M, window W)";
"no change observed under M"; "change not measurable (reason)".
Prohibited without a ratified event-study methodology: "caused / drove / led to"
applied by CSIA to any linked pair; "the action worked"; "the upgrade boosted
adoption"; any implicit upgrade of `causal_status` by adjacency.

## 4. Governance

```text
CAUSAL_STATUS_VOCABULARY = CLOSED (L4 unreachable until D7N-4 closes)
OPEN_DECISION            = D7N-4 (causal-claim governance) — unchanged
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
