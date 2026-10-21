# Chapter 10.1 — Watch Registry

## Mission

Maintain explicit watch relationships between active/stale capability receipts and the upstream/internal objects whose changes could invalidate them.

## Watch Targets

Repository/package releases, pinned branches/tags, dependencies, vulnerabilities, license files, standards/specs, datasets/providers, internal adapters, local patches, contracts, and CEREBUS/manual/config revisions.

## Trigger Types

`SOURCE_CHANGE`, `DEPENDENCY_CHANGE`, `LICENSE_CHANGE`, `SECURITY_SIGNAL`, `CONTRACT_CHANGE`, `DATA_CHANGE`, `DOMAIN_DRIFT`, `INTERNAL_CHANGE`, `POLICY_CHANGE`.

## Risk-Based Cadence

High-impact/high-churn capabilities receive more attention than stable low-impact components. Event-driven signals are preferred where available; scheduled refresh fills gaps.

## Invariants

1. Watches are receipt/evidence-linked.
2. Watch scope follows actual invalidation dependencies.
3. Monitoring depth is risk/churn weighted.
4. A detected change triggers evaluation, not automatic update.

## Exit Criteria

QCAE knows what external/internal changes matter to each trusted capability.
