# Chapter 18.1 — Phase Sequencing

## Mission

Freeze the build order so the implementation agent does not invent architecture or prematurely add autonomy before foundations are proven.

## Canonical Build Phases

### Phase 0 — Skeleton + Domain Schemas
Build package topology, core domain objects, serialization, lifecycle rules, error vocabulary, configuration, test harness, and architecture guards.

### Phase 1 — Evidence + Registry Spine
Build artifact hashing/store, structured persistence, provenance relationships, Capability Receipts, negative knowledge, repositories/unit-of-work, migrations, backup/restore.

### Phase 2 — Job Runtime + Local Governance
Build jobs/steps, queue, leases, idempotency, Context Packets, local identity, AuthorityProvider, policy-as-data, SecretProvider interfaces, CLI/API job inspection.

### Phase 3 — Discovery Vertical Slice
Implement internal baseline lookup plus GitHub repository/code discovery, DiscoveryPlan, candidate normalization/deduplication, ranking, budgets, stop rules, provenance.

### Phase 4 — Repository Intelligence + DeepWiki-Ready Boundary
Implement structural maps, source grounding, capability localization, dependency extraction, claim ledger, archaeology, generic comprehension provider and local fallback. DeepWiki may be wired after the provider contract proves stable.

### Phase 5 — Capability Forensics + Decision Primitives
Implement MEU, specification/interface recovery, assumption ledger, complexity accounting, alternative-path generation, acquisition spectrum/value comparison.

### Phase 6 — Trust + Sandbox
Implement license/supply-chain audits, egress/secrets policy, sandbox profiles/backend, RunManifest, malicious-repo defensive qualification.

### Phase 7 — Generic Proving Lab
Build reproduction, upstream tests, independent contract tests, demo harness, adversarial tests, benchmarks, reproducibility packages.

### Phase 8 — Acquisition + Integration Workflow
Implement adapter/extraction/vendor/fork/reimplementation planning, migration, rollback, integration acceptance, approval packets, receipts.

### Phase 9 — Quant Validation
Implement claim normalization, signal reconstruction, data integrity, independent backtesting, robustness, costs/execution, CEREBUS compatibility, research-vs-trading classification.

### Phase 10 — Agent Orchestration
Turn proven services into specialized workers, orchestrated job graphs, bounded retries, critic/reviewer paths, budgets, escalation, resumability. Autonomy arrives after service correctness.

### Phase 11 — Monitoring + Reverse Acquisition
Implement watch registry, upstream change detection, differential revalidation, supersession, internal capability census, redundancy/burden detection, engineering review queue.

### Phase 12 — OCE Adapter
Only after standalone QCAE is qualified and the OCE contract is stable enough to integrate. Implement identity/authority/evidence/event/registry/secrets adapters plus shadow policy migration.

## Sequencing Law

Later phases may scaffold interfaces early but may not become authoritative dependencies before their prerequisite phases pass exit gates.

## Milestone Commit Pattern

Each phase should use:

```text
P#-I0 phase start / plan lock
P#-I1 first subsystem
P#-I2 next subsystem
...
P#-IT integration tests
P#-IR adversarial/repair
P#-IF phase freeze
```

Names are recommended, not mandatory. Narrow commit history is mandatory.

## Invariants

1. Domain/evidence precede autonomous agents.
2. Sandbox precedes execution of unknown code.
3. Generic proving precedes quant proof.
4. Standalone qualification precedes OCE dependency.
5. Monitoring follows acquisition/evidence identity.
6. Phase advancement requires exit gates, not feature-count optimism.

## Exit Criteria

The coding agent has one authoritative build order and cannot legitimately jump to DeepWiki orchestration or OCE integration while foundational evidence/runtime gates are unfinished.
