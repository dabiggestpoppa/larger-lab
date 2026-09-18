# Model Foundry — implementation status (MF-B0 → MF-B4)

* **Branch:** `agent/model-foundry-mf-b0-b4-build`
* **Start SHA:** `c55e379df3de2c6bb643afc90c10c0a861fa8c8a`
* **Tested SHA (code):** `41257f3712123d9e624218f62a57ecdf501a422f` (the last commit that changes code; documentation commits after it do not change test results). Earlier code was tested at `400af029…`, `9742cfc2…` for the audit-closure repair, and `07ed6617…` before that.
* **Authoritative test command:** `cd model-foundry && PYTHONIOENCODING=utf-8 python -m pytest tests -q`
* **Result:** `157 passed` (39 MF-B0, 19 MF-B1, 44 MF-B2/B3, 27 MF-B4, 22 boundary/cross-block, 6 determinism)
* **Invocation from repo root also works:** `python -m pytest model-foundry/tests -q`
* Later documentation-only commits do not change test results.

Status vocabulary: **implemented** (real, deterministic code), **simulated**
(fixture-executed, declares `noncanonical: true`), **declaration only** (owned by
OCE; no local implementation exists).

## Block status

### MF-B0 — Program constitution / scientific boundary — implemented

`foundry/constitution.py` carries the constitutional artifacts as data (mission
contract, ownership matrix, artifact/runtime/system identity contract, OCE
dependency + retirement map, child-program boundary, truth grammar, evaluation
tier contract, authority ceiling, budget semantics, reproducibility classes,
supply-chain trust, separated lifecycle machines, convergence map) with a stable
constitution fingerprint
`sha256:0bc713f0d414309aa5095efe3998a9248deec3c902932b21ccf805fab8863420`.

`foundry/boundary.py` turns the boundary into executable guards and runs a
20-attack adversarial gate. Result: **PASS — 15 REFUSED, 5 CONTAINED, 0 ALLOWED**,
report fingerprint `sha256:60a9694ff3b8541564a14945e87ca6fa486d7f7605abc9a6b5c7894606bd6d0f`.
The gate distinguishes refusal-by-exception from containment-by-safe-state, so a
defense that silently stops working is reported as `ALLOWED` rather than hidden.

Evidence: `model-foundry/receipts/mf-b0-gate.json`, tests
`tests/test_mf_b0_constitution.py` (38).

### MF-B1 — Compute + experiment resource layer — simulated, provider-neutral

`foundry/resources.py` + `foundry/providers.py`. Implemented: provider-neutral
`ComputeRequest` (no provider field, asserted by test), two-dialect offer
normalization into one contract, cost-to-close estimation (throughput,
preemption with checkpoint credit, setup, storage, egress), placement by
cost-to-close, stale-observation policy, budget ledger, operator grants,
simulated launch receipts, failure taxonomy, portable checkpoints.

Measured, not asserted — 4 observed offers from 3 provider dialects
(`octa_fixture`, `runpod_fixture`, `local_cpu`):

| | hourly USD | effective wall h | cost-to-close USD |
|---|---|---|---|
| `octa_fixture:octa-gpu-4471` (A6000, preemptible) | 0.25 | 16.50 | 4.92 |
| `runpod_fixture:runpod-secure-8891` (A100_80G) | 1.10 | 2.79 | **3.87 (selected)** |

The cheapest eligible hourly offer loses on cost-to-close
(`hourly_trap_detected = true`). With checkpointing enabled, the preemptible
offer wins instead — cost-to-close is a causal model, not a fixed preference.
Rejected: `local_cpu:local-workstation-0` (`INSUFFICIENT_VRAM`),
`runpod_fixture:runpod-secure-2200-stale` (`OFFER_OBSERVATION_STALE`).

No paid path exists: `mode="LIVE"` raises `LIVE_LAUNCH_NOT_AUTHORIZED`; a paid
workload class without an operator grant raises `OPERATOR_HOLD`; a grant from a
non-operator, for another request, or expired is refused. Adapters are
`OBSERVE`/`SIMULATE` only, with `can_launch_instances: false`.

Evidence: `receipts/mf-b1-placement.json`, tests `tests/test_mf_b1_resources.py` (19).

### MF-B2 — Data constitution + source registry — implemented

`foundry/data.py`. A `RightsDisposition` is a *claim*: it names a
`basis_ref` and carries no basis and no resolved flag. The state is derived by
resolving that ref against `fixtures/rights_evidence.json` (a
`RightsEvidenceRegister`), so a basis that was never recorded, or that was
recorded for a different subject, resolves to `REVIEW_REQUIRED` and can never
make a source train-permissive. An unrecognised basis becomes
`REVIEW_REQUIRED`, a terms claim with no recorded scope becomes
`RIGHTS_RESTRICTED`, `UNKNOWN` stays `UNKNOWN`. Sources declare their basis in
`sources.json`, and the loader fails closed (`RIGHTS_BASIS_UNRECORDED` /
`RIGHTS_DECLARATION_MISMATCH`) if a declaration disagrees with the record.
Roles are versioned; a training role requires recorded evidence permitting
training *on every entry path*; expanding from retrieval-only to a training role
requires review evidence; no-op transitions are refused; secret-bearing sources
cannot hold training roles. Mirror aliases resolve to one
lineage (`SRC_NEWS_ALPHA`/`SRC_NEWS_ALPHA_MIRROR` → 1 effective lineage for 2
requested sources). Rights permission is kept distinct from role permission
(`SRC_BENCH_CORE`: rights permit, `HIDDEN_EVAL` role forbids). Contamination is a
graded, typed relation graph where absence of an edge is explicitly *not* a
cleanliness certificate. CEREBUS-family material is withheld operationally.

Fixture registry digest:
`sha256:45a8ca061214e7a925876840edd4fe17f2d61970f68a156e444b021c78e807d1`
(replay-stable; the digest covers the rights *claim* per source, which is why it
changed when the claim stopped carrying caller-settable derived fields — see the
audit-closure defects below). Rights-evidence register fingerprint:
`sha256:58003351106736901f3d235ba10bd7d2d67e1045bfa63c7701f3653ecb5a33f9`, and
it is published as `b2_registry.rights_evidence_fingerprint`, so the evidence the
digest depends on is itself covered by the receipt.
Rights-blocked: `SRC_RIGHTS_UNKNOWN` (RIGHTS_UNKNOWN),
`SRC_VENDOR_TERMS` (RIGHTS_RESTRICTED), `SRC_PROHIBITED` (EXCLUDED_BY_POLICY).
Eligible for training: `SRC_AGENT_TRACE`, `SRC_NEWS_ALPHA`, `SRC_NEWS_ALPHA_MIRROR`.

### MF-B3 — Dataset refinery + corpus architecture — implemented

`foundry/refinery.py`. Declared deterministic recipe, no model inference in the
path. Exact duplicates are collapsed by digest; cross-source mirrors are caught
by near-duplicate detection and counted separately
(`cross_source_duplicate_count`). Secret scanning and point-in-time auditing
gate materialization; splits are by source, never by item. A dataset that cannot
be built yields a first-class negative result naming the dominant *actual*
reason and a reopen condition:

| attempt | outcome |
|---|---|
| governed train corpus | manifest with lineage `sha256:1b731fac408ceddab1aebb97b2d00e4e0a32869d268dfd6614abe68083dcacad` |
| withheld doctrine only | `CONTAMINATION_BLOCKED` |
| secret-bearing note only | `SCHEMA_INVALID` |
| fixture market data with a PIT instant | `PIT_INVALID` |

### MF-B4 — Frozen evaluation institution — implemented; evaluation execution simulated

`foundry/evaluation.py`. Protocol freeze before outcomes (freezing after peeking
refused), builder cannot author the sealed freeze that judges it, frozen
protocols are immutable. Sealed store: builder surface shows existence and
digest only; four builder roles are refused; role without a token refused;
operator-issued tokens required; every attempt — including refusals — recorded
and exposure budgeted per tier. Capability is a vector of dimension deltas;
`master_score` is always `None` and writing one raises
`MASTER_CAPABILITY_SCORE_FORBIDDEN`. PASS requires evidence that a different
runtime reproduced the measurements within tolerance: no replication → 
`INCONCLUSIVE (FRAMEWORK_UNVERIFIED)`; agreement obtained by simulation →
`INCONCLUSIVE (CROSS_FRAMEWORK_AGREED_SIMULATED)`; disagreement →
`CROSS_FRAMEWORK_DISAGREEMENT`. Negative results are first-class, reopening
requires new evidence, and unreachable reopen conditions are surfaced as dogma
risk.

Benchmark `RESEARCH_BENCH_V0` fingerprint
`sha256:9892b9431b095deaa6ec9bc09b9541e9314bbffd5ee840e0d6f393503c8cd280`,
protocol `PROTO_RESEARCH_BENCH_V0_V1`
`sha256:824fb9ae6c63b3bb7ec5c4103bfd4a2be585ce7f441ae3b0275906d3c1e7ee35`.

### Cross-block scenarios F0–F11 — PASS (12/12 HELD)

Report fingerprint `sha256:f85bee7526c074a13fb7867b631eb0860a25144059ff9e494352d1f88ab79d04`.
The behaviour is unchanged (12/12 `HELD`, same verdict, same refusal codes); the
fingerprint moved because F2's `RIGHTS_BLOCKED` refusal detail now names the ref
and the resolved state instead of asserting a disposition, and F5's
`unobserved_is_not_clean` marker became a verified boolean.
F0 constitution+boundary · F1 provider-neutral placement · F2 rights/roles/
permissions · F3 governed corpus · F4 PIT leakage · F5 contamination gating ·
F6 withheld doctrine · F7 evaluation freeze · F8 sealed boundary · F9 subject
credit separation · F10 negative results/reopen · F11 provider loss,
portability, secrets. Each scenario reports the refusals it observed.

## One-OCE boundary

Boundary fingerprint
`sha256:98cb4c61a3eb5856944f54f4495686701263bbc46c8e70928f22e3e41eb7627d`.
Full table: `integration-map.md` and
`model-foundry/fixtures/noncanonical_declarations.json`. Identity, authority, and
artifact storage are declaration-only — no local implementation exists, asserted
by test.

## External / live operations

| operation | count |
|---|---|
| public read-only calls | 0 |
| paid compute launched | 0 |
| provider launches | 0 |
| cloud mutations | 0 |
| production mutations | 0 |
| capital operations | 0 |
| model API calls | 0 |
| model training (any kind) | none |

## Scientific integrity

* rights blocks: 3 registered sources (`RIGHTS_UNKNOWN`, `RIGHTS_RESTRICTED`, `EXCLUDED_BY_POLICY`)
* contamination relations registered: 4, spanning C1–C4
* CEREBUS-family exposures: 0 (material withheld, not merely labelled)
* sealed-evaluation exposures: 0 (refusals recorded)
* negative results recorded: 1 (plus 3 refused dataset builds)
* evidence package: `evidence/MF_B0_B4_EVIDENCE.json`, fingerprint
  `sha256:2e4586e2f1f3755c35089888724eb0576771793215d77e54e709c04127b8f8a4`
  (replay-stable)

## Defect found and fixed during the build

Regenerating the evidence package produced a **different registry digest for
identical content**: `VersionedRegistry.digest()` included each entry's
wall-clock `recorded_utc`. A substrate whose premise is content-addressed
provenance cannot have a digest that moves when nothing scientific changed — the
same registry could not be proved to be the same registry.

Fixed in `07ed6617`: entry digest payloads exclude recorded time while keeping it
in the serialized record, receipts capture their timestamp at creation rather
than at serialization, protocol freezes accept an explicit replay clock, and the
evidence aggregate strips run timestamps before fingerprinting. Six regression
tests in `tests/test_mf_determinism.py` hold this, including one that fails if a
wall-clock key reappears anywhere the evidence fingerprint covers.

## Defects found and fixed in the audit-closure pass

An external audit of this build found that the package documented stronger
guarantees than it enforced. All three load-bearing findings were reproduced
before being fixed, and each now has a regression test that fails against the
old behaviour.

1. **A forged rights basis could make a rights-unknown source train-permissive.**
   `RightsDisposition.basis_resolved` was a caller-written boolean that nothing
   resolved, and `SourceRegistry.transition_role(..., rights=...)` accepted a
   caller-supplied disposition. Constructing
   `RightsDisposition(basis=PUBLIC_DOMAIN, basis_ref='rights://does-not-exist/forged', basis_resolved=True)`
   and passing it through the transition produced a training dataset whose
   `rights_summary` claimed `RIGHTS_VERIFIED_BY_POLICY` and
   `all_sources_train_permissive: true` for a source whose rights are `UNKNOWN`.
   Fixed by making the claim carry no basis and no resolved flag, deriving state
   only through `RightsEvidenceRegister.resolve()` bound to the subject, failing
   closed to `REVIEW_REQUIRED` for unrecorded or non-relevant evidence, and
   removing the `rights=` parameter so a transition cannot swap in a more
   favorable disposition. The invariant now has one owner — the registry's single
   `_commit` guard — rather than a per-method check.
2. **`register()` skipped the role contract that `transition_role()` enforced.**
   A record could be registered directly with `role=TRAIN_CPT`, with no review
   evidence, and `_role_history` recorded it indistinguishably from a legitimate
   transition. Fixed by routing both entry paths through `_commit`; a
   re-registration that changes the role is now held to the same transition
   contract, while a content-only re-registration still versions normally.
3. **The authoritative test command could not be audited for its own count.**
   `model-foundry/pyproject.toml` set `addopts = "-q"`, so the documented
   command `python -m pytest tests -q` ran as `-qq` and printed progress dots but
   no summary line. `addopts` is now `-ra`, and the command reports
   `157 passed`.

Three further defects the audit ranked were also closed: a benchmark status was a
free string compared against a hand-copied literal set, so
`status="COMPROMISEDD"` read as healthy and could still reach `PASS` — the field
is now a `BenchmarkStatus`, an unrecognised status raises
`BENCHMARK_STATUS_UNKNOWN` at construction, and `LIFECYCLE_MACHINES` is derived
from the declared enums instead of duplicating them; `FrozenMap` could not be
deep-copied or pickled (`TypeError: cannot pickle 'mappingproxy' object`), which
broke `copy.deepcopy`, `pickle`, and `dataclasses.asdict` on any record holding
one; and nine exported helpers with no caller anywhere (`IndependenceVector`,
`digest_of_bytes`, `ResumeProof`, `resource_receipt`, `tier_of`,
`claim_class_for`, `trust_class_admissible_for_remote`,
`total_contamination_grade`, `fixture_registry`) were removed rather than left to
inflate the apparent API.

What did **not** change: the constitution fingerprint (`0bc713f0…`), the B3
lineage fingerprint (`1b731fac…`), the 20-attack gate result, the 12/12 cross-block
verdict, and every external/live-operation count in the table below. The scope
limit is intact — no new capability, no training, no provider call, no paid
compute, no new third-party tooling.

## Contradictions and ambiguities carried forward

1. **`AMB-MF-01` (identity boundary).** `WEIGHTS` vs `INPUT_ENCODER` digests are
   recorded separately, but the substrate does not yet define which dimensions
   form the *minimum* identity for credit. Recorded, not resolved.
2. **`AMB-MF-02` (cross-source exact duplicates).** Exact-duplicate detection is
   digest-based and therefore source-scoped; mirrors are caught by near-duplicate
   similarity. If a source re-publishes byte-identical content, it is currently
   detected as a near-duplicate at similarity 1.0 rather than as an exact
   duplicate. Observable, not harmful, but it is a modelling choice.
3. **`CON-MF-01` (evaluator freeze authority).** `FoundryLocalEvaluationFreeze`
   freezes protocols locally. Pre-convergence this is a governed fixture; the
   constitutional question of *who may ratify future evaluation law* remains the
   same open question carried by G6 (`CON-03`/ER02) and is not answered here.
4. **`CON-MF-02` (withheld-doctrine detection).** Withholding is enforced by
   declared payload class; doctrine-shape token detection exists in MF-B0 but is
   not yet wired into the B2/B3 ingest path. Detection coverage is therefore
   declaration-dependent today.
5. **`CON-MF-03` (cost-to-close coefficients).** `THROUGHPUT_COEFFICIENTS` and
   preemption-loss fractions are declared fixtures. They are explicitly labelled
   assumptions in every estimate, but they are not measured hardware data.

## Recommended MF-B5 authorization

**CONDITIONAL — yes, only as a costed, operator-authorized run.** See the final
handoff report for the minimum-cost path and the exact prerequisites.
