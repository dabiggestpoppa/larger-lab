# SENSOR-B5-I04 — READINESS ASSESSMENT (READ-ONLY, NOT AN AUTHORIZATION)

> Produced under directive SENSOR-B5-I03J, Operation B. This document
> reconstructs the frozen B5-I04 contract from the frozen plan branch,
> measures dependency readiness against accepted evidence, and designs the
> implementation blueprint, adversarial test plan, and evidence plan.
> **No I04 code, tests, or placeholders were written.**
> Readiness verdict: **`REQUIRES_OPERATOR_DECISION`** (two smallest
> decisions, §11). Readiness is not permission to begin implementation.

---

## 1. Frozen checkpoint identity (§06.1)

```text
identifier:      SENSOR-B5-I04
frozen title:    contract terms + linear/inverse conversion primitives
owning_bloc:     BLOC 05 — NORMALIZATION / IDENTITY FOUNDATION
frozen_in:       SENSOR-PLAN-B5F (bloc_05/06 §19) and
                 SENSOR-PLAN-B5G (bloc_05/07 §10) — identical wording in both
sequence:        after B5-I03 (lifecycle/alias/PIT resolver),
                 before B5-I05 (time semantics registry)
```

**Purpose.** Supply point-in-time contract-terms truth and the guarded
linear/inverse conversion primitives that economic normalization requires,
without any universal futures-conversion formula (bloc_05/07 F5) and without
collapsing contract identity into an asset label (F1/F3).

**Scope boundaries (frozen clauses).**

- F3 (bloc_05/07 §1): rows with ambiguous or unverified contract terms stay
  native evidence — never verified comparable T1 data.
- F5 (bloc_05/07 §1): linear/inverse/quanto semantics explicit;
  price-dependent inverse conversions require PIT-valid contract terms **and**
  reference-price lineage.
- §6 (bloc_05/03): all derivative quantity conversions reference the
  PIT-valid `ContractInstance`; the terms registry supplies
  `contract_multiplier`, `multiplier_unit`, `payoff_type`, `quote_asset`,
  `settlement_asset`; no provider multiplier hard-coded anywhere; conversion
  code lives in the normalization layer and is versioned.
- §7 (bloc_05/03): linear framework —
  `base_exposure = contracts × base_per_contract`,
  `quote_notional = base_exposure × reference_price`;
  exact formulas provider/term-driven; **may not assume `1 contract = 1 base`**
  unless verified.
- §8 (bloc_05/03): inverse framework — record
  `reference_price`, `reference_price_type`, `reference_price_time`,
  `reference_price_source`; allowed types `PROVIDER_MARK | PROVIDER_INDEX |
  TRADE_PRICE | MID_PRICE | INTERVAL_CLOSE` (no silent substitution); if no
  PIT-safe price: `normalized_value = NULL`, `quality_flag =
  UNIT_CONVERSION_BLOCKED`.
- §22 invariants (bloc_05/03): native values survive; conversion assumptions
  explicit; stablecoin ≠ USD; inverse conversion needs PIT-valid terms +
  reference price; null ≠ zero; every derived value references a methodology
  version; semantics fail closed without discarding raw evidence.
- Source reservation: `src/.../identity/models.py`, `resolver.py`,
  `__init__.py` docstrings all state terms/conversion logic is **B5-I04
  owned** and absent from I01–I03.
- **Inputs:** PIT-valid `ContractInstance` terms fields (via I03 resolution),
  integer/Decimal contract amounts, and — for inverse math — an externally
  supplied reference-price observation (produced by later sensor checkpoints;
  I04 consumes it as an argument).
- **Outputs:** a PIT terms snapshot (see decision D1) + pure conversion
  primitives returning derived exposure or `NULL + UNIT_CONVERSION_BLOCKED`,
  each carrying `conversion_inputs` lineage refs and a methodology version
  (bloc_05/03 §17, G5).
- **Upstream dependencies:** B5-I01 (enums/Decimal/UTC models), B5-I02
  (identity registry/`ContractInstance`), B5-I03 (PIT resolver).
- **Downstream consumers:** B5-I05 (time semantics for
  `reference_price_time`), B5-I08 (common units/stablecoin — orthogonal, must
  not be preempted), sensor normalizers B5-I10…I15 (call the primitives),
  B5-I16 lineage (records `conversion_inputs`), gates G1/G3/G5/G8/G9.
- **Required implementation artifacts:** normalization-layer terms +
  conversion module(s) (path proposed, §7.3), N0/N1/N3 test files, tracked
  evidence producer(s).
- **Required evidence:** see §9.1 (frozen artifact list bloc_05/06 §17 +
  proposed per-checkpoint matrices following the I03 convention).
- **Acceptance predicates:** G1 (no future terms knowledge leaks backward),
  G3 (native values preserved — primitives add fields, never replace),
  G5 (linear/inverse terms drive formulas; blocked conversion yields
  NULL + reason, never a guess; lineage + methodology on every derived
  amount), G8 (deterministic regeneration), G9 (unknown terms fail closed).
- **STOP conditions:** any requirement needing a new semantic rule beyond the
  two decisions in §11; any proposal to modify identity registry history; any
  formula assumption equivalent to `1 contract = 1 base` without evidence; any
  reference-price substitution; any path that converts when terms are
  unverified or identity is not `RESOLVED_*`.

Named differently historically? No — "I04" in the plan always means this
checkpoint; `TERMS_UNVERIFIED` reservations do not make I04 a "terms status"
checkpoint, and time semantics is I05, not I04.

## 2. Authority reconstruction (paths and applicable clauses)

```text
plan canon    : origin/agent/crypto-sensor-fabric-plan (SENSOR-PLAN-B5A…B5G;
                bloc_05 docs frozen at dafcd86a0)
build copies  : quant-lab/research/crypto_foundry/sensor_fabric/bloc_05/*.md
                blob-identical to the plan branch (verified by git rev-parse,
                all 7 files SAME) — reading the worktree copies reads the
                frozen contract
key clauses   : bloc_05/06 §1 gates G1–G9 · §2 test layers · §3 N0 laws ·
                §17 evidence outputs · §18 planned tree · §19 staged commits
                (I04 line) · §20 commit review · §21 stop gate
                bloc_05/07 F1–F30 · §2 frozen identity objects (incl.
                ContractTermsSnapshot) · §10 sequence · §11 gates
                bloc_05/01 §2.5 ContractInstance · §7 terms-version drivers ·
                §9 statuses/blocker set · §10 matching order · §13/§14 flags ·
                §15 registry versioning
                bloc_05/03 §6 terms registry · §7 linear · §8 inverse ·
                §9 stablecoin (I08) · §17 conversion lineage · §21 required
                modules · §22 invariants
research canon: agent/crypto-quant-foundry — research only, never overrides
                the frozen plan; a prior agent report is not an authority
                document (this file included)
```

No named I04 contract is absent from the plan; nothing was substituted.

## 3. Dependency table (§06.2)

```text
dependency_id  | source_path / owner                    | owning_checkpoint | contract_or_interface                          | required_state            | observed_state                                   | evidence_reference                              | readiness_disposition
---------------+----------------------------------------+-------------------+------------------------------------------------+---------------------------+--------------------------------------------------+-------------------------------------------------+----------------------
D-I01-ENUMS    | normalization/enums.py, models.py       | B5-I01 (ratified) | PayoffType, quality flags (UNIT_CONVERSION_    | OPERATOR_ACCEPTED         | OPERATOR_ACCEPTED (8d220ad1c)                    | BLOC_05_I01_OPERATOR_RATIFICATION.md             | READY
               |                                        |                   | BLOCKED), Decimal/UTC base models, T1 envelope |                           |                                                  |                                                 |
D-I01-SCOPE    | normalization/__init__.py surface       | B5-I01            | 24-symbol public API, no conversion symbols    | terms/conversion absent   | absent — scope audit proves absence              | BLOC_05_I03_SCOPE_AUDIT.json                    | READY
D-I02-INSTANCE | identity/models.py::ContractInstance    | B5-I02 (ratified) | 23 fields incl. terms subset (multiplier,      | OPERATOR_ACCEPTED         | OPERATOR_ACCEPTED (9ad8279e2); 11/23 field pins  | BLOC_05_I02_OPERATOR_RATIFICATION.md §3          | READY
               |                                        |                   | units, payoff, tick/lot, terms_version)        |                           | re-verified at I03J                              |                                                 |
D-I02-REGISTRY | identity/registry.py                   | B5-I02            | IdentityRegistrySnapshot (immutable, versioned)| referential integrity     | verified live (I02 §4); no-overlap law on active | BLOC_05_I02_REGISTRY_MATRIX.json                | READY
               |                                        |                   |                                                |                           | terms per provider/venue/symbol                  |                                                 |
D-I03-RESOLVE  | identity/resolver.py::resolve_instrument| B5-I03 (ratified  | IdentityResolution (status, instance/economic/ | OPERATOR_ACCEPTED         | OPERATOR_ACCEPTED (this directive)               | BLOC_05_I03_OPERATOR_RATIFICATION.md §2          | READY
               |                                        | by I03J)          | canonical ids, terms_version, flags, refs)     |                           |                                                  |                                                 |
D-I03-TERMSVER | identity/resolver.py (TERMS_UNVERIFIED) | B5-I03 / unclear  | status constructible when terms unverified     | ownership decided         | RESERVED, never constructed (G4 pin)             | BLOC_05_I03_SCOPE_AUDIT.json g4 pin             | BLOCKED → decision D2
D-I03-SCHEMA   | ContractTermsSnapshot                   | plan §2 name only | frozen object name, NO frozen field list       | schema frozen             | name-only                                        | bloc_05/07 §2                                  | BLOCKED → decision D1
D-I05-TIME     | normalization/time/ (not started)       | B5-I05            | reference_price_time interval semantics        | NOT_STARTED               | absent (correctly — sequence after I04)          | bloc_05/06 §19                                  | NOT REQUIRED FOR I04 (pass time as plain UTC)
D-I08-UNITS    | normalization/common/ (not started)     | B5-I08            | units/stablecoin conversion framework          | NOT_STARTED               | absent; I04 must not preempt (§9 stablecoin)     | bloc_05/03 §9, §21                              | NOT REQUIRED FOR I04 (primitives are payoff math only)
D-I10-PRICE    | sensor normalizers (not started)        | B5-I10+           | reference-price observation production         | NOT_STARTED               | absent; I04 consumes price as an argument        | bloc_05/03 §8                                   | NOT REQUIRED AS UPSTREAM (input contract only)
D-GATES        | 8 bloc gates                           | program-level     | IDENTITY…GOLDEN_T0_T1                          | NOT_YET_EARNED            | NOT_YET_EARNED (unchanged by I03J)               | ledger §163                                     | UNEARNED — I04 completion cannot promote them
D-T0-EVIDENCE  | bloc_04 evidence lake                  | B4 (ratified)     | source_evidence_refs provenance                | immutable                 | immutable; I03I restore discipline documented     | ledger §162                                     | READY (read-only input)
```

No dependency is claimed satisfied by mere import; each observed state cites
accepted evidence. No T0/T1 replay-consumer dependency is established by the
frozen plan before B5-I16/I19.

## 4. I04 interface inventory (§06.3)

```text
interface_name            | owning_module        | input_schema                                   | output_schema                        | required_fields                                            | optional_fields            | enum_dependencies                        | validation_laws                                      | error_or_refusal_behavior                       | PIT_requirements                         | provenance_requirements               | mutation_permissions        | forbidden_behavior                       | state
--------------------------+----------------------+------------------------------------------------+--------------------------------------+------------------------------------------------------------+----------------------------+-------------------------------------------+-----------------------------------------------------+------------------------------------------------+-------------------------------------------+-----------------------------------------+-----------------------------+------------------------------------------+--------
ContractTermsSnapshot     | PENDING D1             | D1: PIT projection of ContractInstance terms    | D1: frozen model, extra="forbid"     | D1 candidate: contract_instance_id, contract_terms_version,| D1 candidate: expiry       | PayoffType (I01)                          | snapshot only from a RESOLVED instance; fields set- | n/a (data object)                                | must be produced at an explicit event_time  | must carry source_evidence_refs         | none (immutable)         | inventing fields not in D1; defaults       | RESERVED (D1)
resolve_terms(snapshot,   | PENDING D1             | IdentityRegistrySnapshot, resolved instance id, | terms snapshot or typed refusal      | instance must be PIT-valid at both clocks                 |                            | IdentityResolutionStatus (I03)           | eligible iff _pit_valid passes at supplied clocks   | refuse (no terms) when identity not RESOLVED_*  | event_time + knowledge_cutoff both supplied | refs passed through, never synthesized  | none (pure)             | resolving terms for AMBIGUOUS/UNKNOWN     | PLANNED
instance, event, cutoff)  |                      | identity resolution context                     |                                      |                                                            |                            |                                           |                                                     |                                                |                                           |                                         |                             |                                          |
linear_base_exposure      | PENDING D1             | contracts: Decimal, terms: resolved snapshot    | base_exposure: Decimal or None       | contracts, contract_multiplier, multiplier_unit, payoff=   |                            | PayoffType                               | refuse payoff != LINEAR/INVERSE as applicable;     | None + UNIT_CONVERSION_BLOCKED when terms       | terms snapshot must be PIT-valid          | conversion_inputs=[contract_multiplier_ | none (pure)             | assuming 1 contract = 1 base; guessing     | PLANNED
(...)                      |                      |                                                |                                      | LINEAR path; Decimal precision preserved                   |                            |                                           | no float math                                        | incomplete                                     |                                           | ref] + methodology version               |                             | multiplier                               |
quote_notional            | PENDING D1             | base_exposure, reference_price observation     | quote_notional: Decimal or None      | reference_price, reference_price_type, _time, _source;    |                            | ReferencePriceType (D1 candidate frozen  | type must be one of the five allowed; no silent     | None + UNIT_CONVERSION_BLOCKED when price       | reference price supplied PIT-safely by    | conversion_inputs=[price_observation_  | none (pure)             | substituting reference-price type;         | PLANNED
(...)                      |                      |                                                |                                      | inverse path requires terms                               |                            | list from bloc_05/03 §8)                 | substitution                                          | absent/unavailable or terms unverified          | caller                                      | ref, terms ref] + methodology           |                             | converting without lineage                |
inverse_base_from_quote   | PENDING D1             | quote_notional, terms, reference_price         | base_exposure: Decimal or None       | payoff=INVERSE; all four price fields recorded            |                            | PayoffType                               | price-dependent math only with recorded price block | None + UNIT_CONVERSION_BLOCKED                 | same as above                            | same as above                            | none (pure)             | inverse math without price/lineage        | PLANNED
UNIT_CONVERSION_BLOCKED   | enums.py (I01, done) | n/a                                            | n/a                                    | flag emitted on the observation layer                     |                            | NormalizationQualityFlag                 | emitted only with NULL value (null != zero)         | n/a                                              | n/a                                        | n/a                                      | none (frozen)           | using the flag with a non-NULL value       | IMPLEMENTED (I01)
TERMS_UNVERIFIED          | identity/enums (done)| n/a                                            | n/a                                    | member of IdentityResolutionStatus blocker set            |                            | IdentityResolutionStatus                 | blocks T1 economic normalization with AMBIGUOUS etc | n/a                                              | n/a                                        | n/a                                      | none (frozen)           | constructing it anywhere today            | RESERVED (D2)
```

Distinguishing: implemented = enums, `ContractInstance` terms fields,
resolver status set. Reserved = `ContractTermsSnapshot`, `TERMS_UNVERIFIED`
construction. Absent (correctly) = any persisted terms registry, any price
sourcing, any unit/stablecoin conversion (I08), any resolver change (D2).
Requiring clarification = the two RESERVED rows. No placeholders were created
in `src/`.

## 5. Identity-to-I04 handoff (§06.4)

Fields I04 may consume from `IdentityResolution` (all present and authorized):
`status`, `contract_instance_id`, `economic_contract_id`,
`canonical_asset_id`, `terms_version`, `quality_flags`,
`source_evidence_refs`, plus the knowledge cutoff and event time supplied to
the resolver call itself. **Not consumed:** `matched_alias_id` (alias tier
tells I03 truth, not terms), `confidence` (advisory, not terms authority).

Frozen status map (bloc_05/01 §9 + F3; no guessing):

```text
RESOLVED_EXACT / RESOLVED_ALIAS / RESOLVED_WITH_WARNING
    → identity eligible; terms snapshot from the resolved instance;
      primitives may run (identity eligibility ≠ terms completeness:
      unverified/missing terms still refuse per F3/G9)
AMBIGUOUS / UNKNOWN_SYMBOL / TERMS_UNVERIFIED / PIT_KNOWLEDGE_BLOCKED
    → BLOCK T1 economic normalization: no terms snapshot, no conversion,
      native evidence retained, no canonical derived values
NOT_YET_LISTED / DELISTED
    → verdict-only: no observation exists for I04 to convert
```

Lifecycle warning rows (`RESOLVED_WITH_WARNING`) remain convertible — inert
state rows do not invalidate PIT-valid instances (C5).

## 6. Contract boundaries — permissions with citations (§06.5)

```text
action                              | permitted? | citation
create/modify identity records      | NO         | registry versioning owned by I02/§15; no clause grants I04 mutation → prohibited by default (directive §06.5)
mutate registry history             | NO         | F28 revisions append; §15 new generation only
infer missing contract terms        | NO         | F3 + G9 fail-closed; §22 inv.8
resolve unresolved identities        | NO         | bloc_05/01 §10 resolver owns matching; AMBIGUOUS dominates (C6)
reinterpret provider aliases        | NO         | §14 manual override needs evidence + versioned registry change
substitute assets or units          | NO         | F6/F7; §22 inv.1/3
apply historical corrections        | NO         | F27/F28; AS_KNOWN_THEN is B5-I07
consume evidence outside its cutoff | NO         | C2 knowledge law; G1 no backward leakage
change source authority             | NO         | F1/F2; native values preserved (G3)
assume 1 contract = 1 base          | NO         | bloc_05/03 §7 explicit
substitute reference-price types    | NO         | bloc_05/03 §8 explicit
publish derived value without       | NO         | G5 lineage + methodology on every derived amount
  methodology/lineage               |            |
```

## 7. Implementation blueprint (§07 — design only)

### 7.1 Work packages

```text
A — Terms schema fidelity      (decision D1 first)
B — Core terms snapshot + primitives
C — Failure/boundary enforcement
D — Integration with I01–I03 outputs (resolver touch ONLY if D2 grants it)
E — Evidence generation (tracked, deterministic)
F — Hardening (adversarial + determinism)
G — Acceptance (exact-set, regression, custody, operator disposition)
```

Sequence A→G is the directive's candidate shape and fits the frozen
obligations; the frozen plan itself stages only "SENSOR-B5-I04" as one commit
series with no squashing (bloc_05/06 §19), so these are reviewable sub-stages
inside that checkpoint, not replacement checkpoint structure.

### 7.2 Per-stage specification

```text
STAGE A — TERMS SCHEMA FIDELITY
GOVERNING AUTHORITY   : bloc_05/07 §2 (ContractTermsSnapshot), bloc_05/01 §2.5/§7, decision D1
PRECONDITIONS         : D1 answered; I01–I03 ratified (true)
ALLOWED FILES         : new terms module (path per D1), tests/crypto_sensor_fabric/normalization/test_b5_i04_*.py
PROHIBITED FILES      : src/identity/** (unless D2 grants resolver edit), bloc_04/**, I01–I03 evidence, plan/research branches
INPUT CONTRACTS       : ContractInstance terms subset (13 fields listed in §4), D1 schema decision
OUTPUT CONTRACTS      : ContractTermsSnapshot model, extra="forbid", UTC/Decimal laws inherited from I01
REQUIRED INVARIANTS   : snapshot fields ⊆ frozen decision; no default values for required terms; no wall-clock
IMPLEMENTATION STEPS  : model + validators + N0 round-trip/validation tests
POSITIVE TESTS        : snapshot from a fully-specified instance; UTC normalization; Decimal exactness
NEGATIVE TESTS        : missing required terms refused; extra field refused; naive datetime refused
ADVERSARIAL TESTS     : INVERSE without price-unit terms; QUANTO flagged instance; unknown enum payload fails explicitly
EVIDENCE ARTIFACTS    : (feeds) bloc_05_identity_validation.json
REGRESSION REQUIREMENTS: I01/I02/I03 suites unchanged-green
ACCEPTANCE PREDICATES : N0 laws (bloc_05/06 §3) all pass
STOP CONDITIONS       : D1 unanswered; any need to alter I02 models
EXPECTED COMMIT BOUNDARY : stage A+B combined review unit inside the I04 series
NEXT DEPENDENCY       : Stage B

STAGE B — CORE TERMS SNAPSHOT + PRIMITIVES
GOVERNING AUTHORITY   : bloc_05/03 §6/§7/§8, F5, G5
PRECONDITIONS         : Stage A
ALLOWED FILES         : terms/conversion module, its tests
PROHIBITED FILES      : as Stage A
INPUT CONTRACTS       : resolved instance + Decimal contract amounts + optional reference-price block (4 fields)
OUTPUT CONTRACTS      : base_exposure / quote_notional / inverse primitives → value | None with conversion_inputs + methodology version
REQUIRED INVARIANTS   : pure functions; no I/O; no float math; null != zero; native values untouched; no global state
IMPLEMENTATION STEPS  : linear primitive; inverse primitive with recorded price block; refusal plumbing (None + flag)
POSITIVE TESTS        : known linear fixture matches manual computation exactly (Decimal); inverse fixture with PROVIDER_INDEX price
NEGATIVE TESTS        : missing terms → None + UNIT_CONVERSION_BLOCKED; unknown payoff → refusal; price type outside the five → refusal
ADVERSARIAL TESTS     : QUANTO input refused (no formula); 1-contract=1-base trap fixture; Decimal exponent-form inputs; zero/negative bounds
EVIDENCE ARTIFACTS    : bloc_05_unit_validation.json (conversion portion)
REGRESSION REQUIREMENTS: full normalization suite green
ACCEPTANCE PREDICATES : G5 sub-clauses (terms drive formulas; PIT price required; NULL+reason never guessed; lineage present)
STOP CONDITIONS       : any formula not derivable from §7/§8 → REQUIRES_OPERATOR_DECISION
EXPECTED COMMIT BOUNDARY : stage B+C review unit
NEXT DEPENDENCY       : Stage C

STAGE C — FAILURE AND BOUNDARY ENFORCEMENT
GOVERNING AUTHORITY   : G9, F3, bloc_05/01 §9 blocker set, C1/C2 boundary laws
PRECONDITIONS         : Stage B
ALLOWED FILES         : same module + tests
PROHIBITED FILES      : as Stage A
INPUT CONTRACTS       : boundary tuples: event_time/knowledge_cutoff vs instance terms interval; unverified terms states
OUTPUT CONTRACTS      : typed refusals only (None + flag / status propagation); zero mutations
REQUIRED INVARIANTS   : cutoff at known_to boundary blocked (half-open, mirrors I03H Option 1); event before valid_from blocked; refusal leaves input objects untouched
IMPLEMENTATION STEPS  : boundary gates around snapshot/primitives; refusal-matrix tests
POSITIVE TESTS        : cutoff == known_from resolves; cutoff == known_to - 1µs resolves (parity with KB matrix)
NEGATIVE TESTS        : cutoff == known_to refuses; event < valid_from refuses; terms unverified refuses
ADVERSARIAL TESTS     : knowledge-ineligible instance with valid-time-eligible window; ambiguous identity with perfect terms; stale contract_terms_version presented as current
EVIDENCE ARTIFACTS    : terms-boundary rows into proposed BLOC_05_I04_TERMS_MATRIX.json
REGRESSION REQUIREMENTS: KB/lifecycle/alias matrices untouched
ACCEPTANCE PREDICATES : every refusal has typed reason; no fabricated identifiers/refs (C7/C8 parity)
STOP CONDITIONS       : any case demanding a new status enum member
EXPECTED COMMIT BOUNDARY : with Stage B
NEXT DEPENDENCY       : Stage D

STAGE D — INTEGRATION WITH ACCEPTED I01–I03 OUTPUTS
GOVERNING AUTHORITY   : §5 status map (bloc_05/01 §9), decision D2
PRECONDITIONS         : Stage C; D2 answered
ALLOWED FILES         : I04 module tests + (ONLY if D2 grants) identity/resolver.py one-way construction of TERMS_UNVERIFIED
PROHIBITED FILES      : registry.py, aliases.py, lifecycle.py, models.py, I01 enums (all frozen)
INPUT CONTRACTS       : IdentityResolution fields per §5 of this document
OUTPUT CONTRACTS      : consumption map implemented as gating, not reinterpretation
REQUIRED INVARIANTS   : blocker statuses produce zero derived values; RESOLVED_WITH_WARNING converts; alias-tier resolutions use instance terms (alias never supplies terms)
IMPLEMENTATION STEPS  : integration tests calling resolve_instrument → snapshot → primitives end-to-end (network-free)
POSITIVE TESTS        : RESOLVED_EXACT → terms → linear conversion chain
NEGATIVE TESTS        : AMBIGUOUS / PIT_KNOWLEDGE_BLOCKED / UNKNOWN_SYMBOL chains produce no derived fields
ADVERSARIAL TESTS     : wrong-venue provider ID must not yield terms (C4 parity); future-known terms instance at early cutoff
EVIDENCE ARTIFACTS    : integration rows in proposed matrices
REGRESSION REQUIREMENTS : I03 focused 84 green; identity suite 0 new errors (mypy)
ACCEPTANCE PREDICATES : status map §5 fully covered; no resolver behavior change unless D2 explicitly granted it
STOP CONDITIONS       : D2 denial ⇒ TERMS_UNVERIFIED stays reserved; D2 ambiguity ⇒ stop, report
EXPECTED COMMIT BOUNDARY : stage D review unit
NEXT DEPENDENCY       : Stage E

STAGE E — EVIDENCE GENERATION
GOVERNING AUTHORITY   : bloc_05/06 §17; I03H/I03I custody lessons; directive §09.3
PRECONDITIONS         : Stage D
ALLOWED FILES         : research/crypto_foundry/sensor_fabric/scripts/b5_i04_*.py (NEW tracked producer; proposed name), evidence/bloc_05/BLOC_05_I04_*.json (proposed names)
PROHIBITED FILES      : copying I03 scripts wholesale; untracked generator sources; .bu_tmp dependencies
INPUT CONTRACTS       : deterministic fixtures only (no clock, no network, pinned dates)
OUTPUT CONTRACTS      : JSON matrices, sort_keys, LF, stable provenance strings naming tracked paths
REQUIRED INVARIANTS   : byte-identical double run; provenance executable from tracked source alone
IMPLEMENTATION STEPS  : write producer beside its tests; regenerate twice; hash-compare
POSITIVE TESTS        : 6-style sha256 double-run equality (as I03I)
NEGATIVE TESTS        : producer refuses non-passing fixtures (adv_wrap-style guard)
ADVERSARIAL TESTS     : hand-edited row detection (matrix carries measured observed values only)
EVIDENCE ARTIFACTS    : §9.1 table
REGRESSION REQUIREMENTS: evidence-structure validator green
ACCEPTANCE PREDICATES : every row reconstructible (case_id, clause, input, probe, expected, observed, disposition, ref)
STOP CONDITIONS       : any hand-written expectation labeled as measurement
EXPECTED COMMIT BOUNDARY : with stage F
NEXT DEPENDENCY       : Stage F

STAGE F — HARDENING
GOVERNING AUTHORITY   : §8 test classes (this document), G8
PRECONDITIONS         : Stage E
ALLOWED FILES         : adversarial test files, producer
PROHIBITED FILES      : production behavior changes to make tests pass
INPUT CONTRACTS       : stages B–E outputs
OUTPUT CONTRACTS      : red-team style probe records (I03 convention)
REQUIRED INVARIANTS   : determinism, idempotence of pure functions (f(b) repeated = same), no mutation of inputs
IMPLEMENTATION STEPS  : class coverage from §8; property tests for impossible combinations (bloc_05/06 §3 list)
POSITIVE TESTS        : repeated invocation byte/Decimal-identical
NEGATIVE TESTS        : impossible combos fail validation (INVERSE + missing terms; NORMALIZED + missing lineage)
ADVERSARIAL TESTS     : full §8 applicable classes
EVIDENCE ARTIFACTS    : adversarial matrix rows
REGRESSION REQUIREMENTS: full project suite
ACCEPTANCE PREDICATES : 0 gaps, 0 errors in probe records
STOP CONDITIONS       : a probe that can only pass by weakening an I01–I03 test
EXPECTED COMMIT BOUNDARY : with Stage E
NEXT DEPENDENCY       : Stage G

STAGE G — ACCEPTANCE
GOVERNING AUTHORITY   : bloc_05/06 §1/§20; directive §08.2 exact-set
PRECONDITIONS         : Stages A–F
ALLOWED FILES         : evidence summary, ledger append (by future directive)
PROHIBITED FILES      : gate promotions, branch changes
INPUT CONTRACTS       : all stage evidence
OUTPUT CONTRACTS      : exact-set equality report; PENDING_OPERATOR_REVIEW disposition
REQUIRED INVARIANTS   : REQUIRED ⊆ IMPLEMENTED and UNAUTHORIZED_EXTRA = ∅
IMPLEMENTATION STEPS  : coverage table fill; full suite; custody diff; report
POSITIVE TESTS        : every required obligation maps to surface + verification + artifact
NEGATIVE TESTS        : unauthorized extra surfaces detected (scope audit style)
ADVERSARIAL TESTS     : scope-audit probe for forbidden I05/I08 vocabulary leakage
EVIDENCE ARTIFACTS    : bloc_05_acceptance_summary.md portion + scope audit
REGRESSION REQUIREMENTS : full project suite; historical digests unchanged
ACCEPTANCE PREDICATES : all gates applicable to I04 remain owned by program (no self-promotion)
STOP CONDITIONS       : any uncovered required contract
EXPECTED COMMIT BOUNDARY : I04 final commit (future directive)
NEXT DEPENDENCY       : operator review
```

### 7.3 Name classification

- **Frozen required names:** `ContractTermsSnapshot`, `UNIT_CONVERSION_BLOCKED`,
  `IdentityResolutionStatus.*`, `PayoffType.*`, the five reference-price
  types, evidence artifact names from bloc_05/06 §17.
- **Existing implementation names:** `ContractInstance`, `resolve_instrument`,
  `IdentityResolution`, `IdentityRegistrySnapshot`, `_pit_valid`, `_known_by`.
- **Proposed names requiring operator approval:** module path
  (`normalization/identity/terms.py` vs `normalization/common/conversion.py`-adjacent
  placement — note §21 already assigns `common/conversion.py` to the I08-era
  required-modules list, so terms/primitives placement must be decided to
  avoid collision), function names in §4 (`linear_base_exposure`,
  `quote_notional`, `inverse_base_from_quote` are illustrative), evidence
  names `BLOC_05_I04_TERMS_MATRIX.json` / `BLOC_05_I04_CONVERSION_MATRIX.json`,
  producer name `b5_i04_mats.py`.

## 8. Adversarial acceptance design (§08 — plan only, not executed)

### 8.1 Test-class applicability

```text
class                                        | applies? | justification / frozen clause
1  valid inputs + required successes         | YES      | G5 positive paths; §7/§8 formulas
2  missing mandatory fields                  | YES      | F3 unverified/missing terms must refuse
3  malformed field types                     | YES      | N0 laws (bloc_05/06 §3)
4  cross-record referential inconsistency    | YES      | terms snapshot must match registry instance ids
5  provider and venue mismatch               | YES      | C4 parity — wrong venue must not yield terms
6  identity ambiguity                        | YES      | §9 blocker set; AMBIGUOUS blocks conversion
7  event-time boundary violations            | YES      | C1 terms interval half-open
8  knowledge-time boundary violations        | YES      | C2 Option 1 parity; G1 no backward leakage
9  stale or superseded evidence              | YES      | §7 drivers: terms-version succession, no silent overwrite
10 unit/economic-contract inconsistency      | YES      | G5 + §22 inv.4 (inverse needs terms+price)
11 unexpected state transitions              | PARTIAL  | primitives are pure/stateless; succession covered under 9 — no transition machinery exists to test (justified exclusion of a state machine)
12 repeated invocation and determinism       | YES      | G8
13 idempotence and rollback                  | EXCLUDED | I04 owns no mutable/persistent state (no registry writes, no T1 writes) — nothing to roll back; justified by F28/§15 ownership elsewhere
14 crash and retry                           | EXCLUDED | no persistent operations owned by I04; evidence producer is deterministic and rerunnable (Stage E) instead
15 unauthorized fallback / inferred values   | YES      | G9, §22 inv.2/5/6, no price-type substitution
16 historical evidence corruption / provenance loss | YES | G6-style refs: conversion_inputs must survive; source_evidence_refs never synthesized
```

Row schema for every applicable class: `test_id, contract_clause, fixture,
operation, expected_output, forbidden_output, side_effect_invariant,
evidence_artifact, acceptance_result` (I03 red-team convention). Example rows:

```text
T-04-001 | bloc_05/03 §6        | fully-specified LINEAR instance | linear_base_exposure(3 contracts) | exact Decimal product, conversion_inputs=[multiplier_ref] | any float artifact; any value when terms incomplete | inputs unmoved | proposed I04 terms matrix | (future)
T-04-008 | bloc_05/07 F5/G5     | INVERSE instance, price absent  | inverse conversion               | None + UNIT_CONVERSION_BLOCKED                            | non-NULL value; default price                          | inputs unmoved | conversion matrix | (future)
T-04-014 | bloc_05/01 §9        | AMBIGUOUS resolution            | terms attempt                    | refusal, zero derived fields                             | snapshot produced                                       | resolver untouched | terms matrix | (future)
T-04-021 | C2 parity (I03H)     | cutoff == known_to              | snapshot attempt                 | PIT_KNOWLEDGE_BLOCKED propagation                        | snapshot                                               | inputs unmoved | terms matrix | (future)
```

No test is created merely to inflate counts; classes 13/14 exclusions are
ownership-based, not convenience-based.

### 8.2 Exact-set inventory (design-time)

```text
REQUIRED_CONTRACT_SET (frozen obligations, clause-cited):
  R1 terms source = PIT-valid ContractInstance (03 §6)          → planned: A/B, T-04-001.., evidence terms matrix
  R2 linear formula parameterized (03 §7)                        → B, positive fixtures, unit validation
  R3 inverse formula + recorded price block (03 §8)              → B/C, T-04-008, unit validation
  R4 blocked conversion = NULL + flag (03 §8, G5)                → B/C, negative tests
  R5 no silent price-type substitution (03 §8)                   → C, adversarial
  R6 unverified terms cannot be verified T1 (F3, §9)             → C/D, status-map tests
  R7 no future terms leakage (G1, C2)                            → C, boundary tests
  R8 native values preserved (G3, §22 inv.1)                     → B, side-effect invariants
  R9 stablecoin untouched (F7, §22 inv.3)                        → B scope audit (absence proof)
  R10 lineage + methodology on derived values (G5, §17 lineage)  → B/E, evidence columns
  R11 determinism (G8)                                           → E/F, double-run hashes
  R12 fail-closed everywhere (G9)                                → C/D/F, refusal matrix
  R13 no identity mutation (§15/F28)                             → D/G, scope audit + custody diff
  R14 N0 schema laws (06 §3)                                     → A, N0 tests
  R15 terms-version succession without overwrite (01 §7)         → A/C, succession tests

IMPLEMENTATION_COVERAGE_SET : planned mapping above — actual coverage EMPTY until a future I04 implementation
EVIDENCE_COVERAGE_SET       : §9.1 mapping — actual artifacts ABSENT (correctly; nothing fabricated now)
UNCOVERED_CONTRACT_SET      : all of R1–R15 (pending implementation; no gap exists today because I04 has not started)
UNAUTHORIZED_EXTRA_SET      : ∅ by construction — no I04 surfaces exist in src/ (scope-audit style proof: 'class ContractTerm', 'def query_t1', conversion symbols absent per BLOC_05_I03_SCOPE_AUDIT.json)
```

A future I04 PASS requires UNCOVERED = ∅ and UNAUTHORIZED_EXTRA = ∅.

### 8.3 Negative-proof types

```text
proof type A — no code path exists:        terms/primitive symbols absent from src/ (scope audit mechanical scan); applies TODAY
proof type B — code path exists but guarded: refusal branches in stages B/C (future)
proof type C — exercised and refused:      negative/adversarial tests (future)
proof type D — no test establishes claim:  explicitly listed per R-row during Stage G; none may remain at acceptance
```

Static grep is used only for class-A claims (absence), never for guarded-
behavior claims (B) or exercised refusals (C).

## 9. Evidence and reproducibility plan (§09)

### 9.1 Artifact inventory

```text
artifact_name (frozen unless marked PROPOSED)
  | type | governing_clause | producer | source/fixture | procedure | expected_fields | pass | failure | reproduction | custody
bloc_05_identity_validation.json (frozen name; terms portion PROPOSED scope)
  | json | 06 §17 + G1 | PROPOSED tracked b5_i04 script | deterministic identity/terms fixtures | run producer twice | blocker-status rows + terms eligibility rows | every row PASS | any FAIL or hand-edited row | PYTHONIOENCODING=utf-8 python research/.../scripts/b5_i04_*.py (from quant-lab) | tracked source; no scratch deps
bloc_05_unit_validation.json (frozen name; conversion portion)
  | json | 06 §17 + G5 | same producer | linear/inverse fixtures with pinned Decimals/prices | same | conversion rows with expected values + blocked rows | exact Decimal equality + NULL+flag rows | guessed value; float artifact; missing lineage | same | same
BLOC_05_I04_TERMS_MATRIX.json (PROPOSED name, I03 convention)
  | json | 01 §9/§2.5 | same producer | boundary/status-map fixtures | same | case_id, acceptance_clause, input_condition, probe, expected_status, observed_status, disposition, evidence_ref | observed==expected | mismatch; input_condition not matching executed values (I03I lesson) | same | GEN_REF names tracked path
BLOC_05_I04_CONVERSION_MATRIX.json (PROPOSED)
  | json | 03 §6-§8, §22 | same producer | conversion fixtures | same | case rows + methodology/lineage columns | same law | same | same | same
BLOC_05_I04_SCOPE_AUDIT.json (PROPOSED, I03 convention)
  | json | 06 §20, §15 | same producer | source scan | mechanical | forbidden-vocab absence, I05/I08 leakage absence, file inventory | all absent | leakage found | same | same
bloc_05_acceptance_summary.md (frozen name, Stage G)
  | md | 06 §17 | future directive | stage evidence | manual+measured | exact-set table | UNCOVERED=∅ & EXTRA=∅ | any uncovered | n/a | append-only
```

### 9.2 Evidence matrix row law

Every measured row reconstructs `case_id, acceptance_clause,
input_condition, probe_or_operation, expected_result, observed_result,
disposition, evidence_reference`; extra columns (methodology_version,
conversion_inputs) justified by G5/§17. Hand-written expectations are never
labeled as executed measurements (I03I correction law carried forward).

### 9.3 Tracked generator requirement (I03H/I03I lesson applied)

Canonical generator ownership decided **before** implementation: a NEW
tracked producer under `research/crypto_foundry/sensor_fabric/scripts/`
(I03 convention), deterministic fixtures, pinned date literals (never
`date.today()`), `sort_keys` + LF output, provenance strings naming the
tracked path, double-run sha256 equality recorded, sidecar outputs kept out
of immutable evidence (volatile ≠ immutable), executable with zero `.bu_tmp`
dependency. I03 scripts are **not** copied; code is reused only if interface
ownership justifies it (they are evidence-writers for I03 rows only).

### 9.4 Historical noninterference

```text
PROTECTED source paths     : src/crypto_sensor_fabric/normalization/{identity,common,time,sensors,...}/** (existing files), config/**, all tests/ existing files
PROTECTED evidence paths   : evidence/bloc_04/**, evidence/bloc_05/BLOC_05_I01*, _I02*, _I03* (all sealed), I01/I02 ratifications, ledger §1–§163 (append-only)
PROTECTED branches         : agent/crypto-quant-foundry, agent/crypto-sensor-fabric-plan, origin/main
PERMITTED new artifacts    : new terms/conversion module files, new test files, new BLOC_05_I04_* evidence, ledger §164+ (future), scripts/b5_i04_*.py
PERMITTED append-only docs : ledger; future ratification file for I04
KNOWN test-generated dirt  : full suite rewrites bloc_04 JSON line endings + I15 files_scanned counts (L4); restoration = git checkout -- evidence/bloc_04 after runs, then re-verify I11R2 digests (procedure executed at I03H/I03I)
REGEN RULE                : never regenerate older evidence for formatting; protected digests (I11R2 pins) must match before/after
```

## 10. Verification performed for this readiness (§10.2/§10.3)

Ran (read-only): plan-branch blob identity check for all 7 bloc_05 docs;
`git` ancestry/merge counts; committed-matrix PASS recounts (KB 14/14,
adversarial 25/25, alias 6/6, leakage 4/4, lifecycle 17/17, match-order
10/10); `InstrumentAlias.model_fields` = 11; import probes of
`resolve_instrument` signature; scope-audit JSON pins (G4 reserved,
I04-vocabulary absent, forbidden imports absent); external CI = 0 check-runs
(`NONE_OBSERVED`). Existing dependency tests: the I03I-measured suites on
this byte-identical tree (84/497/3895+14) remain the acceptance substrate;
ledger-reading and I11R2 digest tests rerun at I03J after governance edits.
**No hypothetical I04 test was run against nonexistent code.**

Environmental debt classification (observed evidence):

```text
Windows manifest-concurrency teardown race | INHERITED DEBT (intermittent; disclosed L5; not claimed repaired)
bloc_04 generated-file drift (line endings + I15 counts) | NONBLOCKING DISCLOSURE (L4; restoration procedure proven)
mypy 10 pre-existing errors (providers/probes) | INHERITED DEBT (0 identity errors)
long-running suites (~17 min full) | NONBLOCKING
temporary evidence-generator history (.bu_tmp era) | RESOLVED by I03I tracked custody (re-verified here)
```

No new failure was labeled inherited.

## 11. Unresolved I04 ambiguities — `REQUIRES_OPERATOR_DECISION`

**D1 — `ContractTermsSnapshot` schema source.**
Conflicting clauses: bloc_05/07 §2 freezes the object **name** among core
identity objects; no plan document gives its field list; bloc_05/01 §2.5
already stores terms fields on `ContractInstance` (I02-frozen, 23 fields);
bloc_05/03 §6 speaks of "the terms registry supplies …" without naming a
separate registry. Impacted interfaces: the snapshot model, N0 tests, every
evidence row shape. Interpretations: (a) snapshot = PIT projection of the
§2.5 terms subset of the resolved instance; (b) snapshot = a separately
versioned record owning additional fields not in the frozen plan. Behavioral
consequences: (b) would introduce schema the plan never froze. Smallest
decision: **confirm (a), or supply the frozen field list for (b).**

**D2 — `TERMS_UNVERIFIED` construction ownership.**
Conflicting clauses: bloc_05/01 §9 lists the status in the resolver's
blocker set; I03H G4 recorded "terms verification is B5-I04+ and no I03 path
constructs this status"; source docstrings say "B5-I04 owns terms logic";
but no clause authorizes I04 to modify `identity/resolver.py` (I03-owned),
and directive §06.5 makes unmentioned actions prohibited-until-decided.
Impacted interfaces: resolver status production, Stage D scope, evidence
status rows. Interpretations: (a) I04 may add a guarded
TERMS_UNVERIFIED construction path to the resolver; (b) terms verification
stays in I04's own layer and the status remains reserved until a later
directive. Smallest decision: **grant (a) with exact guard conditions, or
confirm (b).**

Module-path collision with `common/conversion.py` (I08 required-modules
list) is noted as a Stage-A naming approval item, not a semantic decision.

## 12. Readiness verdict (§13.I)

**`REQUIRES_OPERATOR_DECISION`** — exactly two decisions (D1, D2).

Not `BLOCKED_BY_UNEARNED_DEPENDENCY`: all upstream dependencies (I01, I02,
I03) are OPERATOR_ACCEPTED with evidence, and no other required state is
missing. Not `READY_FOR_OPERATOR_AUTHORIZATION` because D1/D2 are semantic
questions the frozen plan does not answer and implementation convenience may
not resolve them (directive §11.4).

**Readiness is not permission.** `I04_IMPLEMENTATION_AUTHORIZATION = FALSE`;
`next_checkpoint_authorized = FALSE` remain in force until a new operator
directive.
