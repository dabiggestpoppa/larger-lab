# CSIA — BOOK 7 NARRATIVE STATE GOVERNANCE v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessors:** Boundary Review v0.1 (AB-1..AB-3); Event Grammar v0.1;
> Narrative Model v0.1.
> **Scope:** Phases 13–14 — narrative-state vocabulary discipline and the
> Book 6 → Book 7 state-rule seam. Book 6's central lesson is applied verbatim:
> a state name is not a derivation rule.

---

## 1. The Book 6 lesson, imported

Book 6 plan v0.1's withdrawn claim — "states are threshold-free" while six
state names shipped without rules — produced the D6M-3 governance model. Book 7
inherits the repaired law, not the mistake:

```text
STATE NAME != DERIVATION RULE
EVERY narrative/event state requires an EXPLICIT, VERSIONED, EVIDENCE-LINKED,
REPLAYABLE derivation rule, ratified by the operator individually, before any
implementation may emit it.
```

The roadmap's illustrative vocabulary (`EMERGING`, `EXPANDING`, `DOMINANT`,
`FADING`, `CONFIRMED`, `INVALIDATED`) and the Constitution §20 set (`EMERGING`,
`EXPANDING`, `SATURATED`, `FADING`, `REACTIVATED`, `DISPROVEN`, `UNRESOLVED`)
are **name candidates only**. None is ratified. None may be emitted by any
future implementation until its rule exists and is ratified. `CONFIRMED_*`
and `DISPROVEN` additionally collide with epistemic-sounding language —
Constitution §23.1 binds them: `CONFIRMED_*` means "evidence of response was
observed on the named axis," never a causal or investment assertion.

## 2. Planned state classes (mirroring the Book 6 three-class doctrine)

```text
CLASS A  availability/observation states — no directional semantics:
         INSUFFICIENT_DATA, NOT_APPLICABLE, RULE_NOT_RATIFIED,
         PROPAGATION_UNKNOWN, UNRESOLVED (Constitution §20 already reserves it)
CLASS B  specification-only states — ratifiable without empirical research,
         but still an individual operator act. Planned shape: circulation-
         descriptive states derived deterministically from recorded
         propagation epochs and contradiction rows (e.g., "propagation active
         within observed window," "no propagation observed in window") —
         final vocabulary deliberately NOT selected in planning (D7N-3).
CLASS C  threshold/benchmark states — require empirical parameters and are
         DEFERRED by default: anything resembling DOMINANT/SATURATED/FADING
         needs distribution-derived, methodology-robust, cohort-scoped,
         descriptive-only, reversible parameters (the five D6M-5 emergence
         conditions apply by analogy). No Class C narrative state is proposed,
         designed, or ratifiable in this planning round.
```

Rules bound into any future Book 7 state implementation:

- **descriptive** — state names may not encode direction of investment merit;
  §5.3a applies to narrative states exactly as to fundamental states;
- **replayable** — a state emission must be recomputable from its recorded
  inputs (propagation records, contradiction rows, event bindings) under its
  rule version;
- **evidence-linked** — every emission cites the evidence refs and rule
  version that produced it;
- **versioned** — rule versions supersede without rewriting history;
- **non-prescriptive** — no state implies buy/sell/timing (§5.3a).

**Open narrative states exist legitimately:** a narrative with no ratified
applicable rule simply carries `RULE_NOT_RATIFIED`-class availability state —
that is correct pre-rule behavior, not a defect (the Book 6 precedent).

## 3. The Book 6 seam: reuse the pattern, never the code or authority (Phase 14)

**Decision taken in planning (subject to operator confirmation, `D7N-3`):**
Book 7 needs a **Book 7-specific state contract**, informed by — but distinct
from — the Book 6 `StateRule` architecture.

Rationale (why blind reuse fails):

1. **Different evidence inputs.** Book 6 StateRules consume Book 6
   MeasurementObservations (numeric, windowed, methodology-versioned).
   Narrative states consume propagation epochs, contradiction rows, event
   lifecycle transitions, and source-class sets — categorical, bitemporal,
   evidence-class-typed inputs Book 6 rules cannot express.
2. **Different failure modes.** Book 6's core hazard was silent threshold
   invention; Book 7's core hazard is *volume-as-truth* (propagation count
   becoming epistemic weight). The rule contracts must fail differently.
3. **No authority transfer.** D6M-3 = CENTRALIZED_OPERATOR_RATIFICATION
   governs Book 6 Class B/C rules over measured fundamentals. It does not
   extend to narrative states; extending it silently would be authority
   bleed. Book 7 rules need their own ratification trail.

What transfers (the pattern, not the code): operator-only ratification; three
state classes; explicit predicate + input requirements + scope; versioned
supersession without history rewrite; ratification ≠ object status; no
automatic ratification by choosing the governance model; `RULES_RATIFIED = 0`
at planning close.

### 3.1 The seam contract (planned)

```text
BOOK 7 NarrativeStateRule (planned, NOT implemented)
  rule_id / version
  target_state              (from the closed vocabulary, once ratified)
  input_contract            typed refs: propagation epochs, contradiction rows,
                            event lifecycle transitions, source-class sets —
                            Book 6 measurement refs ONLY as measured inputs,
                            never as narrative-circulation proxies
  predicate / derivation    explicit, deterministic where Class B
  scope                     narrative family / subject cohort / window
  evidence_class_bar        which Book 2 evidence classes may feed which inputs
  emission_binding          state, rule version, input refs, observed_at,
                            valid window — recorded per emission
  supersession              new version supersedes; history preserved
```

**Hard seam rules:**

- Book 6 `MeasurementObservation` refs may feed Book 7 rules as *measured
  facts about usage/capital* (e.g., a ladder rung exists). They may **not** be
  re-derived, thresholded, or interpreted by Book 7 (no usage thresholds, no
  health states — D6M-5 untouched, D2-6 intact).
- Book 7 rules may not consume "narrative volume" as a substitute for any
  measured fact (volume feeds only narrative-circulation states).
- A Book 7 narrative state never appears inside a Book 6
  `FundamentalStateVector` (no vector field extension without Book 6
  amendment; none required or performed).

## 4. Governance consequences at planning close

```text
GOVERNANCE_PATTERN_ADOPTED      = OPERATOR_ONLY_RATIFICATION (Book 6 pattern)
NARRATIVE_STATE_RULES_RATIFIED  = 0
NARRATIVE_STATES_AVAILABLE      = CLASS_A_ONLY (availability states, no rules needed)
CLASS_B_NARRATIVE_STATES        = NOT_RATIFIED (vocabulary deliberately unselected)
CLASS_C_NARRATIVE_STATES        = DEFERRED (D7N-3 + future operator round)
OPEN_DECISIONS                  = D7N-3 (governance contract + vocabulary timing)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```

No narrative state name is selected in this planning round. The candidate
matrices record state eligibility per concept; selection happens only in an
operator decision round modeled on D6M-3.
