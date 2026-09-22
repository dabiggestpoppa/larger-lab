# QCAE Implementation Progress Ledger

**Branch:** `qcae-capability-acquisition-engine`
**Canon:** QCAE v0.1 (Blocks 0–18, COMPLETE / FROZEN) under `qcae/books/`
**Active amendments:** A-001 (Research Mesh Boundary and Economic Experience v1.0)
**Build mode:** BUILD MODE per master prompt; phases P0→P12 strictly sequential.

---

## Current Phase

**P3 — IN PROGRESS (I0 + C01–C12 + R1–R3 + A1/A2/A3 + P2-R5 reconciliation + P3-R4 C1–C5/T1 + R1/R2 repairs; 1370/1370 LOCAL TEST EVIDENCE)** — Discovery Vertical Slice. Tranche 1 delivered the discovery *contract* layer: plan domain, adapter port + leads, internal-first baseline, canonical merge/families/ranking/saturation, and the terminal artifact assembler. Not yet delivered: GitHub adapter with egress authority, Research Mesh delegation seam, IT/T01 qualification, freeze. P2 is FROZEN / OPERATOR-REVIEWED + R1–R4 COMPLETE (LOCAL TEST EVIDENCE: 1108/1108 at `f2fc7757`); no P2 repair is open.

### P3-I0 — Phase Start / Plan Lock (this commit)

**Predecessor freeze:** `P2-R4-freeze-manifest.json` at `65ca004b`, blockers `[]`. P3 entry criteria (canon 18.2) checked at this head:

| Entry criterion | Status | Evidence |
| --- | --- | --- |
| predecessor phase freeze exists | PASS | `P2-R4-freeze-manifest.json` (supersedes P2/R1/R2/R3 manifests, digests preserved) |
| required canon chapters frozen | PASS | Book II Block 2 read in full (2.1–2.7) + Book V 15.1/15.3 + Book VI 18.1/18.2 + A-001 §4–§7, §13, §14 |
| unresolved blockers classified | PASS | P2 blockers `[]`; P3 risks classified below (BLOCKER/MAJOR/MINOR) |
| planned files/modules/tests listed | PASS | tranche plan below |
| phase risks and authority needs explicit | PASS | risks + authority section below |
| baseline suite green or known failures documented | PASS | `python -m pytest qcae/tests -q` → **1108 passed / 0 failed / 0 skipped** at `65ca004b` (LOCAL TEST EVIDENCE) |

**Canon P3 definition** (Book VI 18.1): *Discovery Vertical Slice* — internal baseline lookup plus GitHub repository/code discovery, DiscoveryPlan, candidate normalization/deduplication, ranking, budgets, stop rules, provenance. A-001 §13 adds one obligation: capability prior-art discovery stays, and an **explicit Research Mesh delegation seam** is added.

**Planned modules (tranche 1):**

- `qcae/core/discovery/plan.py` — DiscoveryPlan + hypotheses/query families/source portfolio/diversity/stop rules/cost tiers/saturation/budget/amendment proposals (canon 2.1). Domain records live at the dependency center (precedent: P1 put evidence/knowledge/receipts in `core/`); stdlib-only, provider-neutral.
- `qcae/core/discovery/lead.py` — CandidateLead normalization + query lineage (canon 2.1.11/2.1.4, Book V 15.3) that carries provider output into the frozen candidate ontology **without** any verification level (leads are `DISCOVERED` by construction).
- `qcae/core/ports/discovery.py` — `DiscoverySourceAdapter` port + `DiscoveryQuery`/`AdapterOutcome` with typed failure semantics (15.3: `NO_RESULTS`/`PARTIAL_RESULTS`/`RATE_LIMITED`/`AUTH_FAILURE`/`PROVIDER_FAILURE`/`UNSUPPORTED_QUERY` + standalone `NOT_CONFIGURED`).
- `qcae/discovery/internal/baseline.py` — internal-first baseline over the existing P1 `RegistryQuery` port (2.6): classification, partial-reuse narrowing of external scope, prior-decision lookup, internal trust firewall.
- `qcae/discovery/planning/ranking.py` — canonical-candidate merge/dedup (2.1.12), family clustering (2.7.6), hard prefilters with evidence-strength floors (2.7.3), versioned diversity-aware ranking policy with popularity cap (2.7.5/2.7.10/2.7.11), escalation queue + waves (2.7.9/2.7.14), saturation + stop recommendation (2.1.9/2.1.10).
- tests: `qcae/tests/unit/test_p3_plan_domain.py`, `test_p3_adapter_contract.py`, `test_p3_internal_baseline.py`, `test_p3_ranking.py`, `test_p3_t01_adversarial.py`.

**Landed in tranche 1 (LOCAL TEST EVIDENCE: 1247 passed / 0 failed / 0 skipped):**

- **C01 `bfda42b7`** — `qcae/core/discovery/{plan,lead,report}.py`: DiscoveryPlan schema 2.1.15 with anti-capture laws (atom scope, internal-first queries, multi-route per atom, route→family→source coverage, diversity cap 2.1.7, no dead budget, stop-rule completeness incl. `BUDGET_CEILING_REACHED`, hard-prefilter evidence floor 2.7.3, Block 2 tier-3 ceiling 2.1.8) and proposal-only `CONTRACT_AMENDMENT_PROPOSAL` (2.1.14). Task `2.1.16` failure modes are unrepresentable rather than documented.
- **C02 `937cec68`** — `qcae/core/ports/discovery.py`: `DiscoverySourceAdapter` port, `DiscoveryQuery`, `AdapterOutcome` with typed failure semantics (15.3) and `DiscoveryAdapterRegistry.missing_source_classes` so an unconfigured surface is reported `NOT_CONFIGURED`, never imitated. Leads carry no verification field at all (2.1.11/2.3.12); failure statuses cannot carry leads (2.1.13); `PARTIAL_RESULTS` requires its completeness note (2.2.13).
- **C03 `810d4ddc`** — `qcae/discovery/internal/baseline.py`: internal-first baseline over the P1 `RegistryQuery` with canon 2.6.1 classifications, exact partial-reuse narrowing (2.6.8), prior-decision lookup (2.6.5), internal trust firewall (2.6.3/2.6.10), fail-closed unknown-state handling (2.6.11), and comparative/abandoned classifications that retrieval state may not invent.
- **C04 `c2174553`** — `qcae/core/discovery/candidate.py` + `qcae/discovery/planning/ranking.py`: canonical merge/dedup preserving every path (2.1.12), family clustering with representative-first deferral (2.7.6), versioned ranking policy with capped popularity (2.7.10/2.7.11), auditable per-dimension queue rows (2.7.16 invariant 7), wave assignment bounded per family/source class (2.7.14), saturation accounting that only advances on searches that ran (2.1.10), and STOP only from declared stop rules (2.1.9).

**Remaining P3 work (recorded, not hidden):** `discovery/planning/planner.py` (contract → reproducible plan), `discovery/github/` adapter over an injectable transport with pagination/rate budget/partial labeling/immutable anchor, egress authority + policy gate (MAJOR risk above), `discovery/research/` Research Mesh delegation seam + bounded `LOCAL_FALLBACK_RESEARCH` (A-001 §5/§13), `P3-IT01` integration, `P3-T01` adversarial qualification, `P3-FREEZE` manifest + acceptance.

**Risks / blockers (canon 18.2 severity):**

- **MAJOR (open) — GitHub egress authority.** Canon 2.2 requires live GitHub repository/code search; A-001 §5 and Book III 5.6 require capability-specific egress to be policy-controlled and fail closed. Tranche 1 therefore builds the *provider-neutral* contract plus internal-first baseline only; the GitHub adapter lands with an injectable transport and an explicit authority/egress gate, never as a silent default. Until then an absent provider is reported as `NOT_CONFIGURED`, never as an empty-but-successful search.
- **MAJOR (open) — popularity/README firewall enforcement.** Encoded as policy laws (bounded popularity weight, `REJECT` evidence-strength floor, leads carry no verification level) and to be re-proved adversarially in `P3-T01`.
- **MINOR (accepted) — internal classification mapping.** P1's `internal_first_findings` categories are mapped to canon 2.6.1 classifications by a documented retrieval-only table; `INTERNAL_IMPLEMENTATION_SUPERIOR/INFERIOR` are *not* derivable from durable state at P3 and are deliberately not emitted (they need evidence-level comparison, Book IV Block 9/11). Recorded as a derived point for operator review.
- **MINOR (accepted) — P1 surface maturity.** The plan consumes `RegistryQuery` only; no new persistence engine is added in P3 tranche 1 (ADR-0006 remains the single metadata engine).

**Authority needs:** no new authority class. Discovery is read-only against local durable state and (later) policy-gated egress; it can propose, never enact, contract changes (2.1.14) and can never approve acquisition (2.7.4).

### P3-A1 — Structure pass: retrieval query + error boundary (shape only)

No capability added; behavior preserved except three wiring shapes that previously raised.

**Ownership, as it now stands.** Later passes should extend these owners rather than adding parallel machinery:

| Concern | Owner |
| --- | --- |
| **Partial-wiring policy** (an absent component contributes empty findings, never `AttributeError`) | `SqliteRegistryQuery._optional_call` — the single owner. No retrieval method may branch on wiring. |
| Shared derivations over durable state: matched active receipts, contract versions, atom ids, repository revisions, `repo:` source-ref parse | `SqliteRegistryQuery` private accessors + module-level `_repo_id` |
| 9.7 retrieval-order query (three read-only findings methods) | `SqliteRegistryQuery`, typed against the `core/ports` abstractions, not concrete SQLite repos |
| Connection open: path validation, pragmas, schema, version guard, typed open failures | `open_metadata_db` (`store_factory`) |
| Mapping expected operator errors to stable exit codes (2 = rejected/unknown, 3 = worker unavailable, 4 = budget) | `main()` in `interfaces/cli/__main__.py`; runtime construction sits **inside** that boundary |

**Normalizations (the only behavior changes), both in shapes that previously raised:** (1) `internal_first_findings` no longer crashes when capabilities are wired but negatives are not — it now answers the documented empty shape, completing the policy above; (2) `known_capability_state` returns the same key set under every wiring shape, so callers never branch on configuration. Construction contract is unchanged: four positional components remain required (all typed `Optional`), so `SqliteRegistryQuery()` still rejects. Regression guard: `test_every_wiring_shape_answers_without_raising`.

**Deferred (unchanged, already classified):** the freshness lookup in `SqliteRegistryQuery._stale_evidence_ids` reads the lifecycle log's connection directly, because the frozen `LifecycleLogRepository` port exposes no enumeration — recorded in the P1-R1 freeze manifest as MINOR with trigger "P2 job runtime". Collapsing it requires widening a frozen port; do that as its own reviewed change, not inside a shape pass.

### P3-C05 — Terminal artifact: the report assembler

`qcae/discovery/reporting.py` (`assemble_discovery_report`) — one call takes the pieces a caller holds (plan, internal baseline record, adapter outcomes, ranking pass) and returns the `DiscoveryReport` Block 3 receives. Before this, the phase's definition required a terminal artifact that nothing produced: the only way to exercise P3 was to hand-drive its API piece by piece.

It is a pure function of records — no adapter is touched, no transport imported (asserted by `test_the_assembler_has_no_egress_path`) — and two rules govern what it does with each piece:

- **Derive only what the pieces make factual.** Counters, the budget verdict, partial-search notes, negative findings and remaining uncertainties are read off the plan, baseline, outcomes and metrics. The budget stop is derived from the two ceilings the counters can evidence (`max_queries`, `max_results_inspected`); `max_source_calls`/`max_wall_clock_seconds`/`max_cost_usd` have no counterpart in the counters, so a stop on those must be *declared*, never inferred. The judgement flags (sufficient non-dominated set, amendment required) are caller declarations passed through, and a condition the plan never declared still cannot justify a stop because `stop_recommendation` owns that law (2.1.9).
- **Fail closed instead of dropping a piece.** Refused: a discovered candidate absent from the ranking (2.1.12), a baseline whose contract/version/atom scope is not this plan's (2.1.6), a search that reached a source class the plan never allocated (2.1.5/2.1.7), and an unlabelled partial search. Disclosed rather than refused: executed searches carrying no lead lineage (their families are named as absent from `query_families_executed`), and a baseline reporting `sufficient_without_discovery` while external search ran (2.6.7) — both are recorded, not chosen between.

Owned elsewhere and not reimplemented: canonical identity (`planning.canonical`), family identity (`planning.families`), the counting rule (`planning.saturation`), the report's own laws (`core.discovery.report`). Verified end to end over a real P1 registry: baseline → 5 outcomes → 3 canonical candidates → 2 families (one deferral) → report that validates and round-trips through serialization, with a repeat pass adding zero new candidates and the budget stop derived at 11 executed queries against a ceiling of 10.

**Structural residue found while assembling (verified, deliberately not fixed here).** (1) `DiscoveryAdapterRegistry` (`core/ports/discovery.py:325`) is a concrete composition container — mutable `self._adapters`, a real `__init__`, `register`, and `close_all` at `:379` reaching for a `close` method via `getattr` that the `DiscoverySourceAdapter` port never declares — in a module whose every other member is an ABC/Protocol or a frozen record. (2) `SourceClass` (canon 2.1.5 vocabulary) is defined at `core/discovery/plan.py:70` and imported by `candidate.py`, `lead.py` and now `discovery/reporting.py`, so every discovery record imports its vocabulary from the plan module, while `core/vocabulary.py` already hosts `EvidenceClass`/`VerificationLevel`/`EVIDENCE_STRENGTH_ORDER`. (3) Tier coercion is duplicated: `plan.py:174 _coerce_cost_tier` and `ports/discovery.py:113 _coerce_tier` have identical bodies, and the latter's docstring even reads "(see plan.py)". All three are real. The earlier audit's fourth item — family/candidate membership enforced in two places — is **resolved** by the A2 split: `build_families` now constructs members and delegates to `CandidateFamily.validate`, so that rule has one enforcement point. The first three are cleared in **P3-A3**.

### P3-A2 — Structure pass: one module per ranking concern (shape only)

`discovery/planning/ranking.py` had grown to 876 lines owning six behavioural concerns. It is now seven modules, each with one owner and one canon anchor. No capability added, no test count change (1258/1258), and the whole pipeline was re-run end to end afterwards: plan → merge → prefilter → rank → saturation → stop, with repeat passes contributing zero new specifications and `NEGLIGIBLE_NOVELTY` firing.

| Module | Owns | Canon |
| --- | --- | --- |
| `ranking_policy.py` | the dimension vocabulary, the popularity cap, `RankingPolicy` validation | 2.7.10/2.7.11 |
| `canonical.py` | locator normalization, canonical identity, merge/dedup, `descending_id` tie-break | 2.1.12 |
| `families.py` | what a family is (`family_identity_for`), who represents it | 2.7.6/2.7.9 |
| `scoring.py` | dimension derivation, kind priors, the popularity-bounded blend | 2.7.2/2.7.8/2.7.10 |
| `prefilter.py` | the prefilter evidence floor | 2.7.3 |
| `saturation.py` | pass-over-pass counters and stop recommendations | 2.1.9/2.1.10 |
| `ranking.py` | the pass itself: ordering, waves, next action, priority, `RankingResult` | 2.7.5/2.7.14 |

**Dependency direction is one-way**, which is why the split holds: `ranking_policy` ← `canonical` ← `families` ← `scoring` ← `ranking`, with `prefilter` and `saturation` depending only on `families`/core. A later change to any concern lands in exactly one file, and the two properties the R1/R2 repairs established are now structurally enforced rather than incidentally true — `family_identity_for` is the single family identity every module compares (re-verified at runtime: the ids ranking emits equal the ids saturation matches), and candidates are aggregated in `canonical` before either grouping or ranking sees them.

**Two small cleanups:** `build_families` accepted a `RankingPolicy` it never read (the wave limits it looked like it governed actually live in `ranking`), so that parameter is gone; and the one consumer (`test_p3_ranking.py`) now imports each name from its owner instead of from a single catch-all module — no re-export façade, so "where does this live" has one answer.

### P3-A3 — Structure pass: ports purity + one home for discovery vocabulary (shape only)

Clears the three residues P3-C05 verified and left. No capability added, no behavior change for any adapter or record that exists, suite 1273 → 1274 (one new contract test).

| Concern | Owner (now) |
| --- | --- |
| Adapter composition: which adapter serves which source class, missing-class reporting | `qcae/discovery/adapter_registry.py::DiscoveryAdapterRegistry` — moved out of `core/ports/discovery.py`, where it was the only implementation in a module of interfaces; it now sits beside the adapters it wires, as `store_factory` sits beside the repositories it wires |
| Adapter resource release | `DiscoverySourceAdapter.close` — **declared on the port**, default no-op, so `close_all` releases adapters through their own interface instead of `getattr`-probing for a hook |
| Discovery vocabulary: `SourceClass` (2.1.5), `CostTier` (2.1.8) | `qcae/core/discovery/vocabulary.py` — one definition each, eight import sites, no re-exports |
| Int-enum reconstruction from serialized form | `core/serialization.py::coerce_int_enum` — was duplicated verbatim in `plan.py` and `ports/discovery.py` |

**Why `core/discovery/vocabulary.py` and not `core/vocabulary.py`:** the latter is Book I's constitutional vocabulary (canon 0.4.2/0.5.12) and is declared frozen; Block 2 vocabulary is P3's own and belongs beside the Block 2 records that speak it. Neither module is named in any freeze manifest (checked: no manifest pins `core/ports/discovery.py` or `core/discovery/*`).

**Found while clearing, and closed in P3-C06:** a capability with an **active receipt and no registered candidates** could not produce an internal baseline at all (recorded as open here first; see P3-C06 for the characterization and fix).

**Residual, reported not fixed:** declaring `close` on the port makes the obligation *visible*; it does not make a misspelled override fail, because the no-op default still satisfies it. Catching that class requires an abstract method, which would force every stateless adapter to write a no-op — ceremony this phase does not need. The registry relocation and the declaration are still the fix for the observed failure (`close_all` omitting a configured adapter, now pinned by `test_a_stateless_adapter_closes_through_the_port_contract`, red at HEAD as `[]`).

### P3-C06 — Baseline coverage reads the same evidence the verdict does

The residue P3-A3 reproduced over a real P1 registry, characterized and fixed. Suite 1274 → 1275.

**Characterization (public API, real registry).** A capability holding an ACTIVE receipt under the plan's exact contract and version, with no candidate rows, refused to produce a baseline: `FULLY_SATISFIED_INTERNAL cannot leave uncovered atoms (canon 2.6.1)`. Seven shapes probed end to end; the two signals that must agree disagreed, because `CAPABILITY_ACTIVE` maps to `FULLY_SATISFIED_INTERNAL` (canon 2.6.1 table) while `_capability_granularity_coverage` returned empty coverage whenever `candidate_refs` was empty. `build()` therefore assembled a record claiming full internal satisfaction with the whole atom scope uncovered, and `validate()` refused it — so the phase could not state a baseline for its **strongest** internal state, and canon 2.6.7 requires an explicit baseline before any external comparison.

**Not a fixture artifact.** P1 stores receipts without candidate rows in four of its own suites (`test_p1_receipt`, `test_p1_registry_retrieval`, `test_p1_cross_registry`, `test_p1_adversarial` all call `add_candidate` zero times), so the shape is a first-class registry state. The fixture that surfaced it was wrong only in the direction it *did* work: it added candidates to a receipt case, which is what every existing `CAPABILITY_ACTIVE` test does too — that masking is why 1274 tests never saw this.

**Fix (smallest change, in the baseline's owner).** Coverage now reads the registry's **two** internal-candidate records (canon 2.6.12) rather than one: known candidates and active receipts under this exact contract — the same fact that makes `CAPABILITY_ACTIVE` fire. `_capability_granularity_coverage` takes `internal_refs` (the union) and gates on it; the claim granularity and its label are unchanged, so this remains the weaker capability-granularity claim rather than an invented per-atom one.

**Observable contract change (recorded because callers can see it):** `internal_candidate_refs` now carries the receipt ids that evidence a coverage claim, not candidates alone — so in a receipt-without-candidates shape it is `("rcpt-001",)` rather than empty, and in a receipt-with-candidates shape it names both bases. Without that, the record would assert full coverage with no recorded basis.

**Fail-closed discipline preserved, checked per shape:** a capability with no internal evidence is unchanged (`covered=()`, `external_target=(ATOM_A, ATOM_B)`, `external_search_required=True`); unrecognizable findings, non-object detail blocks, unknown categories and out-of-scope coverage still refuse. The change is monotone in one direction only — coverage can grow, so `missing_atoms` and `external_target_atoms` can only shrink. Recognized internal knowledge narrows the external request and can never authorize one.

**Residual, reported not fixed (decided in P3-C07):** in the receipt-without-candidates shape the record carried both `FULLY_SATISFIED_INTERNAL` and `PARTIALLY_SATISFIED_INTERNAL` in `classifications`. The upstream cause is P1's `DEFINITION_WITHOUT_IMPLEMENTATION` category (`sqlite_knowledge_store.internal_first_findings`), which fires from the candidate inventory alone and ignores an active receipt, so P1 emits "defined but unimplemented" while its own receipt table proves an implementation. P3-C07 settled it on P3's side: a category's sufficiency finding is emitted only when coverage supports it, so the pair can no longer appear. The P1 category itself is unchanged — a separate, still-open question for that surface.

**Superseded in P3-C07.** The claim below that coverage stays *capability-granularity* was itself the over-claim an audit then reproduced: a receipt scoped to one atom granted coverage of the whole capability and suppressed the external search for the atom nothing proved. P3-C07 replaces the basis with per-atom attribution.

**Verified:** red then green through the public API over a real registry (`test_an_active_receipt_without_candidates_still_yields_a_baseline`); full suite 1275 passed; and the shape driven on through `merge_leads` → `rank_candidates` → `assemble_discovery_report`, where the report assembles, validates and round-trips through serialization — a path that previously could not be reached at all, because the baseline refused before the assembler ran.

### P3-C07 — Internal satisfaction is a function of attributable coverage

An audit reproduced the failure of P3-C06's resolution: a receipt declaring only `ATOM_B` for a two-atom capability produced `covered=(ATOM_A, ATOM_B)` with `external_target_atoms=()`, so a one-atom proof suppressed the external search for an atom nothing internally proves. Suite 1275 → 1285.

**Root cause, shared with its predecessor.** The invariant "FULLY_SATISFIED implies no uncovered atoms" had three owners — `_capability_granularity_coverage`, `_verdict`/`_classify`, and `validate()` — so `build()` could construct a violating record and only `validate()` refused it, at runtime. And the coverage derivation read *some evidence exists* as *every in-scope atom is covered*, which is a claim its evidence never made.

**Attribution was in the model and thrown away.** `CapabilityReceipt.atom_ids` is required and scope-bounded ("receipt must reference at least one atom"), and P1 retrieves candidates per atom (`list_candidates_for_atom`); both were flattened into id lists by `known_capability_state`/`decision_reuse_findings`, and a flat list cannot support a per-atom claim. The port was checked first: **no freeze manifest pins `RegistryQuery` or its methods** (the only manifest mention is P1-R1's deferred freshness-lookup item, a different concern), the port has exactly **two** implementors (`SqliteRegistryQuery` and the P3 test fake), and nothing asserts its method surface. The addition was therefore warranted and minimal — one method, no dict shape changed (P1 asserts those exactly, and still passes untouched).

| Change | Owner |
| --- | --- |
| `RegistryQuery.internal_evidence_by_atom` — `{atom_id: (ref, ...)}` over records each attributed by its own scope | new port method + `SqliteRegistryQuery`, built from the existing `_atom_ids`/`_candidates_for_atom`/`_matched_active_receipts` derivations so every wiring shape answers `{}` rather than raising |
| Coverage = the requested atoms an internal record names | `_registry_attributed_coverage` (replaces `_capability_granularity_coverage`) |
| How much is satisfied | `_verdict(covered, missing)` — the **single owner**, a pure function of coverage |
| Whether a category may assert satisfaction | `_coverage_supports` — a category's sufficiency finding is emitted only when coverage supports it |

**`internal_candidate_refs` now means:** the references to the internal records that **support this record's coverage claim** — for each covered atom, the records whose own scope names it, or the caller's refs when the caller supplied per-atom coverage. It is the *basis of the claim*, not an inventory: a reference naming no covered atom is not recorded, and `()` means nothing supports coverage. (P3-C06 had widened it to candidates ∪ receipts and left the meaning implicit; this pass documents it on the field.)

**Observable contract changes:** (1) registry-derived coverage is labelled `ATOM_ATTRIBUTED_BY_REGISTRY_STATE`, replacing `CAPABILITY_GRANULARITY_FROM_REGISTRY_STATE`; (2) `FULLY_SATISFIED_INTERNAL` now requires every requested atom to be attributed, so a partially-scoped receipt yields `PARTIALLY_SATISFIED_INTERNAL` with the unproven atoms as the external target; (3) `DEFINITION_WITHOUT_IMPLEMENTATION` no longer yields a `PARTIALLY_SATISFIED_INTERNAL` classification on a record covering nothing (same over-claim class, and its test was rewritten to state the honest outcome); (4) the baseline no longer calls `known_capability_state` — the call became dead once coverage stopped reading its flattened fields, and the call-ordering test now asserts the attribution call.

**Fail-closed direction proved, not asserted:** no internal evidence still yields the full external target (`test_partially_wired_registry_produces_a_baseline`); a superseded receipt, a receipt under another contract version, and a receipt naming no requested atom each yield `NO_INTERNAL_CAPABILITY_FOUND` with both atoms as the external target; unrecognizable findings, non-object detail and out-of-scope caller coverage still refuse. The external target can only ever *shrink* relative to evidence that names atoms — recognizing internal knowledge narrows the request and never authorizes one.

**Deliberately not done:** attributed registry evidence now *could* prove canon 2.6.9 duplication (two records scoped to one atom), but seeding `DUPLICATE_IMPLEMENTATIONS` from state would be new capability, so `duplicate_atom_refs` stays caller-supplied — pinned by `test_registry_evidence_does_not_seed_duplicate_implementations`.

**Verified:** red first on exactly the audit's finding (the one-atom receipt claimed both atoms) and on the candidate analogue; then green: 9 new real-registry/attribution tests, full suite **1285 passed**, and the shape driven downstream — one-atom receipt now yields `external_target=('atom-causal-ordering',)` and the assembled report still validates and round-trips. Also: the two copied real-registry test helpers collapsed into one parameterized `_real_query` (the previous pass had duplicated 21 of its 24 lines), and the new port method is covered by P1's existing "every wiring shape answers" guard.

### P3-C08 — A claim in the artifact cannot survive beside evidence that refutes it

An audit named five ways the assembled report could carry mutually contradictory claims. Each was constructed against the real assembler before anything changed. **Three are reachable; two are not** — stated here with the evidence rather than guarded speculatively. Suite 1285 → 1292.

| Alleged contradiction | Finding |
| --- | --- |
| partial-search notes contradicting outcome statuses | **Reachable.** `_partial_search_notes` keyed on `status == PARTIAL_RESULTS`, but the port's own standing (`AdapterOutcome.exhaustive`) says a *completed* search that qualified its completeness is partial too — `OK` + `completeness_note="stopped after page 3 of 10"` produced `exhaustive=False` and no note. Notes now key on that standing, so a qualified search is recorded partial whatever its status label reads. |
| a stop verdict disagreeing with the counters it derives from | **Reachable.** `enough_non_dominated=True` over an empty pass with nothing known from an earlier pass assembled a `STOP` on a non-dominated set the report does not contain. Now refused by `_require_sufficiency_claim_has_a_set`. The other stop conditions stay derived (budget from the counters, `NEGLIGIBLE_NOVELTY` from saturation under a declared threshold), so they cannot disagree with themselves; candidates known from an earlier pass are a real set, so a later pass that adds nothing may still judge the accumulated set sufficient (2.1.10). `HARD_CONSTRAINTS_ELIMINATE_CLASS` is deliberately *not* guarded: hard constraints can eliminate a candidate class without any candidate having been found. |
| internal sufficiency while external search ran | **Reachable, and disclosed rather than refused.** With `external_target_atoms == ()` and searches that counted toward saturation, the report now carries a coverage note naming the contradiction (the `sufficient_without_discovery` note covers the related declaration flag, this covers the derived target set). Refusing would be wrong: the effort really did happen and the artifact must report it. |
| family deferrals inconsistent with the ranked rows | **Not reachable.** `DiscoveryReport.validate` already refuses it — probed: a ranking row re-pointed at `fam-does-not-exist` raises `escalation entry references unknown family`. Now pinned by `test_a_family_deferral_the_report_does_not_contain_is_refused` (the state needs a hand-built ranking; no ranking pass produces it). |
| coverage claims outrunning the baseline the report references | **Not reachable.** The artifact carries no per-atom claim: `CandidateFamily` and `EscalationEntry` hold candidate and family ids only, and the report's one atom statement, `atom_ids`, is forced to equal the baseline's own requested scope by `_require_baseline_matches_plan` (probed: a candidate claiming `atom-never-requested-by-the-plan` is accepted, and that atom appears nowhere in the report — it is a candidate-scope question, not an artifact contradiction). |

**Verified:** three tests red at HEAD on the changed paths (`3 failed, 18 passed`), then green: 7 new tests, full suite **1292 passed**, ruff clean. One real drive over the real P1 registry (active receipt + candidate → `FULLY_SATISFIED_INTERNAL`, `external_target=()`), 3 outcomes including a qualified `OK` and a completed empty search, 2 candidates → 2 families → assembled report that round-trips through serialization, the hollow sufficiency refused, and a later pass over known candidates still allowed to stop. Also re-confirmed the audit's earlier item is closed rather than merely moved: the refusal fires before any metrics work, so a hollow pass cannot reach a verdict at all.

### P3-C09 — Playtest: two live defects on the multi-pass and coverage paths

Drove the product as a first user would: the P2 CLI (its real commands, careless arguments, empty databases, a typo'd job id) and P3's real surface, the public API — plan authoring, empty registry, loose adapter payloads, the two-source merge, multi-pass handoffs, mismatched pieces, record round-trips. Suite 1292 → 1294. Two defects found, both in P3's own code, both fixed test-first; three findings reported without fixing, with the reason.

**Defect 1 — the artifact's own handoff inflated novelty (canon 2.1.10).** The terminal artifact carries the previous pass's `saturation_metrics` but not the candidate records those counters measured, so the natural durable handoff (`previous_metrics=last_report.saturation_metrics`) is the *metrics-only* shape. Fed that way, `queries_executed` accumulates while novelty is counted as if nothing were known: a repeat pass over the same project reported `new_candidates=3` vs 2, `new_atoms_covered=5` vs 3, and a marginal novelty rate of **4.0 vs 2.667** against the honest handoff — and that rate is what the stop law reads. Neither `validate()` nor any test saw it, because every existing multi-pass test passes both arguments. Fixed by disclosing in `coverage_notes` (`_previous_knowledge_is_missing`): only when the carried counters actually record knowledge (candidates/atoms/specifications) and no candidates came with them, so a first pass stays quiet. Disclosed rather than refused because following the artifact is what reaches this state — the counters travel, the records do not.

**Defect 2 — a record could carry two sufficiency verdicts at once (canon 2.6.1).** `SUFFICIENCY_VERDICTS` documents that *exactly one* of FULLY/PARTIALLY/NO_INTERNAL is the baseline's verdict, but `_coverage_supports` gated the PARTIALLY mapping on `bool(covered_atoms)` alone, while `_verdict` derives PARTIALLY only from `covered_atoms and missing_atoms`. So P1's `DEFINITION_WITHOUT_IMPLEMENTATION` category (contract + atoms + an active receipt, no candidate rows — the shape four P1 suites store) produced `classifications = ['FULLY_SATISFIED_INTERNAL', 'PARTIALLY_SATISFIED_INTERNAL']` on a record whose coverage was complete. This is the residual P3-C06 named and P3-C07 believed closed; the gate was the remaining hole. Each `_coverage_supports` clause is now the clause `_verdict` derives that classification from, so a category can only restate the verdict. Verified across four real-registry shapes: full receipt → `['FULLY_SATISFIED_INTERNAL']`, one-atom receipt → `['PARTIALLY_SATISFIED_INTERNAL']`, no evidence → `['NO_INTERNAL_CAPABILITY_FOUND']`, candidates covering both → `['FULLY_SATISFIED_INTERNAL']` (no verdict value changed).

**Reported, not fixed:**

- **P2 CLI (`interfaces/cli/app.py`), misleading feedback.** `qcae job run <typo'd id>` prints `no eligible step to run` (exit 1) because `job_run_step` returns `None` for an unknown job *and* for a job with no runnable step, while `job status`/`job events` say `unknown job` (exit 2). A mistyped id reads as "the job exists but has nothing to do". Not fixed here: P2 is FROZEN / OPERATOR-REVIEWED, and the fix belongs to a P2 repair pass rather than a P3 playtest edit.
- **Product dead end (P3 tranche 1 scope).** `job submit --kind discovery` succeeds and `job run` then reports `WORKER_UNAVAILABLE` with `missing_step_types: ['discovery']` — permanently, because no discovery worker type exists anywhere in the tree (`register_worker_type` lives on the in-process orchestrator engine) and the CLI offers no worker registration. The CLI helps advertise it: `--kind KIND  job kind (e.g. discovery)`. This is the known deferred gap (GitHub adapter, discovery CLI), not a new defect.
- **`qcae/discovery/__init__.py` carries a stray string literal** after `__version__`/`CANON_VERSION` (a no-op statement, not the module docstring) from P0-C01. Zero user impact — `import qcae.discovery` is unaffected — so it is reported rather than edited in a sealed phase's file.

**Clean on inspection, with evidence:** plan validation names the offending atom/hypothesis/family and the canon clause for each of four careless plans; an `OK` outcome with no leads, a lead from the wrong adapter, and an outcome for an unallocated source class are all refused with the rule that refuses them; a hit naming no atom, and a hit naming an atom outside the plan, both rank honestly (coverage 0.00, LOW, wave 2, rationale stating "atom coverage 0.00 from declared claims (not proof)"); the two-source merge reaches the artifact as one candidate with "2 source class(es), 1 duplicate path(s)"; plan, lead, outcome, candidate, baseline, policy and report all round-trip through serialization; the CLI's DB errors are typed with exit 2 (a path that is a directory, a non-database file, a file where a directory is needed), and unknown commands exit 2.

**Structural note for whoever owns the multi-pass flow:** the disclosure in defect 1 is a stopgap. Canon 2.1.10 wants novelty measured against what was known, but the artifact Block 3 receives carries candidate *ids*, not records, so no durable caller can reconstruct `previously_known_candidates` from the artifact alone. Either the report should carry what the next pass needs (ids plus per-candidate scope), or the multi-pass flow should be defined against in-process state. That is a design decision, not a playtest fix.

### P3-C10 — The artifact is its own hand-off

P3-C09's playtest proved the artifact could not feed the phase's own loop: it carried the previous pass's `saturation_metrics` but not the candidates those counters measured, so the natural durable hand-off inflated novelty (rate 4.0 against an honest 2.667) and the stop law read the inflated number. P3-C09 could only disclose that; this pass carries what the next pass needs. Suite 1294 → 1301.

**Canon supports the shape, so no contract was bent to fit.** 2.7.15 says the terminal artifact *should include* the canonical candidate set — the report carried only `canonical_candidate_ids` (identifiers, not the set) — and 2.1.10 measures novelty against what was already known. So the artifact now carries `known_candidates`: every canonical candidate known as of the pass, accumulated across passes, aggregated by `planning.canonical.merge_canonical_candidates` so one identity stays one record (2.1.12). Family identity is *not* copied in: `known_candidates` holds the records, so the next pass derives families from `families.family_identity_for` under whatever rule is current, and the rule keeps one owner.

**The hand-off is one argument, not two fields to remember.** `assemble_discovery_report(..., previous_report=last_report)` derives both halves — `previous_metrics = last.saturation_metrics` and `previously_known_candidates = last.known_candidates` — so a durable loop that restarts from the artifact cannot get the pairing wrong. `previous_metrics`/`previously_known_candidates` remain for a caller holding the pieces itself; supplying either alongside `previous_report` is refused (`_require_one_history_source`) because a history with two owners is how one pass's counters would meet another pass's candidates. The C09 disclosure stays as belt-and-braces (counters carried without knowledge still says so); its test now also asserts the working hand-off is silent.

**Observable contract changes:**

1. `DiscoveryReport.known_candidates` (tuple of `CanonicalCandidate`) plus the derived `known_candidates_ids`.
2. `DiscoveryReport.SCHEMA_VERSION` **1 → 2** — the first record-schema bump in the repo's core records. The reader requires an exact version match, so leaving it at 1 would have surfaced an old payload as `payload missing field 'known_candidates'` (a corruption-shaped error) instead of `schema_version 1 not supported by reader (expects 2)`. Verified both guards fire; no persisted `DiscoveryReport` exists in the tree, so nothing on disk breaks.
3. Two new refusals: mixing `previous_report` with explicit history, and a report whose `canonical_candidate_ids` are not in its `known_candidates` (the artifact must carry the set it counted, or the next pass re-counts it).

**One existing fixture had to state its intent honestly.** `test_budget_exhaustion_is_derived_from_the_counters` ranked a candidate that no outcome of that pass returned and no earlier pass knew — under the new law that call is refused. The fixture now passes the candidate as `previously_known_candidates` and says so in a comment: the candidate was found by the earlier pass, this pass runs eleven empty searches. The assertion it exists for (budget exhaustion derived from the counters) is unchanged.

**Verified:** 7 new tests, red first (`TypeError: assemble_discovery_report() got an unexpected keyword argument 'previous_report'`) then green; the whole loop driven over the real P1 registry with a **JSON round-trip between passes** — three passes handing over the reloaded artifact alone, with the artifact path's metrics *and* stop recommendation equal to a control built from the caller's own accumulated records at every pass, and that control's records equal to the artifact's `known_candidates` (`rate 4.0 → 2.333 → 1.667` as each pass adds less); the first-pass path unchanged (1 query, 1 known, 1 canonical, same two notes); full suite **1301 passed**, ruff clean.

### P3-C11 — A capability claim is not an atom claim

An audit proved that `CanonicalCandidate.claims_atoms` held capability ids: the merge folded canon 2.1.11's two intake fields — `claimed_capabilities` and `possible_atom_matches` — into one, and canon 2.1.11 lists them separately precisely because they are different vocabularies. Atom coverage is what the ranking's coverage dimension, the baseline's attributed coverage and the report's carried candidates rest on, so a claim set carrying contract ids credited coverage to something that is not an atom. Suite 1301 → 1309.

**The input shape that produced it, and what a caller saw.** A lead shaped the way the adapter port documents — `claimed_capabilities=('CAP-REPLAY-001',)`, `possible_atom_matches=('atom-causal-ordering',)` — merged to `claims_atoms=('CAP-REPLAY-001', 'atom-causal-ordering')`. A single hit matching **1 of the plan's 2 atoms** then reported `new_atoms_covered=2`, i.e. the whole atom scope, because saturation counts that field as atoms; scoring, which intersects it with the plan's atoms, silently ignored the same id — two readers deciding claim kind differently from one ambiguous field.

**The mask.** The repo's own fixture helper fed atom ids into `claimed_capabilities` too, so in every existing test the two sets coincided and the union hid the conflation; a correctly built adapter — the only kind that will exist in production — triggers it. The helper now says so where it builds leads, and the real shape has its own tests.

**One owner.** Every derivation now lives in the merge (`canonical.merge_leads`, `merge_canonical_candidates`): atoms come from `possible_atom_matches` and only from there, capability claims from `claimed_capabilities` and only from there, into their own fields. Nothing downstream re-checks kind — `saturation` and `reporting` read an atoms-only field, and `scoring`'s intersection with the plan's atoms now answers *relevance* (which of this plan's atoms does the candidate match), not kind.

**Fail-closed direction.** A capability-only hit stays an acquisition object (canon 0.2.1 needs a claim, not specifically an atom claim — the port already allows that lead) but earns **no** atom coverage: measured `new_atoms_covered=0` and `coverage_potential=0.00`. A malformed claim is refused by the record (`claims_atoms entry`/`claimed_capabilities entry` must be identifiers) rather than counted.

**The new `known_candidates` hand-off did carry it — confirmed, and closed.** `report.known_candidates[0].claims_atoms` was `('CAP-REPLAY-001', 'atom-causal-ordering')` before this pass, and `reporting.py` builds `previous_covered_atoms` from that field, so a contract id was handed to the next pass as a known atom. Now the carried record holds `claims_atoms=('atom-causal-ordering',)` beside `claimed_capabilities=('CAP-REPLAY-001',)`, and a test round-trips the artifact through serialization to prove the second pass's `new_atoms_covered` does not shift. The hand-off's cross-capability acceptance, the two candidate collections, the assembler's note policy and the baseline are untouched.

**Observable contract changes:**

1. `CanonicalCandidate.claimed_capabilities` (new) and `claims_atoms` now atoms-only.
2. `CanonicalCandidate.SCHEMA_VERSION` **1 → 2** — the persisted shape changed and the reader matches versions exactly, so a record whose atom claims may hold capability ids is refused by version rather than misread. It is nested in `DiscoveryReport.known_candidates`, so an artifact written before either bump is refused.
3. The acquisition-object law relaxed from "`claims_atoms` non-empty" to "at least one claim kind non-empty", because the old form only admitted capability-only hits *by* the conflation.
4. Atom claims must be identifier-shaped (previously any string list was accepted).

**Verified:** 8 new tests, red first in both files (`assert ('CAP-REPLAY-001', 'atom-causal-ordering') == ('atom-causal-ordering',)` and the report-level counter), then green; the affected path driven end to end over the real P1 registry — three hits (capability-only, capability + one atom, capability + one atom from another source kind) → `claims_atoms` per candidate holding only atoms, `coverage_potential` 0.00 for the capability-only hit, `new_atoms_covered=2` of 2 plan atoms from two one-atom hits, carried kinds apart through a JSON round-trip with the candidate record at schema 2, and an unchanged `new_atoms_covered` on the handed-over second pass. Full suite **1309 passed**, ruff clean.

### P3-C12 — A pass history is bound to the capability it measured

P3-C10 made the artifact sufficient to hand over; an audit then showed it was *sufficient but not safe to accept*. Nothing bound the handed-over report to the identity it measured, so a report assembled for another contract, or another revision of it, could be handed in as this pass's past: its known candidates entered this capability's novelty accounting and its stop verdict. A fail-open path of the same class as the P3-C07 over-claim. Suite 1309 → 1315.

**What a caller saw, before anything changed.** Reproduced through the public API against the current code: a report assembled for `CAP-OTHER-001` handed to a pass searching `CAP-REPLAY-001` was accepted, and its `known_candidates` were merged into this pass's known set — silently, and before this pass's counters were computed. A report whose `contract_version` differed was accepted the same way. The artifact already stated both identities (`contract_id`, `contract_version`), so nothing new had to be carried; the binding was simply never checked.

**Where the binding belongs, and why.** The assembler, not the artifact: the assembler already owns history derivation (`previous_report` → metrics + known candidates) and every other fail-closed law (`_require_one_history_source`, `_require_baseline_matches_plan`, `_require_sources_allocated`), while the artifact's own `validate()` has no view of the plan being assembled. `_require_history_is_for_this_capability` therefore runs beside `_require_one_history_source`, before the history is used.

**The two choices, settled by evidence.**

1. *Contract identity is refused; plan scope is disclosed.* `_require_history_is_for_this_capability` refuses a differing `contract_id` or `contract_version`, naming both sides (canon 2.1.10: novelty is measured against what was already known *for this capability*). A differing plan id or atom scope for the **same** capability is accepted and disclosed instead — the history-scope note in `_coverage_notes`, naming both scopes. The counters read candidate identity, family and claimed atoms, all the capability's, and a plan is a search document that is re-cut between passes (amended contracts, refocused scope); refusing a narrower or wider scope would refuse a verifiable history, and a wider one is not a re-count either — the atom the history never saw is still new.
2. *The binding is the assembler's.* The artifact already states the identity; the assembler already owns history derivation and every other fail-closed law, and the artifact's own `validate()` has no view of the plan being assembled. No field was added and `SCHEMA_VERSION` did not move.

The binding reads only stated fields, so it survives the JSON round trip the durable loop uses — asserted, not assumed.

**Verified:** 6 new tests, red first (`Failed: DID NOT RAISE` for the cross-capability and revision hand-offs), then green — the cross-capability refusal, the revision refusal, the JSON round trip, the re-cut plan id accepted + disclosed, a narrower scope accepted + disclosed with counters equal to a hand-supplied control, and a **wider** scope where the atom the history never saw is still counted as new (`new_atoms_covered` 1 → 2, the covered atom not re-credited). The durable loop re-driven end to end over the real P1 registry: three passes, each artifact serialized to JSON and reloaded before being handed on — `queries 3/6/9`, `new_candidates` steady at 2, rate decaying `2.333 → 1.167 → 0.778`, stop `CONTINUE`, no history disclosure on a clean hand-off; the foreign-capability and foreign-revision hand-offs refused with the identity named; the re-cut scope accepted with the scope change disclosed. Full suite **1315 passed**, ruff clean.

**Observable contract changes:** one new refusal and one new note in `coverage_notes`; the artifact's shape is unchanged (no schema bump), and `known_candidates`, the port addition, the baseline, the claim-kind laws and the assembler's existing note policy are untouched.

### P2-R5 — Predecessor operator-gate reconciliation + CLI run truth (this commit)

P3-R4 requires the earlier P2-R5 operator requirements reconciled against executable evidence before P3 continues. Four were already proven; one had no standing anywhere in the tree and is repaired here. **P2-R4 remains preserved as historical evidence; this entry supersedes only its "no P2 repair is open" clause** — P2-R5 was the open repair, and it is now closed at this commit.

| Operator requirement | Classification | Evidence |
| --- | --- | --- |
| evidence attribution | **PROVEN** | `EvidenceRef` canonical digests (`core/evidence_ref.py`, P0-C04/P1-C01 `d5e8882e`); receipts cannot exist without attributed proof refs (`core/receipts/receipt.py` proof firewall, P1-C05 `3aaddeea`). Executable: `test_p2r5_reconciliation.py::TestEvidenceAttribution` (digest identity binds the payload; malformed digest refused; proofless receipt refused). |
| schema authority + migration truth | **PROVEN** | Versioned serialization envelopes fail closed on unknown versions (`core/serialization.py`, Book V 15.2); `PRAGMA user_version` + append-only `schema_migration_ledger` with pre/post digests, no backward/skip (`infrastructure/persistence/migrations.py`, P1-C10 `55ba326d`, P2-C12 v3→v4 `61488273`). Executable: `TestSchemaAuthorityAndMigrationTruth` (envelope refuses schema_version 99; ledger pins versions and digests). |
| live grant binding | **PROVEN** | Durable single-use grants consumed atomically at admission (`governance_approval_use` unique index, `SqliteApprovalRegistry.mark_grant_used`, P2-R4-C03 `1e04778d`); process-memory `_granted_keys` removed. Executable: `TestLiveGrantBinding` (second consumption of the same grant refused; consumption durable). |
| backup/restore truth | **PROVEN** | Digest-verified restore of metadata + artifacts + registry rows (`infrastructure/persistence/backup_restore.py`, P1-C11 `772ab794`, P1-R1-C05 `1817ed57`/`0a3bd46b`, P2-C12 runtime state `61488273`). Executable: `TestBackupRestoreTruth` (round trip restores verified state; a tampered artifact fails the digest check and restore refuses). |
| typed NOT_READY behavior | **UNRESOLVED → repaired here** | No standing existed before this commit (grep: NOT_READY appears only in canon prose, Book V 15.12). New: `governance/standalone/typed_outcomes.py` — `StepNotReadyOutcome` (typed reason from `NOT_READY_REASONS`, standing `CONTRACT_NOT_READY`) and `JobMissingOutcome` (same unknown-job standing as `job status`/`job events`). Executable: `TestTypedNotReadyBehavior`. |

**CLI truth defect repaired (the P3-C09 reported finding).** `qcae job run <unknown-job-id>` returned "no eligible step to run" (exit 1) because `job_run_step` returned `None` for an unknown job *and* for a job with nothing runnable, while `job status`/`job events` say `unknown job` (exit 2) — a mistyped id read as "the job exists but has nothing to do". `QcaeApp.job_run_step` now answers, in order: unknown job → typed `JobMissingOutcome` (CLI exit 2, message byte-identical to `job status`); no claimable step → typed `StepNotReadyOutcome` with the reason derived from durable step rows (`SCHEDULE_NOT_ELAPSED` / `STEP_WAITING_POLICY` / `STEP_WAITING_INPUT` / `STEP_RETRY_SCHEDULED` / `NO_ELIGIBLE_STEP`); missing worker → the existing `WORKER_UNAVAILABLE` outcome (exit 3, unchanged). The claimable check reads the engine's public `eligible_steps_for_claim` law and the queue's public `has_active_claim` — no private reach-in (architecture guard green), no lease/claim/event/budget mutation on any denied path. Executable: `TestCLIRunTruth` (status/events/run agree on one standing for one identifier; a future-dated job reports `NOT_READY`/`SCHEDULE_NOT_ELAPSED` structured with exit 1; nothing leased).

**Boundaries held:** execution mutations 0 on every refused path; no worker registered; no scheduler/ACL/startup artifact created. Suite after this tranche: **1329 passed / 0 failed / 0 skipped** (LOCAL TEST EVIDENCE, this commit).

### P3-R4 — Discovery authority and evidence convergence tranche

The directive's law set: every outcome bound to the exact plan-authorized query, no STOP through an unattributed boolean, external scope truthful against baseline narrowing, novelty only from in-scope identity-deduplicated knowledge, and a terminal artifact that verifies its own claims. P2-R5 reconciled first (above); the five tranche commits follow, then the two audit-driven repairs.

### P3-R4C1 — Every outcome binds to an immutable executed-query record (`15d8835b`)

`AdapterOutcome` now binds to exactly one `ExecutedDiscoveryQuery` at construction (`core/ports/discovery.py`): a typed record naming the plan, contract identity, query identity, family, atom, semantic concept, concrete query (or deterministic `sha256` digest), source class, adapter, envelope limits, execution status, timestamps, provider revision, evidence refs and outcome identity. Assembly (`discovery/reporting.py::_require_outcomes_bound_to_plan`) refuses: unbound outcomes, records from another plan/contract, families the plan never declared, concrete queries outside the family's declared terms, unplanned query identities, out-of-scope atoms, unallocated source classes, tier/result-envelope violations, and leads whose lineage disagrees with the record that found them. `NO_RESULTS` and every failure status keep full lineage — provenance is not a function of whether anything was found. Plan-side query authorization moved from a stored set to a derived property (`plan.query_ids`), so a repeated execution of one planned query binds under its own `-execN` ordinal without duplicating authorization. NO_RESULTS still carries its atom/family/source/adapter lineage in the failure notes and execution coverage.

**Observable contract changes:** `AdapterOutcome.bind_execution_record` + `execution_record_for` new on the port; assembly refuses unbound outcomes. `report.external_scope_atoms` semantics land in C2, not here.

### P3-R4C2 — Requested / internally covered / external target / executed scopes separated (`7805869c`)

`DiscoveryReport` gains the scope quadruple (`requested_atom_ids`, `internally_covered_atom_ids`, `external_target_atom_ids`, `actually_executed_atom_ids`), validated as one coherent scope — coverage inside the request, the external target exactly the uncovered remainder, execution inside the request. `external_scope_atoms` returns the **baseline-authorized external target scope**, not the requested set, which had claimed a wider search than the baseline required. `assert_external_execution_authorized` is the pre-adapter-call egress gate: a fully satisfied baseline blocks external queries outright, a partially satisfied one forbids re-searching covered atoms (the blocking-before-adapter-call law; the report can only tell the truth about what already ran). Novelty accounting (`update_saturation.novel_atom_scope`) credits only atoms inside the authorized external scope, so a provider mention of an out-of-scope atom cannot increase `new_atoms_covered`.

**Observable contract changes:** `DiscoveryReport.SCHEMA_VERSION` **2 → 3** — a pre-C2 artifact is refused by version rather than misread; one new public assembler function; `update_saturation` signature extended additively.

### P3-R4C3 — STOP only from attributable assessments (`75f0424d`)

`StopConditionAssessment` (schema 1) is the typed record behind every satisfied stop condition: condition, plan/contract identity, evaluator id, policy version, validated RFC3339 UTC timestamp, exact subject set, derivation method, evidence refs — and for `CONTRACT_AMBIGUITY_REQUIRES_AMENDMENT` a mandatory proposal id cited among the evidence. `StopRecommendation` (schema **1 → 2**) refuses a STOP whose satisfied conditions lack their assessments; the naked `enough_non_dominated` / `hard_constraints_eliminated_class` / `contract_amendment_required` / `budget_exhausted` boolean parameters are **gone from the assembler**. Budget exhaustion and negligible novelty are *derived* from the typed counters against the plan's declared envelope and threshold, and carry synthesized assessments naming exactly what they were derived from. Sufficiency without a current candidate set stays refused; a failure-only pass cannot manufacture a negligible-novelty STOP because nothing was inspected to derive the rate from. `require_rfc3339_utc` added to `core/validation.py` as the shared timestamp law.

### P3-R4C4 — Negative knowledge is identity-deduplicated (`e8ccd954`)

`NegativeObservation` (schema 1, `core/discovery/report.py`): its `observation_id` derives deterministically from the safe applicable combination of the *planned* query identity (execution ordinals stripped), atom, family, source class, adapter, provider revision, status and bounded query scope (result limit + tier); validation refuses any record whose carried id no longer derives from its fields. Repeated identical failures and repeated identical `NO_RESULTS` merge into one observation with a raised `observed_count` instead of creating new failure information — the marginal-novelty numerator the negligible-novelty stop law reads can no longer be inflated by retries. A materially new state (different status, different provider revision) derives a different identity and is genuinely new; `NO_RESULTS` stays distinct from `PROVIDER_FAILURE` because status is part of the identity; an observation never asserts capability absence. The report carries the deduplicated observations themselves (`negative_observations`, validated against the report's plan), not only prose strings, so negative knowledge survives serialization and artifact handoff.

### P3-R4C5 — The report self-verifies and evidence is deeply immutable (`4dc01393`)

`SerializableRecord.__post_init__` now deeply freezes declared mapping fields: a caller's dict is copied into a `MappingProxyType` whose values are themselves frozen, so mutating the caller's original mapping cannot mutate the record, nested values cannot change after validation, serialization order and record digests stay deterministic, and the JSON round trip preserves exact meaning. `CandidateLead.activity_signals`, `CandidateLead.popularity_signals` and `EscalationEntry.dimension_scores` are frozen evidence, and validators that previously required plain dicts accept the frozen shape. The terminal artifact self-verifies: every claim its `validate()` reads — candidates, families, queue, prefilter decisions, negative observations, stop assessments, the scope quadruple — rides the artifact itself, so a later pass validates a previous report by reloading it, with no hidden process memory.

### P3-R4T1 — Adversarial law set A–S complete (`cc78a7ef`)

All 19 directive adversarial cases A–S are executable tests (`tests/unit/test_p3_report_assembly.py`, `test_p3_ranking.py`): unknown query id refused (A), wrong family/atom refused (B/C), lead-lineage mismatch refused (D), unallocated-source failure refused (E), `NO_RESULTS` retains typed lineage (F), fully satisfied baseline blocks external execution at the gate before any adapter call (G), narrowed baseline preserves requested and external target scope separately (H), out-of-plan atom mention cannot inflate coverage (I), naked booleans unrepresentable (J), historical candidates cannot justify sufficiency without current evaluation (K), failure-only passes cannot produce a negligible-novelty STOP (L), repeated identical failure adds zero new failure information (M), repeated identical `NO_RESULTS` adds zero new negative knowledge (N), amendment STOP without a matching proposal refused (O), hard-constraint STOP without typed class decisions refused (P), caller dict mutation cannot mutate the record (Q), bindings/negative knowledge/assessments survive JSON round trip (R), and every denied path leaves durable state unchanged (S — inputs, plan authorization and baseline survive a refused assembly byte-identical, bound records still validate).

### P3-R4-R1 — The last caller-boolean channel to a STOP is closed (`97e349fb`)

The external audit confirmed §5 law 8 was violated at HEAD: the assembler still accepted `saturated: bool` / `saturation_reason: str` — a pre-C3 survivor the C3 sweep missed, live through C4/C5 — and the flag flowed through `SaturationMetrics.saturated` into `stop_recommendation`'s NEGLIGIBLE_NOVELTY derivation, so a caller flag synthesized a STOP with no attributable typed evidence. The hole went untested because the L test never passed the kwarg. `update_saturation` no longer accepts caller saturation at all: the flag is *derived* from the typed accounting (this pass inspected results and discovered nothing new), and the derived reason is prefixed `derived: ` so `stop_recommendation` distinguishes the accounting's own measurement from an externally supplied record — the undeclared-condition tripwire now fires only for the latter, while a plan that declares no NEGLIGIBLE_NOVELTY rule simply continues on a derived measurement (canon 2.1.9: the plan's own declared choice). A pass whose searches carried no payload (only empty or failed searches) derives nothing — an exhaustion rate is a rate over observations — so the failure-only residual the audit identified (rate 0.0 over zero inspections meeting any threshold) is dead in derived form too. `saturated`/`saturation_reason` removed from `assemble_discovery_report`; the stale pre-C3 docstring ("the judgement flags are the caller's declarations and are never inferred") replaced with the derivation law. Tests prove refusal instead of exercising the channel: the parameter cannot exist (with its three C3 siblings), the accounting raises on it, flags cannot create a STOP, failure-only passes cannot derive saturation, partial execution derives nothing, the declared-threshold law holds at the recommendation, and the honest exhausted-family path still derives a STOP with no boolean anywhere. Suite after this commit: **1363 passed / 0 failed / 0 skipped** (LOCAL TEST EVIDENCE).

### P3-R4-R2 — Deep freeze made annotation-agnostic (`a2cabe0f`)

The audit demonstrated C5's freeze was annotation-gated: `get_origin(dict)` is `None`, so the origin-based trigger never matched a bare `dict` annotation and fields like `AuthorityRequest.context` held the caller's own mapping — a post-construction caller mutation reached into the frozen record **and moved its digest** (reproduced red-first on `WorkerResult.budget_used` before the fix: digest stability itself was broken for bare-dict fields, not just immutability). `SerializableRecord.__post_init__` now freezes by declaration and by the value's nature: every `dict`/`Mapping` spelling (typed, bare, or protocol — `typing.Mapping`'s origin is `collections.abc.Mapping`, also closed) freezes into a deeply frozen proxy, and set-declared fields freeze into a deterministic `frozenset` with sorted-array serialization and `from_dict` rebuilding the declared set so the round trip preserves exact meaning; a mapping- or set-declared field holding the wrong shape is refused rather than silently kept. The flagged `WorkerResult.validate` subclass `getattr` check sits outside the base-class loop but already accepts the frozen shape, so the path holds — pinned by a real-record test covering construction, validation, digesting and round trip. A repo-wide sweep found no legitimate in-place mutation sites on any newly frozen field, so no rebuild rerouting through `dataclasses.replace`/`from_dict` was needed. Seven new serialization tests pin the law. Suite after this commit: **1370 passed / 0 failed / 0 skipped** (LOCAL TEST EVIDENCE).

**P3-R4 validation matrix (LOCAL TEST EVIDENCE, at `a2cabe0f`):** complete suite **1370 passed / 0 failed / 0 skipped** from the repository root, 1370 collected, zero duplicate node ids; focused P2-R5 reconciliation tests 12/12; P3 binding/scope/stop/negative/immutability law tests all green including the R1 refusal set and the R2 freeze set; architecture/dependency guards 23/23; touched-file ruff clean on every tranche and repair commit. Whole-package `ruff check qcae` reports a **pre-existing backlog of 195 findings** (154 F401, 26 F841, 5 E402, 4 F822, and single E702/E731/E741/F541/F811/F821 — the F811/F821 sit in `orchestration/orchestrator/engine.py` and `tests/unit/test_p1r1_freeze_evidence_robustness.py`, neither touched by this tranche) — reported separately per directive; touched-file cleanliness is not whole-package cleanliness. No applicable authoritative CI workflow exists in this repository yet, so local pytest remains LOCAL TEST EVIDENCE, not CI evidence. Boundaries: no P4, no acquisition approval, no repository import, no live GitHub egress, no cloud/broker/capital/execution mutations, main untouched, history append-only.

**Remaining P3 boundary (unchanged in substance, per directive §10):** deterministic contract-to-plan planner, governed GitHub adapter with injectable transport, explicit fail-closed egress authority wiring, pagination/rate budget, partial-result truth, immutable revision anchoring, Research Mesh delegation seam, bounded LOCAL_FALLBACK_RESEARCH, actual discovery worker registration, truthful CLI/API journey, P3 integration qualification, P3 adversarial T01, authoritative CI, P3 freeze manifest.


### P2-R4 — True Crash Durability + Durable Approval + Scheduling Closure (SEALED at `f2fc7757`)

All five operator audit findings (F–J, recorded in I0 before implementation) closed:

- **C01+C02 `5bc38d18`** — `SqliteRuntimeStore.flush()` explicit durability boundaries: lease/RUNNING/attempt/admission committed before execution, no DB write transaction spans `worker.execute()`, post-effect writes committed before return; `_complete` reconstructs canonical truth from COMMITTED whether or not the legacy marker exists; `recover_job` reloads job AND steps after reconciliation (stale snapshots can never regress terminal truth) and finalizes an all-steps-done job idempotently.
- **C03 `1e04778d`** — durable single-use grants: `_granted_keys` removed; admission verifies the grant against the step's recorded authority request and consumes it atomically (`governance_approval_use`, unique `decision_ref`); consumption survives restart and cannot replay; expired/denied/wrong-principal grants admit nothing; authority-request ids are semantics-digest + uniqueness suffix (no restart-reset counter).
- **C04 `081f20c8`** — one scheduling truth: `effective_not_before = max(job, step)`, enforced atomically in claim SQL; `ready_steps` no longer overwrites schedules; availability probes and recovery use the same rule; priority cannot bypass; CLI `--not-before` proven end-to-end.
- **A01 `b283a63e`** — real abrupt-process-death acceptance: subprocess children `os._exit(1)` at crash windows A–E with no pre-crash manual commit; parent verifies durable truth via independent connection; cross-process recovery completes with the external effect executed exactly once; NON_REPLAY_SAFE ambiguity escalates to WAITING_INPUT.
- **A02 `467c6714`** — durable grant acceptance journey (finding J): grant → restart → still discoverable → release → execute once → consumed → terminal truth survives restart → replay decision refused. Original denial journey preserved unchanged.
- **T01 `f2fc7757`** — 14 adversarial cases over the repair laws, all failing closed.
- **FREEZE `f2fc7757`** — `P2-R4-freeze-manifest.json` superseding manifest (P2/R1/R2/R3 manifests + R3 acceptance preserved unchanged with digests, blockers `[]`) plus **observed** evidence artifacts `P2-R4-operator-acceptance.json` and `P2-R4-process-crash-evidence.json` captured from actual pytest runs (full suite 1108/1108, acceptance 14/14).

### P2-R4 operator audit findings (recorded BEFORE implementation; commit I0)

- **F (BLOCKER) — true process-kill durability unproven / tx spans external work.** `open_metadata_db` leaves Python's default isolation; no runtime write path ever calls `conn.commit()`, and `_StoreTransaction` (BEGIN IMMEDIATE) is only used by `submit()`. Every lease, RUNNING-state, attempt, EXECUTING reservation, and event write accumulates in one open transaction while `worker.execute()` performs external work — abrupt death loses ALL runtime state since the last explicit commit. Current acceptance tests do `conn.commit(); conn.close()` and label it "process death": that proves reopen/restart, not crash. Audit sites: queue claim (`sqlite_step_queue.claim_next`), RUNNING+attempt (`engine.lease_next`), authority decision/event, execution reservation/EXECUTING (`reserve_execution`), external `worker.execute()` call (`engine.execute_step`), COMMITTED result, idempotency marker, step finalization, checkpoint, job finalization. Plan: explicit pre-effect durable commit (lease+RUNNING+attempt+authority admission+idempotency reservation+EXECUTING) → `worker.execute()` with NO open write transaction → post-effect durable commit (result/COMMITTED/step state/outputs/checkpoint/events/job finalization); no global autocommit switch — explicit UoW boundaries only.
- **G (BLOCKER) — approval authority is process-memory state.** `engine._granted_keys: set` (line 115) is the execution-side truth: added by `record_exact_scope_grant` (line 610), consulted by `execute_step` (line 468). It vanishes on restart, is never consumed, and can be inherited indefinitely in-process; durable approval records and execution authority can disagree. Repair: durable single-use grant consumed atomically at admission, reusing `SqliteApprovalRegistry`; registry-side idempotent marking.
- **H (MAJOR) — COMMITTED reconstruction can regress/strand canonical state.** (A) `recover_job` loads the Job snapshot once, then reconciliation (`recover_leased_steps`→`_complete`) may finalize the job SUCCEEDED — but `recover_job` continues with its stale object and writes RUNNING back over terminal truth (§10 violation). (B) `_complete` early-returns on `record_idempotent_completion` False (legacy `runtime_idempotency` marker): if the process died after marker creation but before step-state finalization, the canonical RuntimeStep stays RUNNING forever (§11 violation: marker is evidence, never canonical state).
- **I (MAJOR) — job `not_before` is persisted but never enforced.** `JobSubmission.not_before` lands on `runtime_job.not_before` (DDL col exists, indexed) and `ready_steps` OVERWRITES the step's `not_before` with the current clock (engine line 267) — a future-dated job becomes claimable immediately. One scheduling truth required: `effective_not_before = max(job.not_before, step.not_before)` enforced atomically in claim selection; priority/recovery cannot bypass it.
- **J (MAJOR) — acceptance Journey E tests denial, not durable grant→execute→complete.** `TestJourneyE` is named `..._grant_...` but exercises request→DENY→WAITING_POLICY; the grant path and its restart/consumption laws are unexercised at the surface level.

P2-R4 repair tranche: I0 (this entry) → C01 durable crash boundaries → C02 COMMITTED reconstruction + refresh law → C03 durable grants → C04 scheduling truth → A01 real process-kill acceptance → A02 grant acceptance journey → T01 adversarial qualification → FREEZE (superseding manifest, observed acceptance evidence).

Prior phases: P0 FROZEN+RECONCILED · P0-A001 FROZEN · P1 FROZEN / OPERATOR-REVIEWED + R1 COMPLETE (incl. ADR-0007 identity/revision repair).

### P2 milestone ledger (commits)

- `ab0098c5` P2-I0 — ADR-0008 (runtime state vocabulary, additive over frozen P0 identity layer) + ADR-0009 (13.2 policy decisions ↔ P0 authority outcomes) + ledger transition
- `52be767f` P2-C01 — runtime job/step domain, fail-closed state machines (Book V 13.6 step vocabulary verbatim), step graph with cycle/self/missing-dep rejection
- `534f7864` P2-C02 — durable runtime store: jobs, steps, append-only digest-verified event log, checkpoints, idempotency table
- `766efa0d` P2-C03 — durable step queue: token-guarded lease ownership, guarded-claim upsert, expiry recovery
- `cb047e4a` P2-C04 — local identity, versioned fail-closed policy engine (no mutation API), LocalAuthorityProvider behind a port
- `e1936d06` P2-C05 — approval + escalation workflow: exact-scope binding (laundering rejected at write), expiry, durable decision records
- `fbe93cef` P2-C06 — Context Packet (least-context, reference-based) + typed WorkerRequest/WorkerResult (canon 12.3 vocabulary) + six test workers
- `21bc4466` P2-C07 — orchestrator engine: bounded class-specific retries, semantic checkpoints, idempotent completion, crash recovery (completed steps never repeated; authority rechecked after restart)
- `0603b882` P2-C08 — hierarchical budgets: conservation law (child ≤ parent remaining), retry consumption, no reset on recovery, approval-scoped increases
- `38e6ca66` P2-C09 — SecretProvider (handles not values), value-free audit log, centralized Redactor on failure paths
- `c531e12f` P2-C10 — standalone runtime service: submit/inspect/list/run/resume/cancel/approvals/recovery/identity; safe cancellation; job completion semantics
- `49f6fdbc` P2-C11 — composition factory + QcaeApp application service + thin CLI (job/approval/identity commands)
- `61488273` P2-C12 — schema migration v3→v4 (additive runtime + governance tables) + backup/restore carrying full runtime state; stale leases recoverable after restore
- `afdbaa84` P2-T01 — adversarial qualification: forged approvals, stale tokens, budget underflow, retry storms (bounded at max_attempts), tampered payloads, restart-during-wait, durable DENY
- freeze commits — generator (`p2_freeze_manifest.py`) + manifest sealed with captured test results

### P2 exit-gate status

All directive §44 criteria satisfied with committed evidence: durable jobs/steps with explicit transitions; graph dependencies (A→B→C and fan-out/fan-in) proven; queue uses single-owner leases with expiry recovery; crash/restart resumes without repeating committed steps; retries bounded by class and max_attempts; budgets conserved; local identity/policy deterministic and versioned; REQUIRE_APPROVAL blocks execution and approval scope cannot be laundered; secrets are references with value-free audit; Context Packets are least-context; worker handoffs typed; escalation durable; cancellation safe; P1→P2 migration preserves registry/evidence state; backup/restore preserves runtime state; runtime runs with OCE completely absent (`OCE_ABSENT`); architecture guards green (engine confined to infrastructure; core stdlib-only).Freeze manifest: `qcae/implementation/P2-freeze-manifest.json` — test results captured from an actual full-suite run by the fail-closed generator (`qcae/implementation/tools/p2_freeze_manifest.py`), never hardcoded.


### P2-R2 — Governance-Wiring Repair Tranche (opened at reviewed head `a8b20a6c`)

Operator review accepted the P2-R1 structural repairs but identified that
local governance was built as *components* without being bound into the
*execution path*: the engine exposed a public `authority_ok=True` bypass
instead of evaluating the AuthorityProvider, REQUIRE_APPROVAL never reached
WAITING_POLICY on the normal path, recovery re-evaluation was caller-modeled,
`QcaeApp`/`RuntimeService` reached into private attributes (`service._engine`,
`engine._workers`), and `QcaeApp` had no `job submit` (CLI could not durably
submit a job).

Repair plan (narrow commits, additive, no redesign of accepted subsystems):

- **P2-R2-I0** — this audit/plan record.
- **P2-R2-C01** — `StepAuthorityGate` port (core/ports) + engine wiring:
  every `execute_step` evaluation is a typed provider call binding
  principal → action → resource → scope; ALLOW / DENY / REQUIRE_APPROVAL /
  ALLOW_WITH_CONSTRAINTS become operational (WAITING_POLICY + durable
  AuthorityRequest; DENY = POLICY_DENIED failure); the `authority_ok`
  bypass is removed; test gate provided for deterministic qualification.
- **P2-R2-C02** — approval → execution round trip: REQUIRE_APPROVAL persists
  an exact-scope AuthorityRequest, step waits in WAITING_POLICY, an operator
  GRANT (bound to the request's exact action/resource/scope/budget) releases
  the step to READY; deny/expiry/mismatched grant cannot execute.
- **P2-R2-C03** — crash/recovery re-evaluation through the real provider:
  resumed execution re-evaluates authority, so policy changes between crash
  and resume affect the resumed run; committed/idempotent execution records
  are preserved untouched by re-evaluation.
- **P2-R2-C04** — canonical `JobSubmission` validation record +
  `QcaeApp.job_submit` + CLI `qcae job submit`; durable submission across
  CLI process close; no partial persistence (reuses the C07R3 atomic path).
- **P2-R2-C05** — remove private-attribute leaks: `RuntimeService.mark_running`
  public method replaces `QcaeApp`'s use of `service._engine`; registered
  worker ids exposed via `engine.registered_worker_types()` replacing
  `engine._workers` inspection; architecture guard test added.
- **P2-R2-C06** — authority × budget × secrets integration: authority cannot
  widen budget, action permission does not imply secret permission,
  constrained grants remain constrained.
- **P2-R2-T01** — governance adversarial qualification: DENY, approval
  mismatch/replay/expiry, unknown principal, unknown requirement, crash +
  changed policy, budget escalation, secret escalation, CLI bypass attempts,
  full regression.
- **P2-R2-FREEZE** — superseding freeze manifest (P2 and P2-R1 manifests
  preserved), fail-closed test capture, ledger update.

### P2-R3 — Operator Loop + Recovery + Identity Closure (SEALED at `6f0218c0`)

All five findings closed with narrow commits, plus a real-surface acceptance
harness (the class of gap the unit suite cannot see):

- **I0 `6f0218c0`** — findings A–E + repair law recorded (this entry).
- **C01 `07626a08`** — lifecycle truth: submit commits QUEUED (JOB_CREATED +
  JOB_QUEUED exactly once, committed truth returned), granted lease promotes
  RUNNING, finalizer reachable from any live state, JOB_SUCCEEDED exactly
  once, empty graphs refused.
- **C02 `7ac5b80f`** — typed `WorkerUnavailableError` BEFORE any claim/state/
  attempt/budget/STEP_STARTED; per-step coverage; CLI exit 3 structured, no
  traceback; no default worker added (P3 supplies real workers).
- **C03 `66abe540`** — one recovery law (`recover_leased_steps`): TTL-checked
  job-scoped expiry → READY (replay-safe) / COMMITTED finalized (never
  replayed) / WAITING_INPUT (non-replay-safe ambiguity); orphan RUNNING
  classified; active leases never stolen by recover or resume; both CLI
  surfaces delegate to the same law.
- **C04 `50256c6b`** — identity wired at composition root; unknown principals
  refused before claim (policy string-match confers nothing); claim principal
  == execution principal enforced.
- **C05 `f3ceec59`** — CLI stable exit codes 2/3/4 with structured stderr;
  programming errors still traceback; recovery surfaces converge.
- **A01 `c7fa5744`** — acceptance harness `qcae/tests/acceptance/
  test_p2_operator_loop.py`: five journeys over real SQLite + subprocess CLI
  (lifecycle+restart, CLI no-worker, crash/TTL recovery, identity
  fail-closed, approval deny); evidence emitted to
  `P2-R3-operator-acceptance.json`.
- **T01 `205b7b46`** — 14 adversarial cases (lease theft, idempotent
  convergence both orders, orphan classification, committed no-replay,
  ambiguity escalation, no-worker tracelessness, identity matrix, terminal
  truth, CLI no-traceback).
- **FREEZE `6f0218c0`** — `P2-R3-freeze-manifest.json` superseding manifest
  (preserves P2/P2-R1/P2-R2 manifests with digests) sealed by the fail-closed
  generator (`p2r3_freeze_manifest.py`): **1060 collected / 1060 passed /
  0 failed / 0 skipped** (LOCAL TEST EVIDENCE, tested commit `6f0218c0`).
  Blockers `[]`; design debt parked (MINOR) with P10 trigger.

### P2-R2 — Governance-Wiring Repair Tranche (SEALED at `4395aaa8`)

Post-freeze live operator testing of the P2-R2 head exposed a class of defect
the 1000-test suite could not see: every internal subsystem passed, but the
real operator journey was broken. Operator findings, all confirmed by audit:

- **Finding A (job finalization)** — natural `submit → job run → job run`
  left every step SUCCEEDED while the durable job stayed CREATED forever;
  no JOB_SUCCEEDED. The finalizer only fired from an already-RUNNING job and
  nothing promoted the job on the run path.
- **Finding B (worker availability)** — `job run` created a lease, moved the
  step RUNNING, then discovered no worker existed and raised a raw traceback,
  stranding the lease. The composition root registered no workers at all.
- **Finding C (recovery surface split)** — global recovery deleted expired
  queue claims but left the durable step RUNNING; resume could no longer tell
  which RUNNING steps came from expired leases. Orphan RUNNING steps (no
  claim) were silently ignored.
- **Finding D (active-lease preemption)** — `recover_job` force-expired claims
  for ALL RUNNING steps regardless of TTL; recovery could steal a live lease.
- **Finding E (unknown principal)** — policy `principal_match="id-*"` matched
  unregistered strings; identity existence was never proven before lease or
  execution; claim and execution principals were not bound.

Repair law: one authoritative recovery owner; worker availability before any
ownership mutation; identity before availability (request → identity →
policy → authority → budget → queue → worker); lifecycle truth (snapshot and
event stream must agree); CLI expected errors are typed, never tracebacks.
Design debt (774-line engine, façade consolidation, test gates in production
module) is RECORDED and DEFERRED to P10 preparation — not this tranche.

### P2-R2 — Governance-Wiring Repair Tranche (SEALED at `4395aaa8`)

All six operator-directed repairs committed as narrow tranche commits:

- **I0 `30cebe27`** — audit findings + repair plan recorded.
- **C01 `407b7de9`** — `StepAuthorityGate` port + typed verdicts wired into
  `execute_step`; `authority_ok` bypass removed; fail-closed default gate;
  composition root wires the policy-backed gate + approval sink; runtime
  worker principal is a registered identity; policy action matcher fixed.
- **C02 `7f6bccb7`** — durable exact-bound AuthorityRequests with explicit
  approval windows; verified grant release (deny/expiry/mismatch/forged
  cannot release; laundering rejected at write AND service-side).
- **C03 `e93f41dd`** — recovery re-evaluates the LIVE gate; committed
  execution records untouched; terminal steps never re-leased.
- **C04 `3a7783ea`** — canonical `JobSubmission` (validate-before-persist)
  + `QcaeApp.job_submit` + durable CLI `job submit`.
- **C05 `4b88cbd7`** — private-boundary leaks removed; public service/engine
  interfaces; self-verifying `TestInterfaceBoundary` architecture guard.
- **C06 `f1e02304`** — authority cannot widen budget; action permission ≠
  secret permission; constrained grants stay constrained across retries.
- **T01 `8e8b9431`** — 17 adversarial governance scenarios, all fail-closed.
- **FREEZE `4395aaa8`** — `P2-R2-freeze-manifest.json` sealed by the
  fail-closed generator (`p2r2_freeze_manifest.py`) with captured results:
  **1000 collected / 1000 passed / 0 failed / 0 skipped** (LOCAL TEST
  EVIDENCE, tested commit `4395aaa8`). P2 and P2-R1 manifests preserved
  unchanged; blockers `[]`.

### P2 — Job Runtime + Local Governance (opened)

Operator authorization received after P1-R1 freeze (`4f3ec2f6`). Scope per
operator directive: durable jobs/steps with explicit state machines, job
directed graph, durable queue with safe leases, local identity/policy/
authority (Book V 13.2), approval + escalation workflow, Context Packets,
typed worker contracts (Book V 12.3), bounded retries + checkpoints + crash
recovery, budgets, SecretProvider boundary + redaction, standalone runtime
service, CLI, P1→P2 schema migration, backup/restore extension, adversarial
runtime qualification. OCE stays absent (Book V 13.8).

Milestone plan (narrow commits):

- P2-I0 — ADR-0008 (runtime state vocabulary, additive over frozen P0
  identity layer per Book V 13.6) + ADR-0009 (13.2 policy decisions vs P0
  authority outcomes mapping) + schema plan
- P2-C01 — job/step runtime domain + fail-closed state machines
- P2-C02 — job graph + durable job/step/event/checkpoint repositories
- P2-C03 — durable queue + lease ownership
- P2-C04 — local identity + policy engine + authority provider (ADR-0009)
- P2-C05 — approval + escalation workflow
- P2-C06 — Context Packet + WorkerRequest/WorkerResult contracts
- P2-C07 — checkpoint + bounded retry + crash recovery
- P2-C08 — budget representation + enforcement/conservation
- P2-C09 — SecretProvider + central redaction
- P2-C10 — standalone runtime service (submit/run/resume/cancel/recover)
- P2-C11 — CLI + application service boundary
- P2-C12 — schema migration v3→v4 + backup/restore extension
- P2-T01 — adversarial runtime qualification
- P2-FREEZE — freeze manifest with captured test evidence (P1-R1 mechanism)

### P2-R1 — Runtime Repair Tranche (supersedes original P2 freeze bookkeeping)

Operator review of `21bc4466` accepted C01–C06 and accepted C07 in concept
with four required repairs. The original P2 freeze artifact
(`4cca8729`) is preserved unchanged as historical truth; superseded by
`qcae/implementation/P2-R1-freeze-manifest.json` whose `test_results` are
captured from an actual full-suite run by the fail-closed generator
(`qcae/implementation/tools/p2r1_freeze_manifest.py`).

Repairs (no redesign of accepted subsystems):

1. **C07R1 `425ac5f6`** — job-scoped atomic queue claim: eligibility moves
   inside the atomic claim selection; a worker can never own an ineligible
   step; empty eligibility writes no claim rows; lost races fall through.
2. **C07R2 `3b5aaed0`** — durable execution semantics: ExecutionRecords
   (RESERVED→EXECUTING→COMMITTED/FAILED/ABANDONED) with result payloads
   close the crash window between effect and marker; ReplaySafety classes
   (REPLAY_SAFE / IDEMPOTENCY_AWARE / NON_REPLAY_SAFE); ambiguous
   non-replay-safe outcomes escalate to WAITING_INPUT + operator resolution,
   never a blind rerun; orchestrator claims at-least-once + durable dedup,
   never exactly-once. Crash windows A–G tested.
3. **C07R3 `bfead6f6`** — atomic submission: job + steps + initial events
   + queue metadata commit in one BEGIN IMMEDIATE..COMMIT; failure injection
   after any write rolls back to no partial state.
4. **C07R4 `acf31b6f`** — store-owned identity: event_seq/event_id and
   checkpoint ids allocated by the runtime store; orchestrator holds no
   counters and no `_conn`; architecture guard `TestRuntimeStoreBoundary`
   forbids store-internal access and table-name knowledge.
5. **C07RT `cb1cede4`** — combined crash/concurrency/adversarial suite
   proving the four repair laws together across restarts.
6. **C11 gap closure `6ea6dcef`** — job events, recover, approval decide
   (immutable decisions, no laundering), durable CLI sessions that commit
   before close; canonical local operator identity (Book V 13.1).
7. **Coverage closure `ac0dd3c2`** — concurrent budget reservation cannot
   overdraw; policy change between crash and resume forces authority
   re-check; event append concurrency; worker-contract boundary violations
   rejected.

**P2-R1 freeze evidence:** `python -m pytest qcae/tests -q` → 921 collected /
921 passed / 0 failed / 0 skipped (LOCAL TEST EVIDENCE, captured by the
generator at tested commit `ea493b8e`).

### P1-R1 — Registry Completion + Freeze Truth Repair (supersedes original P1 freeze bookkeeping)

Operator review of `bbbe05a7` identified three exit-gate defects; repaired in
P1-R1 without redesigning any accepted P1 subsystem:

1. **Freeze truth** — original `P1-freeze-manifest.json` had
   `test_results: null`. Preserved byte-for-byte (blob `ab9ab86e…`, introduced
   in `20ee6465`); superseded by `qcae/implementation/P1-R1-freeze-manifest.json`
   whose `test_results` are captured from an actual full-suite run by the
   fail-closed generator (`qcae/implementation/tools/p1r1_freeze_manifest.py`
   + `test_evidence.py`). Generator refuses to emit on test failure,
   unparseable output, or commit mismatch. Counts are never hardcoded.
2. **Canonical status** — this ledger now reads P1 — FROZEN /
   OPERATOR-REVIEWED; P2 is not active.
3. **Registry substrate** — CapabilityRegistry (contracts/atoms/composites/
   candidates, versioned keys, digest-verified rows) and provider-neutral
   RepositoryRegistry added in P1-R1-C01/C02; linked via the frozen P0
   Relationship vocabulary (no new edge types); backup/restore covers all
   registry tables with count verification; decision-reuse exposes known
   capability/candidate state; RepositoryRegistry deferral removed from the
   superseding freeze (P3 populates it).

P1-R1 repair commits: `34d256bf` (I0), `9a990a85` (C01), `53106b1f` (C02),
`e3059465`+`31e5ba20` (C03), `7d541a97` (C04), `1817ed57` (C05), `a8ea1014`
(T01), `7fbf5326`+freeze-commit (FREEZE).

### P1-R1 continuation — repository identity/revision repair (reviewed head `31e5ba20`)

Operator review of the first P1-R1 tranche identified one remaining
registry defect: `PRIMARY KEY(repository_id)` contradicted the documented
multi-revision model. Resolved with **ADR-0007** and schema migration v2→v3:

- **Repository identity** = stable `repository_id` (source container);
  **revision identity** = immutable `repository_revision_id`
  (`<repository_id>@<revision>`) with content digest. One identity → many
  immutable revision records; a new commit SHA is never a new repository.
- **"Latest observation"** uses explicit observation metadata, never
  revision-string lexical order (Git SHAs are not chronological).
- **Candidate identity** resolved per §6: `candidate_id` names one immutable
  revision record; new revision = new record (no update path) — pinned by
  test.
- **Relationship edges are revision-scoped**: revA implements X, revB
  implements X+Y, revC implements none coexist without rewriting history.
- **Decision reuse** extended: repository revisions behind known candidates;
  structured A–F internal-first findings (CAPABILITY_ACTIVE,
  EVIDENCE_STALE, CANDIDATE_PREVIOUSLY_FAILED, REVISION_CHANGED,
  DEFINITION_WITHOUT_IMPLEMENTATION, NO_INTERNAL_KNOWLEDGE).
- **Backup/restore** carries full revision history; restore verifies both
  observation records of one identity.
- **Parser robustness**: warnings-summary and deselected tails parse;
  collection errors (singular/plural) refuse freeze.

Continuation commits: `a69baaa8` (C03R + ADR-0007 + migration v3),
`2dd94b85` (C03R2), `47f8f067` (C04R), `0a3bd46b` (C05R), `d9a92e5f`
(T01R), `92547ac1` (FREEZE generator update).

**Final freeze evidence** (regenerated at `92547ac1` by the fail-closed
generator, LOCAL TEST EVIDENCE): `python -m pytest qcae/tests -q` →
**646 collected, 646 passed, 0 failed, 0 skipped, 3.39s** at tested commit
`92547ac1374a…`.

### P1 phase log (original build; superseded bookkeeping per P1-R1 above)

- **P1-I0** `a53b401b` — preflight repairs (ledger test-count 139→141 via
  addendum, vacuous `or True` assertion removed) + **ADR-0006**: SQLite
  (stdlib) metadata engine behind ports; DuckDB declined for OLTP (analytics
  deferred); raw artifacts content-addressed on filesystem.
- **P1-C01** `d5e8882e` — evidence object model: EvidenceObjectType vs
  EvidenceClass kept as separate axes (Book IV 9.1), structured ScopeDimensions,
  FreshnessState, raw/interpretation partitioning.
- **P1-C02** `6890f852` — content-addressed artifact store (sha256,
  `sha256/ab/cd/<digest>` layout, atomic writes, retrieval verification,
  collision/corruption/traversal guards).
- **P1-C03** `93b7a1ea`/`090e7edc`/`f113c396` — persistence ports (core) +
  SQLite adapter (infrastructure): digest-verified rows, INSERT-only factual
  tables, append-only freshness log, forward-compat guard, sqlite3 denial
  scoped to infrastructure only.
- **P1-C04** `01a31a69` — lineage edge store: 9.5 vocabulary, contradiction
  coexistence (no resolution-by-deletion API), idempotent edges.
- **P1-C05** `3aaddeea` — Capability Receipt (9.2): 6 states, scope-bounded,
  authority + rollback required, proof firewall (external-only evidence can
  never satisfy executable proof).
- **P1-C06** `07475b2d` — positive/negative knowledge (9.3/9.4): 11 failure
  categories, causal-detail minimum, mandatory reconsideration conditions,
  material knowledge evidence-linked (notes are non-material).
- **P1-C07** `e59632e7`/`a498a955`/`70c6b306` — knowledge/receipt repositories
  + structured decision-reuse query implementing the 9.7 retrieval order
  (active receipts → positive knowledge → negative blocks → stale evidence →
  external discovery).
- **P1-C08** `e8cfb720` — A-001 cross-registry persistence: ExternalRegistryRef
  durable, owner-domain immutable (laundering rejected), OBSERVE/SUBMIT only.
- **P1-C09** `04983524` — UnitOfWork (BEGIN IMMEDIATE, rollback on any
  failure, no nesting) + atomic evidence+lineage commit service; WAL isolation
  across connections verified.
- **P1-C10** `55ba326d` — migration framework: forward-only runner keyed by
  target version, ledger with pre/post schema digests, v1→v2 mechanism proof,
  rollback and refusal behaviors verified.
- **P1-C11** `772ab794`/`da69813d` — backup/restore: consistent SQLite
  snapshot + flat artifact copies + manifest with digests; restore verifies
  every digest before declaring success (full-cycle exactness tested).
- **P1-T01** `ba9c3e35` — adversarial suite: payload/digest tampering,
  append-only pressure across all stores, restart persistence of the whole
  spine, evidence→receipt firewall chain, classification flow-through.
- **P1-FREEZE** `20ee6465` — `qcae/implementation/P1-freeze-manifest.json`
  (559/559 LOCAL TEST EVIDENCE).

### P1 exit gate (spec §25)

| Criterion | Status | Evidence |
| --- | --- | --- |
| durable local structured persistence | PASS | SQLite adapter + restart tests |
| raw evidence content-addressed, integrity-checked | PASS | test_p1_artifact_store, adversarial binding test |
| evidence provenance-linked, raw/interpretation separate | PASS | EvidenceArtifact validation + lineage store |
| receipts scope-bounded, firewall enforced | PASS | test_p1_receipt |
| positive knowledge evidence-linked | PASS | material flag enforcement |
| negative knowledge durable/searchable | PASS | subject/revision/type retrieval |
| contradictions/lineage preserved | PASS | contradiction coexistence tests |
| cross-registry provenance without ownership collapse | PASS | owner-rewrite rejection, rights visibility |
| transactions rollback correctly | PASS | injected-failure rollback tests |
| schema version/migration mechanism works | PASS | v1→v2 migration + ledger evidence |
| backup restored successfully in test | PASS | full-cycle exactness test |
| registry survives process restart | PASS | complete-spine restart test |
| retrieval detects reusable internal knowledge | PASS | decision-reuse findings tests |
| no provider SDK / Research Mesh / OCE in core | PASS | architecture guards incl. self-verifying engine-free guard |
| all QCAE tests pass | PASS | 559/559 (LOCAL TEST EVIDENCE) |
| ledger + manifest current | PASS | this file + P1-freeze-manifest.json |
| no unresolved high-severity deviation | PASS | deferred items in manifest are MINOR, trigger-tagged |

## Historical: P0 — FROZEN v0.1 + A-001 RECONCILED

### Amendment reconciliation timeline

1. **P0 original freeze** at `6d23c956` (270/270 LOCAL TEST EVIDENCE; manifest
   `qcae/implementation/P0-freeze-manifest.json` — preserved, not overwritten).
2. **A-001 landed** on the branch (`docs(qcae)` commits:
   `66e99505`, `6d98193c`, `a399f525`, `281d1aa9`) — additive amendment register,
   Research Mesh boundary, ResearchCapabilityHandoff + EconomicExperienceRecord
   interface schemas.
3. **P0 amendment reconciliation opened** per operator directive (reconcile
   A-001 §13 P0 obligations; repair reviewed ambiguities).
4. **Reconciliation commits** `983a742e` → (see commit log below).
5. **Amendment tests added** (141 new tests across vocabulary, handoff,
   economic/cross-registry, contract repair, deferred semantics, schema drift;
   count corrected from an earlier 139 transcription error during P1-I0 —
   composition arithmetic in the freeze manifest: 20+31+25+34+7+22 = 139 unit
   + 2 Research Mesh architecture guards = 141).
6. **New freeze** — `qcae/implementation/P0-A001-freeze-manifest.json`
   (411/411 LOCAL TEST EVIDENCE).

### P0-A001 exit gate (reconciliation prompt §17)

| Criterion | Status | Evidence |
| --- | --- | --- |
| all active amendments registered | PASS | A-001 in manifest `active_amendments`; register read in full |
| A-001 P0 obligations have domain/interface representation | PASS | gap taxonomy, resolution vocabulary, handoff contract, EconomicExperienceRecord, ExternalRegistryRef |
| original P0 semantics remain compatible | PASS | all 270 original tests pass unmodified except one terminal-set assertion updated by ADR-0004 (documented, not weakened) |
| no Research Mesh implementation leaked into core | PASS | 2 new architecture guards + fragment scan; interface contracts only |
| no economic/marketplace authority added | PASS | no execution/revenue/mutation code; reference records only |
| customer payment/acceptance cannot become institutional proof | PASS | firewall tests (promotion requires governed refs; PROMOTED requires citation) |
| client-protected material fail-closed | PASS | PROMOTED + protected-rights pre-RIGHTS_FILTERED rejection tests |
| DEFERRED ambiguity resolved | PASS | ADR-0004 interpretation A; consistency tests |
| CapabilityContract validation repair complete | PASS | request_id + all string-tuple fields validated; 34 negative tests |
| schema/interface drift guard exists | PASS | test_p0_a001_schema_drift.py (ADR-0005), self-verifying |
| all qcae tests pass | PASS | 411/411 (LOCAL TEST EVIDENCE) |
| amendment-aware freeze manifest exists | PASS | P0-A001-freeze-manifest.json |
| progress ledger current | PASS | this file |
| no unapproved canon deviation | PASS | ADRs 0003–0005 documented; none contradict canon |

### P0 Checklist — COMPLETE

- [x] P0-I0 progress ledger + implementation decision records (`e1fda033`)
- [x] P0-C01 package skeleton per Book V 15.1 + test wiring (`64b31511`)
- [x] P0-C02 base error taxonomy + schema-versioned serialization base (`22cc49ba`)
- [x] P0-C03 LifecycleState machine + transition guards (canon 0.5) (`42a94352`)
- [x] P0-C04 CapabilityContract (canon 1.1.4 fields, versioning, req/pref/forbidden) (`450308eb`)
- [x] P0-C05 CapabilityAtom (1.2.22), CompositeCapability (1.2.10–11), Candidate (`7451466e`)
- [x] P0-C06 Relationship (1.3.4), EntityRef (1.3.3/1.3.16), EvidenceRef (0.4.2/0.4.3) (`9acd4d2f`)
- [x] P0-C07 AcquisitionDecision (0.5.12), Authority primitives (0.3), Job/Step identity (`102c3c5c`)
- [x] P0-T01 architecture/dependency guard tests (canon 15.2 forbidden deps) (`7ad5277c`)
- [x] P0-FREEZE freeze manifest + full suite green + ledger current

### P0 Exit Gate Evidence (canon 18.2 + master prompt §28)

| Criterion | Status | Evidence |
| --- | --- | --- |
| core package structure exists | PASS | Book V 15.1 tree, topology test (`test_p0_topology.py`) |
| canonical domain objects exist | PASS | 13 versioned record classes (see freeze manifest schema snapshots) |
| schemas are versioned | PASS | `SCHEMA_VERSION` envelope, fail-closed readers, manifest `schema_snapshot_digest` |
| lifecycle rules explicit | PASS | `core/lifecycle/state.py` single authority; 44 transition tests |
| serialization works | PASS | round trips incl. schema-version rejection, unknown-key rejection |
| all P0 tests pass | PASS | 270 passed / 0 failed / 0 skipped |
| no provider leaked into core | PASS | guard-tested: stdlib-only, sqlite3 denied, higher-layer import denied, self-verifying scanner |
| progress ledger current | PASS | this file |
| deviations from canon | NONE | derived points documented below, none contradict canon |
| coherent for P1 | PASS | evidence-ref + digest primitives are the exact substrate P1 needs |

---

## Commit Log

### P0 original freeze (pre-A001, preserved)

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| e1fda033 | P0-I0 | progress ledger + ADR-0001/0002 |
| 64b31511 | P0-C01 | package skeleton + test wiring |
| 22cc49ba | P0-C02 | error taxonomy + serialization base |
| 42a94352 | P0-C03 | lifecycle machine + transition guards |
| 450308eb | P0-C04 | capability contract domain |
| 7451466e | P0-C05 | atoms + composites + candidates |
| 9acd4d2f | P0-C06 | relationships + evidence refs |
| 102c3c5c | P0-C07 | acquisition decisions + authority + job/step |
| 7ad5277c | P0-T01 | architecture dependency guards |
| 6d23c956 | P0-FREEZE | freeze manifest + ledger freeze state |

### P0-A001 reconciliation (additive)

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| 983a742e | P0-A001-01 | gap taxonomy + economic resolution vocabulary |
| 69b347ef | P0-A001-02 | Research Mesh handoff contract |
| 6eee5fb8 | P0-A001-03 | Economic Experience + cross-registry refs + ADR-0003 |
| 16bb5229 | P0-A001-04 | CapabilityContract validation repair |
| 74993b67 | P0-A001-05 | DEFERRED semantics resolution (ADR-0004) |
| 24d3364c | P0-A001-T02 | schema drift guard + Research Mesh isolation guards (ADR-0005) |
| d82f727f | P0-A001-T02 | malformed provenance rejection tests |
| (this commit) | P0-A001-FREEZE | amendment-aware manifest + ledger freeze state |

---

## Test Ledger

All rows are LOCAL TEST EVIDENCE (`python -m pytest qcae/tests -q`).

| Suite | Tests | Passed | Failed | Skipped | Commit |
| --- | --- | --- | --- | --- | --- |
| qcae/tests (P0 original freeze) | 270 | 270 | 0 | 0 | 6d23c956 |
| qcae/tests (P0 + A-001 reconciliation) | 411 | 411 | 0 | 0 | P0-A001-FREEZE |

Composition: 255 unit + 15 architecture guards.

Important adversarial tests delivered (master prompt §27 mapping):

- illegal lifecycle transition rejected (parametrized across 20+ illegal edges) — `test_p0_lifecycle.py`
- waivable gate (DOMAIN_VERIFIED only) rejected without policy justification — `TestIllegalTransitions::test_gate_skip_without_waiver_rejected`
- contract with behavior both required and forbidden rejected — `test_p0_contract.py`
- contract with empty required behaviors / acceptance / evidence rejected
- atom identity independent of implementation — `test_p0_capabilities.py`
- composite single-member ALTERNATIVE, REQUIRED-in-ALTERNATIVE, only-OPTIONAL, empty, duplicate members rejected
- relationship with type outside controlled vocabulary rejected; direction violations rejected (implements reversed, contained_in non-repo, supersedes cross-type…)
- evidence ref with malformed artifact hash rejected
- schema-version mismatch / unknown object type / unknown field rejected on deserialize
- core importing forbidden provider module fails the architecture guard (scanner self-verified against synthetic violating trees, including relative-escape and dynamic `__import__`)

Pre-existing failure outside QCAE (not introduced by this work, verified identical before P0): `tests/forge/phase_00/test_extension_docs.py` — 2 failures on this branch.

---

## Evidence Artifacts (canon 18.3 Phase 0 matrix + reconciliation §10)

- [x] schema snapshots (22: 13 original + 9 amendment) — both freeze manifests
- [x] lifecycle transition tests — `qcae/tests/unit/test_p0_lifecycle.py`, `test_p0_a001_deferred.py`
- [x] architecture/dependency guards — `qcae/tests/architecture/test_p0_dependency_guards.py`
- [x] serialization round-trip evidence — `qcae/tests/unit/test_p0_serialization.py`, `test_p0_contract.py`, A-001 contract tests
- [x] P0 freeze manifest (preserved) — `qcae/implementation/P0-freeze-manifest.json`
- [x] P0-A001 amendment-aware freeze manifest — `qcae/implementation/P0-A001-freeze-manifest.json`
- [x] ADRs — 0001/0002 (original), 0003 (vocabulary layering), 0004 (DEFERRED), 0005 (drift guard)

---

## Implementation Decision Records

- ADR-0001 — core domain: stdlib dataclasses + explicit validation; zero third-party dependencies in `qcae/core`
- ADR-0002 — `qcae/` package at repo root per Book V 15.1; tests under `qcae/tests/`; root pytest config extended
- ADR-0003 — two-layer acquisition vocabulary: CapabilityResolutionMode (institutional) over AcquisitionForm (implementation); no silent replacement
- ADR-0004 — DEFERRED is terminal for that decision/version; resumption = superseding object (canon 0.5.15 + Book IV 11.6)
- ADR-0005 — amendment interface-schema drift guard via explicit compatibility assertions; no new dependencies

Location: `qcae/implementation/decisions/`

---

## Unresolved Questions / Derived Points (for operator review)

1. **Lifecycle branches derived from canon 0.5** (documented in `core/lifecycle/state.py` module docstring): candidate culling (REJECTED/DEFERRED) permitted from CANDIDATE…ACQUISITION_CANDIDATE; REVIEW_REQUIRED → MONITORED return; REJECTED/SUPERSEDED/RETIRED terminal. Localized change if operator wants different branch legality.
2. **Waivable gate set = {DOMAIN_VERIFIED}** (canon 0.5.10). Enforced strictly: waivers on edges that need none are rejected.
3. **VerificationLevel enum** uses canon 1.3.13 (DISCOVERED…DOMAIN_VERIFIED); master prompt §8's illustrative set is superseded by canon per master prompt §0.
4. **AtomStatus values** (PROPOSED/ACTIVE/DEPRECATED/RETIRED) are a P0 derivation — canon 1.2.22 leaves `status` unvalued. Revisit at P5; field is versioned, additive change is safe.
5. **Job/Step statuses** minimal identity contracts; P2 job runtime (Block 12/13 chapters to be read before P2) may extend additively.
6. **NegativeKnowledge, Evaluation, CapabilityReceipt, MonitoringRecord** intentionally not in P0 (P1/P5/P8 scope per 18.1); their substrates (EvidenceRef, Relationship, digests) exist.
7. **Relationship endpoint-role constraints** are deliberately conservative (load-bearing edges only: implements/composed_of/contained_in/depends_on/normalized_as/supersedes); extend as P4+ refines canon semantics.

## Deviations from Canon

None. All derived points above refine within canon; none contradict a frozen invariant.

## Blockers

None.

## Next Action

P0 — FROZEN v0.1 + A-001 RECONCILED. Awaiting operator authorization for **P1 — Evidence + Registry Spine** (canon 18.1 Phase 1: artifact hashing/store, structured persistence, provenance relationships, Capability Receipts, negative knowledge, repositories/unit-of-work, migrations, backup/restore; plus A-001 §13 P1 obligation: cross-registry provenance without collapsing knowledge/capability ownership). Book IV Block 9 chapters + A-001 to be read before P1 starts.
