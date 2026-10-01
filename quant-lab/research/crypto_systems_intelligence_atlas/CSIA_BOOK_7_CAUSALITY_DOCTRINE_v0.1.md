# CSIA — BOOK 7 CAUSALITY DOCTRINE v0.1

> **Status:** PLANNING DOCUMENT — GOVERNANCE DOCTRINE. Not ratified.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Constitutional basis:** §25 (Causality doctrine), §23.1 (Confirmation
> language rules), Axiom 3.
> **Binding predecessors:** Boundary Review v0.1; Action Ladder v0.1.

---

## 1. The four-level separation (binding on all Book 7 surfaces)

```text
LEVEL 1  TEMPORAL ORDER     "usage increased after event E"
                            recorded: rung linkage + timestamps. Asserts sequence only.

LEVEL 2  ASSOCIATION        "usage increases co-occur with events of family F"
                            recorded: co-occurrence across instances under a cited
                            methodology. Asserts correlation, nothing more.

LEVEL 3  MECHANISTIC LINK   "the mechanism by which E could affect usage is
                            documented by sources/evidence"
                            recorded: mechanism description + its evidence class.
                            Asserts a plausible channel exists — not that it fired.

LEVEL 4  CAUSAL CLAIM       "event E caused the usage increase"
                            PERMITTED ONLY under an operator-ratified event-study
                            methodology with explicit identification strategy,
                            counterfactual basis, and scope. Reserved.
```

Movement between levels is a *methodology upgrade*, never a rhetorical one. A
Level 1 observation displayed next to a Level 3 description must not be
rendered, named, or sorted as Level 4.

## 2. Permitted / prohibited language (implementation-time enforceable)

```text
PERMITTED (descriptive, §5.3a-compatible):
  "usage increased after event E"                 (Level 1)
  "capital response was observed following X"     (Level 1; §23.1 CONFIRMED_* reading)
  "sources claim E drove Y"                       (quoted source language, attributed)
  "a plausible mechanism is documented"           (Level 3, attributed)

PROHIBITED (without ratified event-study methodology):
  "E caused Y" / "E drove Y" / "E led to Y"
  "the catalyst worked" / "the upgrade boosted adoption"
  any causal verb applied by CSIA itself to a linked pair
```

Quoted source causality is preserved as source language with attribution —
it never becomes CSIA's own assertion (Axiom 3: the narrative says it; the
system records that it was said).

## 3. Why timeline adjacency is never enough

Adjacent timestamps arise from: scheduling (announcements precede planned
releases), reporting lag (chain data surfaces after events), seasonal/cycle
correlation, shared third causes (market-wide moves), and selection (ladders
are recorded where links exist). A Book 7 causal claim requires, at minimum:
a declared counterfactual basis, a defined comparison window/methodology, and
operator ratification — the same discipline Book 6 applies to empirical
parameters (D6M-5 emergence conditions apply by analogy: distribution-derived,
methodology-robust, cohort-scoped, descriptive-only, reversible).

## 4. Interaction with the ladder and CONFIRMED_* states

- Ladder rung links and `causal_status` are separate fields; a completed ladder
  with every rung evidenced is still `TEMPORAL_PRECEDENCE_ONLY` unless a
  ratified event-study methodology produced more.
- `CONFIRMED_USAGE_RESPONSE` / `CONFIRMED_CAPITAL_RESPONSE` style states, if
  ever ratified, mean "evidence of response was observed on the named axis"
  (§23.1) — never "the action caused the response."

## 5. Governance

```text
CAUSAL_STATUS_VOCABULARY = CLOSED (5 values; Level 4 unreachable until D7N-4 closes)
OPEN_DECISION            = D7N-4 (causal-claim governance: whether/when to
                           authorize event-study methodologies in a later round)
NO_CAUSAL_METHODOLOGY_RATIFIED = TRUE (planning close)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
