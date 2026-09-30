# CSIA — BOOK 6 PRE-RATIFICATION REVIEW v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Scope:** Phase 34 — the 25 structural questions, each answered against the
> Book 6 v0.1 planning set (plan + 11 companion documents).
> **Question type:** each asks whether a *structural failure* is possible —
> i.e. whether the design lacks a guard that makes the failure unreachable.

---

## 1. The 25 questions

| # | Question | Answer | Guard (where the failure is made unreachable) |
|---|---|---|---|
| 1 | Can a metric exist without a methodology ID? | **No** | `methodology_ref` is mandatory on every observation; "value without methodology identity is incomplete" (Grammar §7) |
| 2 | Can missing become zero? | **No** | `value` present only when missingness is OBSERVED/ZERO_OBSERVED; missingness states cannot collapse (Grammar §6; 6D.1 M1–M8) |
| 3 | Can unlike native metrics compare directly? | **No** | false-comparison corpus rows refused/gated (6D.5); `comparability_class` + cohort required; native-before-normalized (Axiom 1) |
| 4 | Can a denominator silently change? | **No** | denominator is a measured subject; `DENOMINATOR_*` states; changed identity ⇒ NOT_COMPARABLE_DENOMINATOR_CHANGED (Grammar §4) |
| 5 | Can a metric window be ambiguous? | **No** | window class is mandatory with calendar/timezone/late-data/revision rules (Grammar §5) |
| 6 | Can price appreciation masquerade as native growth? | **No** | growth measured in native units; USD growth is a ValuationObservation with a cited price, labeled as price-driven (corpus #14) |
| 7 | Can Book 6 rewrite Book 5 capital truth? | **No** | Book 6 measures *over* Book 5; discrepancies are sensitivity findings, never rewrites (Seams §1; anti-bleed rule 1) |
| 8 | Can Book 6 rewrite Book 4 dependency truth? | **No** | Book 4 graph read-only; centrality is a named derived metric; count ≠ fact (Seams §2) |
| 9 | Can Book 6 redefine Sensor market mechanics? | **No** | Sensor retains price state/funding/OI/liquidations/basis/regime; Book 6 only consumes (Seams §3; D8 deferred) |
| 10 | Can ANNOUNCED become USED without usage evidence? | **No** | evidence ladder: announced/deployed ≠ used; used needs observed usage under a ratified methodology (D2-6 recon §3) |
| 11 | Can USED silently mean HEALTHY? | **No** | four separate layers; HEALTH_INTERPRETATION deferred; `HEALTHY` prohibited as a state name (D2-6 recon §3; State §3) |
| 12 | Can a state exist without measurement refs? | **No** | `measurement_refs` required on every StateDimension; a state without them is invalid at construction (State §4) |
| 13 | Can state thresholds be hidden? | **No** | any cutoff is a named versioned field, not an inline literal; and **no threshold is ratified at all** (D2-6), so states needing one read INSUFFICIENT_DATA (State §4, D2-6 recon §4) |
| 14 | Can a normalized metric lose its native source? | **No** | Axiom 1: normalized metric must resolve to preserved native observations; structural under D6M-2 Option B, validator-enforced under Option A (Comparability §3; Grammar §1.2) |
| 15 | Can methodology changes overwrite history? | **No** | revision = supersession; originals retained; methodology change = new version + superseding observation (Grammar §8) |
| 16 | Can cross-source disagreement be averaged without doctrine? | **No** | averaging is itself an explicit versioned methodology; disagreement preserved; Book 2 governs currency (6D.4) |
| 17 | Can a state vector become a score? | **No** | type-level firewall: no total/score/rank/grade field; no weights; no cross-subject ordering; percentile-as-rank rejected (State §7; Seams §4; firewall tests) |
| 18 | Can a metric imply investment attractiveness? | **No** | closed descriptive vocabulary; prescriptive names prohibited (§5.3a; State §3); valuation is descriptive only |
| 19 | Can UNKNOWN / NOT_AVAILABLE / ZERO collapse? | **No** | ten distinct missingness states, stress-tested before ratification; no collapse (Grammar §6; 6D.1) |
| 20 | Can Book 6 perform Book 8 context-bridge authority? | **No** | D8 is deferred to the Book 8 gate; Book 6 records provisional ownership only and finalizes no shared-seam decision (Seams §3) |
| 21 | Can common-value measurement occur without explicit numeraire? | **No** | `numeraire` is a required field with no default; no hidden USD (Valuation contract §7) |
| 22 | Can valuation use price observations with mismatched timestamps? | **No** | `price_timestamp` + `staleness` bound required; mismatched/stale ⇒ STALE_PRICE, state ⇒ INSUFFICIENT_DATA (Valuation §7.2) |
| 23 | Can a metric be compared outside its valid cohort? | **No** | cohort is explicit + versioned; out-of-cohort is NOT_IN_COHORT; "all chains" is never an automatic cohort (Comparability §5) |
| 24 | Can partial coverage appear complete? | **No** | `coverage` mandatory with its own basis; `PARTIAL_COVERAGE` distinct; floors enforced; vector status INCOMPLETE if any dimension partial (6D.1 M5; State §6) |
| 25 | Can historical revision erase the original observation? | **No** | originals retained as SUPERSEDED and queryable; recomputation recorded (Grammar §8; 6D.3 H1–H4) |

## 2. Structural failure count

```text
QUESTIONS = 25
STRUCTURAL_FAILURES = 0
QUESTIONS_DEPENDING_ON_AN_OPEN_D6M_DECISION = 1 (Q14: shape of the
  native-source chain guarantee follows D6M-2; the *guarantee itself* is
  present under both options, only its mechanism differs)
BOOK_6_PLAN_STRUCTURAL_STATUS = COMPLETE
```

**No question lacks a guard.** Q14's mechanism is the only one that depends on
an open decision (D6M-2), but the invariant (a normalized metric must preserve
its native source) is binding under either option — only *how it is enforced*
(type-level vs validator-level) is undecided. This is not a structural failure.

## 3. Does anything force a HOLD?

The HOLD trigger is a **structural failure** — a question with no guard. There
are none. Therefore the plan is not held; it proceeds as
`v0.1 DRAFT_PENDING_OPERATOR_RATIFICATION`, carrying five open `D6M-*` decisions
that the operator may resolve before or at ratification (each is reversible and
conservatively defaulted; only D6M-1 can force a Book 2/Constitution amendment,
and only under its non-default options).

## 4. Honest caveats

1. This review verifies the **planning design**, not an implementation. It is
   25 statements about guard *design*; none is a test result. The corresponding
   tests are 6D obligations for a future, unauthorized implementation phase.
2. The "no" answers are as strong as the companion documents make them. A future
   implementation that drops a guard (e.g. makes `numeraire` optional) would
   invalidate the relevant answer — hence the firewall and validation families
   are exit-gate requirements, not nice-to-haves.
3. Five governance decisions remain genuinely open (D6M-1..5). They are
   surfaced, not decided, and none is load-bearing for the plan's structure
   except D6M-1 (amendment) and D6M-2 (enforcement mechanism).

## 5. Verdict

```text
BOOK_6_PLAN = v0.1 DRAFT_PENDING_OPERATOR_RATIFICATION
BOOK_6_PLAN = NOT HOLD (0 structural failures)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
NEXT = operator review of this plan and the D6M-* decision packet
```
