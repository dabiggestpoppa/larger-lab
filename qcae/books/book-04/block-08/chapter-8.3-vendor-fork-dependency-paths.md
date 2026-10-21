# Chapter 8.3 — Vendor / Fork / Dependency Paths

## Mission

Define disciplined ownership rules for acquiring upstream implementation directly.

## Dependency

Prefer when upstream package boundary is focused, versionable, legally compatible, reproducible, and low-coupling. Pin according to policy and retain source/artifact identity.

## Vendor

Use when source ownership/reproducibility/control justifies carrying code internally. Preserve provenance, license notices, upstream origin, local patch ledger, and update method.

## Fork

Use only when sustained divergence is justified. Record fork point, upstream relationship, patch purpose, merge strategy, test obligations, and ownership responsibility.

## Patch Ledger

Every local deviation must state why it exists, affected atoms, tests proving it, and whether it should be upstreamed/retired.

## Update Discipline

Never update merely because a new release exists. Block 10 evaluates differential relevance and triggers scoped revalidation.

## Invariants

1. Direct dependency is preferred over unnecessary source ownership when burden is lower.
2. Vendoring preserves provenance and legal obligations.
3. Forking creates explicit ownership debt.
4. Local patches are individually explainable/tested.
5. Upstream updates never bypass revalidation.

## Exit Criteria

Any source-owning acquisition path has explicit provenance, patch/update discipline, and maintenance ownership.
