# Chapter 4.5 — Complexity Accounting

## Mission

Estimate the real engineering burden of each plausible acquisition form before Book III invests in proving the wrong shape of solution.

## 4.5.1 Complexity Dimensions

```text
source size of MEU
direct/transitive dependencies
native/build complexity
state complexity
interface complexity
adapter effort
substitution effort
configuration surface
service/infrastructure burden
security surface
license surface
test migration effort
maintenance/churn
specialist knowledge
revalidation burden
exit/migration cost
```

## 4.5.2 Relative, Not Fake Precision

Early estimates should use evidence-backed ranges/classes rather than pretending to know exact engineering hours.

Examples:

```text
LOW / MEDIUM / HIGH
1-2 modules / 8-12 modules
0 services / 3 required services
```

## 4.5.3 Acquisition-Form Comparison

For the same atom compare:

```text
wrap focused dependency
extract component
vendor component
fork
reimplement from spec
adopt framework
extend internal implementation
```

Each has different present and future cost.

## 4.5.4 Framework Excess Burden

Explicitly calculate which dependencies/services/state/interfaces are required by the framework but not by the target capability.

This is the concrete anti-framework tax.

## 4.5.5 Maintenance Horizon

Estimate complexity over intended ownership horizon, not only initial integration.

## 4.5.6 Revalidation Cost

A capability with unstable upstream APIs may require frequent proof reruns. This is ownership cost.

## 4.5.7 Uncertainty Range

Complexity estimates should widen when dynamic dependencies, unclear licensing, undocumented state, or unproven build assumptions remain.

## 4.5.8 Complexity Record

```text
acquisition_form
initial_integration_burden
ongoing_maintenance_burden
operational_burden
revalidation_burden
migration_burden
framework_excess
uncertainties
confidence
```

## Invariants

1. Free code is not zero-cost capability.
2. Initial integration is only one cost dimension.
3. Framework excess is measured against target capability.
4. Revalidation and exit costs count.
5. Early estimates use honest ranges rather than false precision.

## Exit Criteria

QCAE can tell Book III which acquisition forms are worth proving and which are already economically dominated before runtime validation begins.
