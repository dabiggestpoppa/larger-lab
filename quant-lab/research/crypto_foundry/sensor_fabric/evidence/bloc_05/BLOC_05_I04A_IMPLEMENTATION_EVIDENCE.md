# SENSOR-B5-I04A — IMPLEMENTATION EVIDENCE

> Checkpoint verdict: `PASS_SENSOR_B5_I04A_TERMS_FOUNDATION` proposed as
> **I04A_IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW** (recorded, never
> self-ratified). This document measures the I04A contract-terms schema and
> projection foundation on the exact implementation tree; governance values
> are recorded in ledger section 164. No conversion primitive, no resolver
> change, no new enum, and no program-gate promotion occurred.

---

## 0. Scope

Authorized in (I04A directive): source-authority reconstruction,
`ContractTermsSnapshot` schema, terms projection/refusal interface, schema
and PIT eligibility tests, adversarial terms fixtures, deterministic evidence
foundation, I04A evidence and custody.

Explicitly NOT owned: linear/inverse conversion implementation,
reference-price sourcing, I03 resolver changes, I05 time registry, I08
common units, I10+ normalization, I16 lineage, program-level gate promotion.
Verified mechanically (section 6 scope audit, 10/10 PASS).

## 1. Operator decisions as implemented

**D1 (interpretation A).** `ContractTermsSnapshot` is a point-in-time
projection of the applicable verified terms already recorded on the accepted
`ContractInstance`, plus `quote_asset_id` taken from the instance's accepted
`EconomicContract` — required verbatim by `bloc_05/03 §6` ("the terms
registry supplies … quote_asset"), which the instance record alone cannot
carry; this is a read of accepted I02 registry truth, not a new authority,
and it is recorded field-by-field in the schema matrix. No extra economic
term was invented; no missing term was defaulted; nothing in `src/`
represents a term the frozen records cannot express (any such gap would have
been reported as missing authority — none arose).

**D2 (interpretation B).** The I03 resolver is consumed, never modified
(`identity/` diff vs HEAD = empty, measured by the scope audit).
`TERMS_UNVERIFIED` remains a reserved `IdentityResolutionStatus` member: an
AST scan proves zero non-docstring mentions in `terms/` sources and zero
`return`-construction lines in `identity/resolver.py`. Terms verification is
enforced at the I04 boundary: a `RESOLVED_EXACT` identity with
`payoff_type=UNKNOWN` (bloc_05/01 §3 unverified semantics) yields **no
snapshot** while the identity status is untouched. No new status enum, flag,
or public response contract was created: the projection returns the snapshot
or `None` (typed absence; refusal reasons derive from the supplied clocks),
so no STOP condition fired.

## 2. ContractTermsSnapshot schema

17 fields, frozen immutable (`IdentityModelBase`: `extra="forbid"` +
`frozen=True`), Decimals stay `Decimal`, UTC coercion inherited, optional
terms explicit, provenance preserved verbatim:

| field | source | authority |
|---|---|---|
| contract_instance_id | ContractInstance | bloc_05/01 §2.5 association |
| economic_contract_id | ContractInstance | §2.5 / §2.4 grouping ref |
| contract_terms_version | ContractInstance | §7/§15 versioning |
| contract_multiplier | ContractInstance | bloc_05/03 §6 |
| multiplier_unit | ContractInstance | bloc_05/03 §6 |
| price_unit | ContractInstance | §2.5 + 03 §8 price semantics |
| quantity_unit | ContractInstance | §2.5 + 03 §6 |
| payoff_type | ContractInstance | 03 §6 + 07 F5 |
| inverse_flag | ContractInstance | §2.5 recorded structural truth |
| quanto_flag | ContractInstance | §2.5 recorded structural truth |
| quote_asset_id | EconomicContract | 03 §6 quote_asset (F6 separation) |
| settlement_asset_id | ContractInstance | 03 §6 |
| margin_asset_id (opt) | ContractInstance | §2.5 + F6 |
| tick_size / lot_size | ContractInstance | §2.5 + §7 drivers |
| expiry (opt) | ContractInstance | §2.5 |
| source_evidence_refs | ContractInstance | §2.5 provenance (A8) |

The 15 non-projected fields of the two source models (provider, venue,
native_symbol, the four clock fields, grouping metadata, duplicate payoff on
the economic contract) carry explicit EXCLUDED dispositions with reasons in
`BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX.json` (32 source rows, 17 projected,
0 snapshot fields unmapped).

**Placement.** New subpackage `src/crypto_sensor_fabric/normalization/terms/`
(`__init__.py`, `snapshot.py`, `projection.py`) — the smallest I04-specific
path that (a) is not I08's `common/conversion.py`, (b) is not the forbidden
`terms.py` module beside the package (that file remains absent), (c) does
not modify any identity module. The I01 scope audit's subpackage allowlist
was extended `{"identity"} → {"identity", "terms"}` under the established
I02 precedent (I02 extended the same list for `identity/`, disclosed then
and now); every other I01/I02/I03 scope law is untouched and green
(48 + 53 tests). The top-level normalization surface remains exactly the
24 ratified B5-I01 symbols (measured by the scope audit).

## 3. Projection contract

`project_contract_terms(registry, resolution, event_time, knowledge_cutoff)
-> ContractTermsSnapshot | None` — pure, no I/O, no symbol matching, no
ambiguous selection, no price retrieval, no multiplier inference. Refuses
(non-exhaustive by design): unresolved/ambiguous identity (`contract_instance_id`
None or status not `RESOLVED_*`), event outside
`valid_from <= t < valid_to`, cutoff outside `known_from <= c < known_to`
(half-open; the boundary is pinned at ±1µs against a real resolved fixture
rather than claimed from a copied predicate), `payoff_type=UNKNOWN`, or a
referentially missing economic contract (fail-closed, never invented quote).
The I04-owned gate is proven independent of the resolver: a resolution
obtained in-window and re-asked at `known_to` or an early event/cutoff still
refuses (P11, T04A-06/09/11/12).

## 4. RED-first capture

`tests/.../test_b5_i04_terms.py` was authored before any I04A module
existed; the pre-implementation run failed with
`ModuleNotFoundError: No module named 'crypto_sensor_fabric.normalization.terms'`
(pytest exit 2, collection error) — no existing code was touched to produce
the RED. After Stage C the suite passed 28/28 (T04A-01..20 mapped across 20
tests + A1–A8 as 8 further tests).

## 5. Test results (V1–V3) — see section 8 for the full battery

- V1 focused: **28 passed** (T04A-01..20 + A1–A8).
- V2 normalization: **525 passed** (I03I baseline 497 + 28 new).
- V3 I03 resolver regression: **84 passed**, no new failures.

## 6. Evidence outputs (V4)

Generator: `research/crypto_foundry/sensor_fabric/scripts/b5_i04_terms.py`
(tracked in this commit; pinned run-date literal; no `.bu_tmp` dependency).
Double-run byte-identical **4/4**; sha256:

| artifact | rows | sha256 |
|---|---|---|
| BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX.json | 32 (17 projected / 15 excluded) | `014f5aac39b86f2a507fe0abaeb827f4c1d036cb235fe44d9e4542b4cca9351f` |
| BLOC_05_I04A_PIT_TERMS_MATRIX.json | 12/12 PASS | `79de338f0d4a521f8029cf1c8255bd53ae7a6feede67cbcf33fe60a143ef2538` |
| BLOC_05_I04A_ADVERSARIAL_MATRIX.json | 8/8 PASS | `19741accc923e3ae6e981e63ff84e9568d6e07aad7179fb1b55d12942fcd9b27` |
| BLOC_05_I04A_SCOPE_AUDIT.json | 10/10 PASS | `07ca4a69bc6e7eac0d609fd47efdf1680f9d061247827abfd9b7a21317ed02fb` |

Determinism defect found and fixed during Stage E (disclosed): the first
generation embedded `repr()` memory addresses for nested `Annotated`
validators, so a re-run changed the schema matrix hash; the generator now
emits an address-stripped stable repr, after which two consecutive runs were
byte-identical. PIT rows are executed probes (observed status + observed
snapshot presence recorded); hand-written expectations are labeled
`expected_result` only.

## 7. Adversarial results (A1–A8)

All **PASS** in both the test suite and the executed matrix: A1 multiplier
0.25 preserved (never coerced to 1); A2 quote USD vs settlement USDT remain
distinct; A3 sequential v1/v2 instances keep the bound version (no upgrade);
A4 `known_from` after cutoff → blocked + absent; A5 resolved identity with
unverified payoff → `RESOLVED_EXACT` + absent (no escalation, no reserved
status); A6 equal multipliers cannot collapse two candidates; A7 missing
multiplier refused at the model (null never becomes 0); A8 snapshot refs
verbatim subset of authorized sources. Every row carries its
non-mutation assertion (registry dumps compared pre/post projection: HELD).

## 8. Verification battery (V6–V8) and acceptance predicates

- V6 I11R2 governance audit: this commit adds **5 tracked Python files**
  (`terms/{__init__,snapshot,projection}.py`, `test_b5_i04_terms.py`,
  `b5_i04_terms.py`), so the mechanically-recorded `python_files_scanned`
  moves **1037 → 1042**, republished via the established
  `UPDATE_I11R2_EVIDENCE=1` procedure and disclosed here (the I03J lesson —
  the republish is staged with the same commit that creates the count).
- V8 static: ruff changed scope **All checks passed**; mypy: **0 errors in
  `terms/`** (10 pre-existing provider/probe errors, inherited baseline
  unchanged); compileall OK; secret scan clean.
- V5/V7: historical noninterference and the full project suite are recorded
  in ledger section 164 at custody time.

Acceptance predicates (I04A directive §10), each reported individually in
the final report: (1) starting custody ✓, (2) D1 mapping grounded ✓, (3) D2
ownership preserved ✓, (4) source schema fidelity ✓, (5) PIT clock fidelity
✓, (6) no false verified terms ✓, (7) no identity mutation ✓, (8) no
fabricated economic values ✓, (9) no unverified-to-verified promotion ✓,
(10) T04A coverage 20/20 ✓, (11) A1–A8 coverage 8/8 ✓, (12) tracked
generator reproducible 4/4 ✓, (13) protected historical evidence integrity ✓
(one-line disclosed I11R2 republish only), (14) focused + regression passing
✓, (15) no unauthorized expansion ✓ (scope audit 10/10).

The R1–R15 inventory from the readiness assessment remains applicable to the
full I04 checkpoint; I04A closes only the contract/schema portion (R1, R6,
R13, R14, R15 and the snapshot half of R10). Linear/inverse conversion
requirements (R2–R5, R7-style conversion refusals) remain open for the
separately authorized I04B.

## 9. Limitations

- Tick/lot/expiry are projected but their conversion-time use is I04B+.
- `payoff_type=UNKNOWN` is the only terms-unverification signal the frozen
  schema exposes; if a richer verified/unverified terms dimension exists in
  the frozen contract but is unrepresentable here, that is a
  `REQUIRES_OPERATOR_DECISION` gap (none was hit for I04A scope).
- The adversarial matrix is I04A-scoped; no conversion traps (A-style
  reference-price tests) exist yet by design.
- Cross-revision knowledge-overlap probing (I03J limitation L2) remains
  open coverage work, untouched by I04A.

*Governance: `IDENTITY_GATE = NOT_YET_EARNED`; `next_checkpoint_authorized
= FALSE`; B5-I04B+ = UNAUTHORIZED; BLOC_06 = UNAUTHORIZED; RESEARCH =
FROZEN. HARD STOP after push and report.*
