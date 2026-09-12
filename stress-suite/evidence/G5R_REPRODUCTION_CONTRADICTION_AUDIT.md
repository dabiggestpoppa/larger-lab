# G5R REPRODUCTION / CONTRADICTION AUDIT — S16 derived quality + measured result

Scope: G5R-06 (reproduction quality must be DERIVED), G5R-07 (contradiction must be derived
from the MEASURED result), G5R-08 (manual authority and reproduction quality remain
separate), G5R-09 (amendment ratification must use AuthorityState).
Core law: **CLAIMED REPRODUCTION QUALITY != REPRODUCTION QUALITY** and
**CLAIMED CONTRADICTION != MEASURED CONTRADICTION.**

## 1. ReproductionProtocol (frozen BEFORE the observed result)

`engine/g5r.py` — `ReproductionProtocol` carries the actual governed fields:
claim_ref, dataset lineage, implementation version, session/window, tier constraints,
feature definitions, PIT rules, sample definition, metric definition, execution
assumptions, evaluation criterion, independence lineage, falsification criterion,
`frozen_before_result`, and a content-derived `protocol_fingerprint`
(deterministic, changes if ANY governed field changes post hoc).

`ReproductionQualityAssessment` is then DERIVED by
`derive_reproduction_quality(protocol, claim, declared_deviations, claim_fingerprint)`:

- `session_match` — protocol session window vs the claim's applicability session
  (`00:00-08:00 UTC (Asia)` for the P90 claim);
- `tier_match` — protocol tier constraints must cover the claim's tier set
  (`TIER_1_100%`, `TIER_2_75%`, `TIER_3_50%`, `NO_GO_>45p`);
- `pit_clean` — PIT rules present and non-empty;
- `protocol_fingerprint_present` / `protocol_fingerprint_valid` — when a frozen reference
  fingerprint is supplied, the recomputed fingerprint must MATCH (a post-result protocol
  change alters the fingerprint and invalidates the comparison);
- declared deviations are RECORDED but never EXCUSE a detected structured mismatch:
  `known_deviations=[]` cannot launder a wrong session (CASE B).
- Any failed dimension ⇒ `FLAWED` ⇒ runner status `REPRODUCTION_REJECTED`
  (policy rule `g5.doctrine.flawed_reproduction`), manual preserved.

## 2. ObservedResult + generic comparator (G5R-07)

`ObservedResult` represents the measured result explicitly:
`metric = filtered_win_rate`, `estimate`, `uncertainty_interval (lo, hi)`, `sample_size`,
`units`, `source_refs`. The fixture's `result` STRING is never consulted for the verdict.

`compare_measured_result(observed, claim_interval)` derives:

| Observed interval vs doctrine band [0.85, 0.90] | Verdict |
|---|---|
| entirely inside | `SUPPORTS_CLAIM` |
| entirely outside (no overlap) | `CONTRADICTS_CLAIM` |
| partial overlap / touching | `INCONCLUSIVE` |

Primary fixture: REPRO_CLEAN_1 measures `0.72 [0.68, 0.76]` (n=2400) → `CONTRADICTS_CLAIM`
→ `CONTRADICTION_OPEN` with a DoctrineContradictionRecord; REPRO_FLAWED_1 has a structured
session/tier/PIT mismatch → `REPRODUCTION_REJECTED` regardless of its measured value.
CASE C: a clean reproduction whose string claims CONTRADICTS_CLAIM but whose measured
interval is `[0.86, 0.88]` produces **zero** contradictions
(`test_operator_preference_cannot_fabricate_contradiction` — old string-mutation assertion
documented and replaced in the test).

## 3. Object separation (G5R-08)

`DoctrineClaimRecord` / `ReproductionProtocol` / `ObservedResult` /
`ReproductionQualityAssessment` / `DoctrineComparison` / `DoctrineContradictionRecord`
are distinct frozen objects. A perfect reproduction never mutates the claim
(`current_status` stays `AUTHORITATIVE`, `win_rate_band` untouched); an authoritative
claim never rewrites the measurement. The contradiction is a RELATION carrying both ids.

## 4. Governed ratification (G5R-09)

`DoctrineAmendmentProposal` (creation does NOT amend doctrine) +
`DoctrineAmendmentRatification` binding actor, `AuthorityState.level(actor)`, proposal id,
authority basis, scope, manual claim id. `govern_amendment_ratification` enforces:

- proposal must exist and be in PROPOSED state (ratification without proposal rejected);
- `level(actor) == "OPERATOR"` under the provisional test contract (worker rejected);
- the manual source file is never rewritten.

CASE D: a fixture `ratified=true` boolean is never consulted — the runner honors only
governed ratification records, so with none present the manual remains unamended and
`amendment_operator_required=true`. **Until ratification the manual remains canonical.**

## 5. Regression coverage

`test_clean_exact_protocol_passes`, `test_wrong_session_detected_without_declared_deviation`
(CASE B), `test_wrong_tier_detected`, `test_PIT_failure_detected`,
`test_missing_protocol_fingerprint_rejected`,
`test_post_result_protocol_change_changes_fingerprint_and_invalidates_comparison`,
`test_fixture_string_contradicts_cannot_override_measured_result` (CASE C),
`test_numeric_result_inside_claim_band_not_contradiction`,
`test_numeric_result_materially_outside_claim_band_can_contradict`,
`test_uncertainty_overlap_can_return_inconclusive`,
`test_claim_never_rewritten_by_reproduction_or_comparison`,
`test_fixture_ratified_true_without_authority_rejected` (CASE D),
`test_worker_cannot_ratify_doctrine_amendment`,
`test_operator_can_ratify_existing_proposal`,
`test_ratification_without_proposal_rejected`,
`test_ratification_does_not_rewrite_source_file`.

## 6. Result

`S16 REPRODUCTION QUALITY: PASS — derived, not self-declared.`
`S16 MEASURED CONTRADICTION: PASS — derived from the measured interval; fixture strings have no authority.`
`DOCTRINE RATIFICATION: PASS — governed AuthorityState OPERATOR-only via prior proposal; manual unamended.`
