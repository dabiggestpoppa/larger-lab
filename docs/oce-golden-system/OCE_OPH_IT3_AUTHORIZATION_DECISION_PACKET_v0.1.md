# OCE × OPH × IT³ — Authorization Decision Packet v0.3 (supersedes v0.2)

**Date:** 2026-09-24 · **Branch:** `agent/oce-institutional-stress-suite-build`
**Authenticated head at review:** `121bacd59a0704463711dad1289c9ff32c0596c2` (current docs-corrected head; prior `c43c6c265bc47a11018266e8ad1fb18c3825ac0b` ⊳ `ef30cb4955c9b7c1e241fe6218c685e94698430a` ingestion, not a G8 PASS ⊳ `31c68da2b53e899cf64fed393be468f758760008` `STRESS-G8ARCH7-R` published evidence head ⊳ `2cf1bb4b6bc39b2a372851a02ec50d96758a8788` `STRESS-G8ARCH7` tested code tree via `stress-suite/scenarios/g8_tested_tree.py:derived_tested_tree()`, `raw 23f97af88ff31c0e / canonical 6fa5005e1d26dd32`)
**Scope:** planning-only correction of v0.2 Block F custody claim and of the §2/§4/§9 B11-necessity inference. No A–H code, no G8 receipt rewrite, no G9/G10, no merge, external OPH packet stays unratified.

This revision fixes two v0.2 defects: (1) Block F described registry timestamp resolution as an existing capability — **false**: `EvidenceRecord`/`EvidenceRegistry`/`Provenance` have no `observed_at`/`ingested_at` at `121bacd5`; eligible-data cutoff is not independently checkable until a provenance/data-custody extension is implemented and evidenced, and until then prospective status must fail closed to `DIAGNOSTIC`/`CUSTODY_UNVERIFIED` while `freeze_seq < result_seq` remains the separate, already-implemented chronology check; (2) v0.2 §§2/4/9 treated an inference (README `B<n>-I<m>` universally covering nonauthoritative diagnostic research) as a constitutional rule and presented B11/grammar amendment as the only honest path — corrected below to distinguish explicit requires / inferred applies / unresolved boundary and to present the minimum-change narrow dossier option where it is not explicitly forbidden.

---

## 1. Controlling authorization rules — quoted

### 1.1 `docs/oce-golden-system/README.md:34`

> Planning completion is not build completion. Only an exact operator-provided `AUTHORIZED_STAGE=B<n>-I<m>` plus its ratified dependency authorizes an implementation increment.

### 1.2 `docs/oce-golden-system/OCE_MASTER_PROGRAM_ATLAS_v1.0.md:§2.4` (Build authorization)

> A ratified dossier authorizes only the scope it explicitly defines. Implementation begins with a frozen specification and ends with evidence linked to that version.

Atlas §2.4 is the dossier-scope rule: a build is authorized only for the scope a ratified dossier defines, from a frozen spec, with evidence bound to that version.

### 1.3 Constitution `OCE_GOLDEN_SYSTEM_ARCHITECTURE_CONSTITUTION_v1.1.md:Art XVI` (Constitutional change)

> No implementation may weaken these articles through convenience defaults. An amendment requires proposed language, motivation, affected invariants, risk analysis, migration, tests and evidence, rollback, operator ratification, and a new versioned decision record.

Art XVI does not define `AUTHORIZED_STAGE` grammar; it governs how articles change.

### 1.4 `OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md:§3–§5`

- Gate progression: G8 exit `PASS_G8_CROSS_SCENARIO_COHERENCE` or `BLOCKED_G8_ARCHITECTURE_CONTRADICTION`; next eligible gate `G9 — Invariant Extraction` (no invariant accepted because it sounded philosophically attractive before testing).
- Commit contract (§4): each gate needs granular `STRESS-G{n}` commits; one giant commit is prohibited; evidence artifacts are separate.
- Stop conditions (§5): the agent **must stop and report** rather than self-repair architecture when expected behavior contradicts A-009/A-010, two scenarios require mutually incompatible rules, a required authority boundary is ambiguous, contracts would make the test dishonest, a domain scenario requires information not supported by authoritative materials, a fix would change the constitutional rule being tested, or live/production/capital access would be required.

### 1.5 `stress-suite/evidence/G8_RESULT.md:72` (applied rule at current gate)

> `PASS_G8_CROSS_SCENARIO_COHERENCE` -> next eligible gate: **G9 — NOT AUTHORIZED**; G9 requires a new explicit authorization after operator review of this evidence.

---

## 2. Applicability assessment — what is explicitly required, what is inferred, what remains unresolved

### 2.1 What the Golden System explicitly requires

- **`README.md:34` — `AUTHORIZED_STAGE=B<n>-I<m>` plus ratified dependency:** The sentence is real and controlling. Its **immediate context** in `README.md` is the `docs/oce-golden-system` **Block→Chapter→Section hierarchy (B0..B10)** — the Program Order table lists B0 `GATED_COMPLETE`, B1 `IN PROGRESS`, B2..B10 `READY_FOR_OPERATOR_REVIEW | LOCKED`, `OCE_MASTER_PROGRAM_ATLAS` and `OCE_FULL_PROGRAM_BUILD_ROADMAP` map B2..B10 to `B<n>-I<m>` increments. The README line contains **no explicit scoping phrase** like "this rule applies only to Blocks 0–10" **and no explicit phrase** like "this rule governs every branch including nonauthoritative diagnostic research." The text as written is a single sentence; its scope must be read from context, not from a scoping clause the file defines for it.
- **`Atlas §2.4` — dossier scope:** "A ratified dossier authorizes only the scope it explicitly defines" **explicitly** governs any implementation that claims authority from a ratified dossier. It does **not** define a stage grammar. It therefore explicitly requires: no code/schema/test is authorized until a ratified dossier says so in its scope, with a frozen spec and version-linked evidence. It does not by itself say that stage must look like `B<n>-I<m>` — that shape comes from README/roadmap, not from Atlas.
- **`OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md:§3–§5` — gate chain:** This contract explicitly defines G0→G10 as a **separate sequential gate chain on this branch**, with entry statuses `PASS_G8_*`/`BLOCKED_*` and a stop rule when an authority boundary is ambiguous. It explicitly says G9 is `NOT AUTHORIZED` (§1.5). It **does not contain** the string `AUTHORIZED_STAGE` or a `B<n>-I<m>` binding for an OPH research increment (§3–§5 contain zero `AUTHORIZED_STAGE` tokens — verified by grep at `121bacd5`). It defines commit/evidence discipline, not a dossier-stage mapping.

### 2.2 What v0.2 inferred (not an explicit constitutional rule)

v0.2 §2.2 inferred that README `B<n>-I<m>` + ratified dependency **necessarily** governs "any implementation writing code/schemas/tests from a ratified planning unit, including nonauthoritative diagnostic research" via two readings:

1. **Atlas §2.4 universality inference:** that "any implementation... is implementation in that rule's sense" and therefore any diagnostic writing files needs `B<n>-I<m>`. Atlas §2.4 does not state that a stage token is required for every code write — it states a dossier authorizes only its defined scope.
2. **Gates §5 / Atlas §1.4 dependency inference:** that because there is no ratified dossier placing this research after G8, the README rule "therefore still requires" `AUTHORIZED_STAGE` regardless of whether the work is called program work or bounded diagnostic research. Gates §5 says *stop and report when an authority boundary is ambiguous* — it does not resolve the ambiguity toward `B<n>-I<m>`.

Both inferences treat a plausible governance posture (treat every code increment as requiring `B<n>-I<m>`) as if the repository text had written it as a rule. The repository text does not. The inferences are therefore **not citable as constitutional forbidding clauses** until ratified.

### 2.3 What remains an unresolved authority boundary

- **Prior G8 authorization path contradicts the universal-B reading.** The entire `agent/oce-institutional-stress-suite-build` lineage that produced `PASS_G8_CROSS_SCENARIO_COHERENCE` at `2cf1bb4b` (commits `STRESS-G8ARCH*`, `STRESS-G5R*`, etc.) proceeded under the **stress-suite gate contract** (`READY_FOR_AGENT_PROMPT` → granular `STRESS-G{n}` commits → evidence artifacts → gate PASS) — **not** under a recorded `AUTHORIZED_STAGE=B<n>-I<m>` in `infrastructure/*/evidence/*.md` for this branch. No `B<n>-I<m>` dispatch for this branch is discoverable in that history, yet the work was accepted as the G8 baseline. This history is **evidence that the stress-suite tract has operated under its own gate authority**, not under Blocks B1..B10 stage dispatch.
- **No exact clause defines the stage shape for a stress-suite diagnostic research increment.** `OCE_FULL_PROGRAM_BUILD_ROADMAP §4` maps `B2..B10` to `I0..I9` functions; `OCE_FULL_PLANNING_INDEX` shows B1..B10 with `Only current ledger authorization` — neither defines a stage for bounded stress-suite diagnostic work. `OCE_STRESS_SUITE_EXECUTION_GATES` defines the G-gate dimension but not a `B/I` mapping for research.
- **Therefore the boundary is unresolved by the current text:** whether a **narrow, operator-ratified research dossier that explicitly scopes diagnostic (non-G9, non-promotional) work on this branch plus an explicit stress-suite authorization recorded under the stress-suite gate contract** satisfies Atlas §2.4 without triggering README `B<n>-I<m>` — or whether any such work is still held to README `B<n>-I<m>` and thus needs a new block or grammar amendment. **Neither answer is written in a ratified clause today.** Gates §5 says when such a boundary is ambiguous, the agent must **stop and report** and seek operator determination, not self-select B11.

### 2.4 Research is not silently G9

G9 is `Invariant Extraction` (`OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md:§3`) — promotion of invariants from survived scenarios to provisional doctrine. The OPH substrate is **not** G9: its success criteria are `EXISTING_CAPABILITY` / `OPERATOR_INDUCED` / `ANALOGY_ONLY` / `DIAGNOSTIC` / `INSUFFICIENT_DATA`, explicitly non-promotional. Calling it G9 would be claim inflation; leaving it unlabeled and running anyway would be building without authority. Correct resolution: name the dependency it needs and ratify it explicitly, and keep diagnostic evidence in a **distinct namespace** so it never reads as `PASS_G9` precursors (see §6 quarantine).

---

## 3. Authorization inventory — what is valid today

| Required  artifact | Current state | Verdict |
|---|---|---|
| `AUTHORIZED_STAGE=B<n>-I<m>` or other explicit operator authorization for a diagnostic research increment on this branch | No `B<n>-I<m>` or explicit stress-suite gate authorization for OPH×IT³ A–H is recorded in `infrastructure/*/evidence/*.md` for this branch, nor in `docs/oce-golden-system/*.md` as an operator ratification. `G8_RESULT.md` explicitly states `G9 — NOT AUTHORIZED`. The substrate plan and handoff state they are not authorization. | **Missing** |
| Ratified dossier/dependency authorizing the increment's scope | No ratified research dossier exists. `OCE_FULL_PLANNING_INDEX_v1.0.md` lists `B0 GATED_COMPLETE`, `B1 IN PROGRESS; only current ledger authorization`, `B2-B10 LOCKED`. No `B2-B10` dossier and no OPH-research dossier has been ratified. The 225 sections for B2-B10 are `READY_FOR_OPERATOR_REVIEW` planning only. No stress-suite research dossier is ratified. | **Missing** |
| Ledger dispatch carrying authorization for this branch | `B1-RATIFICATION-RECORD.md` (`OCE-BOOK-1-RATIFICATION-AND-BOOK-2-BUILD`) and `BUILD_STATUS_LEDGER.md` (`B1-I2`, `B1-LOCAL`) authorize Cloud Ground / Block 1 work — not `agent/oce-institutional-stress-suite-build` stress-suite research. No stress-suite-equivalent ledger entry authorizes A–H on this branch. | **Missing for this branch** |
| Deterministic canopy: dependency, contracts, gates before edit | Present (not made valid by being present): `121bacd5` head, `derived_tested_tree()` at `engine/g8_test_evidence.py:TESTED_TREE_PATHS = ("stress-suite/engine","stress-suite/scenarios","stress-suite/tests")` + `TESTED_TREE_GIT_ARGS`, `verify_citation(*, repo_root, expected_tested_sha)` keyword-only + `CANONICAL_JUNIT_MINUS_VOLATILE` / `CITATION_RULE`, `g8_tested_tree.py` sole owner via `engine.g8_test_evidence`, `.gitattributes LF` for `stress-suite/evidence/*` | **Present** — canopy is there; authorization is not |

**Consequence:** Under `Atlas §2.4` + Gates §5, **no A–H code/schema/test may be written on this branch** until a ratified dossier whose scope explicitly includes this research exists **and** the operator records explicit authorization for the increment under the contract that governs this branch. The planning-only pass in this packet (§§5–8 below) is allowed; the implementation step is blocked pending the decision in §9.

### 3.1 Correction to v0.1: alias sentence is revoked

v0.1 §4.2 suggested carrying `This AUTHORIZED_STAGE alias is approved as a B<n>-I<m> authorization` inside the same ratification record to make `OCE-RESEARCH-OPHIT3-AH-DIAGNOSTIC` count. That is **revoked**. An alias sentence is a **change to the stage grammar**, not evidence the existing `B<n>-I<m>` rule was met. A dossier wanting a grammar exception must propose it as (or alongside) a constitutional/Atlas amendment per Art XVI, not smuggle it as a string match.

### 3.2 Correction to v0.1: `B1-I0` and `B1-I9` are not available

v0.1's Option R2 (`B1-I0` / `B1-I9` repurposed) is **withdrawn**. `OCE_BLOCK_01_CLOUD_GROUND_PLAN` defines `B1-I0` as "Re-price and purchase decision" and `B1-I9` as "Block gate — only B1-I9 + operator may mark Block 1 GATED_COMPLETE"; `BUILD_STATUS_LEDGER.md` shows `B1-I1` ratified/checkpointed and `B1-LOCAL`/`B1-CLOUD-ACTIVATION` lives on `oce-program-build`, not this branch. Reusing those designations for stress-suite research would silently overload a Block 1 stage that already has a meaning and an active ledger, violating Atlas §1.2 dimensional limits.

No `B<n>-I<m>` in `B1` through `B10` is unallocated for this branch under the current dossiers (see §4 for why that does not alone force B11).

---

## 4. There is no valid unallocated `B<n>-I<m>` stage for *Block-scoped* work — but that finding does not settle whether diagnostic research needs one

**Finding for Block-scoped increments:** Under the ratified and currently planned Block dossiers, there is **no valid, unallocated `B<n>-I<m>` stage** on which to hang an OPH×IT³ diagnostic increment **if the increment must be a Block increment** without first amending or adding a planning unit.

Evidence:

- `OCE_FULL_PLANNING_INDEX_v1.0.md` — `B0 GATED_COMPLETE`, `B1 IN PROGRESS`, `B2-B10 LOCKED` with `B2-I0..I9` through `B10-I0..I9` already mapped to their chapters (25 sections each). No empty slot maps to "bounded stress-suite diagnostic research."
- `OCE_FULL_PROGRAM_BUILD_ROADMAP_v1.0.md §4` — every block `B2-B10` uses ten bounded increments `I0..I9` with fixed functions (`I0` freeze contracts/baseline ... `I8` adversarial/reconciliation ... `I9` gate packet/learning/operator hold). None is defined as a research substrate lane.
- `OCE_BLOCK_02..B10` dossiers are `READY_FOR_OPERATOR_REVIEW — BUILD LOCKED` (not ratified as build authority); `OCE_BLOCK_01` dossiers do not define a stress-suite increment.
- `OCE_STRESS_SUITE_EXECUTION_GATES_v1.0.md` §4 commit contract and §5 stop conditions govern an **execution-gate sequence** (`G0..G10` with statuses `PASS_G8_CROSS_SCENARIO_COHERENCE` / `BLOCKED`) on this branch — but that sequence has **no `B<n>-I<m>` binding** in `OCE_MASTER_PROGRAM_ATLAS` for an OPH increment. The G gates authorize a test baseline, not a scope to write new `engine`/`scenarios`/`tests` code absent a dossier.

**What this finding does not establish:** That diagnostic research necessarily requires `B<n>-I<m>`. The finding above is about **Block increments**. Whether `README.md:34` universally requires `B<n>-I<m>` for a **stress-suite diagnostic tract** is precisely the unresolved boundary in §2.3. No exact clause cited in §1 **explicitly** states "every code increment on `agent/oce-institutional-stress-suite-build`, including nonauthoritative diagnostic work, requires `B<n>-I<m>`." Until such a clause exists, treating that inference as a forbidding rule would be inventing the rule the packet is meant to surface as unresolved.

**Consequence:** The honest status is **no Block stage exists; whether one is needed at all for diagnostic research is operator-determined under Atlas §2.4 + Gates §5**. §9 presents the minimum-change path that is **not explicitly forbidden** alongside the heavier path that would be required **if** the operator determines `B<n>-I<m>` is universally required.

---

## 5. Bounded research scope (what the ratified dossier would allow — and only that)

If a dossier per §9 is ratified and the operator records the explicit authorization defined there, the authorized implementing agent may — and only may — do:

### In scope (bounded to `stress-suite/` and to docs planning artifacts)

* Read `OCE_OPH_IT3_INGESTION_PACKET_2026-09-23.md` (and DOCX source), `OCE_OPH_IT3_RESEARCH_SUBSTRATE_PLAN_v0.1.md`, `OCE_OPH_IT3_AGENT_HANDOFF_v0.1.md`, A012 + OPH/Cadence impact review, G8 evidence (`G8_RESULT.md`, `G8_EVIDENCE_RECEIPT.json`, `G8_TEST_RESULTS.xml` at `2cf1bb4b`), and all `stress-suite/engine` + `stress-suite/scenarios` + `stress-suite/tests` at the frozen ratified head.
* Produce a **frozen contract document** (`OCE_OPH_IT3_RESEARCH_CONTRACT_v0.x.md`) at the **ratified dependency head** before any A–H code: claim classes (`finite_theorem` … `frozen_prediction`), `protected public vs nuisance/presentation` state projection, `valid-schedule` bound, dataset/stream selection, null construction, metrics, premise/target hashes, falsification thresholds, code/config/input digests — versioned with pre/post reasons.
* Implement **only genuinely missing** A–H obligations as **nonauthoritative extensions** under `stress-suite/`, reusing the owners from `OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2.md` (as corrected by this packet §7):
  - **A:** typed `ClaimLedgerView` over existing `EvidenceRegistry`/`KnowledgeRecord` (no second registry); seven-class discrimination is a view, not a new channel.
  - **B:** bounded `schedule_enumerator` + `protected_projection` + `confluence_verdict` on top of `DeterministicReplay` (no new worker fabric).
  - **C:** `InvariantQuotientSpec` + `verify_quotient` reusing `PerturbationRecord`/`RelationVerdict`/`CounterexampleRecord` (no parallel G7/G9 gate).
  - **D:** `ReductionArena` harness that **plugs into existing streams** (`S01_WEAK`+); emits `INSUFFICIENT_DATA` when no stream qualifies (no model/training pipeline, no new dataset).
  - **E:** preservation predicates `preserved_operations / preserved_order / preserved_normalization / refinement_rule` **on `TransferInvariantMap`** + witness-checked `validate_transfer_map` result (`ANALOGY_ONLY` vs `STRUCTURALLY_SOUND` with typed `OPEN_BRIDGE`); **no second registry** — declaration requires witness (see §7.1).
  - **F:** `FrozenPredictionCustody` wrapping existing `verify_freeze_chronology` + `resolve_frozen_target_protocol` + `EvalContractSnapshot` deep-freeze with `eligible_data_cutoff` + `kill_band` and **data-custody verification via the provenance extension described in §7.2**; diagnostics -> `DIAGNOSTIC` not promotion. Until the provenance extension is implemented and evidenced, F remains `CUSTODY_UNVERIFIED`.
  - **G:** `CountermodelGenerator` reusing `CounterexampleRecord` (minimize + null + ablation + compression).
  - **H:** `ClosureResidualReport` composing `g8_closure_evidence.require()` + `verify_citation(..., expected_tested_sha=derived_tested_tree())` + replay `deterministic_fp` protected hash — **no second verdict**.
* Write schemas/tests/receipts plus dependency graph / claim-ledger / comparison tables / minimized counterexamples as **diagnostic artifacts** (see §6 quarantine).
* Re-derive the tested tree and the full G8 evidence custody after any code change (see §6).

### Exclusions (hard — the dossier must state them; the agent must not do them)

* No modifications to `larger-lab-model-foundry` (`MF-B0–B4`) or to branch `oce-program-build`/`oce-full-program-planning-books-2-10`.
* No forward-port, merge, deployment, cloud mutation, credential rotation, broker/capital contact, or production change.
* No G9/G10 gate claim, no historical `G8_EVIDENCE_RECEIPT.json` rewrite, no claim that planning files self-authorize.
* No new `*RECEIPT*.json` under `stress-suite/evidence/` in a way discoverable by `prior_gate_receipts()` unless that auditor scope change is an explicitly reviewed contract revision — use `evidence/diagnostic/` or `evidence/RESEARCH_*` (see §6).
* No second `EvidenceRegistry`, lifecycle, worker fabric, `TransferInvariantMap` authority, freeze mechanism, or gate — extend listed owners.
* No invented stage or gate name beyond the one the ratified authorization defines.

---

## 6. G8 custody reconciliation — moving `derived_tested_tree()` without rewriting G8 history

The proposed scope and the G8 custody rules appear contradictory if read naively: "changes in `stress-suite/engine`, `scenarios`, or `tests` move `derived_tested_tree()`" vs "preserve historical G8 claims". They are reconciled by the actual custody model, which **derives** rather than asserts:

1. **The code tree is derived, not declared.** `engine/g8_test_evidence.py:TESTED_TREE_PATHS = ("stress-suite/engine","stress-suite/scenarios","stress-suite/tests")` and `TESTED_TREE_GIT_ARGS = ("log","-1","--format=%H","--",*TESTED_TREE_PATHS)`; the **sole** implementation is `scenarios/g8_tested_tree.py:derived_tested_tree()` (see `tests/test_g8_contradiction.py:1841` ownership check), shelling out to Git. A later commit that touches only docs or `evidence/*` **does not move** the derived tree (archive-friendly property recovered at `2cf1bb4b` — `G8_RESULT.md: "because the rule names the CODE tree, the package regenerates identically from any later commit that touches only docs or evidence"`).

2. **New code on that tree moves the derived tree — that is correct behavior.** An implementation commit that changes `engine`/`scenarios`/`tests` per §5 **must** create a **new tested tree SHA** (the newest commit touching those paths). The agent must then:
   - run **both** suite commands from that new tree: plain `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q` and artifact-producing `... --junitxml=evidence/G8_TEST_RESULTS.xml`, and publish each command's **measured** counts (`collected/passed/skipped/failed/errors`), not a fixed 1024 expectation;
   - re-derive `verify_citation(repo_root, expected_tested_sha)` with keyword-only `repo_root`/`expected_tested_sha` per `engine/g8_test_evidence.py:CITATION_RULE` and `JUNIT_XML_MINUS_VOLATILE_ATTRS_V1` canonical digest (volatile attrs stripped; `pytest`/`python_version` retained) and confirm the **new** artifact's `artifact_digest`/`artifact_canonical_digest` + `tested_sha` against the bytes at the cited path (`ARTIFACT_RELATIVE_PATH = stress-suite/evidence/G8_TEST_RESULTS.xml`); the **lag check** `test_the_committed_package_names_the_derived_code_tree` is not weakened — it remains the fail-closed proof that the package lags by exactly one artifact-producing run, now **re-proved on the new tree** (artifact run 1023/1/0, plain run 1024/1024 are not fixed — they are re-measured per tree);
   - re-run `scenarios/g8_emit_evidence.py` which delegates to `scenarios/g8_closure_evidence.py:require()` (single owner for RED+GREEN+artifact+survival, one derivation per ARCH row, `HARNESSES=(RED,ARCH)`, `TEST_MODULE`, `PROBE_IDS/PRE_PASS_HEADS`, `require/problems/resolve`, refusing bogus green/artifact/empty `green_tests`, `ANNEX` derived not declared); publish any new `G8_AUDIT_CLOSURE_MATRIX` byte hash if rows changed — that matrix is **derived, not declared**, so a changed hash is not a violation, it is the evidence that the delegation was not behavior-preserving and must be audited.

3. **Historical G8 claims are preserved, not mutated.** `stress-suite/evidence/G8_RESULT.md` / `G8_EVIDENCE_RECEIPT.json` at `31c68da2`/`2cf1bb4b` remain byte-preserved as the record of the `PASS_G8_CROSS_SCENARIO_COHERENCE` at that tree. The new evidence is **new commits** with a new `tested_sha`; `scenarios/g8_run_audit.py:prior_gate_receipts()` (`sorted(EVIDENCE.glob("*RECEIPT*.json"))` excluding `OWN_GATE_RECEIPT_PREFIX`) will discover the historical receipts by design, and `g8_test_evidence:verify_citation` will still re-derive their citations. The research's **diagnostic** outcomes must not masquerade as a historical gate receipt: either use a distinct namespace (`evidence/diagnostic/` or `evidence/RESEARCH_*`) or, if a new `*RECEIPT*.json` at `evidence/` depth is needed, make its auditor-scope effect an **explicit reviewed contract change** with pre/post reasoning. This preserves `G8 prior_gate_receipts()` intent while letting the custody model move.

4. **No weakening.** The lag check, `require_clean` refusal for dirty trees (`g8_tested_tree.py:require_clean`), `CITATION_RULE` (`cited path must resolve inside declared tree and raw+canonical digests must equal published`), and `prior_gate_receipts()` discovery are not loosened to make new research pass. They are **re-proved** on the new tree with measured, not fixed, counts.

---

## 7. Witness rules — what counts as proof (corrections to reconnaissance)

### 7.1 Block E — declaration is not preservation

A populated `preserved_operations` (or `preserved_order`/`preserved_normalization`/`refinement_rule`) tuple is a **declaration**, not proof that the operation is preserved. Under `TransferInvariantMap`'s 13-axis completeness (`validate_transfer_map(): missing_axes` per `TRANSFER_MAP_AXES:1406`, `known_broken_assumptions` invalidates `map_sound`), those fields must be added as **preservation declarations**, but the **classification** `ANALOGY_ONLY` vs `STRUCTURALLY_SOUND` and the **promotion eligibility** `OPEN_BRIDGE` must be derived from an **independently checked witness**, not from string occupancy.

For a proposed `TransferInvariantMap` that claims `preserved_operations=("commutator-closure",)` (or any overlap/order/normalization/refinement predicate from packet §5 `RealizationMap = (source_type, target_type, preserved_operations, preserved_order, preserved_normalization, refinement_rule)` and §16 caution `preserved_operations / overlap / causal order / normalizations / refinement`), the extended `validate_transfer_map()` must distinguish three outcomes:

- **STRUCTURALLY_SOUND with preservation VERIFIED** — every `preserved_*` declaration is accompanied by a typed witness edge that resolves (e.g., an overlap translation `tau` that demonstrably maps `res_{PQ}` to `tau res`, or a commutator-closure invariant check against declared operators) and that witness hash reconciles with the map's `mechanism_invariants`/`source_observables` lineage. Only then may a `DomainTransferHypothesis` depending on the map gate a `DOMAIN_VALIDATION_REQUIRED` promotion.
- **`ANALOGY_ONLY` with `OPEN_BRIDGE` holding the unproven predicate** — any `preserved_*` declaration whose witness edge does not resolve (empty, unregistered, lineage-mismatched, or observing only label/dimension equality without operation/order/refinement proof) forces `ANALOGY_ONLY` classification and the specific obligation stays `OPEN_BRIDGE`. This is the correct handling of refinement-tower closure when the tower is declared but not demonstrated.

**Revised entry-point test for Block E (witness, not string):** Construct two maps equal on the 13 structural axes except both declare `preserved_operations=("commutator-closure",)`. Map A ships an **independently resolvable witness** (e.g., `engine/domain.py -> engine/g5r.py` overlap-translation check where the declared overlap `tau` reconciles the two source `operator` lineages and the trace `commutator(closure)` digest matches pre/post). Map B ships the same string declaration with an **unresolved** witness (empty `evidence_refs`, or a non-resolving `source_lineage` label, or a witness that only names dimensions). `validate_transfer_map` asserts `ANALOGY_ONLY + OPEN_BRIDGE=["preserved_operations"]` for B **even though the string is populated**, and only A may reach preservation-VERIFIED.

This clarifies the reuse verdict: Block E is `EXTEND` because `TransferInvariantMap` exists as a structural owner, but OPH's `preserved_operations / overlap / causal order / normalizations / refinement` obligations are **not** closed by that owner until witness semantics are added — the prior matrix's wording that implied string occupancy alone sufficed is corrected here.

### 7.2 Block F — eligible-data custody is not `freeze_seq < result_seq` alone (and registry timestamps are not existing capability)

**Correction to v0.2:** v0.2 described "provenance lineage whose `observed_at` / `ingested_at` resolves in the `EvidenceRegistry`" as if that field already existed. At `121bacd5` it does not:

- `stress-suite/engine/base.py:164` `class Provenance` has fields `source_kind`, `source_label`, `producing_actor`, `assigning_actor`, `task_ref`, `source_lineage`, `retrieval_lineage`, `prior_conclusion_exposure` — **no** `observed_at`/`ingested_at`/`custody` field.
- `stress-suite/engine/evidence.py:23` `class EvidenceRecord` has `record_id`, `schema_version`, `kind`, `claim`, `provenance`, `evidence_refs`, `status`, `seq`, `source_label`, `source_lineage`, `resolution_class`, `allocator`, `retrieval_lineage`, `subject` — **no** `observed_at`/`ingested_at`.
- `stress-suite/engine/registry.py:86` `EvidenceRegistry` (`from_records`/`register`/`has`/`resolve`/`_coerce`) carries no timestamp; `_coerce` maps `record_id/kind/claim/lineage/resolution_class/allocator/retrieval_lineage/seq` only.

Do not describe registry timestamp resolution as an existing capability. Until such evidence exists, prospective status must fail closed.

`verify_freeze_chronology(protocol, result_seq, registry)` (§1 re-read — `domain.py:717 FrozenExperimentProtocol` + `g5r.py:1481 FreezeChronologyProof / :1510 verify_freeze_chronology` five-rung ladder + `g6_governance.py:180 EvalContractSnapshot` deep-freeze) already proves **chronology** (`freeze_seq < result_seq`) with `FROZEN_BEFORE_RESULT_VERIFIED` only when `recomputed==stored && structured_freeze && refs resolve && chronology_ok`. Keep that ladder intact and separate.

That is **necessary but not sufficient** for a *prospective prediction* (packet §2 ledger — `prospectively fixed conditional test` / `frozen prospective branch prediction` — failure rejects the branch, not the framework; and §6 `Test = (hypothesis, baseline, perturbations, frozen_metric, kill_band, data_custody, result)`).

#### Smallest provenance and data-custody extension that would make `eligible_data_cutoff` independently checkable

Add no more than this, bounded to provenance/data-custody:

1. **Provenance timestamps (one place, not two).** Extend `engine/base.py:Provenance` with optional `observed_at: Optional[str]` and `ingested_at: Optional[str]` (ISO8601, UTC) — or equivalently a single `DataCustodyProvenance` extension that composes `Provenance` and adds `observed_at/ingested_at/custody_hash`. **Do not** duplicate timestamps on every layer; keep them on `Provenance` so `EvidenceRecord.provenance` carries them and `EvidenceRegistry` propagates them without a second registry.
2. **Registry propagation.** Extend `EvidenceRecord.make()` and `EvidenceRegistry._coerce()`/`register()` to carry `observed_at/ingested_at` through `Provenance` without silently defaulting `None` to favorable. `None` must mean **unknown custody**, not late.
3. **New verifier that wraps chronology.** `FrozenPredictionCustody{ prediction_ref, protocol_ref (FreezeChronologyProof status), source_refs, target_binding, hypothesis/mechanism binding, code_hash, metric, kill_band, eligible_data_cutoff, data_custody_hash }` reuses `verify_freeze_chronology` + `resolve_frozen_target_protocol` + `EvalContractSnapshot` deep-freeze lineage. Add `verify_prediction_custody(prediction, registry)` that **first** calls `verify_freeze_chronology` and **then** independently checks: every target-domain `EvidenceRecord` contributing to the evaluated metric resolves in the registry **and** its `provenance.observed_at`/`ingested_at` (as applicable) is `> eligible_data_cutoff`. If any contributing record has `None`/unparseable timestamp or `<= cutoff`, or `TARGET_CONTAMINATED` lineage signals pre-cutoff target leakage, the prediction is **not** prospective.
4. **Frozen binding of cutoff/kill-band.** `eligible_data_cutoff`, `kill_band`, and `precision_floor` are part of the frozen canonical content (included in `deterministic_hex` / deep-freeze lineage); post-hoc movement is a `FINGERPRINT_MISMATCH`-class refusal, not a narrative correction.

#### Fail-closed behavior until the extension is implemented and evidenced

- If `Provenance` timestamps are `None`/unparseable or not registered, `verify_prediction_custody()` returns `CUSTODY_UNVERIFIED` (or `RETROSPECTIVE`/`DIAGNOSTIC`, never `PROSPECTIVE`/`PREDICTION`). The existing `verify_freeze_chronology` may still be `FROZEN_BEFORE_RESULT_VERIFIED` on the same protocol — **chronology and custody are independent**.
- Any dataset whose contributing records lack timestamped provenance is `OUT_OF_CUSTODY` and non-promotional.
- **Kill-band / precision-floor** binding: post-hoc band movement refuses as `FINGERPRINT_MISMATCH`.
- **Post-hoc diagnostics quarantine:** Diagnostics that consumed measured values (observed failures, OOD pathologies, manifold diagnostics per packet §§12-16) are appended as `DIAGNOSTIC` / `BRANCH_REJECTED` receipts in a distinct diagnostic namespace (`evidence/diagnostic/` or `evidence/RESEARCH_*`), not as `PREDICTION` promotion or as `PASS_G9` precursors.

**Revised entry-point test for Block F (custody requires the extension; chronology is already proven):** Freeze protocol at `freeze_seq=10` with resolving `freeze_evidence_refs`; register `FrozenPredictionCustody{code_hash="abc", eligible_data_cutoff="2026-09-23T00:00:00Z", kill_band="[-e,+e]"}`. (1) With the extension implemented, evaluate at `result_seq=20` against registry data where every contributing `Provenance.observed_at="2026-09-24T..."` (post-cutoff) and `verify_freeze_chronology` is `FROZEN_BEFORE_RESULT_VERIFIED` → `FROZEN_BEFORE_DATA_VERIFIED` pass. (2) Re-evaluate the same frozen prediction against data where any contributor has `observed_at="2026-09-22T..."` (pre-cutoff) or `provenance.*_at is None` → `CUSTODY_UNVERIFIED`/`RETROSPECTIVE` refusal **even though** `freeze_seq < result_seq` still holds and the protocol fingerprint matches. **Without the extension**, case (2) collapses to `CUSTODY_UNVERIFIED`/`DIAGNOSTIC` for every non-trivial evaluation — no `PROSPECTIVE` claim is checkable. (3) Attempt with `result_seq=8` (result precedes freeze) → `RESULT_PRECEDES_FREEZE` refusal regardless of custody. Diagnostics that consumed measured values append as `DIAGNOSTIC`, not promotion, when `source_provenance == TARGET_CONTAMINATED` or timestamps are unverified.

---

## 8. Baseline counts are observed, not fixed acceptance numbers

### 8.1 What `1024` / `1023+1` actually record

At the pre-implementation baseline (on the derived tested tree `2cf1bb4b`):

- Plain suite `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q` -> **1024 passed** (1024 collected, 0 failed, 0 error). This is the count that an ordinary run reports **on that tree**, derived from the `pytest` artifact at `G8_TEST_RESULTS.xml`'s `pytest tests` root and from `G8_RESULT.md`'s two-command accounting.
- Artifact-producing `... --junitxml=evidence/G8_TEST_RESULTS.xml` -> **collected 1024 / passed 1023 / skipped 1 / failed 0 / errors 0** (skipped: `tests/test_g8_contradiction.py::test_the_committed_package_names_the_derived_code_tree` — the lag check that the artifact run must skip; passing on the plain run + skipped on the artifact run is the pre-repair-to-green property proved in the closure matrix — `G8_AUDIT_CLOSURE_MATRIX.md` hash `0b3e262468407d46` byte-identical per `STRESS-G8ARCH7`).
- Artifact digests `raw 23f97af88ff31c0e` / `canonical 6fa5005e1d26dd32` are the hash-contract for that artifact instance (canonical strips volatile `time`/`timestamp`/`hostname` per `JUNIT_XML_MINUS_VOLATILE_ATTRS_V1`, retains `pytest`/`python_version`).

These counts are **observed evidence at `2cf1bb4b`**, not a fixed authorization gate for future trees.

### 8.2 How an implementation increment measures its own acceptance

After any §5 code change that touches `stress-suite/engine|scenarios|tests`, the derived tree moves and the new tree must re-measure independently:

- Re-run **both** commands from the **new** tree and publish each command's **measured** `collected/passed/skipped/failed/errors` alongside the tree SHA they were measured on. Never carry `1024` or `1023/1/0` forward as fixed expectations — a new test file (+N cases), a removed test, or a new skip reason **must** move the count, and that move is validated by the JUnit counts plus the new `verify_citation` / `read_test_evidence` artifact content hashes, not by matching an old scalar.
- Re-prove LF/CRLF parity (`.gitattributes` `stress-suite/evidence/* text eol=lf` plus a `--junitxml` run on `core.autocrlf=true` vs `false` if desired) and `verify_citation(repo_root, expected_tested_sha)` re-derivation from definition only (keyword-only `repo_root`/`expected_tested_sha`, `CITATION_RULE`), plus `artifact_digest`/`artifact_canonical_digest` distinctness.
- The **lag check** `test_the_committed_package_names_the_derived_code_tree` vs its harness `test_the_lag_rule_detects_...` is not weakened to keep counts stable. Its expected skip matrix (plain `PASS`, artifact `SKIP`) is re-proved on the new tree with the new artifact instance. A count shift driven by a real test change is correct; a count shift driven by a weakening of that rule is a stop.

---

## 9. The precise operator decision

### 9.1 Plain finding (with the §2 correction applied)

Under the **current** rules there is **no ratified dossier and no explicit operator authorization** that allows A–H code/schema/test on `agent/oce-institutional-stress-suite-build` (see §3). G9 remains `NOT AUTHORIZED`. This is not fillable by re-labeling an `OCE-RESEARCH-*` string or repurposing `B1-I0`/`B1-I9` (§3.1–3.2).

What **would** fill it is distinguished below: the **minimum-change** path is a narrow research dossier plus explicit stress-suite authorization **if the operator determines that path satisfies existing rules** (Atlas §2.4) without invoking `B<n>-I<m>`. The **heavier** path (new block or `README` grammar amendment) is required **only if the operator determines README `B<n>-I<m>` universally governs this tract**. No exact clause currently forces the latter conclusion; treating v0.2's inference as constitutionally required would be the gap.

### 9.2 Two authorization paths — minimum-change vs grammar-amending (operator selects; none claimed approved)

**Path M — Minimum-change (narrow dossier + explicit stress-suite authorization). Present this first; it is not explicitly forbidden.**

- **Record:** a single narrow dossier, e.g. `OCE_STRESS_SUITE_RESEARCH_DOSSIER_OPHIT3_DIAGNOSTIC_v1.0` (or other operator-chosen ID), ratified under `Atlas §1.3/§2.5` (`MAPPED -> READY_FOR_OPERATOR_REVIEW -> RATIFIED`) and explicitly scoping **only** the §5 In-scope items with the §5 hard Exclusions verbatim, plus acceptance evidence per §8, G8 custody per §6, and witness rules per §7 (including the §7.2 provenance extension and fail-closed `CUSTODY_UNVERIFIED`/`DIAGNOSTIC`). Scope is diagnostic, nonauthoritative, bounded to `stress-suite/` plus docs planning artifacts; **no G9 promotion, no MF-B0–B4 mutation, no forward-port/merge**.
- **Authorization:** the operator records **one explicit authorization on this branch** scoped to `agent/oce-institutional-stress-suite-build` and to that dossier version at its frozen dependency SHA (prior `121bacd5` lineage `121bacd5 ⊳ c43c6c26 ⊳ ef30cb49 ⊳ 31c68da2 ⊳ 2cf1bb4b` recorded as context), authorizing **exactly one bounded implementation increment** of Blocks A–H per §§5–7 with acceptance per §8. The authorization lives in the **stress-suite gate surface** (explicit ledger entry for this branch tied to the ratified dossier), not in the `B<n>-I<m>` ledger for Blocks 1..10. No invented `B<n>-I<m>` token is needed for this path because the stress-suite tract's own gate history (`STRESS-G{n}` commits, `PASS_G8` at `2cf1bb4b` without a `B<n>-I<m>`) is the precedent that the dossier and explicit authorization are extending.
- **Why this may satisfy existing rules:** `Atlas §2.4` requires only "a ratified dossier authorizes only the scope it explicitly defines." A ratified research dossier that explicitly defines diagnostic scope meets that predicate. `README.md:34` does not contain the explicit phrase "every increment on every branch requires `B<n>-I<m>`" — its explicit text lists `B<n>-I<m>` as the shape for the increment it governs, but the stress-suite gate history was not produced under `B<n>-I<m>` and was still gated. If the operator ratifies the dossier as the governing unit for this tract, no exact clause forbids carrying forward that tract's own gate surface for a bounded diagnostic increment, keeping G9 unauthorized and promotion separate.
- **Gate for this path:** the implementing agent may write bounded code/tests per §§5–7; acceptance per §8; hold `BLOCKED` until the dossier, its frozen spec, and the explicit branch authorization are recorded. Diagnostic evidence uses `evidence/diagnostic/` (never `PASS_G9`).

**Path G — Grammar-amending (new planning unit or `README` amendment). Required only if operator determines Path M is forbidden.**

- **Trigger:** operator determines — and records with an **exact forbidding clause** — that `README.md:34` must be read as universally requiring `B<n>-I<m>` for any implementation increment on this branch, including nonauthoritative diagnostic work. The clause to cite would be `README.md:34` itself: `Only an exact operator-provided AUTHORIZED_STAGE=B<n>-I<m> plus its ratified dependency authorizes an implementation increment`, read as applying to this branch. No other file supplies a more specific forbidding clause; the stress-suite gate history would then be treated as an exception that does not survive for new OPH work.
- **Record:** then — and only then — a grammar amendment is required before any OPH `AUTHORIZED_STAGE` is valid. Two reviewable options, operator chooses or proposes its own — none claimed approved:
  - **G-A) Add a Block 11 dossier for bounded institutional research (`B11`)** with its own `B11-I{m}` increments for nonauthoritative diagnostic work. Keeps `B<n>-I<m>` literal; duplicates a full block for a narrow tract. Requires Atlas-coherent amendment + `OCE_FULL_PLANNING_INDEX` + `OCE_FULL_PROGRAM_BUILD_ROADMAP` version bump and a `B11` `OCE_BLOCK_11_*_PLAN` dossier.
  - **G-B) Add an explicit `RESEARCH` dossier class outside `B<n>-I<m>`** (e.g., `RESEARCH-I{m}` lane) and **amend `README.md:34`** to state that `RESEARCH-I{m}` is an approved alternative to `B<n>-I<m>` for diagnostic-only work on `agent/oce-institutional-stress-suite-build`.
- **Gate for this path:** both a grammar amendment record **and** a separate scope dossier (Decision B in v0.2 terms) must be ratified as **separate reviewable records** (changing grammar does not silently carry scope). Either amendment carries per Constitution Art XVI: proposed language, motivation, affected invariants, risk analysis, migration, tests/evidence, rollback, operator ratification and a new versioned decision record; `MAPPED -> ARTICULATING -> READY_FOR_OPERATOR_REVIEW -> RATIFIED -> BUILDING` per Atlas §1.3/§2.5.

**Why this replaces v0.2 §9's single heavy path:** v0.2 presented only the grammar-amending path and bundled the stage choice into the same decision. The corrected §9 separates the inference that drove that path, presents the minimum-change path that is **not explicitly forbidden by any quoted clause**, and makes the heavier path contingent on an explicit operator determination with a cited forbidding clause, per Gates §5 *must stop and report* when an authority boundary is ambiguous.

### 9.3 The operator choice — short, concrete, no invented stage, no premature code authorization

Until a ratified dossier and its explicit authorization per §9.2 exist, every agent treats this branch as **planning-only**. The operator selects one disposition and records it in the ledger/history (no code is authorized by this packet itself):

**HOLD — planning-only remains (valid Gates §5 disposition).**

> OPH×IT³ diagnostic research stays planning-only; agent does not write A–H code on this branch.

If the operator intends to enable bounded implementation, author must record **one** of the following verbatim intentions **and then perform the ratification/authorization it names before any code**:

**AUTHORIZE (Path M — minimum-change, if operator determines it satisfies existing rules).**

> Ratify the narrow research dossier (`OCE_STRESS_SUITE_RESEARCH_DOSSIER_OPHIT3_DIAGNOSTIC_v1.0` or operator-chosen ID) scoping §§5–8 at frozen dependency SHA (`121bacd5` lineage `c43c6c26 ⊳ ef30cb49 ⊳ 31c68da2 ⊳ 2cf1bb4b`) and record explicit operator authorization for one bounded increment on `agent/oce-institutional-stress-suite-build` under that dossier. Until that dossier is ratified and that explicit authorization is recorded, no A–H code is authorized.

**AUTHORIZE (Path G — grammar-amending, only if operator determines Path M is forbidden under README:34).**

> Record the determination that `README.md:34` `AUTHORIZED_STAGE=B<n>-I<m>` universally governs this branch (cite `README.md:34` as forbidding Path M) and ratify the grammar amendment (Block 11 `B11-I{m}` or `README` `RESEARCH-I{m}` exception per Art XVI) plus the separate bounded research dossier scoping §§5–8 at frozen SHA (`121bacd5` lineage) before any A–H code. Until both records exist, no A–H code is authorized.

In either AUTHORIZE case G9 is not authorized, research remains diagnostic (`DIAGNOSTIC`/`CUSTODY_UNVERIFIED` until provenance extension is evidenced), and the `AUTHORIZED_STAGE` or gate token actually used is **exactly the value the ratified Path M or Path G record defines** — this packet invents none and authorizes no code.

---

## 10. Related files & retention

- Reconnaissance corrected in `docs/oce-golden-system/OCE_OPH_IT3_CORRECTED_RECONNAISSANCE_v0.2.md` (exact file:line table, `REUSE/EXTEND` decisions, harnesses, entry-point tests). v0.2 is patched in this revision's companion commit only for the E/F witness clarifications and the Block F registry-timestamp correction that mirror §7 — it is otherwise preserved.
- Ingestion packet/plan/handoff remain at `OCE_OPH_IT3_INGESTION_PACKET_2026-09-23.md` + `OCE_OPH_IT3_RESEARCH_SUBSTRATE_PLAN_v0.1.md` + `OCE_OPH_IT3_AGENT_HANDOFF_v0.1.md` — all explicitly non-ratifying and their `no-OPH-ontology-as-axiom` boundary holds.
- This decision packet is **v0.3 superseding v0.2** (which superseded v0.1): the v0.2 Block F registry-timestamp description and the v0.2 inference that B11 was necessarily required are revoked and superseded by this document's §§2/4/7.2/9. Do not mix v0.2's revoked language with v0.3.

*Retention:* This packet and its reconnaissance companion are durable planning artifacts; if superseded, keep the tombstone and reason. Failed or rejected implementations under any later authorization must remain distinguishable from successful ones (Constitution Art XVII — `No implementation may weaken these articles through convenience defaults; amendment requires ... operator ratification, and a new versioned decision record`).
