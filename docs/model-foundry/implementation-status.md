# Model Foundry — implementation status (MF-B0 → MF-B4)

* **Branch:** `agent/model-foundry-mf-b0-b4-build`
* **Start SHA:** `c55e379df3de2c6bb643afc90c10c0a861fa8c8a`
* **Tested SHA:** `5ac46b5ee4bfeebdfa96884eb7891e9f97918d92`
* **Authoritative test command:** `cd model-foundry && PYTHONIOENCODING=utf-8 python -m pytest tests -q`
* **Result:** `142 passed`

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

`foundry/data.py`. Rights states are derived from recorded basis evidence, not
from strings: an unresolved basis becomes `REVIEW_REQUIRED`, a terms claim with
no recorded scope becomes `RIGHTS_RESTRICTED`, `UNKNOWN` stays `UNKNOWN` and
never authorizes training. Roles are versioned; expanding from retrieval-only to
a training role requires review evidence; no-op transitions are refused;
secret-bearing sources cannot hold training roles. Mirror aliases resolve to one
lineage (`SRC_NEWS_ALPHA`/`SRC_NEWS_ALPHA_MIRROR` → 1 effective lineage for 2
requested sources). Rights permission is kept distinct from role permission
(`SRC_BENCH_CORE`: rights permit, `HIDDEN_EVAL` role forbids). Contamination is a
graded, typed relation graph where absence of an edge is explicitly *not* a
cleanliness certificate. CEREBUS-family material is withheld operationally.

Fixture registry digest:
`sha256:479ea7d31d31a1d6dc55f2ccd8d5d318df9c1152c94c3c08f2d459918f34f8b6`.
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

Report fingerprint `sha256:1eee59bc236a4262c6bfee2eafdbcad40c38bc9f53466d3fa978993be79b283f`.
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
  `sha256:1ea9bacc96e7e4d5d99d16abb5b125060a217234dabedf47644dfb389a0bdfbb`

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
