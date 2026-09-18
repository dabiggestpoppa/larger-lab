# Model Foundry → OCE integration map

The Foundry is a **domain institution beneath OCE**. It owns model-side
semantics (sources, rights decisions, dataset manifests, training recipes,
provider-neutral compute plans, benchmarks, evaluation protocols, capability
vectors, negative results). It owns none of the generic institutional services.

Generated from code: `model-foundry/fixtures/noncanonical_declarations.json`
(`python -m foundry.cli boundary`). The registry is enforced by
`foundry.oce_boundary.assert_boundary_complete()` and asserted in tests, so a
new local fixture cannot be added without a retirement path.

## Fixtures that exist in this build

| Local fixture | Canonical OCE target | Replacement condition | Present scope |
|---|---|---|---|
| `FoundryLocalEvidenceLedger` | OCE EvidenceGraph / evidence registry | convergence branch exposes canonical evidence graph | provenance links only; no generic evidence graph |
| `FoundryLocalOfferNormalizer` | OCE B10 Resource Intelligence (`COMPUTE.GPU.RENT`) | B10 exposes provider-neutral offer/routing | offer normalization + placement; no provider API calls |
| `FoundryLocalRunLifecycle` | OCE WorkGraph / governed workflow | generic workflow service exists | dataset/experiment run records only; no scheduler |
| `FoundryLocalNegativeKnowledge` | OCE NegativeKnowledge with governed reopen semantics | canonical NegativeKnowledge consumable | negative results + reopen records only |
| `FoundryLocalEvaluationFreeze` | OCE B6 Evaluation Service / evaluator freeze (G6 lineage) | OCE owns evaluator freeze/ratification authority | protocol freeze + sealed access boundary only |
| `FoundryLocalCheckpointRecovery` | OCE recovery/resume service | generic recovery exists | portable checkpoint manifests + simulated resume only |
| `FoundryLocalBudgetLedger` | OCE resource budget service | OCE budget authority consumable | explicit operator budget arithmetic only; no spend path |

## Declarations only (no local implementation)

These are named in `foundry.core.GENERIC_SERVICE_DOUBLES` so the boundary is
complete on paper, but the Foundry builds **no** local implementation of them —
OCE owns them outright:

* `FoundryLocalIdentity` → OCE identity / actor registry
* `FoundryLocalAuthorityProjection` → OCE AuthorityState / capability grants (A-009/A-010 lineage)
* `FoundryLocalArtifactStore` → OCE artifact registry + artifact-manifest envelope

Tests assert that no module implements these three
(`tests/test_mf_boundary_and_cross_block.py::
test_declared_generic_services_are_not_implemented_locally`).

## Ownership split

| State | Canonical owner | Foundry role |
|---|---|---|
| Operator authority | OCE | consume projection only |
| Institutional truth | OCE | submit evidence/candidates |
| Evaluator activation authority | OCE / governed fixture pre-convergence | consume |
| Global capability status | OCE CapabilityGraph | propose candidate only |
| Model identity, dataset lineage, benchmarks, runs, checkpoints, capability assessments | Foundry domain | own |

## Injection points for convergence

1. **Compute**: replace `foundry.providers` adapters with a client that submits a
   `ComputeRequest` to B10 and consumes a routing decision. `ComputeRequest` has
   no provider field, so nothing else changes.
2. **Evidence/provenance**: replace `FoundryLocalEvidenceLedger` links in
   `SourceRecord`/`DatasetManifest` with canonical OCE envelope ids.
3. **Authority**: replace the local operator-grant check in
   `foundry.resources.verify_operator_grant` with the canonical OCE authority
   projection. The operator-hold behaviour must survive the swap.
4. **Evaluation governance**: move `freeze_protocol` to the canonical evaluator
   service so freeze receipts are issued outside the Foundry.
5. **Negative knowledge**: route `NegativeKnowledgeStore` reopen decisions
   through the canonical lifecycle so reopen conditions are not Foundry-local.

## Non-duplication guarantees

* no second authority engine, identity system, generic evidence constitution,
  WorkGraph, artifact store, institutional memory, scheduler, or recovery system;
* no constitutional amendment machinery;
* every local stand-in is `noncanonical: true` with a declared retirement path;
* `FOUNDRY_FORBIDDEN_AUTHORITIES` blocks the ten authority actions the Foundry
  may never perform, including `amend_doctrine` and
  `write_global_capability_status`.
