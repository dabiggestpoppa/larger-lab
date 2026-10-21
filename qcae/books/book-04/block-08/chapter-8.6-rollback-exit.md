# Chapter 8.6 — Rollback & Exit

## Mission

Ensure every acquisition has a credible path back out before Quant Lab becomes dependent on it.

## Exit Questions

- Can the dependency be removed without system-wide rewrites?
- Can old implementation resume?
- Is state portable?
- Are upstream-specific types contained?
- What data/config must be migrated?
- What happens if upstream disappears or license changes?

## Rollback Trigger Classes

Contract regression, security incident, upstream compromise, legal incompatibility, unacceptable performance drift, operational instability, or superior replacement may trigger exit review.

## Exit Assets

Maintain adapter contract, state export/conversion, prior implementation or replacement path, pinned last-known-good evidence, and dependency removal instructions.

## No Hostage Architecture

A capability with high switching cost must have that burden recorded before adoption, not discovered during failure.

## Invariants

1. Exit is designed before cutover.
2. Adapter boundaries support replacement.
3. State portability is part of reversibility.
4. Last-known-good evidence is retained.
5. Switching cost is an acquisition cost.

## Exit Criteria

Quant Lab can describe and test the path to disable, replace, or roll back the acquired capability.
