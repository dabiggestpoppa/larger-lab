# Chapter 15.8 — Acquisition Services

## Mission

Implement the Book IV acquisition spectrum as explicit services that generate integration plans/artifacts without bypassing authority.

## Services

```text
AcquisitionDecisionService
AdapterPlanner
ExtractionPlanner
VendoringPlanner
ForkPlanner
ReimplementationPlanner
MigrationPlanner
RollbackPlanner
IntegrationAcceptanceService
```

## Inputs

Acquisition services consume:

- proven capability/contract state;
- trust/legal findings;
- quant findings where required;
- complexity/value analysis;
- internal baseline;
- approved acquisition-form constraints.

## Outputs

They emit implementation plans, adapter/interface definitions, patch/work-package proposals, migration/rollback plans, and authority requests where required.

## No Direct Promotion

Generating code or an integration patch does not mean that patch is authorized for protected merge/deployment. Build artifacts and authority are separate.

## Interface-First Rule

Adapters/internal contracts are created before upstream-specific APIs spread into Quant Lab. Vendoring/forking/extraction preserve provenance metadata automatically.

## Reimplementation Traceability

Clean reimplementations retain references to normative specs/papers/tests and avoid copying implementation-specific code where the acquisition decision requires independent implementation.

## Invariants

1. Acquisition services implement the full Book I spectrum.
2. Integration plans are distinct from promotion authority.
3. Quant Lab-owned interfaces are preferred boundaries.
4. Provenance follows vendored/forked/extracted assets.
5. Migration and rollback are mandatory for material integrations.
6. Reimplementation paths preserve specification/research provenance.

## Exit Criteria

The coding agent can turn a proven recommendation into a reversible implementation work package while keeping governance gates intact.
