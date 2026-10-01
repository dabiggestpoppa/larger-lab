# CSIA — BOOK 7 NARRATIVE / ACTION FALSE-POSITIVE CORPUS v0.2

> **Status:** PLANNING DOCUMENT — DRAFT (successor). Not ratified. No implementation.
> **Supersedes (on plan ratification):** `CSIA_BOOK_7_FALSE_POSITIVE_CORPUS_v0.1.md`.
> **v0.1 is preserved unmodified as history.** Cases 1–20 are carried forward
> **by reference** (their NAIVE/FAIL/OWN/EVID rows are unchanged); only their
> ALLOWED conclusions were tightened where they relied on the weak response
> semantics (see §1), and Cases 21–30 are new response-semantics cases from
> the Reconciliation v0.1 audit.
> **Date:** 2026-10-01 · **Authority:** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Row key:** NAIVE · FAIL · OWN · EVID · ALLOWED · PROHIBITED (unchanged).

---

## 1. v0.1 → v0.2 correction log (response semantics)

| Case | v0.1 ALLOWED text | v0.2 corrected ALLOWED text |
|---|---|---|
| 5 | "usage response `NO_RESPONSE_OBSERVED`/`RESPONSE_NOT_MEASURED` per measurement state" | ladder stops at rung 3 (`DEPLOYED`); outcome = `BASELINE_UNAVAILABLE` / `POST_DATA_UNAVAILABLE` / `NOT_COMPARABLE` per the nine-outcome vocabulary; **never** `NO_RESPONSE_OBSERVED` without basis |
| 6 | "usage increased after T (Level 1)" | "an `ObservedChange` exists under comparison methodology M within window W (comparison + response predicate cited); causal_status = ASSOCIATION_ONLY"; the increase itself is a Book 6 fact, not Book 7's |
| 7 | "usage increase preceded the announcement (recorded pre-trend)" | unchanged in substance; the pre-trend is a baseline/comparison result, cited to Book 6 refs + M |
| 8 | "capital response observed" | "`CHANGE_OBSERVED` on the capital axis requires baseline + comparable post observations + change methodology + window; otherwise `CHANGE_NOT_MEASURABLE`" |

All other v0.1 rows carry forward verbatim.

---

## 2. New response-semantics cases (21–30)

### Case 21 — Post-action observation, no change (the reviewer's example)
- **NAIVE:** usage 100 before, 100 after → "usage response observed."
- **FAIL:** `POST_ACTION_OBSERVATION != OBSERVED_CHANGE`; the weak v0.1 definition let sequence alone occupy rung 4.
- **OWN:** Book 6 (measurement) + Book 7 (response linkage).
- **EVID:** baseline ref + post ref, same metric definition/methodology/unit/denominator/cohort/window class, comparable coverage, non-missing.
- **ALLOWED:** "post-action observation recorded; `ObservedChange` = no change under M ⇒ `NO_CHANGE_OBSERVED` (valid run, no response link)."
- **PROHIBITED:** `USAGE_RESPONSE_LINKED`; "response occurred"; treating the observation's existence as a change.

### Case 22 — Unchanged value counted as response
- **NAIVE:** value identical to baseline ⇒ "no change, but response exists."
- **FAIL:** collapses "a measurement was taken" with "a response occurred"; response is a *change* claim (Reconciliation §2.3).
- **OWN:** Book 7 response predicate.
- **EVID:** valid comparison + predicate P1/P2 evaluation (Reconciliation §9).
- **ALLOWED:** `NO_CHANGE_OBSERVED` as a *result of assessment*, distinct from the response link.
- **PROHIBITED:** a response link with an unchanged change; "flat but live" framing that implies a response.

### Case 23 — Baseline missing, post data present
- **NAIVE:** post-action spike with no baseline ⇒ "response observed."
- **FAIL:** without a baseline there is no comparison; a single value cannot be a change.
- **OWN:** Book 7 (baseline contract) + Book 6 window semantics.
- **EVID:** `ResponseBaseline` with cited selection methodology (or named baseline-free methodology).
- **ALLOWED:** `BASELINE_UNAVAILABLE`; the post observation recorded as `UNASSESSED`.
- **PROHIBITED:** fabricating a baseline; defaulting to "the value looks high"; response link.

### Case 24 — Baseline present, post data missing
- **NAIVE:** deployment happened; presumably usage moved ⇒ "response observed."
- **FAIL:** presumption of movement without measurement; Axiom 6 (missing ≠ false, missing ≠ zero).
- **OWN:** Book 6 missingness + Book 7 outcome vocabulary.
- **EVID:** baseline ref; absence of post-action observation records.
- **ALLOWED:** `POST_DATA_UNAVAILABLE` (or `TOO_EARLY_TO_ASSESS` inside the window).
- **PROHIBITED:** "usage likely increased"; response link; substituting silence for data.

### Case 25 — Incomparable before/after
- **NAIVE:** usage before the tokenomics change vs after ⇒ "usage response."
- **FAIL:** Book 6 comparability gate violated (metric definition/methodology/denominator/cohort/window mismatch); v0.1 had no comparability gate for responses.
- **OWN:** Book 6 comparability doctrine (D6M-2 normalization contract).
- **EVID:** comparability status across the nine §4 gates.
- **ALLOWED:** `NOT_COMPARABLE` with the failing gates named.
- **PROHIBITED:** normalizing in Book 7 to force comparability; response link; cross-methodology delta.

### Case 26 — Nothing changed because nothing was looked at
- **NAIVE:** no records ⇒ no change ⇒ `NO_RESPONSE_OBSERVED`.
- **FAIL:** absence of research attention ≠ measured absence; the old state asserted a proven absence from an unproven basis (Reconciliation §8).
- **OWN:** Book 7 outcome vocabulary.
- **EVID:** none — this is exactly why the case is a false positive.
- **ALLOWED:** `UNKNOWN` (or `CHANGE_NOT_MEASURABLE` where a methodology is known absent).
- **PROHIBITED:** `NO_RESPONSE_OBSERVED` / `NO_CHANGE_OBSERVED` without a valid run.

### Case 27 — Capital observation after event ⇒ "capital response"
- **NAIVE:** supply/liquidity reading taken after the burn ⇒ "capital response."
- **FAIL:** same leak on the capital axis (v0.1 §1.4 had no baseline requirement).
- **OWN:** Book 5 (capital records) + Book 6 (measurement).
- **EVID:** baseline + comparable post capital observation + change methodology + window.
- **ALLOWED:** capital-axis `ObservedChange`/`CHANGE_NOT_MEASURABLE` per the nine outcomes.
- **PROHIBITED:** capital response link from a single post-event reading; any Book 5 write-back.

### Case 28 — Methodology-dependent change (baseline choice flips the outcome)
- **NAIVE:** report the single baseline-selected change as *the* change.
- **FAIL:** hides methodology dependence (Reconciliation §12); Book 6 methodology-sensitivity discipline inherited.
- **OWN:** Book 7 sensitivity record + Book 6 methodology registry.
- **EVID:** outcomes under ≥2 declared baseline/comparison alternatives.
- **ALLOWED:** the change under each methodology, side by side, with a sensitivity note.
- **PROHIBITED:** averaging methodologies; selecting the flattering baseline; omitting a flip.

### Case 29 — Incentive spike used to assert the action "worked"
- **NAIVE:** usage rose after a launch, and incentives were live ⇒ "the action succeeded."
- **FAIL:** attribution leap (Causality v0.2 §2); confounder annotation may not upgrade `causal_status` (Reconciliation §11).
- **OWN:** Book 6 (measurement) + event records for the incentive.
- **EVID:** observed change under M; incentive event ref as context.
- **ALLOWED:** "change observed; incentive program live concurrently (context annotation); association only."
- **PROHIBITED:** "succeeded"; "adoption confirmed"; discounting the change because of the incentive.

### Case 30 — Window elapsed ⇒ rung filled by silence
- **NAIVE:** assessment window passed; the ladder row is empty ⇒ write "no response."
- **FAIL:** the exact failure the NO_RESPONSE repair closes: silence is not evidence (Reconciliation §8).
- **OWN:** Book 7 outcome vocabulary.
- **EVID:** closed window + valid baseline + post observations + valid comparison + unsatisfied predicate — or none of these.
- **ALLOWED:** `NO_CHANGE_OBSERVED` only with the full basis; otherwise the specific missingness state.
- **PROHIBITED:** auto-filling any rung from time passage.

---

## 3. Corpus verdict

```text
CASES_TOTAL            = 30 (v0.1: 20 carried by reference, 4 ALLOWED rows tightened;
                           v0.2 new: 10 response-semantics cases 21-30)
RESOLVED               = 30 / 30
RECURRING_FAILURE_MODES = stage-collapse, count-to-truth, valence-attachment,
                          identity-duplication, seam-violation,
                          OBSERVATION-AS-CHANGE (new; closed by Reconciliation)
EXIT_EVIDENCE_CORE     = B7A/B7B/B7C adversarial families (now response-aware)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
