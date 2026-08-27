# Chapter 15.10 — Monitoring Services

## Mission

Implement continuous capability intelligence as scheduled/event-driven services that detect material upstream and internal change, calculate blast radius, and create targeted revalidation work without auto-updating protected systems.

## Services

```text
WatchRegistryService
UpstreamChangeDetector
DependencyChangeDetector
LicenseChangeDetector
VulnerabilitySignalService
CapabilityDriftAnalyzer
BlastRadiusService
RevalidationPlanner
SupersessionScanner
EngineeringReviewQueue
```

## Monitor State

Every watch record links:

```text
capability/integration
source/package/service identities
last reviewed revision
revalidation triggers
last check
current health state
open review jobs
```

## Differential Revalidation

Change detection maps modified source/dependencies/specification into affected atoms, assumptions, tests, and receipts. Re-run only bounded evidence when impact can be proven; otherwise escalate to broader proving.

## No Auto-Upgrade

Monitoring may fetch metadata/source into quarantine and create recommendations. It cannot silently update an integrated dependency, fork, adapter, or strategy.

## Security Priority

Material vulnerability, license, ownership, or supply-chain changes can raise urgent review jobs and policy alerts.

## Invariants

1. Monitoring detects and proposes; it does not auto-promote updates.
2. Watch state is tied to immutable reviewed revisions.
3. Differential revalidation requires defensible impact mapping.
4. Unknown blast radius escalates to broader validation.
5. Security/legal changes can override normal review priority.
6. Supersession intelligence considers internal and external alternatives.

## Exit Criteria

The coding agent can maintain acquired capability over time without either ignoring upstream drift or rerunning the entire validation universe on every change.
