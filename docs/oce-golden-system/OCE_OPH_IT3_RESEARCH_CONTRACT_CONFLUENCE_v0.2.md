# OCE × OPH × IT³ — Frozen Research Contract: Confluence (Path M Increment 1)

**Document ID:** `OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.2`
**Version:** `0.2` · **Status:** `FROZEN — REVIEWABLE — FOR OPERATOR-BOUND IMPLEMENTATION`
**Date:** 2026-09-26
**Branch:** `agent/oce-institutional-stress-suite-build`
**Dossier:** `OCE_STRESS_SUITE_RESEARCH_DOSSIER_OPHIT3_DIAGNOSTIC_v0.1` at `bfb8ca4896c9a7f8466efe4fdfa08f5fbd357e8b`
**Supersedes:** `OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.1` at `e2b06cdf` (deterministic hash `93f09b5a88b2b4d9`, raw `d99b86c22101fbd4`, 38368 bytes) — frozen research contract. v0.2 amends R1 predicate scoring (assessed/unassessed), enumeration truncation vs bound, projection evidence availability — see §11.
**Frozen dependency:** `92a99d5448e417473a5d00c24a3fe75cabca30a7` (parent `121bacd5 ⊳ c43c6c26 ⊳ ef30cb49 ⊳ 31c68da2 ⊳ 2cf1bb4b961`)
**Tested code tree (derived):** `19b6077f456b1df2a751d38385ae4d6ca3a7a54d` via `scenarios/g8_tested_tree.derived_tested_tree()` (`engine/g8_test_evidence.TESTED_TREE_PATHS/GIT_ARGS`)
**Parents:** `OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md` · `OCE_MASTER_PROGRAM_ATLAS_v1.0.md §2.4` · `OCE_STRESS_SUITE_SCENARIO_CATALOG_v1.0.md` · `OCE_OPH_IT3_AUTHORIZATION_DECISION_PACKET_v0.1.md v0.3` · `OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2.md` · `OCE_STRESS_SUITE_RESEARCH_DOSSIER_OPHIT3_DIAGNOSTIC_v0.1.md` (defects repaired per operator instruction) · `stress-suite/evidence/G8_RESULT.md + G8_EVIDENCE_RECEIPT.json + G8_TEST_RESULTS.xml` (`tested_sha 19b6077f…`, raw `9267e8b103e04279` / canonical `9c5456ec3e21039f`) — re-derived at v0.2; historical package byte-preserved at `31c68da2⊳2cf1bb4b961` (tested_sha `2cf1bb4b…`, raw `23f97af88ff31c0e`)
**Scope class:** Diagnostic, nonauthoritative, non-promotional. Not G9. Not Block 2–10.
**Operator authorization (this contract's basis):** Explicit Path M branch authorization on `agent/oce-institutional-stress-suite-build` tied to dossier `bfb8ca48` and frozen dependency `92a99d54`: frozen research contract + ONE bounded confluence experiment using an existing deterministic workflow + minimum read-only `ClaimLedgerView`. G9 NOT AUTHORIZED. See §10.
**Content hash (frozen):** `deterministic_hex("ophit3-confluence-contract", canonical_bytes)` = `TO_BE_COMPUTED_AT_COMMIT` — recomputed from the committed bytes of this file; the diagnostic receipt binds this hash.
**Allowed implementation paths:** `stress-suite/engine/confluence.py` (new), `stress-suite/tests/test_confluence.py` (new), `stress-suite/engine/__init__.py` (re-export only), docs planning links, `stress-suite/evidence/diagnostic/OPHIT3_CONFLUENCE_RECEIPT_v0.1.json` (diagnostic). No other `stress-suite/engine/**` mutation without versioned amendment. No `larger-lab-model-foundry`, `oce-program-build`, cloud/production/capital contact. No G9.

> **Freeze box.** This contract is frozen at the dependency head above. Any post-freeze change bumps the version, records reason, shows pre/post verdicts where affected, and invalidates the prior receipt hash. Implementation must bind this contract hash verbatim.

---

## 1. Purpose

Bounded confluence of one existing deterministic workflow reusing `DeterministicReplay` + governed execution + `EvidenceRegistry`/`CounterexampleRecord`. Tests schedule-independent protected normal forms honestly. No physical hypothesis test, no promotion, no invariant extraction.

- Success is diagnostic: `CONFLUENCE_VERIFIED` or minimized `CONFLUENCE_FAILURE` — both rank below `PROMOTED` and remain `DIAGNOSTIC`.
- Research execution status is distinct from scientific verdict (§1.1). `CONFLUENCE_FAILURE` and `INCONCLUSIVE` are reported honestly; neither becomes `CONFLUENCE_VERIFIED`.
- If fixture rule R1 finds no valid pair, the contract prescribes `INSUFFICIENT_DATA` with disclosed coverage gap and stops before claiming a confluence result.

### 1.1 Execution status vs scientific verdict — separate typed fields

| Field | Values | Meaning |
|---|---|---|
| `execution_status` | `COMPLETED` / `INSUFFICIENT_DATA` / `INVALID_INPUT` / `BUDGET_EXCEEDED` | Whether the harness could run the experiment honestly. |
| `scientific_verdict` | `CONFLUENCE_VERIFIED` / `CONFLUENCE_FAILURE` / `INCONCLUSIVE` / `NOT_CLAIMED` | The measured claim about protected equivalence, only valid when `execution_status=COMPLETED`. |
| `claim_status` (ClaimLedgerView) | `CANDIDATE` / `TESTED` / `VERIFIED` / `CONFLUENCE_FAILURE` / `INCONCLUSIVE` / `INSUFFICIENT_DATA` | Ledger row status for this diagnostic check — never `PROMOTED`. |

Rules:

- `INSUFFICIENT_DATA` (valid schedules <2 within bound) → `execution_status=INSUFFICIENT_DATA`, `scientific_verdict=NOT_CLAIMED`, `claim_status=INSUFFICIENT_DATA`, receipt publishes `coverage_gap` and stops.
- `INCONCLUSIVE` (enumeration budget exhausted, or valid schedules exceed bound) → `execution_status=COMPLETED` or `BUDGET_EXCEEDED`, `scientific_verdict=INCONCLUSIVE`, `claim_status=INCONCLUSIVE`. Not collapsed to `VERIFIED` or `FAILURE`.
- `CONFLUENCE_FAILURE` → `execution_status=COMPLETED`, `scientific_verdict=CONFLUENCE_FAILURE`, `claim_status=CONFLUENCE_FAILURE` with minimized `CounterexampleRecord` preserved.
- `CONFLUENCE_VERIFIED` → `execution_status=COMPLETED`, `scientific_verdict=CONFLUENCE_VERIFIED`, `claim_status=VERIFIED` (diagnostic).

---

## 2. Workflow selection rule R1 (applied at frozen dependency head)

*Rule R1 — deterministic, predeclared:*

1. **Candidate set:** every directory `stress-suite/scenarios/s*_*` at the frozen head that contains `scenario.json` + `stimulus_events.jsonl` + at least one of `observable_evidence.json` / `run_receipt.json`; plus every `stress-suite/fixtures/smoke/*.json` that is a `StressScenarioSpec` with `stimulus_events` (existing deterministic smoke harness). The candidate set is enumerated in lexicographic directory order.
2. **Governed-determinism predicate (must hold):** running the candidate via the existing harness (`engine/fixtures.run_smoke` + `DeterministicReplay`) with `seed_records` from `initial_knowledge` and `authority` seeded from `initial_authority_state` yields a deterministic `ReplayResult{terminal_phase, terminal_lifecycle, trace, fingerprint}` and no `ReplayInputError` on the canonical order. Proven in-tree by `tests/test_g1r_*`, `tests/test_g2_scenarios.py`, `tests/test_replay.py`.
3. **Confluence-relevance predicate (research kernel):** after applying the stable-action (§3.1) per-schedule `seq` assignment, the harness can enumerate at least two distinct **valid** schedules (§3.2) that both respect prerequisite order and both complete deterministically. A candidate whose valid-schedule count <2 carries no independent-order signal and would make `CONFLUENCE_FAILURE` tautologically impossible — it scores `INSUFFICIENT_DATA`, not `VERIFIED`.
4. **Nuisance-presence predicate:** the candidate has at least one field whose lineage/presentation identity is exercised without requiring a physical model. For this contract the field is `seq` presentation vs protected payload identity — the harness proves `seq` variation is presentation-only (§3.1). No new model/observation needed.
5. **Exclusion predicate:** the candidate must not require live capital, production mutation, broker/exchange contact, wall-clock timing, or a model call — per `GATES §2` and `engine/base.py` G1 scope guards.
6. **Tie-break (deterministic):** if multiple candidates satisfy 1–5, prefer (a) smokes over `s*_*` scenarios for bounded enumeration (smallest `|stimulus_events|` first), (b) lexicographically earliest `scenario_id` among ties, (c) smallest content digest of `stimulus_events` canonically. Record the tie-break distance and the full candidate scoring table. Each predicate (2-5) is either `ASSESSED` (executed) or `UNASSESSED` with a specific reason; `nuisance`/`exclusion` are never `True` by default. Scenario packs are `UNASSESSED` in Increment 1 (coverage narrowed to smoke fixtures only); the receipt distinguishes “no eligible evaluated smoke fixture” from “no eligible workflow”.
7. **Publication:** the implementation publishes the chosen `scenario_id` (if R1 yields a scenario-pack candidate) or the chosen `fixture_id` (if the smoke-tract wins) together with the full candidate table and the content digests of the files the rule consumed, so a reviewer can re-run R1 at the same head and recompute the same choice. **Chosen for this contract:** the R1 enumeration is run at implementation time against the frozen head `92a99d54`; the receipt records the chosen id and table. **Expectation from pre-freeze audit:** the smoke `knowledge_reactivation_smoke` and `legal_transition_smoke` are the only candidates with ≤4 events and therefore within `VALID_SCHEDULE_BOUND=24`; among them `knowledge_reactivation_smoke` converges on protected projection (candidate for main experiment) while `legal_transition_smoke` diverges (candidate for seeded failure control). The contract freezes the rule, not a hard-coded winner — if the measured enumeration at the frozen head yields <2 valid schedules for every candidate, the correct receipt is `INSUFFICIENT_DATA`.
8. **Fallthrough:** *No synthetic/null schedule is substituted for the real workflow.* If no candidate satisfies 1–5 with ≥2 valid schedules, the receipt is `INSUFFICIENT_DATA` with disclosed `coverage_gap` (`candidates_considered`, `valid_schedules_per_candidate`, `bound`, `prerequisite_dag`), not a confluence claim.

---

## 3. Schedule model — stable identity, valid schedules, bound

### 3.1 Stable action identity vs execution seq (defect 1 repair)

**Problem repaired:** `DeterministicReplay.run()` enforces `seq` monotonicity (`ReplayInputError` on `seq <= prev`). Reordering a list of `ReplayEvent(seq=N, …)` with fixed `seq` values therefore raises `ReplayInputError` and measures nothing about confluence. The previous dossier conflated execution order (`seq` monotonicity) with prerequisite semantics.

**Frozen repair:**

- **Action identity (stable):** `ActionIdentity = (machine, actor, target, event_type, payload_canonical, contract_version)` — deterministic, without `seq`. `payload_canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))`. Two actions with identical identity are the same governed operation regardless of `seq`.
- **Schedule:** an ordered list `S = [a1, …, aN]` of `ActionIdentity` values. `N` is the `schedule_length` (frozen per workflow).
- **Per-schedule seq assignment (deterministic):** `schedule_to_replay_events(S) -> List[ReplayEvent]` assigns `seq = 1..N` in schedule order:
  ```python
  [ReplayEvent(seq=i+1, event_type=a.event_type, machine=a.machine, actor=a.actor,
               target=a.target, payload=dict(a.payload), contract_version=a.contract_version)
   for i, a in enumerate(S)]
  ```
  This assignment is a deterministic function of schedule order; its output hash is published per schedule (`schedule_seq_hash = deterministic_hex("schedule-seq", S)`).
- **Preservation proof (frozen):** per-schedule seq assignment preserves:
  1. **Action payload:** `ReplayEvent.payload` bytes equal `a.payload` verbatim (canonical json equality); no payload field is derived from `seq`.
  2. **Prerequisite semantics:** lifecycle edge legality (`LifecycleEngine`/`PhaseStateMachine` `allowed/applied/violation`) depends only on `(target, to_state, current_state)` and `rule_ids`, never on `seq` except for monotonicity which is satisfied by construction (`1..N` strictly increasing). Phase topology, forbidden edges, and `FORBIDDEN_LIFECYCLE_EDGES` are `seq`-independent. Therefore any `S` that respects the prerequisite DAG yields the same per-action `allowed/applied/violation` as executing its actions in that order with original `seq` values reassigned.
  3. **Evidence identity:** `evidence_refs` inside `payload` are record_ids resolved via `EvidenceRegistry`; their identity is `record_id` string equality, not `seq`.
  4. **Authority checks:** `_bind` in `GovernedTransitionExecutor` checks `actor ∈ AuthorityState.actors` and `authority_level == AuthorityState.level(actor)` — both `seq`-independent. `seq` is passed only as trace index, not as authority input.
  5. **Determinism:** `ReplayClock` and `deterministic_fp`/`deterministic_hex` derive timestamps/fingerprints from `seq` order, but two schedules that differ only in action order and have reassigned `seq=1..N` are compared via the protected projection (§4.2), not via raw `seq`-including fingerprint.

- **Invalid-input control (separately tested):** reusing fixed-`seq` events without reassignment and permuting them **must** raise `ReplayInputError` (`out-of-order seq`). The harness tests this as `invalid_input` (`ReplayInputError` on `seq <= prev`) and does not count it as a confluence result. This proves the defect existed and is repaired.

- **If proof cannot be made:** if at the frozen head no candidate yields at least two valid schedules with the above assignment, the receipt is `INSUFFICIENT_DATA` with `coverage_gap` and evidence of attempted enumeration; no confluence verdict is claimed.

### 3.2 Valid schedules and enumerator

- **Valid schedule:** a schedule `S` that respects **declared prerequisites** as a DAG:
  - For lifecycle actions targeting the same `record_id`, prerequisite order is the order required by `DEFAULT_LIFECYCLE_EDGES` reachability: if `a = (target=@K, to_state=X)` and `b = (target=@K, to_state=Y)` and `Y ∉ legal_edges[X]`, then `b` after `a` may still execute (as `TOPOLOGY_DENIED` with `allowed=False`) but is classified as **invalid for confluence enumeration** when the contract requires `all_allowed=True` for valid schedules (see below). For the confluence experiment, **valid** means every trace entry has `allowed=True` and `applied=True` — every governed transition succeeded. A schedule with any `TOPOLOGY_DENIED`/`FORBIDDEN` entry is excluded from the confluence equivalence check (it is not a counterexample; it is an invalid input shape). Its exclusion is published in the `valid_schedule` table.
  - For phase actions, prerequisite is `phase.can_transition(to_state)` reachability from current `phase.state`; similarly requires `allowed`.
  - For actions on disjoint `target` (`@A` vs `@B`), no prerequisite edge exists — they are declared **independent** (§5) and both orders are valid.
- **Enumerator:** `schedule_enumerator(spec, bound) -> List[List[ReplayEvent]]` is a deterministic function:
  - Input: `spec` = the chosen `StressScenarioSpec` (or smoke fixture), `bound = VALID_SCHEDULE_BOUND`.
  - Output: the list of all valid schedules (per above) with `len(S) == schedule_length` and `valid_schedules_count ≤ bound`, in lexicographic permutation order of `ActionIdentity` tuples, each converted via `schedule_to_replay_events`. The enumerator's content hash `enumerator_hash = deterministic_hex("schedule-enumerator", bound, valid_schedules)` is published.
  - If `total_valid_up_to_bound > bound`, the enumerator returns the first `bound` valid schedules in lexicographic order and marks `bound_exceeded=True` → `INCONCLUSIVE` for beyond-bound.
  - For `n>7`, enumeration is budget-capped at 5000 permutations (not `n!`). If the budget is hit before exhaustion, `truncated=True` is set distinctly from `bound_exceeded`. Either `truncated` or `bound_exceeded` makes the result `INCONCLUSIVE` unless a divergent pair has already been observed (which is `CONFLUENCE_FAILURE` and takes precedence). `truncated` and `bound_exceeded` are reported separately in `enumerator_snapshot` and `_final_state_equivalence_check`/`_termination_check`.
- **Bound (`VALID_SCHEDULE_BOUND = 24`):** frozen finite integer bound on the number of valid schedules enumerated. `24 = 4!` covers the largest smoke fixture (`legal_transition_smoke` has 4 events). `knowledge_reactivation_smoke` has `3! = 6` total perms. `S01–S05` have up to `10!` but are not chosen as primary; if a scenario-pack wins R1, `bound=24` limits enumeration to the first 24 valid schedules lexicographically and `INCONCLUSIVE` is reported for the remainder. Beyond-bound behavior is validly `INCONCLUSIVE`, not `PASS` or `FAIL`. The `coverage` statement is `enumerated_valid / total_valid_up_to_bound / beyond_bound = inconclusive`.

### 3.3 Prerequisite-violating order — separate test (defect 3 repair, part 2)

A prerequisite-violating permutation where order violates a declared prerequisite (e.g., swapping a lifecycle chain `CANDIDATE->TESTED` to `TESTED->CANDIDATE` from `OBSERVED`) is **invalid** and must be:

- excluded from confluence enumeration,
- tested separately as:
  1. `ReplayInputError` when reusing fixed `seq` without reassignment (defect 1's old behavior), and
  2. `TOPOLOGY_DENIED` (`allowed=False`, `applied=False`) when executing with per-schedule seq assignment but with an invalid order — the trace shows the violation is recorded, state unchanged, and the schedule is counted as `invalid_prerequisite_violation` in the receipt, not as `CONFLUENCE_FAILURE`.

Neither `ReplayInputError` nor `TOPOLOGY_DENIED` becomes `CONFLUENCE_VERIFIED`.

---

## 4. State projection — forensic fingerprint vs protected projection (defect 2 repair)

### 4.1 Forensic replay fingerprint (retained, order-sensitive)

- **Forensic evidence:** the existing `DeterministicReplay.deterministic_fp` / `ReplayResult.fingerprint` = `deterministic_hex("replay", phase, lifecycle, trace)` over the raw `trace` entries **including** `seq` order and per-entry `kind`/`rule_ids` is retained as forensic evidence. It is published per schedule as `forensic_fingerprint` and as `forensic_trace_hash`. It is **not** the confluence decision.

### 4.2 Protected-state projection for confluence (separately named, canonical)

**Name:** `confluence_protected_digest` (`p_protected`)

- **Input:** `ReplayResult{terminal_phase, terminal_lifecycle, trace, authority_state_snapshot, lifecycle_states}`
- **Projection:** `p_protected = deterministic_hex("confluence-protected", canonical_bytes)` where `canonical_bytes = json.dumps({ "terminal_phase": phase, "terminal_lifecycle": sorted(lifecycle.items()), "allowed_trace": [ { "machine": e.machine, "target": e.target, "to_state": e.payload.get("to_state") or e.to, "allowed": e.allowed, "applied": e.applied, "violation": e.violation or "", "kind": e.kind, "authority_level": e.payload.get("authority_level",""), "evidence_refs": sorted(e.payload.get("evidence_refs",[])) } for e in trace if "institutional" not in e ], "evidence_kinds": (sorted({r.kind for r in registry}) if registry and len(registry)>0 and kinds else "UNAVAILABLE_NO_REGISTRY"/"UNAVAILABLE_NO_EVIDENCE_KINDS"), }, sort_keys=True, separators=(",", ":"))` — when `registry` is None or empty, `evidence_kinds` is the sentinel string `UNAVAILABLE_*` (never an empty list), and the digest domain is `confluence-protected-unavailable` so it never collides with a verified evidence-bearing digest. Evidence is AVAILABLE only when read from the `EvidenceRegistry` for the evaluated workflow; `projection_evidence_status()` reports `AVAILABLE | UNAVAILABLE_NO_REGISTRY | UNAVAILABLE_NO_EVIDENCE_KINDS | UNAVAILABLE_NO_REGISTRY_EVIDENCE`.

- **What is retained as consequential:** `terminal_phase`, `terminal_lifecycle` (`@K -> state`), `allowed/applied/violation`, `authority_level`, `evidence_refs` resolution class — all `seq`-independent.
- **What is excluded without claim:** `seq` numeric values themselves, `trace` order beyond the action sequence (captured by `forensic_fingerprint` separately), presentation `source_lineage` alias spellings that map to the same `distinct_source_lineages` count (not present in this minimal workflow), whitespace, JSON key order (canonicalized), `RecordId` hash prefix length. **No `seq` or field is classified as `nuisance` unless its variation is proved presentation-only for this workflow** — the contract's proof (§3.1) shows `seq` variation via reassignment is presentation-only when prerequisite order is respected; therefore filtered `seq` from `p_protected` is justified, while any payload field that changes the protected terminal is by definition not nuisance.

- **Confluence verdict:** `CONFLUENCE_VERIFIED` iff every valid schedule's `p_protected` digests are equal (byte-equal). Any valid-schedule divergence on `p_protected` is `CONFLUENCE_FAILURE` with minimized `CounterexampleRecord`.

- **Changing the projection after seeing results is a `FINGERPRINT_MISMATCH`-class refusal**, not a narrative correction.

---

## 5. Confluence checks — four typed verdicts + seeded failure control + minimization

Each check is a separate typed predicate with PASS/FAIL — a summary scalar must not conflate them. All checks use `p_protected` where applicable; `forensic_fingerprint` is published alongside but never conflated.

| Check | Spec frozen before run | What it proves | Valid when |
|---|---|---|---|
| **Termination** | `timeout_ms = 5000` · `max_steps = bound` · `too_large_to_enumerate → INCONCLUSIVE` | Every valid schedule reaches a terminal state within the bound, or the run is `INCONCLUSIVE` (not conflated with `PASS`) | `COMPLETED` or `INCONCLUSIVE` |
| **Single-action idempotence** | `idempotent_action = (target=@K, to_state=CANDIDATE)` from `OBSERVED` — replaying same action twice from same start: first succeeds (`OBSERVED->CANDIDATE`), second from `CANDIDATE` attempting `CANDIDATE` again is `TOPOLOGY_DENIED` with state unchanged — protected state after second equals after first (deterministic denial is idempotent, not a second promotion) | Replaying the same governed action twice leaves protected state idempotent | Honest `PASS`/`FAIL` |
| **Local diamond (independent actions)** | `independent_pair = (a=@A OBSERVED->CANDIDATE, b=@B OBSERVED->CANDIDATE)` — `a` and `b` act on disjoint knowledge objects with no shared prerequisite | `a;b` and `b;a` land on the same `p_protected` when the pair is declared independent — the core confluence hypothesis | `PASS` if digests equal, else `FAIL` with minimized pair |
| **Final-state equivalence (protected)** | `p_protected` from §4.2 applied to each valid schedule's terminal state + allowed trace | All valid schedules agree on `p_protected` up to the bound — the `CONFLUENCE_VERIFIED` vs `CONFLUENCE_FAILURE` verdict | `VERIFIED` or `FAILURE` |
| **Seeded failure control (order-sensitive shape) — two valid divergent schedules** | **Seeded workflow:** `legal_transition_smoke`-derived or minimal same-record chain `CANDIDATE -> (CHALLENGED | TESTED)` — two valid schedules: `S1 = [CANDIDATE->CHALLENGED, CHALLENGED->TESTED]` and `S2 = [CANDIDATE->TESTED, TESTED->CHALLENGED]` — both orders valid (each `allowed=True`) from start `CANDIDATE`, but terminals differ (`TESTED` vs `CHALLENGED`) so `p_protected` diverges. **Requirement:** the harness must yield `CONFLUENCE_FAILURE` on this seeded workflow, with minimized counterexample. The harness does not tautologically pass. | `CONFLUENCE_FAILURE` with minimized pair | Must `CONFLUENCE_FAILURE`; else `FAIL — harness tautologically passes` |

**Invalid prerequisite chain (separate):** `OBSERVED->TESTED` before `OBSERVED->CANDIDATE` on same `@K` — first action `TOPOLOGY_DENIED` (not `ReplayInputError` with reassigned seq), excluded from valid set, tested as `INVALID_INPUT`.

**Minimization (§5.6):** given `CONFLUENCE_FAILURE`, the harness produces the smallest valid replayable trace pair that reproduces divergent `p_protected` — smallest by (valid schedule prefix length, then total event count), both tied to content digests so minimization is byte-reproducible. Comparison baseline is one alternative valid trace from same validity set (same initial state + prerequisites) that diverges on `p_protected` — never a fabricated control with different premise. Preserved as `CounterexampleRecord`-shaped typed object (reusing `engine/g7_sensitivity.py:101` shape) with `{counterexample_id, protected_before, protected_after, expected_relation="protected equivalence across valid schedules", observed_relation="divergent p_protected digest", preserved_evidence: {initial_state_hash, valid_schedules_enumerated, minimized_trace_hash, divergent_schedules_pair_hash}}` bound to receipt.

**Consistency ladder:** `INCONCLUSIVE` (bound exhausted) < `CONFLUENCE_FAILURE` (one valid-schedule divergence) < `CONFLUENCE_VERIFIED` (all valid schedules within bound agree on `p_protected`). No rank silently subsumes one below it.

---

## 6. Block F disposition — outside Increment 1

At `92a99d54` the harness has `engine/base.py:164 Provenance`, `engine/evidence.py:23 EvidenceRecord`, `engine/registry.py:86 EvidenceRegistry` — none have `observed_at`/`ingested_at`; `eligible_data_cutoff` is not independently checkable. A populated `observed_at` is a recorded claim, not custody proof. Block F requires a custodied append-only witness: (1) trusted wall-clock/monotonic counter not controlled by subject (`ReplayClock`/commit_time/artifact hash), (2) hash-chain binding bytes to witness, (3) `source_lineage` linkage. Until implemented, prospectiveness is `CUSTODY_UNVERIFIED`/`DIAGNOSTIC` (`RETROSPECTIVE`), separate from `freeze_seq < result_seq` chronology (`g5r.py:1481/1510` ladder — already implemented and kept). **No `observed_at`/`ingested_at` field and no witness is added in Increment 1.** Block F remains outside Increment 1.

---

## 7. Implementation scope — exact files

- **Read-only before freeze:** every file at frozen head under `stress-suite/` and the OCE planning docs listed as parents. Frozen dependency `92a99d54` verified `0 0` left-right at `bfb8ca48`.
- **Implementation commit (only after this contract is committed):**
  - `stress-suite/engine/confluence.py` (new) — exposes `ActionIdentity`, `schedule_to_replay_events`, `schedule_enumerator`, `confluence_protected_digest`, `forensic_fingerprint`, `IdempotenceCheck`, `LocalDiamondSpec`, `verify_confluence` → `ConfluenceVerdict`.
  - `stress-suite/tests/test_confluence.py` (new) — typed acceptance harness: positive (`CONFLUENCE_VERIFIED` or honest `CONFLUENCE_FAILURE`), failure-control (`CONFLUENCE_FAILURE` with minimized pair), invalid-input (`ReplayInputError` on fixed-seq reorder + `TOPOLOGY_DENIED` on prerequisite violation), reproducibility (byte-reproducible minimization + `p_protected` re-derive).
  - `stress-suite/engine/__init__.py` — re-export only, no logic change.
  - No other `stress-suite/engine/**` mutation without documenting as versioned amendment.
- **Evidence commit:** `stress-suite/evidence/diagnostic/OPHIT3_CONFLUENCE_RECEIPT_v0.1.json` (diagnostic — not `*G8*` and not `*RESEARCH_RECEIPT*.json` at the evidence root) containing `ConfluenceVerdict`, `CounterexampleRecord` fragment if `FAILURE`, negative-control receipt, `DependencyDigest`, `G8CustodyCheck`, measured commands/counts/SHA/hashes.

---

## 8. Expected diagnostic artifacts

| Artifact | Content | Hash-bound? |
|---|---|---|
| `ConfluenceVerdict` JSON fragment | `{contract_hash, dossier_id bfb8ca48, frozen_dependency 92a99d54, scenario_or_fixture_id, schedule_length, valid_schedules_enumerated, valid_schedules_total_up_to_bound, bound_exceeded_is_INCONCLUSIVE, forensic_fingerprint_per_schedule[], confluence_protected_digest_per_schedule[], termination_verdict, idempotence_verdict, local_diamond_verdict, final_state_equivalence_verdict, seeded_negative_control_verdict, execution_status, scientific_verdict, claim_status, coverage, claim_cap="DIAGNOSTIC"}` | Yes — `deterministic_hex` over canonical bytes |
| `CounterexampleRecord` fragment (only if `CONFLUENCE_FAILURE`) | Minimized valid trace pair per §5 with content hashes + preserved evidence | Yes |
| `Seeded-negative-control` receipt | Two valid divergent schedules + minimized counterexample proving harness not tautological | Yes |
| `DependencyDigest` | `{tested_sha 2cf1bb4b… , g8_test_evidence.TESTED_TREE_PATHS/GIT_ARGS, g8_closure_evidence single-owner hash, DeterministicReplay version HARNESS_VERSION 0.1.0, smoke fixture digests (legal/knowledge_reactivation/illegal), contract hash}` | Yes |
| `G8CustodyCheck` fragment | `verify_citation` re-derivation and lag-check re-prove on new tree if moved; historical receipts intact in Git history per §9 | Yes |

All receipts diagnostic; no `evidence/G8_*` rewritten; no G9 promotion.

---

## 9. G8 custody — historical intact, current archive regeneration

Historical committed receipts stay byte-intact in Git history (`stress-suite/evidence/G8_RESULT.md`, `G8_EVIDENCE_RECEIPT.json`, `G8_TEST_RESULTS.xml` at `31c68da2⊳2cf1bb4b`). Any current archive regeneration required by an altered tested tree (`stress-suite/engine|scenarios|tests` changed) must use the **existing** machinery:

- `scenarios/g8_tested_tree.derived_tested_tree()` — sole owner, via `engine/g8_test_evidence.TESTED_TREE_PATHS/GIT_ARGS`, no second derivation.
- `engine/g8_test_evidence.verify_citation(*, repo_root, expected_tested_sha)` keyword-only + `CITATION_RULE` + `ARTIFACT_RELATIVE_PATH=stress-suite/evidence/G8_TEST_RESULTS.xml` + `JUNIT_XML_MINUS_VOLATILE_ATTRS_V1` canonical digest (retains `pytest`/`python_version`).
- Lag check `tests/test_g8_contradiction.py:test_the_committed_package_names_the_derived_code_tree` — not weakened; re-proved on new tree (artifact run skipped=1, plain run passed).
- `scenarios/g8_emit_evidence.py` which delegates to `scenarios/g8_closure_evidence.require()` single derivation (`HARNESSES=(RED,ARCH)`, `TEST_MODULE`, `PROBE_IDS/PRE_PASS_HEADS`, `require/problems/resolve`, refusing bogus green/artifact/empty `green_tests`, `ANNEX` derived not declared).

After any code change, re-measure **both** suite commands from the new tree:

- Plain `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q`
- Artifact-producing `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q --junitxml=evidence/G8_TEST_RESULTS.xml`

Publish each command's **measured** `collected/passed/skipped/failed/errors` alongside the tree SHA they were measured on. Never carry `1024`/`1023+1` as fixed expectations — a new test file (+N cases) moves the count, validated by JUnit counts plus new `verify_citation`/`read_test_evidence` artifact content hashes, not by matching an old scalar. Re-prove LF/CRLF parity (`.gitattributes` `stress-suite/evidence/* text eol=lf`). Publish `tested_sha` and `artifact_digest`/`artifact_canonical_digest` distinctness.

---

## 10. Operator authorization — exact scope (recorded)

**Operator instruction (2026-09-24):**

> Work on the existing `agent/oce-institutional-stress-suite-build` branch. Start by verifying that origin is at `bfb8ca4896c9a7f8466efe4fdfa08f5fbd357e8b` and inspect the actual replay, fixture, G8 custody, and dossier contracts. Do not create a branch.
> I authorize one bounded OPH × IT³ diagnostic Increment 1 under Path M: a frozen research contract, one confluence experiment using an existing deterministic workflow, and the minimum read-only `ClaimLedgerView` needed to report its result. This is explicit branch authorization for that scope, tied to the dossier at `bfb8ca48` and its frozen dependency `92a99d54`. Record this operator instruction and the exact scope in the decision record. G9 remains unauthorized.
> Before freezing or implementing the contract, repair these defects in the proposed dossier: (1) stable action identity vs execution seq, (2) forensic fingerprint retained separately from protected projection, (3) two distinct valid divergent schedules for failure control, (4) execution status distinct from scientific verdict, (5) G8 custody clarification.
> Commit the corrected, reviewable contract and decision record first. Then implement only the authorized increment using existing `DeterministicReplay`, governed execution, `EvidenceRegistry`, and `CounterexampleRecord` owners. Run meaningful positive, failure-control, invalid-input, and reproducibility tests through the real entry points. Place research receipts under `evidence/diagnostic/`, re-run the applicable G8 custody checks, and publish the measured commands, counts, derived tested SHA, hashes, verdict, and any coverage gap. Push the resulting commits to this same branch.

**Exact authorized scope (frozen):**

- Branch `agent/oce-institutional-stress-suite-build` only.
- Frozen contract `OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.1` at `92a99d54` lineage `92a99d54 ⊳ 121bacd5 ⊳ c43c6c26 ⊳ ef30cb49 ⊳ 31c68da2 ⊳ 2cf1bb4b961`.
- ONE bounded confluence experiment reusing `DeterministicReplay`, governed `GovernedTransitionExecutor`, `EvidenceRegistry`, `CounterexampleRecord` owners, exercising an existing deterministic workflow (smoke fixture `knowledge_reactivation_smoke` for main + `legal_transition_smoke`-derived seeded failure control), with per-schedule `seq` assignment proof, forensic fingerprint retained, protected projection `confluence_protected_digest` for verdict, four checks + seeded failure pair + minimization + coverage gap.
- Minimum read-only `ClaimLedgerView` typed view over one `KnowledgeRecord` transit for this experiment: `{record_id, claim_class ∈ {diagnostic, confluence_check}, premise_refs, evidence_refs[], protected_fields, input_hash, code_hash, falsifier, execution_status, scientific_verdict, receipt}` — no second registry, no new lifecycle edge.
- Bounded to `stress-suite/{engine,tests,scenarios,evidence/diagnostic}` + docs planning links. Explicitly excluding four-reducer arena and remaining A–H (Blocks C–H incl. Block F prospective custody). Diagnostic, nonauthoritative, `evidence/diagnostic/` only, G9 NOT AUTHORIZED, no promotion, no MF-B0–B4 mutation, no merge/deployment/cloud/capital.
- Controlling clause check: `docs/oce-golden-system/README.md:34` quoted; no exact clause forbids Path M for this diagnostic increment on the stress-suite tract (prior `STRESS-G*` lineage produced `PASS_G8` at `2cf1bb4b` under G-gates without `B<n>-I<m>`). No invented `AUTHORIZED_STAGE`.
- Until this contract is committed, no implementation commit is valid. After, one bounded implementation commit plus one evidence regeneration per §9.

---

## 11. Acceptance gate for Increment 1 (frozen)

All predicates conjunctive — one `FAIL` is gate `FAIL`. Post-hoc threshold/projection movement is `FINGERPRINT_MISMATCH`-class refusal.

### 11.1 Structural gates

| # | Predicate | Proved by | Fail closes as |
|---|---|---|---|
| 1 | Commit discipline: contract-frozen commit precedes implementation commit; each gate needs granular commits, no giant commit | `git log --graph --before/after` shows contract hash commit first | `FAIL.STOP — contract not frozen before code` |
| 2 | Allowed-file list respected | `git diff --stat HEAD~1` inside allowed paths only | `FAIL.STOP — scope violation` |
| 3 | Deterministic harness reused, not duplicated (no second worker fabric/registry/lifecycle/freeze authority) | `grep -R DeterministicReplay` reuse; new harness composes `DeterministicReplay` | `FAIL.STOP — duplicate harness` |
| 4 | Diagnostic namespace honored | `ls stress-suite/evidence/*.json` unchanged except `G8_TEST_RESULTS.xml` regenerated if `TESTED_TREE` moved | `FAIL.STOP — auditor namespace violation` |

### 11.2 Behavioral gates

| # | Predicate | Exact call | Expected |
|---|---|---|---|
| 5 | Fixture rule R1 applied and published; `INSUFFICIENT_DATA` valid if no valid pair | `schedule_enumerator` contract + fixture id + file digests in receipt; re-running R1 at same head recomputes same id (unless head moved) | `PASS` or `INSUFFICIENT_DATA` with gap disclosed — not `VERIFIED` |
| 6 | Protected-projection equivalence holds or fails honestly | `verify_confluence(chosen_spec, bound=24)` over all valid schedules up to `bound`; `confluence_protected_digest` compared; `forensic_fingerprint` published alongside but not conflated | `CONFLUENCE_VERIFIED` or `CONFLUENCE_FAILURE` (both diagnostic) — lying about `p_protected` is a gate block |
| 7 | Four checks each typed | Four verdicts present in `ConfluenceVerdict`; `INCONCLUSIVE` beyond bound valid, not collapsed to `PASS` | Each typed `PASS`/`FAIL`; beyond-bound → `INCONCLUSIVE` |
| 8 | Seeded failure control provides two valid divergent schedules | Seeded order-sensitive workflow → two valid schedules with `confluence_protected_digest` mismatch + minimized counterexample | Must `CONFLUENCE_FAILURE`; else `FAIL — harness tautologically passes` |
| 9 | Invalid prerequisite chain excluded and tested separately | One `ReplayInputError` case (fixed-seq reorder) + one `TOPOLOGY_DENIED` invalid schedule excluded from confluence | Both `PASS` as invalid-input proofs |
| 10 | Minimization byte-reproducible | Minimized `CounterexampleRecord` content hash deterministically recomputed; pair is two valid schedules from same validity set | `PASS — minimization reproducible` |
| 11 | `ClaimLedgerView` row for experiment uses only `diagnostic`/`confluence_check`; `CONFLUENCE_VERIFIED` maps to at most `TESTED/VERIFIED` diagnostic, never `PROMOTED`; `CONFLUENCE_FAILURE` maps to `DIAGNOSTIC` downgrade + counterexample preserved; `INSUFFICIENT_DATA` never becomes `VERIFIED` | Ledger row check | `PASS` |

### 11.3 G8 custody preservation (not weakened)

Same as dossier §8.3: `TESTED_TREE` derived via `g8_test_evidence` sole impl `g8_tested_tree.derived_tested_tree()`, both suite commands re-measured with published measured counts + `tested_sha` + digests, `verify_citation` keyword-only + `CITATION_RULE` + `JUNIT_XML_MINUS_VOLATILE_ATTRS_V1`, historical receipts intact in Git history, new evidence diagnostic only, `prior_gate_receipts()` not polluted, LF preserved.

- Observed counts are evidence, not fixed gates — `1024`/`1023+1` at `2cf1bb4b` are the counts observed at that tree; new tree publishes its own measured `collected/passed/skipped/failed/errors`.

**Gate outcome:** `PASS.increment-1.confluence.diagnostic` or `BLOCKED.*` with typed reason. Diagnostic `PASS` is still diagnostic — does not imply `PASS_G9`.

---

## 12. Stop conditions — when the agent must stop

Beyond Gates §5, stop and report (no self-repair) when: expected behavior contradicts `A-009`/`A-010` or Book; two scenarios require mutually incompatible protected-projection rules; prerequisite edge ambiguous and test would be dishonest if guessed; domain scenario requires live data, wall-clock, capital; fix would change constitutional rule rather than survive it; valid-schedule enumeration cannot be bounded honestly without collapsing prerequisites; additional A–H block would be needed to make verdict pass; frozen contract's field list would need to move after result seen. All stop reasons typed and preserved as `DIAGNOSTIC` with `NOT_IMPLEMENTED` for deferred blocks.

---

## 13. Claim ledger view — minimum for this increment

Already owned: `EvidenceRegistry` (G2R-02), `LifecycleEngine` (A-009 §9), `EvidenceRecord.kind` FAIL-CLOSED, `CounterexampleRecord` typing (G7). Increment 1 adds a typed **view** `ClaimLedgerView` over one `KnowledgeRecord` transit for this experiment: `{record_id, claim_class ∈ {diagnostic, confluence_check}, premise_refs, evidence_refs[], protected_fields, input_hash, code_hash, falsifier, execution_status, scientific_verdict, receipt}` — read-only, no second registry, no new lifecycle edge. Reuses `engine/g7_sensitivity.py:101` shape.

---

## 14. Attribution

Existing `EvidenceRecord`/`EvidenceRegistry`/`KnowledgeRecord`/`LifecycleEngine`/`DeterministicReplay`/`CounterexampleRecord`/`g8_test_evidence`/`g8_tested_tree`/`g8_closure_evidence` owners cited by file and line in `OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2.md` and above. No attribution is claimed for OPH/IT³ hypotheses — they remain external, unratified source statements per `OCE_OPH_IT3_INGESTION_PACKET_2026-09-23.md:2`.

*Retention:* This contract and the dossier/decision packet/reconnaissance trio are durable planning artifacts; if superseded, keep the tombstone and reason. Failed or rejected increments remain distinguishable from successful ones (Constitution Art XVI/XVII).

---

## 11. Amendment record (v0.1 → v0.2)

**Old contract:** `OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.1` at `e2b06cdf` — deterministic hash `93f09b5a88b2b4d9`, raw SHA-256 `d99b86c22101fbd4`, 38368 bytes.
**New contract:** `OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.2` — deterministic hash =  (recomputed from committed bytes at review; same mechanism as  line above), raw SHA-256 = . Historically:  before §11,  first §11 draft,  after first hash-patch — each patch moves the hash, so the receipt binds the final committed value rather than a literal inside the file.

**Reason:** Path M Increment 1 defect repairs on the bounded confluence harness. Three clauses tightened so the contract matches the corrected implementation; no new workflow, no smoke fixture, no expansion of scope:

| Clause | v0.1 | v0.2 | Affected verdicts |
|--------|------|------|-------------------|
| §2 rule 6 (R1 candidate table) | predicates assumed True; nuisance/exclusion defaulted to True; scenario packs not distinguished | predicates are `ASSESSED` (executed) or `UNASSESSED` with reason; `nuisance_ok`/`exclusion_ok` never default True; scenario packs `UNASSESSED` in Increment 1 with distinguish between "no eligible smoke fixture" vs "no eligible workflow"; coverage narrowed to smoke fixtures only when packs unevaluable | primary workflow selection now `UNASSESSED` with audit gap, not a confluence claim; candidate count / tie-break distance recomputed at new tree |
| §3.2 enumerator | only `bound_exceeded` (valid count > bound) reported; `n>7` budget of 5000 implicit | `truncated` (budget 5000 hit before exhaustion) reported distinctly from `bound_exceeded`; either → `INCONCLUSIVE` unless a divergent pair already observed (`CONFLUENCE_FAILURE` takes precedence). `truncated` vs `bound_exceeded` are separate fields in `enumerator_snapshot` and `_final_state_equivalence_check`/`_termination_check` | verdicts on specs with `n>7` or `valid_count>bound` correctly become `INCONCLUSIVE` (or `CONFLUENCE_FAILURE` if a divergent pair was found) rather than being reported as `VERIFIED`; new regression (>7 actions) proves `truncated` cannot be `VERIFIED` |
| §3.4 projection (`confluence_protected_digest`) | `evidence_kinds: sorted({r.kind ...}) if registry else []` — an empty list presented as verified equivalence | `evidence_kinds` read from `EvidenceRegistry` only when `registry` is non-None and non-empty; otherwise sentinel `UNAVAILABLE_NO_REGISTRY` / `UNAVAILABLE_NO_EVIDENCE_KINDS` / `UNAVAILABLE_NO_REGISTRY_EVIDENCE` with digest domain `confluence-protected-unavailable` distinct from evidence-bearing digests. `projection_evidence_status()` reports `AVAILABLE | UNAVAILABLE_*` | digests for workflows without a registry are no longer a vacuous match; `INSUFFICIENT_DATA` / `UNAVAILABLE` is reported rather than an empty-list digest that could collide |

**Frozen text preserved:** `OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.1.md` is byte-identical to `e2b06cdf` in this commit; v0.1 is not silently edited. v0.2 is a new file that supersedes it. Reviewers must read v0.2; v0.1 remains in history at `e2b06cdf`/`92a99d54`.

**Implementation binding:** this contract hash governs `stress-suite/engine/confluence.py` (`CONTRACT_ID = "OCE_OPH_IT3_RESEARCH_CONTRACT_CONFLUENCE_v0.1"` at this tree will be updated to v0.2 at the next code touch) and the diagnostic receipt `stress-suite/evidence/diagnostic/OPHIT3_CONFLUENCE_RECEIPT_v0.1.json` → rebinding to v0.2. The code repair at `19b6077f` is the same bytes that v0.2 now authorizes; no new code mutation is introduced by the version bump itself.
