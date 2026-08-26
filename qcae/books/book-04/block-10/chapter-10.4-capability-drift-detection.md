# Chapter 10.4 — Capability Drift Detection

## Mission

Detect when a capability's real usefulness, behavior, burden, or validated domain changes even if upstream source identity remains stable.

## Drift Types

`BEHAVIOR_DRIFT`, `PERFORMANCE_DRIFT`, `DEPENDENCY_BURDEN_DRIFT`, `OPERATIONAL_DRIFT`, `DOMAIN_DRIFT`, `DATA_DRIFT`, `INTERFACE_DRIFT`, `MAINTENANCE_DRIFT`.

## Baselines

Use Capability Receipt evidence and accepted integration measurements as reference, not undocumented expectations.

## Quant Drift

For financial capability, monitor whether the structural/regime conditions supporting validated behavior have materially changed. Do not equate short-term P&L variance with automatic invalidation; use predeclared domain/regime evidence and CEREBUS framing.

## Burden Drift

A dependency can remain functionally correct while becoming expensive, abandoned, insecure, or operationally complex enough that replacement should be reconsidered.

## Invariants

1. Capability value can drift without code change.
2. Drift is measured against explicit baselines.
3. Quant drift uses domain/regime evidence, not emotional P&L reaction.
4. Ownership burden is monitored alongside behavior.
5. Drift triggers review/revalidation, not automatic replacement.

## Exit Criteria

QCAE can recognize when an acquisition that was once rational is becoming stale or dominated.
