# Book V — Block 13: Standalone Runtime

**Status:** IN BUILD

## Objective

Define the local runtime that allows QCAE to operate independently before OCE is complete while preserving contracts that OCE can later govern.

## Chapters

- 13.1 Local QCAE Runtime
- 13.2 Local Policy Engine
- 13.3 Local Evidence Store
- 13.4 Local Secrets Boundary
- 13.5 Local Sandbox Manager
- 13.6 Local Job Queue
- 13.7 Standalone CLI/API
- 13.8 Graceful OCE Absence

## Rule

Standalone mode is a real operating mode, not a temporary pile of mocks. It must be safe, testable, persistent, and migration-compatible with future OCE authority.
