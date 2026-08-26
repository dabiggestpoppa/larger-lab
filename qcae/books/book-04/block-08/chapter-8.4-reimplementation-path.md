# Chapter 8.4 — Reimplementation Path

## Mission

Acquire capability semantics without inheriting upstream implementation when recovered specification and burden analysis show independent implementation is superior.

## Inputs

Use normative/public specification, recovered contract, independently created tests/fixtures where appropriate, and documented behavioral requirements. Preserve provenance of informational sources.

## Clean Boundary

Do not present copied/transformed source as independent reimplementation. Legal/policy requirements from Book III govern permissible reference material and process.

## Test-First

Implement against Quant Lab-owned contract tests, then adversarial/performance tests. Upstream implementation may serve as a comparison oracle only where policy permits and semantics are not known-buggy.

## Behavioral Divergence

When observed upstream quirks conflict with normative/desired semantics, record deliberate divergence instead of silently cloning bugs.

## Ownership

Reimplementation trades dependency burden for internal maintenance burden; that burden enters the Capability Receipt.

## Invariants

1. Reimplementation targets capability semantics, not source imitation.
2. Legal/provenance boundaries remain explicit.
3. Quant Lab-owned tests define acceptance.
4. Known upstream bugs are not automatically reproduced.
5. Internal ownership cost is acknowledged.

## Exit Criteria

A clean implementation can satisfy the same contract while remaining independently owned and evidence-traceable.
