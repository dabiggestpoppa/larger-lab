# CSIA — BOOK 7 SEAMS AND ANTI-PRESCRIPTION FIREWALL v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1; Action Ladder v0.1;
> Narrative State Governance v0.1.
> **Scope:** Phases 40–42 — the Book 6 consumption seam, the Book 8 forward
> seam, and the anti-prescription firewall for every Book 7 surface. Companion
> to Book 6's `CSIA_BOOK_6_SEAMS_AND_FIREWALL_v0.1.md` (same discipline, one
> book later in the dependency chain).

---

## 1. Book 7 / Book 6 seam (Phase 40)

**Book 6 owns:** measurement definitions, MeasurementObservations, descriptive
FundamentalStateVectors, methodology identities, missingness semantics.

**Book 7 may consume (reference-only):**

```text
MeasurementObservation refs        as usage/capital response rungs and
                                   narrative-state inputs (typed as measured facts)
FundamentalStateVector refs        as descriptive context attached to ladders/diffs
methodology-sensitive outputs      cited with methodology identity intact
```

**Book 7 may NOT:**

```text
recompute Book 6 truth silently         (a "corrected" measurement is a
                                        methodology-sensitivity finding, never a rewrite)
invent usage thresholds                 (D2-6 parameters deferred; D6M-5 OPEN_DEFERRED)
invent health states                    (USAGE RESPONSE OBSERVED != USAGE HEALTH)
override missingness                    (Axiom 6; missing != zero; absence vocabulary
                                        governs response rungs)
feed volume where measurement belongs   (narrative volume is not a usage proxy — AB-3)
extend the Book 6 vector                (no narrative state inside FundamentalStateVector
                                        without a Book 6 amendment — none required/performed)
```

Mechanical plan (implementation-time testable): every Book 7 consumption of a
Book 6 record is a reference field typed as `book6_measurement_ref` /
`book6_state_vector_ref`; no Book 7 module may construct or arithmetic-over
Book 6 values; the seam test family asserts reference-only consumption.

## 2. Book 7 / Book 8 seam (Phase 41)

Recorded explicitly as the Book 7 forward boundary:

- Book 7 models the ladder **up to a `MARKET_RESPONSE_REF`** — a typed forward
  reference with no semantics: no market-regime vocabulary, no confirmation
  states combining CSIA + Sensor observations, no lag windows, no price or
  market data consumed.
- **Book 8 will own** (from the roadmap + Constitution §24): identity mapping
  to Sensor observations, temporal alignment, lag research, combined
  structural/market context states, and historical Context Bridge validation.
- **No D8 decision is performed or pre-empted in Book 7 planning.** D8 remains
  reserved to the operator, gate: before Book 8 planning.
- If a future Book 7 implementation encounters market evidence, it records it
  as E4/E3-class source material *about* market response — never as a market
  observation (Sensor owns those).
- Candidate decision `D7N-5` surfaces the ref-only ceiling for binding
  confirmation; until then the ceiling is doctrine-level (this document),
  binding on Book 7 planning artifacts.

## 3. Anti-prescription firewall (Phase 42)

### 3.1 Forbidden outputs (constitutionally; §5.3a, §20, §23.1, Axiom 8)

```text
bullish narrative / bearish narrative        (as CSIA state)
strong catalyst / weak catalyst              (as CSIA state)
high-conviction catalyst / catalyst score
good event / bad event
best narrative / top narrative
top ecosystem / ranked ecosystem list
buyable catalyst / tradeable catalyst
any composite narrative/event score
any conversion of propagation into conviction
```

Quoted source language (a source calling something "bullish") is preserved
verbatim **as attributed source language**, clearly not CSIA state — recorded
on utterances/messages, never on states, never aggregated, never scored.

### 3.2 Permitted outputs (descriptive)

```text
narrative existence + identity lineage (split/merge/relapse)
narrative propagation (epochs, source classes, venues — descriptive)
event occurrence + lifecycle + temporal windows
action status per rung (declared/deployed/…)
usage response / capital response as reference-linked observations
contradiction (typed, both lines preserved)
unresolved / RULE_NOT_RATIFIED states
dimension-specific evolution descriptions
```

### 3.3 The firewall is structural, not editorial

Mirroring the Book 6 approach (type-level, not review goodwill), a future Book 7
implementation must make it impossible to express:

- a narrative/event/evolution object carrying any score/rating/conviction field
  (type-level prohibition);
- a state name outside the closed ratified vocabulary (enum, not string);
- a causal_status beyond the closed five-value vocabulary (Level 4 unreachable
  without a ratified methodology — Causality Doctrine §5);
- a market_response field that is not the typed ref (rung-6 ceiling);
- any aggregate over propagation counts as a state input (AB-3 mechanical).

These are the Book 7 firewall test-family obligations for the (unauthorized)
implementation phase.

## 4. Verdict

```text
BOOK_6_SEAM       = REFERENCE_ONLY_CONSUMPTION (typed refs; no recompute; D2-6/D6M-5 intact)
BOOK_8_SEAM       = MARKET_RESPONSE_REF_CEILING (no semantics; D8 untouched; D7N-5 open)
ANTI_PRESCRIPTION = STRUCTURAL (type-level; quoted-source carve-out defined)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
```
