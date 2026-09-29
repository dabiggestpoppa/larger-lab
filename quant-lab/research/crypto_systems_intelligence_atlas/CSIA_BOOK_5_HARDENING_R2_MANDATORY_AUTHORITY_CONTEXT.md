# CSIA Book 5 Hardening R2 — Mandatory Authority Context + Quantitative Context Closure

- **Date:** 2026-09-29
- **Branch:** `agent/crypto-systems-intelligence-atlas-book5-build`
- **Starting HEAD:** `fe4e1ba7dc3367387d898c29bc1f9f62242f6669` (R1 exit state; origin-matched, clean)
- **Accepted Book 4 base:** `a2526e8220513b34967ab11f227ddbddc14e7e4a`
- **Trigger:** two demonstrated defects from external review — R2-D1 (optional provenance bypass) and R2-D2 (optional claim-context-binding bypass). This is NOT generic hardening.

## Why R2 Existed

R1 made live Book 2 validation **AVAILABLE** at Book 5 authority boundaries —
but only when a provenance resolver happened to be supplied. External review
demonstrated that validation was **OPTIONAL** at exactly the points that
produce economic conclusions. That distinction is the core defect:

- **R2-D1** — `PrincipalComponentSet.aggregate_same_unit(..., provenance=None)`
  silently downgraded the boundary to `require_canonical_state` (a bare enum
  check). Reproduced: UNKNOWN → `model_copy(attribution_state=EXACT)` →
  `aggregate_same_unit("ETH")` **without** provenance returned `"3"`. A
  generic `ECONOMIC_FACT` claim marked EXACT aggregated with zero Book 2
  verification; an explicitly passed `None` also bypassed.
- **R2-D1B** — `CapitalFieldSynthesis()` (provenance `None`) composed
  stripped-ref, swapped-claim, and detached-claim positions with all
  canonical-input validators early-returning.
- **R2-D2** — `validate_principal_component` executed
  `binding = self._context_bindings.get(ref); if binding is None: continue`.
  With a correct `PRINCIPAL_EXACT_FACT` basis, unit ETH→USDC, asset ETH→WBTC,
  realization chain-A→chain-B mutations, and a fully contextless exact
  component all **PASSED** authority aggregation.

## Repairs

1. **Mandatory authority provenance (Phases 2/7/8).** `provenance` is a
   required keyword on `aggregate_same_unit`, `components_for`,
   `collapse_same_unit`, and the required first constructor argument of
   `CapitalFieldSynthesis(provenance, ledger=None)`. No default `None`; an
   explicit `None` raises the typed `Book5ProvenanceError`. Purely structural
   graph inspection is separated as
   `CapitalPrincipalLineageGraph.inspect_components_for(record_id)`
   (documented non-authoritative; performs no Book 2 validation; its output
   must not back any economic conclusion). Central R2 invariant: **forgetting
   an optional argument must never change the epistemic strength of an
   output.** No global provenance singleton; no second epistemic engine.
2. **Context-binding closure (Phases 3/4/6).** The `binding is None: continue`
   bypass is removed. Every claim ref of a quantitative component must carry
   an explicit `ClaimContextBinding` agreeing with the component's live
   asset/unit/realization, and the binding set must **establish** asset and
   unit context (realization context too whenever `realization_ref` is
   present). Rule: **NO CONTEXT BINDING ≠ CONTEXT VERIFIED** — an
   unverifiable dimension is never silently treated as a verified one.
3. **Evidence-bound `ClaimContextBinding` (Phase 5).** New
   `basis_claim_refs` are resolved through the accepted Book 2 claim/evidence
   engines at registration (canonical, current, evidenced). Raw dict binding
   input, duplicate/conflicting binding identity, detached basis claims, and
   vacuous (dimension-less) bindings are refused. Documented honestly: Book 2
   proves the basis claims canonical/current/evidenced; the
   asset/realization/unit **fields** are a Book 5-local typed contextual
   interpretation used by the economic kernel, because the Book 2 Proposition
   schema cannot natively represent those dimensions.
4. **S4 coverage closure (found by the Phase 10 attack matrix).** 5G compose
   additionally requires the position's claim refs to cover every nested
   component's claim refs; the R1-D4 typed guard runs first so raw nested
   payloads still fail closed with typed errors, never `AttributeError`.

## Attack Proof

- **Phase 9 model_copy matrix D1–D11** (attribution cycle, unit, asset,
  realization, claim refs, binding identity swap, quantity, naive valid_time,
  nested component, raw string state, raw binding dict): every
  authority-producing operation revalidates the live object. D7 documents the
  quantity-magnitude boundary deliberately: magnitude-vs-claim verification
  lives in the evidence layer, not Book 2's Proposition schema — this row is
  an explicit design boundary, not a silent pass.
- **Phase 10 synthesis attacks S1–S10:** only S10 (coherent canonical input
  with explicitly bound authority context) passes; S1 proves the engine
  cannot even be constructed into an authority-bearing mode without
  provenance.

## Failure-First Discipline

12 R2 tests were red at commit 1 (R2-D1 ×4, R2-D1B ×4, R2-D2 ×4) and each
group turned green only with its corresponding seal commit. Positive
baselines (A3b/A5/B5/C5–C8) anchored the repair throughout.

## Quality

- **Ruff:** PASS — full Book 5 tree clean (6 source + 5 test modules). 31
  findings fixed lint-only, including the 9 pre-existing findings in
  `test_book5_adversarial.py` authorized for this pass. Behavior unchanged;
  no coverage removed; Books 1–4 files untouched. Reported as lint cleanup,
  not correctness.
- **mypy:** PASS — no issues in 43 source files.

## Freeze & Sensor

- Freeze vs `a2526e822…`: `git diff --name-only` over the full range shows
  ONLY Book 5 modules/tests and append-only CSIA evidence/ledger files —
  `BOOK_1..4_ACCEPTED_CONTRACT_MUTATIONS = 0`, `CRYPTO_SENSOR_MUTATIONS = 0`.
- Sensor: **2325 PASS / 14 FAIL / 4 SKIPPED** (~153s). Failure set: i05r2 (3) +
  i05r3 (2) + i05r4 (3) + i06 (3) + i06r1 (3) storage evidence-matrix regen —
  identical to the accepted baseline. `BOOK5_INTRODUCED_SENSOR_FAILURES = 0`.

## Counts

| Suite | Before R2 | After R2 |
|---|---|---|
| Book 1 | 107 | 107 |
| Book 2 | 108 | 108 |
| Book 3 | 83 | 83 |
| Book 4 | 230 | 230 |
| Book 5 | 115 | **159** (115 preserved + 44 R2 focused) |
| **Total CSIA** | **643** | **687** |

## Status

```text
BOOK_5_HARDENING_R2 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```

NEXT = BOOK 5 OPERATOR ACCEPTANCE. No R3: another hardening round requires a
newly demonstrated concrete correctness defect.

## Limitations (unchanged, still explicit)

Offline deterministic kernel only — no live acquisition, RPC, CEX feeds,
persistent DB, graph DB, production scheduler, Book 6 valuation, production
pricing, or trading/execution authority.
