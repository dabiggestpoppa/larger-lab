# Part 1 — Repository Fingerprint and Core Components

> **Status:** implemented_unverified — builder evidence passes; independent review is pending

## Goal

Produce deterministic, sanitized evidence for repository identity and the required Phase 0 component paths without inferring operational classification.

## Inputs

- Current git checkout
- Root workspace rules
- Phase 0 README and Book 1
- Required component path registry

## Allowed Changes

- tools/forge/
- tests/forge/phase_00/
- QUANT-LAB-INFRA-UPGRADE/implementation/phase-00/book-1/
- artifacts/forge/phase-00/book-01-part-01/

## Forbidden Changes

- Legacy trading, OCE, SRRA-OPH, agent, data, or execution implementation
- Git history, branch, remote, ignore, dependency, or secret configuration
- Live, paper, sandbox, or broker actions

## Deliverables

- A standard-library CLI for repository fingerprint and core-component discovery
- Sanitized remote metadata
- Stable fingerprint hash excluding generation time
- Bounded content identities for dirty and untracked worktree files
- Explicit self-output exclusion so generated evidence cannot create recursive drift
- Required-path coverage including explicit absent records
- Entrypoints mapped to exactly one component
- Part 1 evidence manifest

## Tests

- P0-REP-001: two unchanged collections have identical stable fingerprint fields
- P0-COV-001: every required path is represented or explicitly absent
- P0-COV-002: every discovered entrypoint has exactly one component
- P0-SEC-002: embedded remote credentials and sensitive query fields are removed

## Failure Cases

- Not a git repository: fail loudly
- Git command unavailable: fail loudly
- Unreadable tracked file: record bounded error metadata
- Required path absent: record absent, do not create it
- Oversized file: record metadata without full content scan
- Repository mutates during collection: evidence SHA mismatch blocks closure

## Exit

Part 1 closes when its tests pass, generated artifacts contain no remote credential, a second collection reproduces the stable fingerprint, and Part 2 accepts the component IDs and scan bounds.

## Current Builder Evidence

- python3 -m unittest discover -s tests/forge/phase_00 -p 'test_*.py': 12 passing
- Python compile check: passing
- Actual workspace collection: 15 required components represented
- Discovered entrypoints: 376, all uniquely owned
- Consecutive repository fingerprint replay: stable
- Consecutive core inventory replay: stable
- Generated credential-shaped literal scan: zero matches
- Generated artifacts: artifacts/forge/phase-00/book-01-part-01/

This evidence does not close the part because the required independent review has not occurred.
