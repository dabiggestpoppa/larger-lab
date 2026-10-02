# CSIA RATIFIED-PLAN PHANTOM CITATION SWEEP v0.1

**Document ID:** CSIA-PCT-SWEEP-001
**Version:** 0.1
**Status:** AUDIT — DECISION-READINESS ONLY — NO IMPLEMENTATION AUTHORITY
**Date:** 2026-10-02
**Planning HEAD at authoring:** `ca9bbdfe3dc8581e61b830cb3c857a7e5688c527`
**Implementation branch inspected:** `agent/crypto-systems-intelligence-atlas-book6-build` @ `5f94c3f40cea4441470c57671f51454da7377361`
**Runtime tree inspected:** `quant-lab/src/crypto_systems_intelligence_atlas/` — 62 Python modules
**Requested by:** operator — "audit the other ratified CSIA plans for the same defect this review found — doctrine that cites an accepted artifact that does not exist in the codebase"

---

# 0. Scope and the defect under audit

The Book 6 Comparison/Change Implementation Authorization Review returned HOLD
on four gaps. Every one of the four shares a single shape:

> doctrine asserts that a determination, contract, or derivation is **derived
> from an accepted artifact**, and that accepted artifact **does not exist** in
> the codebase.

This sweep applies that test to the **other** ratified CSIA planning artifacts.

It is an audit. It creates no runtime object, ratifies nothing, decides nothing,
and grants no authority.

**This sweep does not re-open the four existing gaps.** It reports what the same
test finds elsewhere, and it records one new gap.

---

# 1. Verdict

```text
RATIFIED_PLAN_PHANTOM_CITATION_SWEEP = HOLD

NEW_DEFECTS_FOUND                          = 1
  PHANTOM_BENCHMARK (GAP-5)                = CONFIRMED, RATIFIED, PROPAGATED

PRIOR_GAPS_STRENGTHENED                    = 1
  GAP-2 (unit contract)                    = CONFIRMED, ABSENT FROM CODE *AND* DOCTRINE

PRIOR_GAPS_UNCHANGED                       = 3
  GAP-1 (numeric representation)           = no change
  GAP-3 (coverage applicability)           = no change
  GAP-4 (comparability status domain)      = no change

CITATIONS_EXAMINED                         = 106 prose citation phrases
                                           + 69 unresolved symbol citations
CLEAN_ARTEFACTS                             = 7 of 10 ratified plans
AFFECTED_ARTEFACTS                          = 3 of 10 ratified plans

PRIOR_REVIEW_VERDICT_CORRECTED             = 1
  BENCHMARK_RUNTIME_PATH_SUFFICIENT        = TRUE -> NOT SUPPORTABLE (see §9)
```

**One sentence:** the defect the Book 6 review found is not isolated to the four
gaps it reported — a **fifth instance exists, is already ratified, has been
propagated across five binding artifacts, and escaped detection because the
boundary artifact used it as a premise to declare the question out of scope.**

---

# 2. Method, and two corrections to my own extraction

### 2.1 What was tested

For each ratified planning artifact, every citation of an accepted substrate was
extracted and tested against the runtime tree, in two passes:

1. **Symbol pass** — every code-font identifier (`` `X` ``) resolved against all
   62 runtime modules and the whole test tree.
2. **Prose pass** — every citation-introducing construction
   (*the accepted X*, *the existing X*, *already-ratified X*, *the canonical X*,
   *the upstream X*, *derived from X*) resolved to a named substrate.

The prose pass is the one that matters. **The Book 6 defect was in prose** —
"an accepted unit contract" carries no code font — so a symbol-only sweep finds
almost nothing. That methodological point is recorded here because it is the
reason a symbol-only sweep would have produced a false all-clear.

### 2.2 Correction 1 — the prefix blind spot (a false phantom I had to retract)

The first symbol pass matched base names exactly and reported
`CapitalPrincipalLineage` (Book 5 v0.3 plan line 62, "Many-to-many
`CapitalPrincipalLineage` graph ... all stand") as a **phantom**.

It is not. The accepted substrate is `CapitalPrincipalLineageGraph` at
`book5_lineage.py:117`, with `PrincipalContribution` edges at
`book5_lineage.py:47` and `add_edge()` at `book5_lineage.py:145`. Exact-name
matching missed a `Graph` suffix.

**All symbol results were re-run prefix-aware before any conclusion was drawn.**
This is recorded because a sweep that reported it would have been wrong.

### 2.3 Correction 2 — symbol absence is not the defect

The raw symbol pass yielded 69 unresolved citations. Reading them, the large
majority are **legitimate forward specifications** — artifacts naming objects
they intend to create (`ComparisonRule`, `ChangeObservation`, `ObservedChange`,
`PostActionObservation`, `ResponseLink`, `MARKET_RESPONSE_REF`) — or **explicit
negations** — artifacts naming something forbidden or rejected (`ATTRACTIVE` as
a constitutional violation example, `BUILDING` as a forbidden skip,
`CHANNEL_REPRESENTATIVE` as "**not** adopted").

A symbol that does not exist is only a defect when the surrounding sentence
asserts that it **already does**. The sweep therefore classified on assertion
verb, not on symbol absence. 19 of 69 carried assertion verbs; those were read
individually.

---

# 3. Sweep inventory

Ten ratified planning artifacts were examined. Six ratified plans are named
"PLAN" in their filename and carry the governing decision-log blocks; the
Comparison/Change grammar is included because it is the binding specification
those plans ratify.

| # | Ratified artifact | prose citations | result |
|---|---|---|---|
| 1 | `CSIA_CONSTITUTION_v0.2.md` | 12 | **CLEAN** |
| 2 | `CSIA_BOOK_1_IDENTITY_ONTOLOGY_TEMPORAL_GRAPH_PLAN_v0.3.md` | 10 | **CLEAN** |
| 3 | `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.2.md` | 6 | **CLEAN** |
| 4 | `CSIA_BOOK_3_NATIVE_CHAIN_LEDGER_ATLAS_PLAN_v0.2.md` | 12 | **CLEAN** |
| 5 | `CSIA_BOOK_4_PROTOCOL_INFRASTRUCTURE_DEPENDENCY_ATLAS_PLAN_v0.2.md` | 5 | **CLEAN** |
| 6 | `CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.3.md` | 0 | **CLEAN** |
| 7 | `CSIA_BOOK_6_FUNDAMENTAL_MEASUREMENT_STATE_MODELING_PLAN_v0.2.md` | 1 | **AFFECTED** — origin of GAP-5 |
| 8 | `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md` | 16 | **AFFECTED** — GAP-1/2/3/4, propagates GAP-5 |
| 9 | `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.4.md` | 24 | **AFFECTED** — GAP-1/2/3/4, creates GAP-5 |
| 10 | `CSIA_BOOK_7_NARRATIVE_EVENTS_ECOSYSTEM_EVOLUTION_PLAN_v0.2.md` | 0 | **CLEAN** |

Books 1–5 and 7 are **clean**. Every defect sits in the Book 6 Comparison/Change
amendment family, and one of them (GAP-5) was born in the Book 6 *base* plan
v0.2 and then hardened into a REQUIRED field by the amendment.

Books 1–5 and 7 being clean is a real result, not an absence of looking: §7
records the specific substrate each one cites and where it was verified.

---

# 4. PHANTOM-BENCHMARK (GAP-5) — a ratified, propagated phantom

## 4.1 The finding

The amendment doctrine requires every `ComparisonRule` to carry a
**non-null** `baseline_selection_methodology_ref` citing an **ACCEPTED,
individually operator-ratified** Book 6 benchmark rule drawn from a closed
five-member domain.

**No benchmark rule namespace exists in the codebase. None is ratified. The
field has no defined absent state. No `ComparisonRule` can therefore ever be
validly constructed.**

## 4.2 The citation chain — five artifacts, one phantom

The same non-existent namespace is asserted in five binding artifacts:

**(a) Birth — Book 6 base plan v0.2, lines 121–124**

```text
Own-history comparison cites a `benchmark_methodology_ref` drawn from a
benchmark **namespace** (`PRIOR_COMPARABLE_WINDOW`, `ROLLING_MEAN`,
`ROLLING_MEDIAN`, `HISTORICAL_DISTRIBUTION`, `BASELINE_EPOCH`); none is chosen
by this plan.
```

Here the artifact is **honest**: the namespace is named, and the artifact says
plainly that none of its five members is chosen. At this point the citation
does not claim existence.

**(b) Hardening — Grammar v0.4 §2, lines 246–251**

```text
baseline_selection_methodology_ref: REQUIRED — an ACCEPTED Book 6 benchmark
                                     rule (PRIOR_COMPARABLE_WINDOW |
                                     ROLLING_MEAN | ROLLING_MEDIAN |
                                     HISTORICAL_DISTRIBUTION |
                                     BASELINE_EPOCH) with identity,
                                     version, canonical fingerprint;
                                     individually operator-ratified (D6M-3)
```

The five members the base plan left unchosen are promoted to a **closed,
REQUIRED, individually operator-ratified** domain. Grammar v0.4 line 341 repeats
it as `baseline_selection_methodology_ref  (accepted benchmark rule; cited)`, and
line 583 assigns Book 6 ownership of "baseline selection (accepted benchmark
namespace)".

**(c) Propagation — Amendment plan v0.4, line 35 and line 134**

```text
REUSED:  accepted benchmark-rule namespace; accepted coverage-sufficiency
         rules
```
```text
The accepted benchmark namespace is reused under D6M-3's existing
individual-ratification rule, unmodified
```

Listed under **REUSED** — a category meaning "already accepted, not in scope,
not re-derived".

**(d) Boundary v0.3 §1 contract-class re-audit, line 41 — the concealment**

```text
| candidate | authority-bearing? | v0.4 resolution | new class? |
| baseline-selection methodology | would be | **accepted** benchmark
  namespace, reused unmodified | no |
```

**(e) Ratification record v0.1 §4, lines 152 and 230 — the ratification**

```text
baseline benchmark methodology identity / version / canonical fingerprint
```
```text
the accepted benchmark namespace is reused unmodified
```

Line 152 binds a benchmark methodology fingerprint as one of the **seven
bound derivation-binding elements**. Line 230 records the reuse inside the
ratified record itself.

## 4.3 Runtime evidence

```text
$ grep -rn "Benchmark" src/crypto_systems_intelligence_atlas/*.py
(no output — zero matches across all 62 modules)

$ grep -rni "benchmark" src/crypto_systems_intelligence_atlas/*.py
book6_grammar.py:47:    BENCHMARK = "BENCHMARK"          <- enum MEMBER
book6_states.py:72:     C_THRESHOLD_BENCHMARK = "..."   <- state CLASS
book6_states.py:178:    benchmark_methodology_ref: str | None = None
```

Every occurrence is either an enum **member** (`BENCHMARK` at
`book6_grammar.py:47`, one value inside a measurement-family enum) or a state
**class** (`C_THRESHOLD_BENCHMARK` at `book6_states.py:72`).

There is no `BenchmarkRule`, no `BenchmarkRuleRegistry`, no benchmark namespace
constant, and no benchmark fingerprint function.

The state class is notable: `book6_states.py:212–220` **rejects** a Class C
state that lacks `benchmark_methodology_ref`. The runtime encodes the
*requirement* and the *absence*, never the *namespace*.

Governance counters agree with the runtime and contradict the doctrine:

```text
BENCHMARK_RULES_RATIFIED           = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

## 4.4 Why this is worse than GAP-3, not the same as it

GAP-3 (coverage applicability) has a defined escape. R-2 gives
`coverage_applicability_source_ref` an absent state —
`NO_UPSTREAM_DETERMINATION_EXISTS` — and P10 requires the determination to be
derived rather than authored. So when the derivation is unavailable, coverage
degrades to a named state and the record stays constructible.

**`baseline_selection_methodology_ref` has no such escape.** It is REQUIRED, it
is absent from the §8.1 nullable inventory (§8.1 spans lines 524–543; the field
appears nowhere in it — the artifact mentions the name only at lines 246, 341
and 583), and its only permitted values are five identifiers that cannot be
registered because no registry exists to register them into.

This is the decisive difference:

| | GAP-3 coverage | GAP-5 benchmark |
|---|---|---|
| field | nullable | **REQUIRED** |
| absent state defined | yes — `NO_UPSTREAM_DETERMINATION_EXISTS` | **none** |
| registry exists | yes — `CoverageRuleRegistry` | **no** |
| ratified count | 0 | 0 |
| record constructible | yes, degraded | **no** |

Under a fail-closed implementation the coverage path yields a valid record with
an explicit `UNRESOLVED` verdict. The benchmark path yields **nothing** — every
`ComparisonRule` is rejected at construction, and checks 1–19 never run for any
comparison that has a baseline. Since `PRIOR_COMPARABLE_WINDOW`,
`ROLLING_MEAN`, `ROLLING_MEDIAN`, `HISTORICAL_DISTRIBUTION` and
`BASELINE_EPOCH` are the only sanctioned baseline methods, **the entire
baseline-bearing half of the comparison surface is unreachable.**

## 4.5 Why it was never caught — the boundary artifact concealed it

The boundary v0.3 contract-class re-audit asks, for each candidate, "is this a
new authority-bearing contract class?" For baseline-selection methodology it
answers "**no**" — on the ground that the candidate is *already* the accepted
benchmark namespace.

That inference is circular, and it is load-bearing:

1. The phantom premise is used to answer "no new class?"
2. Answering "no new class?" places baseline selection **out of the amendment's
   authority accounting**.
3. Being out of the authority accounting is exactly why no one then audited
   whether the namespace exists.
4. The review's no-policy-invention test — which inventoried 17 ratified
   domains and found 4 gaps — could not flag it, because the boundary had
   already declared the domain settled **by assumption** before the test ran.

Boundary v0.3 line 129 lists as **OUT**: "any change to MeasurementMethodology
or the accepted benchmark namespace". The exclusion is written as protection of
an existing thing. If the thing does not exist, the exclusion protects nothing
and forecloses the question.

This is the most important structural lesson in the sweep: **a phantom citation
that appears in a boundary artifact does not merely survive review — it
disqualifies itself from review.**

## 4.6 Cross-artifact drift, stated plainly

```text
Book 6 base plan v0.2  L123 : "none is chosen by this plan"     <- HONEST
Grammar v0.4            L246 : "REQUIRED - an ACCEPTED ... rule" <- PHANTOM
Ratification record     L230 : "reused unmodified"               <- RATIFIED PHANTOM
```

The amendment converted an explicitly unchosen five-name list into a required
citation of accepted rules, without any artifact recording a decision to do so.
No operator decision in `CSIA_OPERATOR_DECISION_LOG.md` ratifies a benchmark
rule, a benchmark namespace, or a benchmark value domain. The hardening is
undocumented policy invention — which is precisely the class the review's
`NO_UNRATIFIED_POLICY_NEEDED` criterion exists to catch.

## 4.7 Operator options for GAP-5

These are recorded. **None is chosen here. This sweep decides nothing.**

```text
GAP-5A  Out of scope; comparison surface is baseline-bearing only.
        baseline_selection_methodology_ref is REMOVED from ComparisonRule.
        Every ComparisonRule requires an explicit baseline_measurement_refs
        set (already non-empty per grammar L342); no method is claimed.
        Zero benchmark rules remain, permanently.
        Cost: own-history comparison unavailable. No new contract class.

GAP-5B  Out of scope, but fail-closed rather than absent.
        Field kept, made NULLABLE, given an explicit absent state parallel to
        coverage: absent = NO_ACCEPTED_BENCHMARK_RULE_EXISTS, making every
        baseline-bearing comparison UNAVAILABLE and every Check 19 verdict
        UNDEFINED. Mirrors GAP-3A.
        Cost: the five-member domain must still be deleted or frozen, or the
        absent state re-imports the phantom.

GAP-5C  In scope; author and ratify a benchmark-rule contract before
        implementation. A further authority-bearing contract class (alongside
        GAP-2's unit contract if 2A is chosen). Requires a BenchmarkRule frozen
        model, a registry with a distinct identity, a canonical fingerprint,
        D6M-3 individual ratification, and at least one ratified rule or the
        domain is inert.
        Cost: largest; two new contract classes if combined with GAP-2A.

GAP-5D  Defer the benchmark question to a follow-on amendment; block the
        baseline-bearing surface until then. Comparison rules carrying no
        baseline proceed; those that do are held.
```

**Note on every option:** each requires amending Grammar v0.4 §2 lines 246–251,
§8.1, Amendment plan v0.4 lines 35 and 134, Boundary v0.3 lines 41 and 129,
and Ratification record v0.1 lines 152 and 230. The phantom is **in the
ratification record**, so at least one re-ratification is unavoidable under
every option. **No option preserves the current ratification text unchanged.**

---

# 5. GAP-2 strengthened — the unit contract is absent from doctrine too

The sweep did not merely re-confirm GAP-2. It found a fact that makes the
option set sharper, and it constrains option 2A.

The review established that grammar §1.4 and P3 derive arithmetic validity from
an "accepted unit contract" that does not exist in code, and that `unit` is a
bare `str` on both models.

The new finding: **the nearest candidate artifact is itself not ratified, and it
defines no dimensional-class algebra.**

```text
CSIA_BOOK_5_UNIT_DOMAIN_VALUATION_SEAM_DOCTRINE_v0.1.md
  Status: REPAIR DOCTRINE - INCORPORATED INTO PLAN v0.3 - NOT RATIFIED
  Units: "asset-symbol denomination plus realization identity where relevant"
  Hard rules: "no implicit conversion; no common-value field; no hidden
               numeraire"
  Cross-unit aggregation -> deferred to BOOK 6 valuation
```

Its "unit" is a **naming convention on an asset symbol** — 3 ETH mainnet ≠ 3
weETH — not a dimensional class with arithmetic compatibility. It explicitly
declines to define cross-unit arithmetic and hands that to Book 6, which is the
very contract the grammar assumes already exists.

Runtime confirmation:

```text
$ grep -rn "class .*Unit|UnitContract|unit_domain|dimensional" *.py
(no output)
$ grep -rn "POL-11|POL_11" *.py
(no output)
```

**Consequences for the operator's GAP-2 decision:**

```text
- Option 2A (unit contract in scope) does NOT have an existing doctrine
  substrate to ratify. It requires authoring dimensional-class algebra from
  nothing: a class taxonomy, a compatibility relation, and a divisibility law.
  This is materially larger than "add a third contract class" implies.
- Option 2B (unavailable by absence) is the only option consistent with both
  the code and the existing doctrine. Book 5's doctrine already declares
  cross-unit arithmetic out of its own scope; nothing contradicts 2B.
- Option 2C (defer, ship the citation unenforced) is the weakest. The grammar
  would then cite a contract that is absent from code AND unratified in
  doctrine, which is the exact GAP-5 failure mode repeating itself inside the
  unit domain.
```

This is recorded as **evidence for the operator's decision, not as the
decision.** GAP-2 remains open and operator-owned.

---

# 6. Per-artifact citation register

Every assertion-verb citation resolved. `PRESENT` = substrate exists at the
cited location. `PARTIAL` = concept exists but no named artifact, or substrate
exists with zero ratified content. `PHANTOM` = asserted to exist, absent.

## 6.1 Constitution v0.2 — CLEAN (12 citations)

| citation | verdict | evidence |
|---|---|---|
| canonical identity / asset / node / relationship ontology | PRESENT | `identity.py`, `ontology.py`, `relationships.py` |
| hyperedge primitive (§11.1) | PRESENT | `Hyperedge` `relationships.py:495`; `HyperedgeClass:461`; `_HYPEREDGE_REQUIRED_ROLES:472` |
| claim state machine §7.1 | PRESENT | `claims.py`, `promotion.py` (166 lines) |
| tier-to-claim-state §6.1 | PRESENT | `types.py`, `promotion.py` |
| `GATED_COMPLETE`, `BUILDING` | n/a | state names defined in doctrine; **negations/hypotheticals**, not substrate claims |

## 6.2 Book 1 plan v0.3 — CLEAN (10 citations)

| citation | verdict | evidence |
|---|---|---|
| `RealizationIdentity` adopted via R-1A-5 = Option C | **PRESENT** | `RealizationIdentity` `identity.py:267` |
| hyperedge registry (plan v0.1 §1C.6) | **PRESENT** | `HyperedgeRole` `relationships.py:440`; `HyperedgeClass:461` |
| bitemporal graph / temporal records | **PRESENT** | `temporal.py`; `TemporalRecord` (base of `Hyperedge`) |
| constitutional anchors canonical per ratification record | PRESENT | decision log R-1A-5 |
| `CHANNEL_REPRESENTATIVE` | n/a | explicitly "**not** adopted" — negation |

## 6.3 Book 2 plan v0.2 — CLEAN (6 citations)

All six ratified D2-x substrates were verified individually. **This is the
cleanest artifact in the sweep.**

| ratified decision | verdict | evidence |
|---|---|---|
| D2-1 source classes + aggregator exclusion | **PRESENT** | `SourceClass` `types.py:13`; `sources.py` (227 lines) |
| D2-2 promotion doctrine (+ INFERRED reachability) | **PRESENT** | `promotion.py` (166 lines) |
| D2-3 time-split-first contradiction doctrine | **PRESENT** | `ContradictionEngine` `contradiction.py:41` |
| D2-4 four-kind staleness, no universal stale window | **PRESENT** | `StalenessKind` `freshness.py:27`; `freshness.py` (158 lines) |
| D2-5 claim-family/time-scoped authority, no global trust score | **PRESENT** | `ClaimFamily` `types.py:32`; `claims.py` (546 lines) |
| D2-6 announced/deployed/used distinction | PRESENT (deferred params) | D2-6 is explicitly confirmed-with-deferral; `D6M_5=OPEN_DEFERRED` counterpart |

## 6.4 Book 3 plan v0.2 — CLEAN (12 citations)

| citation | verdict | evidence |
|---|---|---|
| `SECURED_BY` "with its accepted mechanism semantics" | **PRESENT** | `EdgeType.SECURED_BY` `relationships.py:112`; docstring `relationships.py:31` "mandatory on every security edge"; enforced `book4_boundary.py:31` |
| current network identity / D3-5 anchor priority | PRESENT | `network_identity.py` |
| D3-6 two-tier registry admission | PRESENT | registry governance code present |
| already-ratified registry (admission policy) | PARTIAL | policy names no specific registry; D3-6 supplies it. Loose but not a phantom |
| `HISTORICAL_CONTINUATION` | n/a | forward/union reference, not asserted as accepted |

## 6.5 Book 4 plan v0.2 — CLEAN (5 citations)

| citation | verdict | evidence |
|---|---|---|
| "the existing Book 1 hyperedge primitive" | **PRESENT** | `Hyperedge` `relationships.py:495` |
| "an accepted pairwise edge" | **PARTIAL** | no `PairwiseEdge` type. Concept is real — `TypedEdge` `relationships.py:304`, `EdgeType:107`, `EdgeSpec:148`, allowlist `book4_boundary.py:14`, IR-9 pairwise-flattening prohibition `relationships.py:7`/`500` — but the phrase names no artifact. **Naming imprecision, not a phantom** |
| Book 2 provenance binding for every future canonical fact | PRESENT | `dependency_provenance.py` |
| "current facts remain unacquired" | PRESENT | `LIVE_ACQUISITION_AUTHORITY=FALSE` |

## 6.6 Book 5 plan v0.3 — CLEAN (0 assertion citations)

The five-member benchmark namespace appears in the **Book 6** plan, not here.
This artifact makes no accepted-substrate assertion of the phantom kind.

| citation | verdict | evidence |
|---|---|---|
| `CapitalPrincipalLineage` graph "all stand" | **PRESENT** (after §2.2 correction) | `CapitalPrincipalLineageGraph` `book5_lineage.py:117`; `PrincipalContribution:47` |
| unit-domain artifact §2 | PARTIAL | file exists, but self-declares NOT RATIFIED — see §5 |
| `PrincipalComponentSet` vector, no common-value field | PRESENT | `book5_records.py`; hard rules codified |

## 6.7 Book 6 base plan v0.2 — AFFECTED (1 citation; origin of GAP-5)

| citation | verdict | evidence |
|---|---|---|
| benchmark **namespace** of 5 members, "none is chosen by this plan" | **PRESENT-AND-HONEST** | correctly declares non-existence at authoring. Became the phantom when Grammar v0.4 hardened it (§4.2a→b) |
| "ratified metric definitions" (§14 exit evidence) | n/a | §14 is headed "future, unauthorized" — forward spec |
| `COVERAGE_OBSERVATION` != `COVERAGE_SUFFICIENCY_RULE` | PRESENT | `book6_coverage_rules.py` — both exist as distinct concepts |

## 6.8 Amendment plan v0.4 — AFFECTED (16 citations)

| citation | verdict | evidence |
|---|---|---|
| **"accepted benchmark-rule namespace"** (L35, REUSED) | **PHANTOM** | zero `Benchmark*` symbols in 62 modules; `BENCHMARK_RULES_RATIFIED=0` |
| **"accepted benchmark namespace ... reused ... unmodified"** (L134) | **PHANTOM** | as above |
| "accepted coverage-sufficiency rules" (L35) | **PRESENT** | `CoverageRuleRegistry` `book6_coverage_rules.py:112`, identity `csia:book6:coverage-rule-registry`; `CoverageSufficiencyRule`; `ratify():177`; `authorize():227` |
| "accepted canonical numeric representation" (L76) | **PHANTOM** | = GAP-1. `value: float \| None` `book6_records.py:113`; no canonical-numeric contract |
| "accepted typed unit contract" (L51) | **PHANTOM** | = GAP-2, now reinforced (§5) |
| "all accepted tests" / "all accepted Book 6 tests still pass (1341)" | **PRESENT — VERIFIED** | 1341 collected, exact match (see §7.1) |
| "full CSIA suite still passes (2162)" | **PRESENT — VERIFIED** | 2162 collected, exact match (§7.1) |
| "Sensor ... 2325 PASS / 14 FAIL / 4 SKIPPED" | **PRESENT — VERIFIED** | 2343 collected = 2325+14+4 (§7.1) |
| "Comparison-rule ratification authority established by this amendment" | PRESENT | authority-mechanism claim, no external substrate cited |

## 6.9 Grammar v0.4 — AFFECTED (24 citations)

| citation | verdict | evidence |
|---|---|---|
| **`baseline_selection_methodology_ref` = REQUIRED accepted benchmark rule** (L246) | **PHANTOM — GAP-5** | §4 |
| "accepted benchmark" (L341, L583) | **PHANTOM — GAP-5** | §4 |
| "accepted typed unit contract" (L47), "accepted unit semantics" (L149), "accepted unit dimensional class" (L266), "cites the accepted unit contract" (L562, P3) | **PHANTOM — GAP-2** | §5 |
| "canonical fingerprint" (L48, 198, 251, 454) | PRESENT | `methodology_fingerprint()` `book6_methodology.py:132`; `canonical_methodology_spec():99` |
| "canonical UNROUNDED" numeric law (L41, 103) | **PHANTOM — GAP-1** | no unrounded/canonical-numeric substrate |
| "P10 cites a derived determination" (L569) | **PHANTOM — GAP-3** | no applicability field on `MetricDefinition`/`MeasurementMethodology` |
| `comparison_rule_ref ... fingerprint` / derivation binding | PRESENT | `derivation_binding_digest()` + `RatificationLedger` in `book6_ratification.py` |
| "canonical counts remain zero" (L596) | PRESENT | 0 rules ratified; verified |

## 6.10 Book 7 plan v0.2 — CLEAN (0 assertion citations)

| citation | verdict | evidence |
|---|---|---|
| Book 6 `FROZEN_ACCEPTED` anchor `3919fb80...` | **PRESENT — VERIFIED** | ancestor of impl branch HEAD `5f94c3f4`; 0 commits after acceptance |
| `PASS_CSIA_BOOK6_FUNDAMENTAL_MEASUREMENT_STATE_KERNEL` | PRESENT | gate marker in decision log |
| `ObservedChange`, `PostActionObservation`, `ResponseLink`, `ResponseWindowMethodology`, `MARKET_RESPONSE_REF`, `NO_CHANGE_OBSERVED`, `CHANGE_NOT_MEASURABLE` | n/a | **Book 7's own forward specifications.** Zero `book7_*.py` exists, correctly — Book 7 is unratified for implementation. Not phantoms |
| "P2 only where Book 6 defines it" | PRESENT | correct deference; asserts no Book 6 object |
| "amend the frozen Book 6 ... None decided. OPEN_D7N_DECISIONS = 7" | PRESENT | honest deferral |

---

# 7. Verified-clean results

Clean results are reported with the same evidence standard as findings. Three
checks produced exact confirmations.

## 7.1 The three accepted regression baselines are REAL

Amendment plan v0.4 §14 cites accepted baselines as numbers. All three were
independently reproduced by collection:

| cited baseline | cited | measured | result |
|---|---|---|---|
| Book 6 accepted tests | 1341 | 1341 | **EXACT** |
| full CSIA suite | 2162 | 2162 | **EXACT** |
| Sensor 2325 PASS / 14 FAIL / 4 SKIPPED | 2343 | 2343 | **EXACT** |

Book 6 per-file: traceability 614, hardening R1 93, state-rule 84, state-vector
100, comparability 69, normalization 58, adversarial 52, valuation 44, temporal
40, missingness 38, sensitivity 21, core 20, families 17, hardening R2 46,
hardening R3 45 — sums to 1341.

**These three citations are the strongest in the corpus and they all hold.**
That is worth stating explicitly: the sweep found a real phantom *and* verified
three numeric baselines exactly, so the finding is not an artifact of a
hostile or broken method.

## 7.2 Book 2's six ratified decisions all have runtime substrate

D2-1 through D2-5 each verified at a named file and line (§6.3). Book 2 is the
model the rest of the corpus should be held to: every ratified decision maps to
an enforcing symbol.

## 7.3 The Book 1 hyperedge primitive and Book 3 `SECURED_BY` both hold

Book 4 and Book 3 cross-cite Book 1's relationship kernel twice, and both
citations resolve to enforcing code (`Hyperedge:495`, `EdgeType.SECURED_BY:112`,
allowlist `book4_boundary.py:31`). This is what a legitimate cross-book citation
looks like — and it is the direct contrast with GAP-5, which cross-references a
namespace that has no symbol at all.

---

# 8. Second-order finding — ratified artifacts self-declare NOT RATIFIED

Independent of phantom citations, the sweep found a metadata defect in the
corpus. The artifacts ratified by the decision log carry `Status:` headers that
say the opposite.

| artifact | in-file `Status:` header | decision log says |
|---|---|---|
| `CSIA_CONSTITUTION_v0.2.md` | `DRAFT — OPERATOR REVIEW REQUIRED — NOT RATIFIED` | **RATIFIED via D1** |
| `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` | **RATIFIED** (`BOOK6-COMPARE-AMEND-v0.4`) |
| `CSIA_BOOK_5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_PLAN_v0.3.md` | `PLANNING DRAFT — READY_FOR_OPERATOR_RATIFICATION — NOT RATIFIED` | **RATIFIED** (`BOOK5-RATIFICATION-v0.3`) |
| `CSIA_BOOK_6_FUNDAMENTAL_MEASUREMENT_STATE_MODELING_PLAN_v0.2.md` | `DRAFT / PENDING OPERATOR RATIFICATION` | Book 6 `FROZEN_ACCEPTED` |
| `CSIA_BOOK_7_..._PLAN_v0.2.md` | `DRAFT_PENDING_OPERATOR_RATIFICATION` | partially ratified (D7N-3, D7N-7) |

Governance truth currently lives **only** in `CSIA_OPERATOR_DECISION_LOG.md`.
An artifact read in isolation understates its own authority.

This matters for the phantom-citation class specifically. A reviewer who opens
Grammar v0.4 or the amendment plan sees "NOT RATIFIED" in the header and may
reasonably treat its assertions as provisional — which would mask a
ratification-bound phantom. Conversely, a reviewer who trusts the header over
the log would mis-govern ratified artifacts.

**This is not filed as a gap.** It is a metadata-consistency defect with no
runtime consequence, and correcting it changes no decision. It is recorded so
the operator can decide whether to (a) leave headers as authored-state and rely
on the log, or (b) add an explicit `RATIFICATION: see decision log <ID>` line.
Recommendation is deliberately withheld: option (b) touches ratified artifact
text, which is itself a governance action.

---

# 9. Effect on the prior review's verdicts

One prior verdict does not survive this sweep. It is recorded as a correction,
not softened.

```text
PRIOR (BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1):
  BENCHMARK_RUNTIME_PATH_SUFFICIENT = TRUE
```

That TRUE appears to have rested on the observation that the runtime path for
benchmark handling exists and that zero benchmark rules are ratified — which is
consistent. But it did not test the citation that Grammar v0.4 §2 line 246
makes **REQUIRED**: a `baseline_selection_methodology_ref` citing an *accepted,
individually operator-ratified* benchmark rule. That citation is a phantom, and
it is load-bearing for every baseline-bearing `ComparisonRule`.

Revised position:

```text
BENCHMARK_RUNTIME_PATH_SUFFICIENT = NOT SUPPORTABLE AS STATED
  The runtime path is adequate; the DOCTRINE CITATION it was credited with
  satisfying is a phantom with no absent state. The criterion conflated "the
  code can express this" with "the cited artifact exists".
```

This **does not change the HOLD verdict** — HOLD stands on 5/10 and is
strengthened, not weakened, by a fifth gap. It corrects one supporting
criterion.

The other nine criteria are untouched. In particular `NO_RUNTIME_AUTHORITY_GAP`,
`BENCHMARK`-adjacent traceability, and the negative-surface and traceability
work were not affected by this sweep.

**Method lesson, recorded for the next review:** a criterion of the form
"X_IS_SUFFICIENT" must be evaluated against the *citation*, not only the
runtime path. Where doctrine says "derived from an accepted Y", sufficiency of
X is not established until Y exists.

---

# 10. Verdict and non-authorizations

```text
RATIFIED_PLAN_PHANTOM_CITATION_SWEEP = HOLD

GAPS_NOW_OPEN = 5
  GAP-1  canonical numeric representation      (unchanged)
  GAP-2  unit dimensional-class contract      (strengthened - absent from
                                               doctrine as well as code)
  GAP-3  coverage-applicability derivation     (unchanged)
  GAP-4  comparability_status domain + producer(unchanged)
  GAP-5  accepted benchmark-rule namespace     (NEW - ratified and propagated)

CLEAN_RATIFIED_ARTIFACTS = 7 of 10
  Constitution v0.2, Book 1 v0.3, Book 2 v0.2, Book 3 v0.2, Book 4 v0.2,
  Book 5 v0.3, Book 7 v0.2
  (Book 6 base plan v0.2 is affected only as the origin of GAP-5;
   its own citations are honest - see section 6.7)

PHANTOM_CITATIONS_CONFIRMED = 1 new + 4 prior (GAP-1..GAP-4)
VERIFIED_CLEAN_CITATIONS    = 3 numeric baselines exact + 6 Book 2 decisions
                               + 2 Book 1/3/4 cross-book primitives
METADATA_DRIFT_RECORDED     = 1 (artifact Status headers vs decision log)

AUTHORIZATION_PACKET = NOT CREATED
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
D6M_5                           = OPEN_DEFERRED
COMPARISON_RULES_RATIFIED       = 0
BENCHMARK_RULES_RATIFIED        = 0
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
```

**Not authorized and not performed by this sweep:** any implementation, any
source or test change, any re-ratification, any amendment edit, any new policy,
value domain, contract class or absent state, any decision on GAP-1..GAP-5, any
Book 7/8 work, live acquisition, branch creation, force-push, rebase or history
rewrite. The four operator decisions from the prior review remain open and
operator-owned; a fifth is added. **This artifact decides none of the five.**

---

# 11. Next move

```text
NEXT = operator decisions on GAP-1, GAP-2, GAP-3, GAP-4, GAP-5.
       GAP-5 is newly opened by this sweep and is coupled to the others:
       every option for it requires at least one re-ratification, because the
       phantom is inside the ratified record.
       Re-run the authorization review with GAP-5 included before any
       implementation authorization is considered.
AUTHORIZATION_PACKET = NOT CREATED (still conditional on PASS)
```

**Highest-value operator decision first:** GAP-5 must be decided before GAP-3,
because GAP-5A/5B remove the entire baseline-bearing surface and therefore
change what "all 19 replay checks implementable" even means. Deciding GAP-3
first would mean deciding it twice.
