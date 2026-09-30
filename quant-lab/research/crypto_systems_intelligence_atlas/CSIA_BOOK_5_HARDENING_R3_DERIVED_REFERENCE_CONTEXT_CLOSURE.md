# BOOK 5 HARDENING R3 — DERIVED-REFERENCE CLOSURE + NON-COMPONENT QUANTITATIVE CONTEXT SEAL

> **Date:** 2026-09-29
> **Branch:** `agent/crypto-systems-intelligence-atlas-book5-build`
> **Starting HEAD:** `9f5c0ea03a2c6975d5689dbc11d6145fa61a9ddb` (R2 exit state)
> **Book 4 base (freeze reference):** `a2526e8220513b34967ab11f227ddbddc14e7e4a`
> **Trigger:** newly demonstrated concrete correctness class on the R2 kernel
> **Status:** all 21 R3 gates PASS — `BOOK_5_HARDENING_R3 = PASS`

---

## 1. Why R3 exists — and precisely what R2 did NOT close

R2 made authority context mandatory for the **principal-component and snapshot
composition** surfaces: provenance became a required constructor argument of
`CapitalFieldSynthesis`, `validate_principal_component` stopped skipping
unbound claims (NO CONTEXT BINDING != CONTEXT VERIFIED for components), and
`compose_snapshot` revalidated every canonical input against live Book 2
state.

R3 was triggered by the remaining, concretely demonstrated defect surfaces the
R2 seal did not touch:

| Defect | Surface | R2-kernel behavior (demonstrated) |
|---|---|---|
| R3-D1 | `CapitalFieldSynthesis.compose_path` | checks only `len(stage_record_refs) > 0`; `("fake:issuance", "fake:credit", "fake:exit")` produced a **`derived=True`** `CapitalFieldPath` — an arbitrary string became derived 5G authority (INV-5G-1 input-lineage violation) |
| R3-D2 | `CapitalFieldSynthesis.topology_view` | checked only that `node_record_refs` was non-empty; `("ghost:node",)` + `edge_flow_refs=("ghost:flow",)` produced a **`derived=True`** `CapitalTopologyView` |
| R3-D3 | `observed_value_display` | rendered fields directly with NO live validation; a valid fact → `model_copy(book2_claim_refs=())` → display **succeeded**, bypassing the R2 compose seal |
| R3-D4 | `_validate_flow` / `_validate_liability` / `_validate_observed_value_fact` | called only `resolve_claim_refs` (claim exists, current, evidenced); an ETH flow → `model_copy(unit="USDC")` with identical canonical claim refs **passed 5G composition** (likewise liability asset/site and fact numeraire/subject/reporter mutations) |

R2 closed omission/context bypass for principal components and snapshot
composition. R3 closes the remaining 5G derived-reference surfaces and the
semantic context of non-component quantitative records. Nothing else changed.

## 2. Reproductions (failure-first commit `97270f92`; all rows now enforce)

All 27 initial rows failed on the unmodified R2 kernel exactly at the missing
seal — demonstrating each defect live before any implementation commit.

**Fake path (R3-D1, A1):**

```python
synthesis.compose_path(
    "path:a1",
    stage_record_refs=("fake:issuance", "fake:credit", "fake:exit"),
    valid_time=T0, observed_at=T0,
)                       # R2 kernel: returned derived=True path  → now Book5ProvenanceError
```

**Fake topology (R3-D2, B1/B2):**

```python
synthesis.topology_view(
    "topo:b1",
    node_record_refs=("ghost:node",),
    edge_flow_refs=("ghost:flow",),
    valid_time=T0, observed_at=T0,
)                       # R2 kernel: returned derived=True view → now Book5ProvenanceError
```

**Display bypass (R3-D3, C1):**

```python
tampered = valid_fact.model_copy(update={"book2_claim_refs": ()})
synthesis.observed_value_display(tampered)   # R2 kernel: rendered payload → now Book5ProvenanceError
```

**Flow context mutation (R3-D4, D1):**

```python
tampered = eth_flow.model_copy(update={"unit": "USDC"})   # same canonical claim refs
synthesis.compose_snapshot("snap:d1", flows=(tampered,), ...)
# R2 kernel: composition succeeded → now Book5ProvenanceError
```

**Liability context mutation (D5–D7):** `unit USDC→ETH`, `asset USDC→WBTC`,
`market_site_id → unrelated site` — identical claim refs, all refused.

**Observed-value context mutation (D9–D11):** `numeraire USD→BTC`,
`subject_ref → other subject`, `reporter_ref → imposter (when bound)` — all
refused at compose and display.

## 3. Design

### 3.1 QuantitativeRecordContextBinding (R3 Phase 5/6)

`book5_provenance.py` gains a narrow, Book 5-local typed family — PrincipalComponent
keeps its R2 `ClaimContextBinding` semantics untouched:

- `QuantitativeRecordKind` = `FLOW | LIABILITY | OBSERVED_FACT`;
- `QuantitativeRecordContextBinding(claim_id, record_kind, asset_ref?,
  realization_ref?, unit?, site_ref?, subject_ref?, reporter_ref?, numeraire?,
  basis_claim_refs=())` — frozen, `extra="forbid"`, must establish ≥ 1
  dimension;
- `REQUIRED_CONTEXT_DIMENSIONS` (Phase 6, mechanical — only dimensions present
  in the ratified record contracts are bound; nothing is invented to satisfy
  validation):
  - `FLOW` → `asset_ref, unit` (+ realization context whenever the live record
    carries a `realization_ref`);
  - `LIABILITY` → `asset_ref, unit` (+ `site_ref` where the binding declares
    it);
  - `OBSERVED_FACT` → `subject_ref, numeraire` (+ `reporter_ref` when binding
    doctrine requires reporter identity);
- registration via `bind_quantitative_record_context` mirrors the R2 contract:
  typed-only (raw dicts refused), subject claim and every `basis_claim_refs`
  entry resolved through Book 2, rebinding refused (registration-time facts,
  not mutable state);
- decision-time `validate_quantitative_record(record)` enforces
  **NO BINDING != CONTEXT VERIFIED**: the binding set must ESTABLISH every
  required dimension and every bound dimension must AGREE with the live record
  (`market_site_id` carries the liability's site dimension). Context fields
  remain explicitly BOOK 5-LOCAL TYPED INTERPRETATION — Book 2 proves the
  claims are canonical, current, and evidenced; it does not natively encode
  these dimensions, and R3 claims no more than that.

### 3.2 Book5CanonicalRecordRegistry (R3 Phase 7)

New module `book5_registry.py` — the narrowest offline resolver that lets 5G
derived views prove their references exist:

- in-memory, deterministic, offline; **no database, no graph DB, no second
  epistemic engine**; it registers, it never mints;
- categories: positions, flows, liabilities, observed facts, transformations,
  economic sites (site namespace `csia:site:` is Book 1-anchored identity);
- registration is fail-closed in a deliberate order: typed identity guard →
  live Book 2 provenance validation → R3 context seal (flow/liability/fact
  kinds) → namespace + uniqueness checks;
- resolution distinguishes **UNKNOWN** (never registered), **DETACHED**
  (class cannot appear in the requested role), and **WRONG-KIND** (registered,
  different kind) — all three REJECT.

### 3.3 5G reference closure (R3 Phase 8–10)

`CapitalFieldSynthesis.compose_path` / `topology_view` now REQUIRE the
canonical registry (keyword, explicit `None` fails closed):

- **Path semantics:** every stage ref resolves as a canonical position record;
  order preserved exactly as given; duplicates REJECT (no ratified semantics
  allow repeated stages — a repeat fakes a multi-stage path); a stage the
  inputs do not assert can only be an explicit `Gap`, never a fabricated ref;
  no economic causality is inferred.
- **Topology semantics:** every node ref resolves as a canonical position
  (flows are edges; facts are never capital nodes); every edge flow ref
  resolves as a canonical flow; for each edge flow whose canonical record
  asserts position endpoints, the endpoint must resolve in the registry and,
  when registered but absent from the node set, the omission is carried as an
  explicit `Gap` (`FLOW_ENDPOINT_NOT_IN_TOPOLOGY`) — never a fabricated node;
  incomplete truth stays incomplete.
- The derived-view boundary (not `__init__`) carries the registry so the R2
  mandatory-provenance construction seal keeps exactly one blast radius.

### 3.4 Display seal (R3 Phase 11)

`observed_value_display` validates the LIVE fact before rendering: typed guard
(raw dict → typed fail-closed error), Book 2 claim resolution, and the R3
quantitative context seal. Display-only is preserved: no conversion, no
valuation derivation; the payload kind stays `OBSERVED_COMMON_VALUE_FACT`
(≠ `CSIA_DERIVED_COMMON_VALUE`) and `valuation_request()` stays
`NOT_AUTHORIZED` (C5).

## 4. model_copy R3 attack matrix (R3 Phase 12; commit `25949c64`)

Every authority-producing path revalidates live state — a `model_copy`-
tampered artifact is inert data whose refs cannot re-enter the boundary that
produced it:

| Group | Rows | Demonstrated rejection |
|---|---|---|
| PATH | P1, P2, P3 | stage removed (empty re-entry refused), stage → fake ref, stage → wrong-kind canonical ref (flow as stage) |
| TOPOLOGY | T1, T2, T3, T4 | fake node, fake flow, node swapped to canonical non-position record, flow endpoint ref mutated to an unresolvable position |
| FLOW | F1, F2, F3, F4 | unit, asset, realization, claim refs stripped |
| LIABILITY | L1, L2, L3, L4 | unit, asset, site, claim refs stripped |
| OBSERVED | O1, O2, O3, O4 | numeraire, subject, reporter, claim refs stripped — rejected at display |

## 5. Preservation (R3 Phase 13)

- **R1 gates:** `test_book5_hardening_r1.py` 37/37 PASS. Only fixture change:
  the R1 flow-corpus kernel binds the fixture claim's flow context
  (`QuantitativeRecordContextBinding`, asset ETH / unit ETH) — the flow-only
  defect demonstrations (no fabricated principal, explicit gap, no placeholder
  token, no fake claim refs) are unchanged and stay pointed at their original
  defect class. A side repair in the same commit: `compose_snapshot` no longer
  refuses facts-only inputs (an observed fact IS a canonical input; its refs
  were already isolated out of `liability_refs`).
- **R2 gates:** `test_book5_hardening_r2.py` 44/44 PASS; zero changes to any
  R2-sealed API (`aggregate_same_unit`, `components_for`, `collapse_same_unit`,
  `CapitalFieldSynthesis.__init__` provenance requirement,
  `validate_principal_component`, S4 coverage closure).
- **45 stress rows + T-1..T-14:** `test_book5_blocs.py` 25/25 and
  `test_book5_adversarial.py` 31/31 PASS; the write-count-zero proof
  (`test_5g_canonical_write_count_zero_by_construction`) unchanged — the
  registry registers, it never mints.
- **Books 1–4 + Sensor:** untouched (freeze section below).

## 6. Verification

| Check | Prior baseline | After R3 |
|---|---|---|
| Book 1 | 107 | 107 |
| Book 2 | 108 | 108 |
| Book 3 | 83 | 83 |
| Book 4 | 230 | 230 |
| Book 5 | 159 | **205** (core 22 + adversarial 31 + blocs 25 + R1 37 + R2 44 + **R3 46**) |
| Total CSIA | 687 | **733** |
| R3 focused | — | 46/46 PASS |
| Ruff (full Book 5) | PASS | PASS |
| mypy | 43 files clean | 44 files clean |
| Sensor | 2325 PASS / 14 FAIL / 4 SKIPPED | identical (pre-existing storage-evidence regen set only; Book5-introduced = 0) |

R3-focused rows: A1–A5, B1–B5, C1–C5, D1–D12 (27 reproductions) + P1–P3,
T1–T4, F1–F4, L1–L4, O1–O4 (19 matrix rows) = 46.

## 7. Freeze (R3 Phase 17)

`git diff a2526e822..HEAD` touches only Book 5 modules/tests and append-only
CSIA evidence/ledger files:

- BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
- BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
- BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
- BOOK_4_ACCEPTED_CONTRACT_MUTATIONS = 0
- CRYPTO_SENSOR_MUTATIONS = 0

## 8. Status

```text
BOOK_5_HARDENING_R3 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL (still PROPOSED)
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```

No R4: another hardening round requires a newly demonstrated concrete
correctness defect. The next action belongs to the operator: Book 5
acceptance review.

## 9. Limitations (unchanged, still explicit)

Offline deterministic kernel only — no live acquisition, RPC, CEX feeds,
persistent DB, graph DB, production scheduler, Book 6 valuation, production
pricing, or trading/execution authority. Magnitude-vs-claim verification
remains the evidence layer's authority (Sensor/Book 4), as documented in R2
(D7). Context dimensions bound here are Book 5-local typed interpretations of
canonical Book 2 claims, not fields Book 2 natively encodes.
