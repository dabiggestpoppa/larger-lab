# Book V — Block 15 Freeze Review

**Result:** READY TO FREEZE

## Chain

```text
15.1 Package Topology
→ 15.2 Core Domain Boundaries
→ 15.3 Discovery Adapters
→ 15.4 Intelligence Services
→ 15.5 Audit Services
→ 15.6 Proving Services
→ 15.7 Quant Services
→ 15.8 Acquisition Services
→ 15.9 Evidence & Registry Services
→ 15.10 Monitoring Services
→ 15.11 OCE Adapter Boundary
→ 15.12 CLI/API Interfaces
```

## Frozen Invariants

1. QCAE source topology reflects domain responsibilities, not vendor identities.
2. Core domain packages are provider/infrastructure independent.
3. External providers enter through adapters/ports.
4. DeepWiki remains a replaceable comprehension provider.
5. Trust audits return structured findings but never grant authority.
6. Proving is sandboxed, manifest-driven, evidence-first, and backend-neutral.
7. Quant validation remains a separate domain firewall with CEREBUS-specific authoritative logic isolated under its own module.
8. Acquisition services produce reversible work packages; they do not auto-promote integrations.
9. Evidence/registry persistence is abstracted from storage engines and preserves negative knowledge.
10. Monitoring detects and plans revalidation; it does not auto-update protected systems.
11. OCE implementation code lives only in governance adapters.
12. CLI/API call stable application use cases, not workers directly.
13. Deployment topology can begin as one local application despite strong source modularity.
14. Provider/model/storage substitutions should not require capability-semantic changes.

## Implementation Consequence

The coding agent now has a canonical dependency direction:

```text
Interfaces
   ↓
Application / Orchestration Services
   ↓
QCAE Core Domain
   ↑
Provider Ports
   ↑
Infrastructure / GitHub / DeepWiki / Sandbox / LLM / OCE Adapters
```

Concrete providers depend inward on stable contracts; domain logic never depends outward on provider implementations.

**Block 15 status: FROZEN v0.1.**
