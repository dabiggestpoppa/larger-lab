# CSIA — BOOK 6 PRE-RATIFICATION REVIEW v0.2

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Supersedes (upon ratification):** `CSIA_BOOK_6_PRE_RATIFICATION_REVIEW_v0.1.md`,
> preserved unmodified. v0.1's row-13 answer ("state thresholds hidden: No")
> was **not supported** by v0.1's own vocabulary; it is re-answered here against
> the repaired design.
> **Scope:** Q1–Q35. Each asks whether a *structural failure* is possible — i.e.
> whether the design lacks a guard that makes the failure unreachable.

---

## 1. Q1–Q25 (re-run against the v0.2 design)

| # | Question | Answer | Guard (where the failure is unreachable) |
|---|---|---|---|
| 1 | Metric without methodology ID? | **No** | `methodology_ref` mandatory on every observation (Grammar v0.1 §7) |
| 2 | Missing become zero? | **No** | `value` only under OBSERVED/ZERO_OBSERVED; missingness never collapses (Grammar §6; 6D.1) |
| 3 | Unlike native metrics compare? | **No** | corpus refusals/gates (6D.5); `comparability_class` + cohort; Axiom 1 |
| 4 | Silent denominator change? | **No** | denominator is a measured subject; `DENOMINATOR_*` states; changed identity ⇒ NOT_COMPARABLE (Grammar §4) |
| 5 | Ambiguous metric window? | **No** | window class + calendar/timezone/late-data/revision mandatory (Grammar §5) |
| 6 | Price appreciation as native growth? | **No** | growth in native units; USD growth is a labeled ValuationObservation (corpus #14) |
| 7 | Book 6 rewrite Book 5 truth? | **No** | measure-over; discrepancies are sensitivity findings (Seams §1; anti-bleed 1) |
| 8 | Book 6 rewrite Book 4 truth? | **No** | Book 4 read-only; centrality derived; count ≠ fact (Seams §2) |
| 9 | Book 6 redefine Sensor mechanics? | **No** | Sensor retains price state/funding/OI/liquidations/basis/regime; D8 deferred (Seams §3) |
| 10 | ANNOUNCED → USED without evidence? | **No** | evidence ladder; used needs observed usage under a ratified methodology (D2-6 §3) |
| 11 | USED silently = HEALTHY? | **No** | four layers; HEALTH deferred; `HEALTHY` prohibited (D2-6 §3; State v0.2 §7) |
| 12 | State without measurement refs? | **No** | `measurement_refs` required; invalid without (State v0.2 §8) |
| 13 | State thresholds hidden? | **No (v0.2)** | **withdrawn overclaim replaced by rule-gating**: every Class B/C state cites a ratified `StateRule`; Class C states are `UNAVAILABLE_PENDING_RULE`; tolerances/benchmarks are rule fields, never inline constants or code-level epsilon (State v0.2 §1, §3) |
| 14 | Normalized metric lose native source? | **No** | Axiom 1 + `NormalizationRule` lineage (type-enforced under D6M-2 B, validator-guaranteed under A) (Comparability §3) |
| 15 | Methodology change overwrite history? | **No** | supersession; originals retained (Grammar §8) |
| 16 | Cross-source disagreement averaged? | **No** | averaging is itself an explicit versioned methodology; disagreement preserved (6D.4) |
| 17 | State vector become a score? | **No** | type-level firewall: no total/score/rank/grade/weight (State v0.2 §2, §7) |
| 18 | Metric imply investment attractiveness? | **No** | closed descriptive enum; prescriptive names prohibited (§5.3a) |
| 19 | UNKNOWN / NOT_AVAILABLE / ZERO collapse? | **No** | ten distinct missingness states, no collapse (Grammar §6) |
| 20 | Book 6 perform Book 8 bridge authority? | **No** | D8 deferred; provisional ownership only (Seams §3) |
| 21 | Common-value without explicit numeraire? | **No** | `numeraire` required, no default (Valuation §7) |
| 22 | Valuation with mismatched price timestamps? | **No** | `price_timestamp` + staleness bound; mismatched ⇒ STALE_PRICE (Valuation §7.2) |
| 23 | Compare outside valid cohort? | **No** | explicit versioned cohort; out-of-cohort = NOT_IN_COHORT (Comparability §5) |
| 24 | Partial coverage as complete? | **No** | coverage observation + sufficiency rule; `COVERAGE_SUFFICIENCY_UNKNOWN` otherwise (State v0.2 §5) |
| 25 | Revision erase the original? | **No** | originals retained as SUPERSEDED; recomputation recorded (Grammar §8) |

## 2. Q26–Q35 (the state-rule additions)

| # | Question | Answer | Guard |
|---|---|---|---|
| 26 | STABLE without a defined stability rule? | **No** | Class C; requires `stability_rule_ref` (tolerance/noise/dispersion); UNAVAILABLE_PENDING_RULE; no code-level epsilon (State v0.2 §3, §4.3) |
| 27 | VOLATILE without a volatility methodology? | **No** | VOLATILE is not primitive; requires `volatility_measure_ref` + `decision_rule_ref`; UNAVAILABLE_PENDING_RULE (State v0.2 §3, §4.4) |
| 28 | HIGHER_THAN_OWN_HISTORY without benchmark identity? | **No** | OWN_HISTORY is a namespace; every own-history state cites `benchmark_methodology_ref`; else RULE_NOT_RATIFIED (State v0.2 §3, §4.6) |
| 29 | Coverage % → sufficiency judgment? | **No** | `COVERAGE_OBSERVATION` != `COVERAGE_SUFFICIENCY_RULE`; `coverage_sufficiency_ref` required to judge (State v0.2 §5) |
| 30 | NOT_APPLICABLE defecting an architecture-native vector? | **No (v0.2 repairs v0.1)** | `NOT_APPLICABLE` satisfies SCHEMA_COMPLETE; DATA_COMPLETE is separate; no quality reading (State v0.2 §6) |
| 31 | A state containing an unversioned rule? | **No** | every Class B/C state cites a versioned `StateRule`; unversioned rule ⇒ no state (State v0.2 §4) |
| 32 | Exact directional comparison implying significance? | **No** | Class B asserts ordering only, under a named comparability/precision rule; no statistical claim, no significance label (State v0.2 §4.1) |
| 33 | A state rule hiding epsilon/noise tolerance? | **No** | tolerance is a ratified, versioned `tolerance_ref`; never an inline constant or code-level epsilon (State v0.2 §3) |
| 34 | One universal price-source authority forced? | **No (v0.2 doctrine)** | `PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME x METHODOLOGY`; no global class; divergence preserved (Plan v0.2 §11; D6M-4 reframed) |
| 35 | D6M-3 absorbing D2-6 health governance? | **No** | D6M-3 governs descriptive state rules only; health/usage thresholds stay with D6M-5; `HEALTHY` prohibited (D6M packet v0.2 D6M-3) |

## 3. Result

```text
QUESTIONS = 35
PASS = 35
FAIL = 0
QUESTIONS_DEPENDING_ON_AN_OPEN_D6M = Q14 (D6M-2 mechanism; invariant holds
  under both), Q34 (doctrine adoption is the operator's call; the *absence* of a
  forced global authority is what guarantees the "no")
STRUCTURAL_FAILURE_COUNT = 0
BOOK_6_PLAN = NOT HOLD
```

The v0.1 defect was not a missing guard on a question — it was a **vocabulary**
that shipped unratified rules under label names (a design defect, reproduced in
the reconciliation). v0.2 repairs the vocabulary itself: states are now
rule-gated, and the specific "hidden rule" questions (26–35) each have an
explicit guard. The v0.1 vocabulary must not be ratified in its old form; the
v0.2 vocabulary may be.

## 4. Honest caveats

1. This review verifies the **planning design**, not an implementation: 35
   statements about guard *design*, none a test result. The corresponding tests
   (6D) are exit-gate obligations for a future, unauthorized implementation.
2. The "no" answers are as strong as the companion documents make them. A
   future implementation that drops a rule reference (e.g. makes `tolerance_ref`
   optional, or re-adds a global price class) invalidates the relevant answer —
   hence rule-integrity and firewall tests are exit-gate requirements.
3. Five governance decisions remain genuinely open (D6M-1..5); two were
   mis-asked in v0.1 and are reframed in v0.2. None is decided here; none blocks
   ratification of the *plan* (they block *implementation* of the affected
   mechanics).

## 5. Verdict

```text
BOOK_6_PLAN = v0.2 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_6_PLAN = NOT HOLD (35/35 pass; 0 structural failures)
BOOK_6_PLAN_v0.1 = SUPERSEDED (not ratifiable; state-rule contradiction)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
NEXT = operator review of plan v0.2 + D6M packet v0.2
```
