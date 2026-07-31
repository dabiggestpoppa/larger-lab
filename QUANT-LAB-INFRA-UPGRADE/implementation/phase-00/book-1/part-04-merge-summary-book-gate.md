# Part 4 — Canonical Merge and Book Gate

## Goal

Merge verified Part 1–3 evidence into the draft WorkspaceInventory, human-readable summary, component diagram, and reproducible Book 1 gate.

## Inputs

- Current matching repository fingerprint
- Verified Part 1–3 artifacts
- All Book 1 executable test results

## Required Behavior

- Reject artifacts produced from a different repository SHA or scan policy.
- Preserve absent, unknown, claimed, blocked, truncated, and contradiction states.
- Generate workspace-inventory.json, inventory-summary.md, and Mermaid topology.
- Record passing, failing, blocked, not-run, and not-implemented obligations separately.
- Emit a nonauthorizing BookGateRecord for independent validation.

## Exit

Book 1 closes only when every required component has a stable ID, every discovered entrypoint maps to a component, fingerprint replay passes, claims have provenance, secret outputs are redacted, all unknowns remain explicit, and the independent validator can reproduce the result.
