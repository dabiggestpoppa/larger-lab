# OCE Stress Suite — Research Dossier: OPH × IT³ Diagnostic (Path M)

**Document ID:** `OCE_STRESS_SUITE_RESEARCH_DOSSIER_OPHIT3_DIAGNOSTIC_v0.1`
**Version:** `0.1` · **Status:** `PROPOSED — FOR OPERATOR REVIEW` · **Not ratified. No code authorized.**
**Date:** 2026-09-24
**Branch:** `agent/oce-institutional-stress-suite-build`
**Frozen dependency (proposed):** `92a99d5448e417473a5d00c24a3fe75cabca30a7` (ancestor `121bacd5 ⊳ c43c6c26 ⊳ ef30cb49 ⊳ 31c68da2 ⊳ 2cf1bb4b961`)
**Parents:** `OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md` · `OCE_MASTER_PROGRAM_ATLAS_v1.0.md §2.4` · `OCE_STRESS_SUITE_SCENARIO_CATALOG_v1.0.md` · `OCE_OPH_IT3_AUTHORIZATION_DECISION_PACKET_v0.3` (supersedes v0.2) · `OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2` (v0.3 patch) · `OCE_OPH_IT3_INGESTION_PACKET_2026-09-23.md` (external, unratified) · `stress-suite/evidence/G8_RESULT.md` + `G8_EVIDENCE_RECEIPT.json` + `G8_TEST_RESULTS.xml` (`tested_sha 2cf1bb4b6bc39b2a372851a02ec50d96758a8788`, `raw 23f97af88ff31c0e / canonical 6fa5005e1d26dd32`)
**Scope class:** Diagnostic, nonauthoritative, non-promotional research substrate. Not G9. Not an A012 ratification. Not a Block 2–10 increment.
**Authorization model (proposed):** Path M — narrow operator-ratified dossier + explicit stress-suite branch authorization under the existing stress-suite execution contract (`G0–G10`). See Decision Packet v0.3 §2/§9 and Appendix A. **If ratified, this dossier itself does not authorize code** — a separate explicit operator authorization tied to this ID and frozen dependency is required before any implementation commit.

> **Planning-only box.** This file is a proposal. No `AUTHORIZED_STAGE`, no gate, and no dossier ratification is claimed. No A–H code, schema, test, or receipt is produced by this commit. The next step is operator review. If the operator ratifies, a separately authorized agent may implement exactly Increment 1 on this same branch — and only that — per §7. No other file is amended by approving this dossier unless the operator says so.

---

## 1. Purpose — what this dossier is and is not

* **Is:** a bounded proposal to exercise one existing deterministic stress-suite workflow through a frozen confluence experiment that reuses the current harness (`DeterministicReplay` + governed engines) and adds only the minimum logic needed to test schedule-independent public normal forms honestly.
* **Is not:** a promotion claim, a physics endorsement, a G9 invariant extraction, a production or capital change, or a precedent for silently expanding `stress-suite/engine` authority.
* **Success is still diagnostic:** the best outcome is a measured `CONFLUENCE_VERIFIED` or a minimized, attributable `CONFLUENCE_FAILURE` — both rank below `PROMOTED` in the claim ladder and remain `DIAGNOSTIC`.

The decision record at the end names the exact frozen dependency and the separate authorization that would be required. Until both exist, every agent on this branch stays `HOLD`.

---

## 2. Controlling rules — quoted

### 2.1 `OCE_MASTER_PROGRAM_ATLAS_v1.0.md §2.4`

> A ratified dossier authorizes only the scope it explicitly defines.

### 2.2 `docs/oce-golden-system/README.md:34`

> Planning completion is not build completion. Only an exact operator-provided `AUTHORIZED_STAGE=B<n>-I<m>` plus its ratified dependency authorizes an implementation increment.

*Context.* The sentence's immediate context is the `docs/oce-golden-system` Block→Chapter→Section hierarchy (B0–B10). It contains no explicit scoping phrase that says "this rule governs every branch including nonauthoritative diagnostic research." Its scope must be read from context, not inferred. See Decision Packet v0.3 §2 for the explicit-vs-inferred analysis and the unresolved boundary.

### 2.3 `OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md §5` (Stop conditions)

> The implementation agent MUST stop and report rather than self-repair architecture when: … a required authority boundary is ambiguous; … current repo contracts make the planned test dishonest; … a domain scenario requires information not currently supported by authoritative materials …

An ambiguous authority boundary is a stop — the agent reports it, it does not self-select B11 or invent a stage.

### 2.4 `stress-suite/evidence/G8_RESULT.md:72`

> `PASS_G8_CROSS_SCENARIO_COHERENCE` → next eligible gate: **G9 — NOT AUTHORIZED**.

---

## 3. Authority posture — proposed Path M interpretation

This dossier advances the **Path M** reading described in Decision Packet v0.3 §9.2 as a *proposed interpretation* of the existing contracts, not as already ratified. The proposal:

* A ratified dossier that explicitly defines diagnostic, bounded scope satisfies `Atlas §2.4` for that scope.
* The stress-suite tract has an independent gate surface: `G0–G10`, granular `STRESS-G{n}` commits, artifact-derived `tested_sha`, and `PASS_G8` at `2cf1bb4b` — all produced and accepted **without** a `B<n>-I<m>` dispatch for this branch (verified history: `121bacd5 ⊳ … ⊳ 2cf1bb4b`).
* A narrow, non-`B<n>-I<m>` explicit branch authorization tied to this dossier ID and frozen dependency can therefore authorize one bounded diagnostic increment on `agent/oce-institutional-stress-suite-build` without contradicting any quoted clause — *unless* the operator determines that `README.md:34` universally governs this branch (see §3.1 and Appendix A).

### 3.1 The one clause that would forbid Path M, if read that way

> `README.md:34` — `Only an exact operator-provided AUTHORIZED_STAGE=B<n>-I<m> plus its ratified dependency authorizes an implementation increment.`

If the operator determines this sentence must be read as covering every implementation increment on this branch — including nonauthoritative, branch-local diagnostic research — then Path M is forbidden and the grammar-amending Path G is required. **No other file supplies a more specific forbidding clause;** see Appendix A. The operator should record that determination before B11 is created. This proposal does not create B11 by default.

### 3.2 If Path M is not forbidden — what the operator would still need to record

Ratification of *this* dossier **plus** a separate explicit operator authorization naming this ID and frozen dependency and the exact increment. The dossier alone authorizes nothing.

---

## 4. Out of scope — postponed A–H blocks

**This dossier proposes only one bounded confluence experiment (Block B) plus the minimum Block A ledger view to report it honestly.** The following are explicitly **deferred to separately authorized future increments** — the agent must not implement them as part of Increment 1:

| Deferred block | One-line summary | Deferred to |
|---|---|---|
| D — `ReductionArena` (four-reducer adversarial bench on one stream) | Continuous baseline, clustering, IT³ quantizer, OPH repair; held-out scoring; `OPERATOR_INDUCED` / `CROSS_METHOD_ROBUST` | Future increment 2+, separate dossier amendment or new dossier |
| C — `InvariantQuotientSpec` (`protected/nuisance` quotient invariant) | Quotient-visible protected data while presentation varies | Future increment |
| E — `TransferInvariantMap` preservation predicates (`preserved_operations / overlap / order / normalization / refinement`) | `ANALOGY_ONLY` vs `STRUCTURALLY_SOUND` with witness | Future increment |
| F — `FrozenPredictionCustody` prospective custody (`eligible_data_cutoff`) | Needs trusted time/lineage witness; see §6.4 correction | Outside all of Increment 1; remains `CUSTODY_UNVERIFIED` |
| G — `CountermodelGenerator` beyond confluence minimization | Null-model competition for universal claims | Future increment |
| H — `ClosureResidualReport` (spec vs impl vs observed) | Depends on multiple increments' specs | Future increment |

Implementing a deferred block under the Increment 1 authorization is a scope violation — fail closed and report.

---

## 5. Frozen research contract (what would be frozen before any code)

The contract is a file, not a claim. Before any Increment 1 code the authorized agent must publish it at a frozen head and bind its content hash to the implementation receipt. Re-derivation must use this hash, not an inferred one.

### 5.1 Frozen contract ID and placement

* **Proposed path:** `docs/oce-golden-system/OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.1.md`
* **Content hash:** `deterministic_hex("ophit3-confluence-contract", canonical_bytes)` published in both the contract and the run receipt.
* **Frozen fields (all of them, not a summary):**

| Field | Frozen value for Increment 1 | Rationale |
|---|---|---|
| `purpose` | Bounded confluence of one existing deterministic workflow; no physical hypothesis test | Prevent scope creep |
| `workflow_selection_rule` | See §5.2 — applied to `stress-suite/scenarios/*` at frozen dependency; the agent must record the chosen scenario ID and the rule's `specificity_score` | Keeps the workflow deterministic and predeclared |
| `fixture_set` | The existing fixture set of the chosen scenario (e.g. `scenario.json`, `stimulus_events.jsonl`, `observable_evidence.json`); file digests recorded verbatim | No new dataset; no training data |
| `state_projection` | `protected_fields` and `nuisance_fields` per §5.3; projection function `p(state) -> digest` frozen as canonical bytes | Presentation/IDs cannot masquerade as authority |
| `schedule_model` | Valid-schedule definition per §5.4, bound `N`, enumerator name + bound hash | Arbitrary permutation measures nothing |
| `termination` | Timeout + bound + failure classification per §5.5; `INCONCLUSIVE` beyond bound is valid | Unbounded search is not verification |
| `checks` | Four checks + negative control + minimization per §5.5–§5.6 | Each has a typed PASS/FAIL |
| `premise/target/code hashes` | `tested_sha`, `DeterministicReplay` artifact digests, `EvidenceRegistry`/`CounterexampleRecord` version pins, input fixture digests | Replay without provenance is not evidence |
| `falsification_thresholds` | Protected-digest mismatch → `CONFLUENCE_FAILURE`; local-diamond failure → `ANALOGY_ONLY_DIAMOND`; seed-dependent control must fail | Thresholds do not move after seeing results |
| `kill_band / precision_floor` | `N/A` for confluence (no prediction) — explicitly `N/A` rather than omitted | Keeps Block F language honest |

* **Versioning:** any post-freeze change bumps the contract version, records reason, shows `pre/post` verdicts where affected, and invalidates the prior run receipt hash.

### 5.2 Fixture-selection rule — which workflow Increment 1 may exercise

*Rule R1 (applied at the frozen dependency head, exactly as written):*

1. **Candidate set:** every directory `stress-suite/scenarios/s*_*` at the frozen head that contains `scenario.json` + `stimulus_events.jsonl` + at least one of `observable_evidence.json` / `run_receipt.json`.
2. **Governed-determinism predicate (must hold):** running the scenario via the existing harness (`engine/fixtures.run_smoke` + `engine/replay.DeterministicReplay`) with `seed_records` from `initial_knowledge` and `authority` seeded from `initial_authority_state` yields a deterministic `ReplayResult{terminal_phase, terminal_lifecycle, trace, fingerprint}` and no `ReplayInputError`. Proven in-tree by `tests/test_g1r_*`, `tests/test_g2_scenarios.py`, `tests/test_replay.py`.
3. **Confluence-relevance predicate (the research kernel):** the scenario's stimulus contains **at least two non-sequenced evidence/event steps whose relative order is not imposed by a prerequisite chain** — i.e., the harness can enumerate at least two distinct valid schedules that both respect prerequisite order. This is the property the confluence harness tests; a scenario whose steps are strictly prerequisite-linear carries no independent-order signal and would make `CONFLUENCE_FAILURE` tautologically impossible.
4. **Nuisance-presence predicate:** the scenario has at least one field in its `observable_evidence` / `scenario.json` whose lineage or presentation identity (e.g. `source_lineage`, `producing_actor`, alias vs canonical lineage) is sufficient to exercise the `nuisance_fields` projection without requiring a physical model.
5. **Exclusion predicate:** the scenario must not require live capital, production mutation, broker/exchange contact, wall-clock timing, or a model call — per `GATES §2` and `stress-suite/engine/base.py` G1 scope guards.
6. **Tie-break:** if multiple candidates satisfy 1–5, prefer (a) Class A deterministic-constitutional scenarios (`S01–S05, S10–S13, S20–S24` per Scenario Catalog) over cognitive-ecology / domain simulations, (b) smaller fixture sets, (c) scenarios whose existing `run_receipt.json` was already regenerated by the deterministic replay (lowest amendment risk). Record the tie-break distance.
7. **Publication:** the agent publishes the chosen `scenario_id` (e.g. a candidate among `S01`, `S03`, `S04`, etc.) together with the rule result and the content digests of the files the rule consumed, so a reviewer can re-run the rule at the same head and recompute the same choice.

*No synthetic/null schedule is substituted for the real workflow.* If no scenario satisfies R1 at the frozen head, the correct outcome is `INSUFFICIENT_DATA` with a disclosed coverage gap — the run receipt must say so, not invent a confluence claim.

### 5.3 Protected vs nuisance state — the projection under test

The projection `p` is the research hypothesis: which fields are **public / protected** (depended on by authority, governance, and phase disposition) and which are **nuisance / presentation** (must be quotiented away). Increment 1 freezes one projection and does not invent a new evidence channel.

| Class | Fields (examples frozen in contract) | Verdict when varied |
|---|---|---|
| **Protected** | `terminal_phase` · `terminal_lifecycle.state[*]` · `evidence_refs` resolution class per `EvidenceRegistry` · `authority_state` (`AuthorityLevel`, `CapabilityGrant`) · `transition.allowed / applied / violation` · `fingerprint` of trace governance decisions (`GovernanceEvent` / `EvidenceGraph`) | Must remain equivalent across valid schedules — confluence obligation |
| **Nuisance / Presentation** | `source_lineage` alias spellings that map to the same `distinct_source_lineages` count · `producing_actor` display label where `AuthorityState` distinguishes by `AuthorityLevel` not string · deterministic `seq` ↔ presentation-order tie where `DeterministicReplay` orders by `seq` · whitespace / JSON key order before canonicalization · `RecordId` hash prefix length where contract allows | Varying these must leave the protected projection digest invariant |

> The exact field list and the canonicalization rule (`deterministic_hex("replay", phase, lifecycle, trace)` plus any field-level projections) are frozen as canonical bytes. **Changing the projection after seeing results is a `FINGERPRINT_MISMATCH`-class refusal**, not a narrative correction. The same failure-reason taxonomy as `g8_test_evidence` applies by analogy.

### 5.4 Valid schedules and the declared bound

* **Valid schedule:** a permutation of the scenario's stimulus events that respects **declared prerequisites** — `seq` monotonicity enforced by `DeterministicReplay.run()` (`ReplayInputError` on `seq <= prev`, §L54–110), plus any explicit prerequisite edges carried by the scenario file itself. An arbitrary permutation that violates `seq` or a declared prerequisite is **invalid** and must be excluded — counting it would inflate confluence coverage without meaning.
* **Enumerator:** the harness exposes `schedule_enumerator(spec, bound) → List[List[ReplayEvent]]` as a deterministic function. Its output set and its bound `N` are frozen in the contract; its content hash is published.
* **Bound (`VALID_SCHEDULE_BOUND = k`):** the contract freezes a finite integer bound `k` on the number of distinct protected states / schedule permutations the harness will enumerate. `k` is sized so that all valid schedules up to that bound are exercised and the bound is disclosed in the coverage statement (`enumerated_valid / total_valid_up_to_bound / beyond_bound = inconclusive`). **Beyond-bound behavior is validly `INCONCLUSIVE`, not `PASS` or `FAIL`.**

### 5.5 Confluence checks — four typed verdicts + negative control

Each check is a separate typed predicate with PASS/FAIL — a summary scalar must not conflate them.

| Check | Spec frozen before run | What it proves | Implemented already? | Increment 1 would add |
|---|---|---|---|---|
| **Termination** | `timeout = t_ms` · `max_steps = k` · backstop ledger `too_large_to_enumerate → INCONCLUSIVE` | Every valid schedule reaches a terminal state within the bound, or the run is `INCONCLUSIVE` (not conflated with `PASS`) | `DeterministicReplay.run()` is bounded; no bound declaration or `INCONCLUSIVE` typing exists for schedules | Bound record + `INCONCLUSIVE` Receipt class |
| **Single-action idempotence** | `idempotent_action ∈ {seeded KnowledgeRecord transition that is its own retry}` where meaningful | Replaying the same action twice (or the retry path) leaves protected state idempotent | Lifecycle `FORBIDDEN_LIFECYCLE_EDGES` + `TransitionRecord.allowed` exist; no idempotence predicate | One `IdempotenceCheck` harness + test |
| **Local diamond (independent actions)** | `independent_pair = (a, b)` where `a` and `b` act on disjoint knowledge objects / phase windows with no shared prerequisite | `a;b` and `b;a` land on the same protected state when the pair is declared independent — the core confluence hypothesis | No diamond predicate exists | `LocalDiamondSpec` + check that compares `p(state_{a;b})` vs `p(state_{b;a})` |
| **Final-state equivalence (protected)** | `protected_projection p` from §5.3 applied to each run's `terminal_phase + terminal_lifecycle + trace` | All valid schedules agree on `p(terminal_state)` up to the bound — the `CONFLUENCE_VERIFIED` vs `CONFLUENCE_FAILURE` verdict | `DeterministicReplay.deterministic_fp` + `EvidenceRegistry` lineage exist; no protected-projection equivalence over schedules exists | `ProtectedProjection` function + equivalence verifier |
| **Negative control (seeded order-sensitive shape)** | One preregistered seeded variant where schedule *should* matter (e.g. an evidence-dependency chain where order violates a prerequisite, or a deliberately causal stimulus) | The harness does not tautologically pass: the control must yield `CONFLUENCE_FAILURE` with a minimized counterexample (see §5.6) | No seed registry | One preregistered negative-control fixture + its expected failure |

* **Consistency ladder:** `INCONCLUSIVE` (bound exhausted) < `CONFLUENCE_FAILURE` (one valid-schedule divergence) < `CONFLUENCE_VERIFIED` (all valid schedules within bound agree on `p`). No rank silently subsumes the one below it.

### 5.6 Counterexample minimization and reporting ladder

* **Minimizer:** given a `CONFLUENCE_FAILURE`, the harness must produce the **smallest valid replayable trace** that reproduces the divergent protected digest — smallest by (valid schedule prefix length, then total event count), both tied to content digests so minimization is byte-reproducible.
* **Comparison baseline:** the minimized trace is paired with **one alternative valid trace from the same validity set** (same initial state + prerequisites) that diverges on `p` — never a fabricated "control" with a different premise.
* **Preservation:** the minimized counterexample is stored as a `CounterexampleRecord`-shaped typed object (reusing `stress-suite/engine/g7_sensitivity.py:101` shape) with fields `{counterexample_id, protected_before, protected_after, expected_relation="protected equivalence across valid schedules", observed_relation="divergent p digest", preserved_evidence: {initial_state_hash, valid_schedules_enumerated, minimized_trace_hash, divergent_schedules_pair_hash}}` and bound to the research receipt.
* **Claim cap:** the allowed claim for a confluence failure is at most `CONFLUENCE_FAILURE` diagnostic — not `PROMOTED` and not an A012-scale invariant.

---

## 6. Block F planning-language correction — what time evidence would need

### 6.1 Current truth (do not describe as existing)

At `92a99d54` (inherited from `121bacd5`) the harness has:

* `stress-suite/engine/base.py:164` `class Provenance` — `source_kind, source_label, producing_actor, assigning_actor, task_ref, source_lineage, retrieval_lineage, prior_conclusion_exposure` — **no `observed_at` / `ingested_at`**.
* `stress-suite/engine/evidence.py:23` `class EvidenceRecord` — `record_id, schema_version, kind, claim, provenance, …` — **no `observed_at` / `ingested_at`**.
* `stress-suite/engine/registry.py:86` `class EvidenceRegistry` — `from_records / register / has / resolve / _coerce` over `record_id/kind/claim/lineage/resolution_class/allocator/retrieval_lineage/seq` — **no eligible-data cutoff**.

Therefore `eligible_data_cutoff` is **not independently checkable** today.

### 6.2 What `observed_at` / `ingested_at` would actually be

A populated `observed_at` string on a `Provenance` is a **recorded claim** that some producer says the evidence was observed at time `T`. By itself it proves nothing about when the bytes entered custody or whether the source is append-only. Treating a self-stamped field as temporal proof would be circular.

### 6.3 What would make eligible-data time independently checkable

A custodied, **append-only witness** outside the claim it timestamps. Minimal form:

1. **Trusted wall-clock or monotonic counter not controlled by the test subject** — e.g. the evaluation harness's own `ReplayClock` sequence, a repo `commit_time` / signed artifact hash bound by `g8_test_evidence`, or an external append-only log with provider-attested timestamps.
2. **Cryptographic or hash-chain binding** — the evidence bytes' content hash (e.g. `deterministic_hex` / `G8_TEST_RESULTS.xml` digest lineage) bound to that witness entry, so a later rewrite cannot backdate without breaking the chain.
3. **Lineage linkage** — the `Provenance.source_lineage` → evidence-record binding survives transitions, so the cutoff comparison compares **custody witness time** against `eligible_data_cutoff`, not an inner claim.

Without (1)–(3), a correctly implemented `FrozenPredictionCustody` would still verify `freeze_seq < result_seq` (chronology) — the Block F predicate that **is** implemented — but time-of-data custody would correctly remain unverified.

### 6.4 Disposition of Block F for this dossier

* **Block F is outside Increment 1.** No `observed_at`/`ingested_at` field and no witness is added in Increment 1.
* Until the witness above is implemented and evidenced, any `FrozenPredictionCustody` evaluation must label prospectiveness as **`CUSTODY_UNVERIFIED` / `DIAGNOSTIC`** — never `PROSPECTIVE`. The existing `freeze_seq < result_seq` chronology remains the only independent check, and the two must stay separate predicates.
* The dossier does not widen Block F to a retrospective "prediction" and does not confer promotion authority.

---

## 7. Increment 1 — exact scope, files, and expected artifacts

### 7.1 Allowed paths for this increment

* **Read-only before freeze:** every file at the frozen head under `stress-suite/` and the OCE planning docs listed as parents.
* **Implementation commit (only after the contract is frozen):**
  * `stress-suite/engine/confluence.py` *(new, or equivalent path under `scenarios/` if the build keeps scenario harnesses together — the implementer records the chosen path in the contract)* — exposes `ProtectedProjection`, `schedule_enumerator`, `IdempotenceCheck`, `LocalDiamondSpec`, and `verify_confluence(spec, bound) → ConfluenceVerdict`.
  * `stress-suite/tests/test_confluence.py` *(new)* — typed acceptance harness (see §8) plus one negative-control negative test. Reuses `RelationVerdict`/`CounterexampleRecord`-shaped typing where applicable; does not create a second gate.
  * `stress-suite/engine/__init__.py` — re-export only, no logic change.
  * No other `stress-suite/engine/**` mutation without documenting it as a versioned amendment per §8.
* **Evidence commit:** `stress-suite/evidence/diagnostic/OPHIT3_CONFLUENCE_RECEIPT_v0.1.json` (diagnostic — not `*G8*` and not `*RESEARCH_RECEIPT*.json` at the evidence root).

Any write outside this list is a scope violation.

### 7.2 Expected diagnostic artifacts (Increment 1)

| Artifact | Content | Hash-bound? |
|---|---|---|
| `ConfluenceVerdict` JSON fragment | `{contract_hash, scenario_id, valid_schedules_enumerated, valid_schedules_total_up_to_bound, bound_exceeded_is_INCONCLUSIVE, protected_projection_hash_before, protected_projection_hash_per_schedule[], termination_verdict, idempotence_verdict, local_diamond_verdict, final_state_equivalence_verdict, negative_control_verdict, coverage, claim_cap="CONFLUENCE_VERIFIED|CONFLUENCE_FAILURE|INCONCLUSIVE"}` | Yes — `deterministic_hex` over canonical bytes |
| `CounterexampleRecord` fragment (only if `CONFLUENCE_FAILURE`) | Minimized valid trace pair per §5.6 with content hashes + preserved evidence | Yes |
| `Negative-control` receipt | The preregistered seeded control's expected `CONFLUENCE_FAILURE` and its minimized counterexample | Yes |
| `DependencyDigest` | `{tested_sha, g8_test_evidence.TESTED_TREE_PATHS/GIT_ARGS, g8_closure_evidence single-owner hash, DeterministicReplay version, input fixture digests, contract hash}` | Yes |
| `G8CustodyCheck` fragment | Citation re-derivation per §8.3 | Yes |

*All receipts are diagnostic. No `evidence/G8_*` file is rewritten and no G9 promotion is produced.*

### 7.3 What already exists vs what Increment 1 would add

| Obligation | Existing code already satisfies | Increment 1 would actually add |
|---|---|---|
| **A — Epistemic Claim Ledger** (minimum for this increment) | `EvidenceRegistry` (G2R-02) — fail-closed `EvidenceRecord` accounting, duplicate/conflict detection, `LineageSummary`; `LifecycleEngine` (A-009 §9) — `OBSERVED→CANDIDATE→…` with provenance never deleted; `EvidenceRecord.kind` FAIL-CLOSED; `CounterexampleRecord` typing (G7) | A typed **view** `ClaimLedgerView` over one `KnowledgeRecord` transit for this experiment: `{record_id, claim_class ∈ {diagnostic, confluence_check}, premise_refs, evidence_refs[], protected_fields, input_hash, code_hash, falsifier, status ∈ {CANDIDATE, TESTED, VERIFIED, CONFLUENCE_FAILURE, INCONCLUSIVE}, receipt}` — read-only, no second registry, no new lifecycle edge |
| **B — Confluence Harness** | `DeterministicReplay` (G1) — strict `seq` order, `ReplayInputError`, governed `GovernedTransitionExecutor`, deterministic `fingerprint`; scenario runners | `ProtectedProjection` + `schedule_enumerator(valid, bound)` + four checks + negative control + minimization per §§5.3–5.6 — ~1 module + harness, reusing existing engines |
| **G — Countermodel (minimization part)** | `CounterexampleRecord`/`RelationVerdict` shapes | Minimizer + `CounterexampleRecord` emission for confluence failures (no four-reducer arena) |
| **H — Closure custody** | `g8_closure_evidence.require()` single derivation; `g8_tested_tree.derived_tested_tree()`; `g8_test_evidence.verify_citation` | Re-derivation check in acceptance (§8.3) — no new verdict |
| **D/C/E/F** | Owned separately (transfer map, G7 sensitivity, etc.) | Deferred — out of scope for Increment 1 |

---

## 8. Acceptance gate for Increment 1

All predicates are conjunctive — one `FAIL` is a gate `FAIL`. Post-hoc threshold or projection movement is a `FINGERPRINT_MISMATCH`-class refusal, not a narrative fix.

### 8.1 Structural gates (must pass before any verdict is read)

| # | Predicate | Proved by | Fail closes as |
|---|---|---|---|
| 1 | Commit discipline: contract-frozen commit precedes implementation commit; each gate needs granular `STRESS-G{n}`-style commits, no giant commit | `git log --graph --before/after` shows contract hash commit first; each material change carries its own gate/scenario commit | `FAIL.STOP — contract not frozen before code` |
| 2 | Allowed-file list respected; no `larger-lab-model-foundry`, `oce-program-build`/`oce-full-program-planning-books-2-10`, cloud/production/capital contact | `git diff --stat HEAD~1` inside `stress-suite/{engine,tests,scenarios,evidence/diagnostic}` + `docs` planning only | `FAIL.STOP — scope violation` |
| 3 | Deterministic harness reused, not duplicated (no second worker fabric / registry / lifecycle / freeze authority) | `grep -R DeterminationReplay` shows reuse; new harness composes existing `DeterministicReplay` | `FAIL.STOP — duplicate harness` |
| 4 | Diagnostic namespace honored: no `stress-suite/evidence/*RECEIPT*.json` or `G8/G7` receipt written at evidence root | `ls stress-suite/evidence/*.json` unchanged except `G8_TEST_RESULTS.xml` regenerated per G8 archive contract if `TESTED_TREE` moved | `FAIL.STOP — auditor namespace violation` |

### 8.2 Behavioral gates (the experiment itself)

| # | Predicate | Exact call | Expected |
|---|---|---|---|
| 5 | Fixture selection rule R1 applied and published | `schedule_enumerator` contract + `scenario_id` + file digests in receipt; re-running R1 at the same head recomputes the same `scenario_id` (unless head moved) | `PASS` or `INSUFFICIENT_DATA` with gap disclosed |
| 6 | Protected-projection equivalence holds or fails honestly | `verify_confluence(chosen_spec, bound=k)` over all valid schedules up to `k`; `p(terminal)` compared across schedules | `CONFLUENCE_VERIFIED` or `CONFLUENCE_FAILURE` (both diagnostic) — lying about `p` is a gate block |
| 7 | Termination / idempotence / local-diamond each typed | Four verdicts present in `ConfluenceVerdict`; `INCONCLUSIVE` beyond bound is valid, not collapsed to `PASS` | Each typed `PASS`/`FAIL`; beyond-bound → `INCONCLUSIVE` |
| 8 | Negative control fails as seeded | Seeded order-sensitive control → `CONFLUENCE_FAILURE` with minimized counterexample | Must `CONFLUENCE_FAILURE`; else `FAIL — harness tautologically passes` |
| 9 | Minimization is byte-reproducible | Minimized `CounterexampleRecord` content hash deterministically recomputed; pair is two valid schedules from the same validity set | `PASS — minimization reproducible` |

### 8.3 G8 tested-tree, citation, archive, and measured-count preservation

These rules are not weakened to make a diagnostic pass.

| # | Predicate | How the CI checks it |
|---|---|---|
| 10 | `TESTED_TREE` still derived from Git via `engine/g8_test_evidence.TESTED_TREE_PATHS` + `TESTED_TREE_GIT_ARGS`, sole implementation `scenarios/g8_tested_tree.derived_tested_tree()` | `grep` ownership check; `tests/test_g8_contradiction.py:1841` ownership test |
| 11 | If `derived_tested_tree()` moved (any `stress-suite/engine|scenarios|tests` change), **both** suite commands re-measured: plain `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q` and artifact `… --junitxml=evidence/G8_TEST_RESULTS.xml`; **measured** `collected/passed/skipped/failed/errors` published with `tested_sha` against the bytes at `ARTIFACT_RELATIVE_PATH` | Artifact-level parsing per `engine/g8_test_evidence.py` — bare-integer claims refused (`UnverifiableTestEvidence`) |
| 12 | `verify_citation(repo_root, expected_tested_sha)` keyword-only + `CITATION_RULE` (`cited path must resolve inside declared tree and raw+canonical digests must equal published ones`) re-derived from `ARTIFACT_RELATIVE_PATH=stress-suite/evidence/G8_TEST_RESULTS.xml` with `JUNIT_XML_MINUS_VOLATILE_ATTRS_V1` canonical digest (retains `pytest`/`python_version`) | `tests/test_g8_contradiction.py` citation tests; `emit()` refuses stale/malformed artifact |
| 13 | `G8_RESULT.md` / `G8_EVIDENCE_RECEIPT.json` at `31c68da2⊳2cf1bb4b` remain byte-preserved as the `PASS_G8` record at that tree; new evidence in diagnostic namespace only | `git diff -- stress-suite/evidence/G8_*` clean except measured artifact regeneration if tree moved; no historical receipt rewrite |
| 14 | `prior_gate_receipts()` (`scenarios/g8_run_audit.py`) discovery not polluted; LF (`stress-suite/evidence/* text eol=lf`) preserved | `grep -R prior_gate_receipts` scope check + `git diff --check` |

*Observed counts are evidence, not fixed gates:* `1024` / `1023+1` are the counts observed at `2cf1bb4b` (`G8_RESULT.md`). A new tree must publish its own measured `collected/passed/skipped/failed/errors`. Matching the old scalar is not acceptance.

### 8.4 Claim-status honesty

| # | Predicate |
|---|---|
| 15 | `ClaimLedgerView` row for the experiment uses only `diagnostic` / `confluence_check` claim classes; a `CONFLUENCE_VERIFIED` maps to at most `TESTED/VERIFIED` diagnostic, never `PROMOTED`; a `CONFLUENCE_FAILURE` maps to a `DIAGNOSTIC` downgrade with its minimized `CounterexampleRecord` preserved |
| 16 | No `B1-I*` stage alias; no invented `AUTHORIZED_STAGE` outside the operator's explicit authorization for this dossier (see §10) |

**Gate outcome:** `PASS.increment-1.confluence.diagnostic` or `BLOCKED.*` with a typed reason from the table above. A diagnostic `PASS` is still diagnostic — it does not imply `PASS_G9`.

---

## 9. Stop conditions — when the agent must stop

Beyond Gates §5, the Increment 1 agent must stop and report (no self-repair) when any of these holds:

1. Expected behavior contradicts `A-009`/`A-010` or the Book.
2. Two scenarios require mutually incompatible protected-projection rules.
3. A required prerequisite edge is ambiguous and the test would be dishonest if guessed.
4. A domain scenario requires information not supported by authoritative materials (live data, wall-clock ordering as proof, capital).
5. A proposed fix would change the constitutional rule being tested rather than survive it.
6. The valid-schedule enumeration cannot be bounded honestly without collapsing prerequisites.
7. An additional A–H block would need to be implemented to make the verdict pass.
8. The frozen contract's field list would need to move after the result was seen.

All stop reasons are typed and preserved as `DIAGNOSTIC` with `NOT_IMPLEMENTED` for the deferred blocks.

---

## 10. Operator decision record (proposed — for approval)

> **Not ratified.** Copy the approved wording into a ledger/evidence entry; do not treat this file as the authorization.

### Proposed decision text — HOLD vs. AUTHORIZE (one must be recorded)

Until this dossier is ratified and the operator records explicit authorization, no A–H code is authorized on this branch. Valid `HOLD` under Gates §5:

> **HOLD** — OPH × IT³ diagnostic research stays planning-only on `agent/oce-institutional-stress-suite-build`; agent does not write A–H code under this proposal.

To enable exactly Increment 1, the operator would record — after ratification, on the governing ledger/evidence record the operator chooses to use for stress-suite decisions — a sentence equivalent to:

> **AUTHORIZE** — Ratify `OCE_STRESS_SUITE_RESEARCH_DOSSIER_OPHIT3_DIAGNOSTIC_v0.1` at frozen dependency `92a99d54` (lineage `92a99d54 ⊳ 121bacd5 ⊳ c43c6c26 ⊳ ef30cb49 ⊳ 31c68da2 ⊳ 2cf1bb4b961`) for **one bounded Increment 1** on `agent/oce-institutional-stress-suite-build`: frozen research contract + bounded confluence experiment on one existing deterministic workflow (§5) plus the minimum Block A `ClaimLedgerView` to report it, reusing `DeterministicReplay` and existing `EvidenceRegistry`/`CounterexampleRecord` owners, bounded to `stress-suite/{engine,tests,scenarios,evidence/diagnostic}` plus docs planning links, per acceptance gate §8 and stop conditions §9; explicitly **excluding** the four-reducer arena and remaining A–H (Blocks C–H, including Block F prospective custody). Scope is diagnostic, nonauthoritative, `evidence/diagnostic/` only, G9 NOT AUTHORIZED, no promotion, no MF-B0–B4 mutation, no merge/deployment/cloud/capital. Until that ratification and explicit authorization exist, no A–H code is authorized.

The `AUTHORIZED_STAGE` or gate token actually used is exactly the value the ratified record defines — this proposal invents none and authorizes no code.

---

## 11. Planning links — how this dossier connects to the current plan

* **Authorization packet:** `OCE_OPH_IT3_AUTHORIZATION_DECISION_PACKET_v0.1.md` (v0.3) — §2 applicability (explicit vs inferred vs unresolved), §4 Block-stage inventory, §5 bounded scope, §6 G8 custody, §7 witness/Block F correction, §9 Path M vs Path G. Ratifying this dossier **does not** replace that packet; both remain as planning lineage.
* **Reconnaissance:** `OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2.md` (v0.3-patched witness paragraph + F-row) — reuse/extend verdicts per block; Block B's missing confluence harness and Block A's minimum ledger view are the only obligations Increment 1 needs; Blocks D/C/E/F/G/H remain `EXTEND` or deferred.
* **Ingestion:** `OCE_OPH_IT3_INGESTION_PACKET_2026-09-23.md` — external hypotheses; §2 and §6 frozen-prediction ledger language about `eligible_data_cutoff` is captured here as Block F, which is correctly **outside** Increment 1 until the witness of §6.3 exists.
* **Full Program Planning:** `OCE_FULL_PLANNING_INDEX_v1.0.md` / `OCE_FULL_PROGRAM_BUILD_ROADMAP_v1.0.md` — Blocks 2–10 remain `LOCKED`; this dossier is not a Block increment and does not advance them. The index's `Only current ledger authorization` line is the invariant that keeps a planning proposal from being read as build authority.

---

## Appendix A — The controlling clause that would forbid Path M (if read that way)

**Quoted clause:** `docs/oce-golden-system/README.md:34`

> Planning completion is not build completion. Only an exact operator-provided `AUTHORIZED_STAGE=B<n>-I<m>` plus its ratified dependency authorizes an implementation increment.

**Scoping note.** The sentence's anchor context is the Block→Chapter→Section hierarchy (B0–B10) shown immediately above it in `README.md`'s Program Order table. It contains no explicit phrase such as "this rule applies only to Blocks 0–10" and no explicit phrase such as "this rule governs every branch including nonauthoritative diagnostic research." Whether it covers a branch-local, non-B< n> diagnostic increment on `agent/oce-institutional-stress-suite-build` is **ambiguous on the face of the text** — which is why this dossier treats it as an **unresolved authority boundary** per `GATES §5` *must stop and report*, rather than as a self-evident bar.

**If the operator determines Path M is forbidden:** then (and only then) a grammar amendment is required before Increment 1 is valid. The reviewable options remain as in Decision Packet v0.3 §9.2 / Appendix G — none created by default:

* **G-A:** Add a Block 11 dossier (`B11`) with its own `B11-I{m}` increments for bounded institutional research; keep `B<n>-I<m>` literal; requires `Atlas §1.3/§2.5` lifecycle + `OCE_FULL_PLANNING_INDEX`/`OCE_FULL_PROGRAM_BUILD_ROADMAP` version bump + `OCE_BLOCK_11_*_PLAN` dossier.
* **G-B:** Add an explicit `RESEARCH` dossier class outside `B<n>-I<m>` (e.g. `RESEARCH-I{m}` lane) and amend `README.md:34` to state `RESEARCH-I{m}` as an approved alternative for diagnostic-only work on this branch.

Either amendment carries per `Constitution Art XVI`: proposed language, motivation, affected invariants, risk analysis, migration, tests/evidence, rollback, operator ratification and a new versioned decision record; lifecycle `MAPPED → ARTICULATING → READY_FOR_OPERATOR_REVIEW → RATIFIED → BUILDING`.

Because **no other exact clause** forbids Path M and the `G0–G10` execution contract is a separate ratified surface that already governed the `STRESS-G*` lineage without `B<n>-I<m>`, this appendix is **conditional**: it is reached only if the operator reads `README.md:34` as universally covering this tract. The recommendation is therefore to **ratify Path M narrowly first** — the smallest provenance-preserving change — and create B11 only after an explicit forbidding determination.

---

## Appendix B — Frozen dependency and head lineage (for reviewer re-derive)

```
proposed frozen dependency:  92a99d5448e417473a5d00c24a3fe75cabca30a7
parent:                      121bacd59a0704463711dad1289c9ff32c0596c2
grandparent:                 c43c6c265bc47a11018266e8ad1fb18c3825ac0b
great-grandparent chain:     ef30cb4955c9b7c1e241fe6218c685e94698430a ⊳ 31c68da2b53e899cf64fed393be468f758760008 ⊳ 2cf1bb4b6bc39b2a372851a02ec50d96758a8788
tested code tree (derived):  2cf1bb4b6bc39b2a372851a02ec50d96758a8788  (sole owner: stress-suite/scenarios/g8_tested_tree.py:derived_tested_tree via engine/g8_test_evidence:TESTED_TREE_PATHS/GIT_ARGS; see tests/test_g8_contradiction.py:1841)
artifact:                    stress-suite/evidence/G8_TEST_RESULTS.xml  (raw 23f97af88ff31c0ed1372d8bd0e594fb379195d7737b79dbe4b14c0a1fc8a7f2 / canonical 6fa5005e1d26dd326e58ab5d6a67d60ee8637f7697a07f858a94115fb07532e1 via JUNIT_XML_MINUS_VOLATILE_ATTRS_V1)
G8 gate:                     PASS_G8_CROSS_SCENARIO_COHERENCE  (stable at 2cf1bb4b; byte-identical G8_AUDIT_CLOSURE_MATRIX hash 0b3e262468407d46 via scenarios/g8_closure_evidence.require single derivation)
G9:                          NOT AUTHORIZED  (stress-suite/evidence/G8_RESULT.md:72 — requires new explicit authorization after review)
```

*This proposal does not move the tested tree. A later implementation commit that touches `stress-suite/engine|scenarios|tests` must move it and re-derive per §8.3.*

---

## Appendix C — Attribution

Existing `EvidenceRecord` / `EvidenceRegistry` / `KnowledgeRecord` / `LifecycleEngine` / `DeterministicReplay` / `CounterexampleRecord` / `g8_test_evidence` / `g8_tested_tree` / `g8_closure_evidence` owners are cited by file and line in `OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2.md` and above. No attribution is claimed for OPH/IT³ hypotheses — they remain external, unratified source statements per `OCE_OPH_IT3_INGESTION_PACKET_2026-09-23.md:2`.

*Retention:* This dossier and the decision packet/reconnaissance trio are durable planning artifacts; if superseded, keep the tombstone and reason. Failed or rejected increments under any later authorization remain distinguishable from successful ones (`Constitution Art XVI/XVII`).

