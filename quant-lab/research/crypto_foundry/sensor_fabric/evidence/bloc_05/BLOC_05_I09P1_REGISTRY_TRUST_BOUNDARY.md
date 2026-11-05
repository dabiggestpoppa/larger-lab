# BLOC 05 / SENSOR-B5-I09P1 — REGISTRY TRUST BOUNDARY

**Repository:** `dabiggestpoppa/larger-lab`
**Branch:** `agent/crypto-sensor-fabric-build`
**Required and actual starting HEAD:** `05eb98aae110946713562535ac772b6af057532e`
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`
**Entering state:** `B5-I09a = OPERATOR_ACCEPTED`, `B5-I09b = DEFERRED`, `B5-I10 = OPERATOR_ACCEPTED` (bounded), `B5-I11 = IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD`, `B5-I12+ = UNAUTHORIZED`, eight gates `NOT_YET_EARNED`, research `FROZEN`.
**Nature:** planning and security-verification checkpoint (`SENSOR-B5-I09P1`, deliberately **not** the already-used identifier `SENSOR-B5-I09R1`). No production authority is changed, no provider is certified, no I09/I10/I11 ratified behaviour is amended. Companion record: `BLOC_05_I09P1_ADVERSARIAL_TEST_CONTRACT.md`.

---

## 01 — Custody

| Item | Observed |
|---|---|
| local HEAD | `05eb98aae110946713562535ac772b6af057532e` |
| remote branch tip | `05eb98aae110946713562535ac772b6af057532e` |
| tracked tree | clean; only the three preserved scratch paths untracked |
| frozen plan | `4bb677f9e` resolves; no plan blob is modified by this checkpoint |
| I09 ratification | `BLOC_05_I09_OPERATOR_RATIFICATION.md` reachable (`B5-I09a` accepted, `B5-I09b` deferred) |
| I10 acceptance | `BLOC_05_I10_OPERATOR_RATIFICATION.md` reachable (bounded, seven conditions) |
| I11 evidence chain | `BLOC_05_I11_IMPLEMENTATION_EVIDENCE.md`, `…I11F1_REPAIR_EVIDENCE.md`, `…I11R1_INDEPENDENT_AUDIT.md`, `…I11R1_PIT_NARRATIVE_CORRECTION.md`, `…I11R2_INDEPENDENT_AUDIT.md` all reachable |
| this checkpoint's durable output | this document, the adversarial contract, ledger §189 |

No reset, rebase, amend or force-push was performed, and none is required.

---

## 02 — Present trust-boundary map

Every seam where caller-controlled material becomes semantic authority, read at source:

| # | seam | exact path | what it trusts |
|---|---|---|---|
| S1 | record construction | `normalization/common/semantic_registry.py::ProviderSemanticMapping` | any non-pending `evidence_reference` **string**; any `methodology_id` **string**; any `transformation`/`native_definition` text; provider token (eight-venue check only) |
| S2 | set construction | `…::ProviderSemanticRegistry` | a caller-supplied tuple of rows plus a free-form `schema_version` **string** |
| S3 | text parsing | `…::parse_provider_semantic_registry_yaml` | arbitrary YAML text; **no path, no digest, no provenance** |
| S4 | ladder | `…::admits_critical_t1_use` / `is_first_party_grade` | the row's **declared** confidence |
| S5 | liquidation admission | `normalization/sensors/liquidation.py::_admit_field` (≈L886) via `_admissions` (≈L950) and `normalize_liquidation(registry: ProviderSemanticRegistry \| None = None)` (≈L1003) | the registry object handed in |
| S6 | liquidation record law | `…T1LiquidationRecord` side-admission law | the **admission object's** own fields |
| S7 | trade admission | `normalization/sensors/side_maps.py::resolve_side_mapping` (≈L298), `require_side_mapping` (≈L314), `apply_side_map` | the registry object handed in |
| S8 | trade consumer | `normalization/sensors/trade.py::normalize_trade(…, registry: object, …)` (≈L407) | **`object`** — duck-typed, so any object exposing `resolve` is authority |
| S9 | version token | `…::version_token()` → `RegistryVersion` | a declared string, never a content digest |

Measured consequence: the only type distinguishes *registry-shaped* from *not registry-shaped*. Nothing distinguishes **approved upstream** from **minted two lines ago**.

### 02.1 Where the registry objects actually come from (measured)

`ProviderSemanticRegistry(` is constructed in exactly five places in the tracked tree: its own class definition, one documentation example, and **three test modules** (`test_b5_i11_liquidation_semantics.py`, `test_b5_i11r1_independent_audit.py`, `test_b5_i11f1_semantic_admission.py`). No production ingestion path constructs or loads one.

Two facts follow, and both matter for adjudication rather than for comfort:

1. the exposure is **latent, not live** — no accepted production path today feeds a real registry into a normalizer;
2. the **first** ingestion path will inherit the hole unless the boundary exists before it is written.

---

## 03 — Threat model

Thirteen threats, each mapped to a seam and to the enforcement this design proposes:

| # | threat | seam | proposed enforcement |
|---|---|---|---|
| T1 | arbitrary client-provided registry | S1/S2/S5/S7 | authority object only; plain registry refused at the consumer |
| T2 | synthetic evidence strings | S1 | evidence reference must resolve in the approved evidence index, bound to the row's provider |
| T3 | fabricated confidence rungs | S1/S4 | confidence is a property of the **approved bytes**; any edit is a digest mismatch |
| T4 | wrong-venue evidence | S1 | per-provider evidence binding |
| T5 | wrong field or sensor family | S1 | `(provider, field, family)` key plus declared-native-field list in the manifest |
| T6 | unregistered methodology ids | S1 | loader resolves every cited id against the I09 methodology registry |
| T7 | unsupported transformations | S1 | transformation must equal the manifest's approved transformation for that field |
| T8 | contradictory blocking assumptions | S1 | assumptions carry a resolution state; unresolved ⇒ admission refused |
| T9 | stale provider semantics | manifest | `last_verified_date` + manifest validity window; expiry is a typed refusal |
| T10 | mutated registry after approval | loader | byte digest compared against the manifest |
| T11 | replay of an old, previously valid registry | loader | approval id + revocation list; revoked ⇒ typed refusal |
| T12 | validly shaped but unauthorized admission objects | S6/S5 | admissions carry the authority digest; a context-free admission is unrepresentable in the proposed record law |
| T13 | trusted code accidentally passing untrusted configuration | S8 | `registry: object` is replaced by a typed authority parameter; a bare registry no longer type-checks |

Explicit non-claim: a digest establishes **approved-byte integrity**. It does not establish that a venue's documentation says what the row claims. That is the separate, external provider-evidence problem (§09, §11).

---

## 04 — Trust-root inventory

Classification is measured, not inferred from naming.

| mechanism | state | evidence |
|---|---|---|
| approved provider-evidence inventory | **ABSENT** | no `provider_semantics/` directory exists; the only semantic config is the Bloc 1 `semantic_equivalence.yaml` with six `BLOC2_PROBE_PENDING` planning rows |
| first-party source-document custody | **PRESENT_NOT_ENFORCED** | `storage/` holds provider bytes with `blob_sha256` = SHA-256 of exact source bytes and full acquisition lineage, but **no semantic row references a blob** |
| approved registry artifacts | **ABSENT** | no artifact, no manifest, no approval record anywhere in the tree |
| pinned configuration digest | **ABSENT** for semantics; **PRESENT_AND_ENFORCED** elsewhere | `storage/export.py` pins `manifest_sha256`/`pack_root_sha256` with a declared **non-circular** digest domain (`_DIGEST_NEUTRAL`), and `contracts/base.py::canonical_hash` exists — the *discipline* exists, it is simply not applied to semantic authority |
| trusted artifact loading | **ABSENT** | both registries are text-in only ("no path is read here, ever"); committed config is read by callers, not by a loader with provenance |
| source and provider bindings | **ABSENT** | nothing connects an `evidence_reference` string to a provider, a document or a blob |
| methodology registration | **PRESENT_AND_ENFORCED (lookup) / ABSENT (admission)** | `NormalizationMethodologyRegistry.require` refuses unknown ids, but neither `_admit_field` nor `apply_side_map` ever resolves the cited `methodology_id` |
| registry version/revision | **PRESENT_NOT_ENFORCED** | `schema_version` is a free string; `version_token()` returns it; no consumer compares it to anything |
| approval and revocation | **ABSENT** | no approval id, no revocation list, no expiry |
| consumer-side admission enforcement | **PRESENT_AND_ENFORCED (per field) / ABSENT (provenance)** | I11R2 measured both halves |
| Bloc 1 provider capability status | **PRESENT_NOT_ENFORCED** | `provider_registry.yaml` carries `verified: false`/`status` claims that no normalization path reads |

**Finding (explicit, as directive §03 requires): no authentic trust root for semantic authority exists in this repository.** The design below must therefore be able to refuse everything, and must not bootstrap trust by letting the same actor author both the artifact and its proof.

---

## 05 — Proposed authoritative architecture

One registry (I09's), one evidence repository (the storage layer's), one approval root, one loader, typed consumers.

### A — Evidence repository

Reuse `storage/` rather than invent a second store: each semantic row's evidence reference resolves (through an index) to one or more `blob_sha256` values already held under acquisition custody, plus source identity (venue, document title, URL or archive id, retrieval time, applicable version). This is what makes "authenticated evidence" testable: the reference must name a blob that exists.

### B — Approval boundary

A committed manifest, `config/crypto_sensor_fabric/provider_semantics/approval_manifest.json`, authored by an operator-authorized checkpoint (**not** by the loader, **not** by the ingestion process), containing per artifact:

```
artifact_id, sha256, approval_id, approved_at, valid_until?, revoked[]
methodologies[]                 # ids the artifact may cite
evidence_by_provider{}          # provider -> evidence refs bound to it
declared_native_fields{}        # provider -> native field names that may appear
approved_transformations{}      # native field -> the exact approved transformation
blocking_assumption_resolutions{}# assumption -> true only when resolved
```

Its own integrity is established by being committed under review (and, when it changes, by a governance digest line in the ledger) — **not** by a digest it carries about itself.

### C — Trusted loader

`normalization/common/authority.py`:
`load_semantic_authority(manifest_bytes, artifact_id, artifact_bytes) -> SemanticAuthority`

Order of checks, each a distinct typed refusal: manifest entry exists → not revoked → within validity → **byte digest equals the manifest's** → parse with the existing parser → every cited methodology registered → every evidence ref bound to that row's provider → native field declared → transformation approved → blocking assumptions resolved. Only then mint `SemanticAuthority` (frozen model with a loader-private constructor sentinel).

The expected digest always comes **from the manifest**. A digest travelling beside the artifact it hashes is ignored — that is the exact prohibition in directive §04.

### D — Consumer authority

`normalize_liquidation` and `normalize_trade` accept `SemanticAuthority` only. A bare `ProviderSemanticRegistry` is demoted to a **test/diagnostic value type**: it remains a ratified I09 object (nothing is deleted or weakened), but it is no longer authority. Consumers must also keep the ability to emit `UNTRUSTED_AUTHORITY` when invoked dynamically without one.

### E — Record provenance

Every admitted canonical field carries `registry_digest`, `approval_id`, `mapping_identity` (provider + field + family + version), `methodology_id`/version, `evidence_reference` and the confidence rung. Today `LiquidationSideAdmission` carries the last three but no digest, so a post-hoc forgery is undetectable.

### 05.1 Constraint compliance

| constraint | how the design satisfies it |
|---|---|
| no hidden network calls during normalization | loader takes bytes; no I/O in the pure layer (unchanged property) |
| no new confidence vocabulary | the five-member ladder is reused verbatim |
| no fabricated real provider mapping | the manifest ships empty; an empty manifest refuses everything |
| no default admission for unknown providers | provider token check plus manifest binding |
| no trust from a nonempty citation string | evidence must resolve to a bound blob |
| no acceptance of a digest supplied with the artifact | expected digest is manifest-owned |
| no implicit first-party claim from `COMMUNITY_DOCUMENTED` | `is_first_party_grade` unchanged; manifest cannot widen it |
| no unapproved expansion of I09/I10 public interfaces | additive module; the registry types keep their meaning |
| no promotion from mutable process-global state | loader is a pure function of bytes given to it; no module-level cache |

---

## 06 — The seven gaps: exact disposition

Measured on the real surface (harness `.bu_tmp/probe_i09p1.py`, untracked scratch). `CURRENT` = reproduced today; `PROPOSED` = the design's simulated refusal.

| GAP_ID | FROZEN_CLAUSE | CURRENT_PRODUCTION_PATH | UNTRUSTED_INPUT | CURRENT_OBSERVED_BEHAVIOR | REQUIRED_BEHAVIOR | AUTHORITY_SOURCE | ENFORCEMENT_OWNER | NEGATIVE_TEST | POSITIVE_TEST | CUSTODY_IMPACT |
|---|---|---|---|---|---|---|---|---|---|---|
| **G1** | 03 §13; 07 F17 | `liquidation.py::_admit_field` → `registry.resolve(...)` | caller-minted registry, invented evidence string, `VERIFIED_FIRST_PARTY` | `position=LONG execution=SELL admissions_all_admitted=True SEMANTICS_UNVERIFIED=False` | admit only from an approved artifact | operator-approved manifest | I09P2 loader | `test_authority_rejects_self_declared_digest` | `test_positive_synthetic_approval_admits` | new module + manifest; no ratified file changes |
| **G2** | 03 §16; 07 F14 | same path (no methodology resolution) | `methodology_id=METHODOLOGY_THAT_DOES_NOT_EXIST_V99` | `admitted=True cited=['METHODOLOGY_THAT_DOES_NOT_EXIST_V99', …]` | refuse or stay provisional | normalization methodology registry | I09P2 loader | `test_authority_rejects_unregistered_methodology` | `test_registered_methodology_admits` | none beyond G1 |
| **G3** | 03 §12; §13 | same path | Kraken evidence string on a `BINANCE_USDM` row | `admitted=True evidence=['KRAKEN_FUTURES_PUBLIC_API_DOCS_v4.pdf']` | evidence must bind to the row's provider | manifest evidence index + blob custody | I09P2 loader | `test_authority_rejects_foreign_evidence` | `test_bound_evidence_admits` | manifest schema only |
| **G4** | 03 §12 | same path | native field no venue publishes | `admitted=True position=LONG` | field must be declared for that provider | manifest declared-field list, derived from evidence | I09P2 loader | `test_authority_rejects_undeclared_native_field` | `test_declared_native_field_admits` | manifest schema only |
| **G5** | 03 §11; §22 inv.7 | same path | `transformation="do_whatever_looks_right"` | `admitted=True transformation_accepted=True` | transformation must equal the approved one | manifest approved transformations | I09P2 loader | `test_authority_rejects_unapproved_transformation` | `test_approved_transformation_admits` | manifest schema only |
| **G6** | 04 §3.1–3.2; 07 F18 | same path | assumption asserting execution side *is* position side | `admitted=True four_way_separation_still_asserted=True` | unresolved assumption blocks admission | assumption resolution state in the manifest | I09P2 loader | `test_authority_blocks_unresolved_assumption` | `test_resolved_assumption_admits` | manifest schema only |
| **G7** | 04 §3.1; 07 F25 | `T1LiquidationRecord` side-admission law | hand-minted admitted decisions, invented evidence ref | `ACCEPTED_WITH_CANONICAL_LONG` | model validity must not imply upstream authorization | loader-issued digest carried on the admission/record | I11 + I09P2 record law | `test_admission_requires_authority_digest` | `test_admitted_record_carries_registry_digest` | record field addition (P2) |

**What is mechanically enforceable vs externally blocked.** G2, G3 (binding), G4, G5, G6, G7 and the digest half of G1 are pure code: they become true the moment the loader and manifest exist, with an empty manifest refusing everything. **Provider-document authenticity is not** — proving that Binance's `isBuyerMaker` means what a row says requires first-party documentation or verified fixtures that this repository does not hold (`B5-I09b` deferred). A SHA-256 check does not close that, and this design does not claim it does.

---

## 07 — I10 and I11 consumer contract

### 07.1 I10 — bounded acceptance is not revoked

| question | measured answer |
|---|---|
| does I10's accepted behaviour remain provisional under approved data? | **yes** — the only live semantic row is `BLOC2_PROBE_PENDING`/`AMBIGUOUS`, so `canonical_admitted` is `False` and `aggressor_side` stays `UNKNOWN` |
| can its API admit fabricated high-confidence rows? | **yes** — `apply_side_map` reads a caller-supplied row, and `normalize_trade(registry: object)` accepts any duck-typed object |
| does any production path consume such rows? | **no** — no production caller constructs a registry (measured, §02.1) |
| is a trusted loader an unfulfilled integration precondition? | **yes**, and it is exactly condition 5 of the I10 ratification (provider certification open) plus F3/F6-style evidence debt |
| do I10's ratification conditions already prohibit unsupported promotion? | **partially** — they prohibit *relying on the probe* and *inferring USD*, but they do not forbid a fabricated row from being admitted by the API |

**Ruling:** `B5-I10 = OPERATOR_ACCEPTED` **stands**. Discovery of an upstream weakness does not retroactively falsify the behaviour that was ratified (per-field provisional carriage, native preservation, PIT economics, lineage). What changes is that the trusted-loader contract becomes a **documented P2 precondition** for any future I10 consumer, and I10's `registry: object` annotation is named as an unfilled obligation rather than a design choice.

### 07.2 I11 — how the boundary repairs A11-14 without touching its economics

A11-14 failed on authority, not on economics. The repair is additive at exactly one seam: `_admit_field` obtains its row from `SemanticAuthority` instead of a bare registry. Everything the I11R2 audit measured as correct is untouched by construction: the per-field refusal order, the all-or-nothing promotion, contradiction quarantine, the PIT conversion, zero-versus-missing, USD refusal, native preservation, and the four-way side separation.

### 07.3 Required consumer behaviour, seven cases

| case | required outcome |
|---|---|
| no trusted authority context | `UNTRUSTED_AUTHORITY`; canonical slots `UNKNOWN`; `SEMANTICS_UNVERIFIED` set |
| structurally valid but unauthorized registry | same as above (identical refusal; no partial credit) |
| approved registry, `AMBIGUOUS` mapping | existing `AMBIGUOUS_MAPPING` refusal, unchanged |
| approved registry, pending evidence | existing `PENDING_EVIDENCE` refusal, unchanged |
| approved registry, valid evidence but inapplicable field | `FIELD_MISMATCH` / `NO_REGISTRY_MAPPING`, unchanged |
| approved registry with full authority | admitted, with digest, approval id, confidence, evidence ref on the record |
| expired / revoked / version-mismatched authority | `AUTHORITY_EXPIRED` / `APPROVAL_REVOKED` / `VERSION_MISMATCH`; nothing promoted |

---

## 08 — Provider-evidence and methodology controls

1. **Evidence onboarding is an operator act, permanently.** A row may cite only a blob already in custody, and the binding to `(provider, field)` is written into the reviewed manifest. No checkpoint may invent a citation.
2. **Methodology identity is resolved, not asserted.** Every cited id must exist in `NormalizationMethodologyRegistry` at the cited version; unknown ids fail the load, so an artifact cannot carry an unregistered methodology into production. This also means `B5_I08_UNITS_V1` (still UNRESOLVED per the I09 ruling) cannot be cited by a semantic row until the operator rules on its cross-family representation.
3. **Staleness is a state, not a comment.** `last_verified_date` plus a manifest validity window produce `AUTHORITY_EXPIRED`, which is a refusal — never an automatic re-admission.
4. **Community evidence stays community.** `is_first_party_grade` is untouched; the manifest cannot raise a rung, only approve or refuse bytes.
5. **Empty by default.** No `provider_semantics/` artifact ships with this checkpoint; the design's default state is "nothing admitted", which is the current honest state of provider evidence.

---

## 09 — Acceptance matrix P09-01 … P09-24

Runtime-enforcement gates name the executable test that must exist; evidence gates name the external prerequisite. Nothing here is satisfied by documentation alone.

| ID | requirement | satisfied by |
|---|---|---|
| P09-01 | frozen authority unchanged | git diff of the seven plan blobs = EMPTY |
| P09-02 | trusted approval source identity | `test_approved_artifact_requires_manifest_entry` (runtime) |
| P09-03 | registry authenticity/provenance | `test_authority_rejects_self_declared_digest` (runtime) |
| P09-04 | evidence-reference binding | `test_authority_rejects_foreign_evidence` (runtime) |
| P09-05 | methodology registration | `test_authority_rejects_unregistered_methodology` (runtime) |
| P09-06 | provider-field correctness | `test_authority_rejects_undeclared_native_field` (runtime) |
| P09-07 | confidence ladder unchanged | existing SEM/I11 tests re-run green (runtime) |
| P09-08 | pending evidence refusal | existing `PENDING_EVIDENCE` assertions (runtime) |
| P09-09 | cross-venue refusal | `test_authority_rejects_foreign_provider_row` (runtime) |
| P09-10 | direct-construction bypass closed | `test_authority_context_not_constructible_by_caller` (runtime) |
| P09-11 | I10 trade consumer | `test_trade_consumer_refuses_plain_registry` (runtime) |
| P09-12 | I11 liquidation consumer | `test_liquidation_consumer_refuses_plain_registry` (runtime) |
| P09-13 | native data preservation | existing native-preservation tests, unchanged (runtime) |
| P09-14 | all-or-nothing semantics | existing I11F1 T22-equivalent (runtime) |
| P09-15 | zero/missing noninterference | existing I11 zero tests (runtime) |
| P09-16 | PIT noninterference | existing inverse/linear tests + T33 (runtime) |
| P09-17 | determinism | `test_same_bytes_same_digest` (runtime) |
| P09-18 | adversarial mutation detection | `test_bit_flip_detected`, `test_confidence_tamper_detected` (runtime) |
| P09-19 | historical custody | sealed I08/I09/I10/I11 evidence diffs EMPTY (runtime assertion) |
| P09-20 | regression | full canonical suite, measured (runtime) |
| P09-21 | governance binding | audit rerun; tracked-Python delta disclosed (runtime) |
| P09-22 | no first-party evidence fabrication | manifest ships empty; every fixture labelled synthetic (review + test) |
| P09-23 | no program-gate promotion | eight gates `NOT_YET_EARNED` (review) |
| P09-24 | fast-forward Git custody | local == remote, linear (runtime) |

**External prerequisites (cannot be satisfied by any code):** real first-party provider documentation for any non-synthetic row; an operator review act for the first real manifest entry; resolution of `B5_I08_UNITS_V1`.

---

## 10 — Custody blast radius (pre-authorized map only)

| surface | anticipated change |
|---|---|
| `normalization/common/authority.py` | **new** loader, manifest models, typed refusals, `SemanticAuthority` |
| `normalization/common/__init__.py` | export additions only |
| `config/crypto_sensor_fabric/provider_semantics/approval_manifest.json` | **new**, ships with zero artifacts |
| `normalization/sensors/liquidation.py` | `registry` parameter type + one gate in `_admit_field`; no law, order or economics change |
| `normalization/sensors/trade.py` | `registry: object` → typed authority; one gate |
| `normalization/sensors/__init__.py` | export additions only |
| `tests/.../test_b5_i09p2_authority.py` (+ scope audit) | **new** |
| I09 scope audit | frozen module set 7 → N (one disclosed entry) |
| I10/I11 scope audits | one allowlist prefix each (disclosed) |
| governance binding audit | mechanical `python_files_scanned` republish |
| `bloc_05_semantic_validation.json` | extensions merge (new rows appended, no old row rewritten) |
| sealed I08/I09/I10/I11 evidence, both Bloc 1 YAMLs, `conversion.py`, PIT/terms modules | **untouched** |

No whitespace/line-ending normalization anywhere; the ledger stays LF-only.

---

## 11 — Implementable now vs externally blocked

**Implementable and enforceable in P2 without any provider evidence:** the loader, the manifest schema, the empty-manifest default, methodology resolution, evidence-binding enforcement, declared-field and transformation checks, assumption resolution, revocation/expiry, the consumer gates, record digests, and every negative test in §06. This is the fail-closed half, and it is the half that repairs A11-14.

**Externally blocked:** any manifest entry describing a real venue's semantics; `B5-I09b`; the `B5_I08_UNITS_V1` citation; the operator review workflow itself.

---

## 12 — Next directive proposal (NOT EXECUTED)

### `SENSOR-B5-I09P2` — trusted registry loader and provenance enforcement

**P2a (authorized-scope proposal, code):** add `common/authority.py`; add the empty manifest; wire `_admit_field` and `normalize_trade` to `SemanticAuthority`; add `registry_digest`/`approval_id` to admitted decisions; new authority suite + scope audit; disclosed allowlist/governance deltas; full regression; **no real manifest entry, no provider claim**.

**P2b (separately authorized, external):** provider-evidence onboarding and certification workflow — collecting first-party documents into blob custody, reviewing them, authoring manifest entries, ruling on `B5_I08_UNITS_V1`.

**Stop conditions for P2a:** any need to edit a sealed artifact; any need to widen an allowlist beyond one disclosed entry per audit; any test that can only pass with a non-empty manifest; any claim of provider authenticity.

---

## 13 — What this checkpoint does not do

It certifies no provider, writes no registry row, creates no config artifact, changes no production or test byte, promotes no gate, and does not move `B5-I11` off `RATIFICATION_HOLD`. It establishes the design and the falsifiable contract; it does not claim the design is implemented.

## 14 — Status

```
B5-I09a = OPERATOR_ACCEPTED              (unchanged)
B5-I09b = DEFERRED                       (unchanged; still no provider evidence)
B5-I10  = OPERATOR_ACCEPTED (bounded)    (unchanged; loader named as P2 precondition)
B5-I11  = IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD   (unchanged)
B5-I12+ = UNAUTHORIZED
BLOC_05 = INCOMPLETE
gates   = eight NOT_YET_EARNED
RESEARCH = FROZEN
next_checkpoint_authorized = FALSE
```
