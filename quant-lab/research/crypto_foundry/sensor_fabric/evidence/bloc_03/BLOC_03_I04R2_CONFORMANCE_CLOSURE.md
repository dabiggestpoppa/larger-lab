# SENSOR-B3-I04R2 — Final Common-Foundation Conformance Closure

**Checkpoint verdict:** `PASS_SENSOR_B3_I04R2_COMMON_FOUNDATION_CLOSED`

**Parent head:** `bfa5c580` (I04R1B). **Status:** common foundation complete /
hardened / behaviorally closed. **No provider adapter was built. No network
call was made. No Bloc 4 code was started.**

## Readiness summary

| Field | Value |
|---|---|
| COMMON_FRAMEWORK_READY | TRUE |
| BEHAVIORAL_CONFORMANCE_READY | TRUE |
| REAL_PROVIDER_ADAPTERS | 0 |
| PROVIDER_PARSER_CONFORMANCE | NOT_YET_APPLICABLE (no provider parser exists yet) |
| NETWORK_VALIDATION | NOT_YET_RUN (I13 was Bloc 2 probe; no Bloc 3 live smoke) |
| human_review_required | TRUE |
| provider_adapter_implementation_authorized | FALSE (awaiting operator review) |
| next_checkpoint_authorized | FALSE |

## Issues closed

1. **Empty-valid vs unsupported is BEHAVIORAL (Issue 1).** The conformance
   suite (`q1_empty_valid_distinct`) now invokes the adapter's real fetch
   method via dispatch and asserts: supported + 0 rows => a `FetchBatch` with
   the explicit `EMPTY_VALID` quality flag; unsupported sensor => typed
   `CapabilityUnavailable`. Never `[]`/`0`/`None`.
2. **Offline dispatch (Issue 2).** New provider-independent `dispatch_fetch`
   maps each sensor family to its protocol method
   (`fetch_trades/liquidations/open_interest/funding/book/book_metrics/
   positioning/basis`). Conformance and tests exercise this exact path, so a
   future provider adapter can never "pass" while its fetch methods break the
   protocol. `test_dispatch.py` proves each sensor routes to the correct
   method and unsupported/unknown sensors fail typed.
3. **Valid-typed adversarial fixtures (Issue 3).** `model_copy(update=...)`
   raw-string into enum-typed-field paths removed. All overrides go through
   `model_dump` + `model_validate` with real enum members; tests assert
   `isinstance(field, ExpectedEnum)`.
4. **Full surface binding (Issue 4/9).** `promotion_bound_violations` now
   compares `live_mode`, `archive_mode`, `access_mode`, `auth_requirement`,
   `free_access_status` and `history_scope` one-to-one. CURRENT_ONLY cannot
   become historical, ARCHIVE_ONLY cannot become REST, historical does not
   auto-grant live, a non-archive surface cannot silently become archive, and
   an exact native historical_mode is never manufactured (Issue 8).
5. **Evidence ref must resolve (Issue 5).** `q0_evidence_ref_resolves` verifies
   ref.provider_id == adapter, ref.sensor_family == the declared sensor, and
   ref.evidence_id is one of that I14 candidate's evidence_basis ids. A correct
   basis with unrelated primary ref, provider mismatch, or sensor mismatch all
   FAIL.
6. **Strict promotion-file structure (Issue 6).** `load_promotion_candidates`
   fails closed on: root not mapping, missing/unsupported schema_version,
   candidates not a non-empty list, candidate not mapping, missing provider,
   missing sensor, and (in `capabilities_from_promotion`) duplicate
   provider×sensor (never overwritten silently).
7. **Auth override removed (Issue 7).** `auth_mode_override` is gone; the I14
   `access_path` alone is authoritative. Signature test asserts its absence.
8. **History vs native mode (Issue 8).** `HistoryScope` carries the coarse I14
   label verbatim; `SensorCapability.historical_mode` (exact native mode) is
   left for the provider's own Bloc 2 evidence and is NEVER inferred. The old
   generic `HISTORICAL -> REST_RANGE` and `CURRENT_ONLY -> LIVE_REST_ONLY`
   inference is removed.
9. **Schema policy vs parser (Issue 10).** `assess_schema` /
   `parse_fail_closed` / `assert_no_zero_coercion` prove COMMON SCHEMA POLICY:
   KNOWN parses, ADDITIVE flags, BREAKING/UNKNOWN block with raw preserved and
   no zero coercion. No real provider parser has passed these yet (that is I05+
   provider conformance).

## Promotion-bound invariants now enforced (fail closed)

- provider present in `source_promotion_candidates.yaml` (production mode)
- sensor not promoted -> supported must not be declared
- allowed_role / historical_mode / history_scope / verified_history_start /
  verified_history_end / PIT / methodology_pin / redundancy_class unchanged
- live_mode, archive_mode, access_path, auth_requirement, free_access_status
  unchanged
- no exact-native-mode manufacturing from a coarse label
- hazards not removed; evidence_basis resolves; evidence ref resolves
- CURRENT_ONLY stays CURRENT_ONLY; ARCHIVE_ONLY never REST; historical never
  auto-grants live; MECHANISM_MICROSCOPE never generalized

## Live/history representation decision

- Coarse I14 label (`history_mode`) -> `HistoryScope` (authoritative).
- `historical_mode` (native surface) left `None` until a provider supplies it
  from Bloc 2 evidence — generic inference REMOVED.
- CURRENT_ONLY public REST -> `live_mode = LIVE_REST`, scope CURRENT_ONLY.
- HISTORICAL -> `live_mode = NONE` (no auto-granted live).
- ARCHIVE_ONLY / THIRD_PARTY_ARCHIVE -> `archive_mode = True`, `live_mode =
  NONE`.

## Adversarial tests added

provider mismatch; sensor mismatch; unsupported declared supported; role
change; history-scope change; exact-native-mode manufacture; history-start
earlier; history-end later; live widening of historical; live removal from
CURRENT_ONLY; archive->REST; non-archive->archive; access-path change; auth
change; free-only downgrade; PIT change; methodology-pin change/removal;
redundancy change; hazard removal; evidence-basis removal; evidence-ref id /
provider / sensor mismatch; duplicate provider×sensor; malformed promotion
row; missing promotion file in PRODUCTION_CANDIDATE mode; geo never retried.

Every negative test uses a type-valid degraded model and asserts the intended
conformance check fails with a name of the semantic violation.

## Pass proofs

legitimate I14-bounded fake adapter passes all checks; explicit EMPTY_VALID
supported response; raw preservation + parsed-output blocking on unknown
schema; valid deterministic dispatch; valid free-only access; valid I14
evidence lineage.

## Validation

- pytest (crypto_sensor_fabric): **666 passed / 0 failed** (baseline was 636).
- ruff: clean.
- Network calls: **0**. Provider adapters built: **0**. Bloc 4 code: **0**.