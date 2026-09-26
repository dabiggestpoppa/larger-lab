# CSIA Book 4 Hardening R3 — Multi-Provider Independence Completeness

- **Date:** 2026-09-26
- **Trigger:** external review demonstrated a concrete correctness defect.
  R3 is a demonstrated-defect repair, **not** a generic hardening round.
- **Baseline HEAD:** `199cad59603c079a1a5b1ed6c8630e0268b32ea3` (R2 + audit record)
- **Repair commits:** `074cd6cc` (failing probes), `27471815` (pair-coverage seal),
  `c67d5241` (fail-closed untyped bindings + decision-point probes)

## Historical Context (do not rewrite R2 evidence)

The R2 adversarial audit (`CSIA_BOOK_4_HARDENING_R2_ADVERSARIAL_AUDIT.md`)
correctly identified that **partial** pair coverage was a defect (defect D3:
a third provider riding on first-pair evidence). Its remedy — requiring
**every consecutive provider pair** — was, however, incomplete:

1. **PAIRWISE_TRANSITIVITY_FALSE** — consecutive coverage for
   `providers = (A, B, C)` requires only A-B and B-C. An unverified A-C pair
   could still share a material failure mechanism while the whole set was
   classified INDEPENDENT_REDUNDANCY. Independence is not transitive:
   A⊥B and B⊥C does **not** imply A⊥C.
2. **FIRST_PAIR_BINDING_ASSUMPTION** —
   `RedundancyAssessment._binding_matches` bound every independence binding
   against `provider_refs[0]`/`provider_refs[1]` only, so a legitimate B-C
   binding in a 3-provider assessment could not be represented faithfully at
   all.

Both defects had to be fixed together, exactly as external review specified.

## Superseded Invariant

> R2 (superseded): "every consecutive provider pair must carry its own
> pair-scoped binding."

**R3 (current): COMPLETE_UNORDERED_PAIR_COVERAGE.**

## R3 Invariant

For `INDEPENDENT_REDUNDANCY` over `N` assessed providers:

- `required_pairs` = all unordered 2-combinations of `provider_refs`
  (count: `N * (N - 1) / 2`).
- `bound_pairs` = normalized pairs of the assessment's typed independence
  bindings, re-derived at the decision point (`RedundancyBook.add`) from the
  record's **current** state.
- Gate: `bound_pairs == required_pairs` — exact set equality. Not subset, not
  consecutive pairs, not "at least N-1", not transitive inference.

Pair identity is normalized deterministically
(`normalized_provider_pair`: `(A, B)` and `(B, A)` are the same redundancy
pair), so provider tuple ordering cannot change independence truth.
Failure-domain directional comparison semantics are untouched — this R3 is
specifically redundancy-set coverage.

## `_binding_matches` Contract (Phase 4)

A redundancy independence binding must prove **all** of:

1. `left_domain_ref` belongs to `assessment.provider_refs`
2. `right_domain_ref` belongs to `assessment.provider_refs`
3. `left != right` (no self-pair)
4. `left_system_ref`/`right_system_ref` match `assessment.subject_ref`
5. `correlation_scope` matches `assessment.function`
6. the claim resolves as canonical `POSITIVE_INDEPENDENCE` (unchanged R2 gate)
7. the binding `claim_ref` exactly covers the declared
   `positive_independence_claim_refs` (claim coverage — unchanged R2 doctrine)
8. the provider pair is one of the required normalized pairs

External providers can never enter the set; untyped/raw binding payloads are
refused closed (never crash) at the decision point.

## Probe Results

### Pair-completeness matrix (`test_book4_r3_pair_coverage.py`, 17 probes)

| Probe | Scenario | Result |
|---|---|---|
| R3-A1 | A/B/C with A-B, B-C only (A-C missing) | REJECT (incomplete pair coverage) |
| R3-A2 | A/B/C with complete A-B, A-C, B-C | PASS (INDEPENDENT_REDUNDANCY) |
| R3-A3 | providers reordered to C, A, B, same unordered evidence | PASS (order-invariant) |
| R3-A4 | two distinct A-B claims + A-C, B-C missing | REJECT (duplicates never substitute) |
| R3-A5 | complete in-set coverage + external A-D binding | REJECT (provider outside assessed set) |
| R3-A6 | self-pair A-A binding | REJECT (self-pair refused) |
| R3-A7 | 2-provider A/B with correctly scoped claim | PASS (two-provider behavior preserved) |
| R3-A8 | 4-provider, each of the 6 pairs dropped in turn (6 params) | REJECT every time |
| R3-A9 | 4-provider complete six-pair coverage | PASS |
| extra | A⊥B ∧ B⊥C does not imply A⊥C (no-transitivity) | REJECT without A-C |
| extra | UNKNOWN with no bindings stays UNKNOWN | PASS (doctrine preserved) |
| extra | CORRELATED + declared positive refs keeps CORRELATED | PASS (no silent upgrade) |

### Decision-point probes (`test_book4_r3_model_copy_adversarial.py`, 4 probes)

| Probe | Scenario | Result |
|---|---|---|
| R3-B1 | complete A/B/C record, `model_copy` strips to 2 bindings (claims kept consistent) | REJECT (incomplete pair coverage) |
| R3-B2 | `model_copy` expands (A, B) → (A, B, C) without new bindings | REJECT (incomplete pair coverage) |
| R3-B3 | `model_copy` reorders provider_refs with complete normalized coverage | PASS |
| R3-B4 | raw dict binding injected via `model_copy` | FAIL CLOSED (explicit refusal; defect found and fixed) |

**Defect found during R3 probing:** raw dict bindings injected through
`model_copy` crashed `RedundancyBook.add` with `AttributeError` (the R2
fail-closed fix had covered the HARD_RUNTIME gate but not the redundancy
decision point). Fixed in `c67d5241`: untyped binding payloads are explicitly
refused.

## Verification

- Pre-R3 CSIA baseline: **486 PASS** (reproduced on `199cad59`).
- Post-R3 CSIA: **507 PASS** (486 preserved + 17 pair-coverage + 4
  decision-point probes).
- Ruff: PASS. mypy: PASS (37 source files).
- Sensor: 2325 PASS / 14 FAIL / 4 SKIPPED; failure IDs byte-identical to the
  R2 equivalence record; `BOOK4_INTRODUCED_SENSOR_FAILURES = 0`.
- Freeze: Books 1/2/3 and Sensor mutation count **0**.
- No transitivity primitive, no set-level claim shortcut, no consecutive-pair
  shortcut was introduced.
