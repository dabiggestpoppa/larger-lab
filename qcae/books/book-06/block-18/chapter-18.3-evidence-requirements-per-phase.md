# Chapter 18.3 — Evidence Requirements per Phase

## Mission

Define the minimum artifacts each implementation phase must leave behind so later flywheel review can audit what was built, why it passed, and what remains uncertain.

## Evidence Matrix

### Phase 0
- schema snapshots;
- lifecycle transition tests;
- architecture/dependency guards;
- serialization round-trip evidence.

### Phase 1
- persistence migration tests;
- artifact hash tests;
- receipt reconstruction fixture;
- backup/restore proof;
- negative-knowledge retrieval proof.

### Phase 2
- queue crash/resume evidence;
- idempotency/lease tests;
- policy decision fixtures;
- secret-provider denial tests;
- CLI/API job-state examples.

### Phase 3
- discovery benchmark report;
- internal-first fixture;
- GitHub pagination/rate-limit tests;
- candidate deduplication/provenance report;
- recall/false-positive metrics.

### Phase 4
- grounded repository maps;
- hallucination/contradiction fixtures;
- comprehension-provider contract tests;
- DeepWiki-off fallback proof.

### Phase 5
- MEU/spec/interface/assumption forensic fixture;
- acquisition-form comparison examples;
- anti-framework burden test.

### Phase 6
- license-conflict fixtures;
- supply-chain inventory;
- sandbox profile enforcement;
- malicious-repository tests;
- egress/secret denial evidence.

### Phase 7
- reproducible build fixture;
- upstream vs independent tests;
- adversarial regression suite;
- benchmark receipt;
- reproducibility package replay.

### Phase 8
- at least two distinct acquisition-form work packages;
- adapter containment test;
- migration/rollback rehearsal;
- approval-scope fixture.

### Phase 9
- known-bad quant fixtures rejected;
- one valid research fixture;
- data/leakage audit;
- robustness/cost report;
- CEREBUS compatibility fixture;
- trading-authority denial proof.

### Phase 10
- end-to-end job graph;
- fresh-context worker restart;
- bounded retry/failure recovery;
- critic/escalation path;
- budget enforcement.

### Phase 11
- upstream-change simulation;
- differential revalidation;
- unknown-blast-radius escalation;
- internal redundancy/reverse-acquisition report.

### Phase 12
- provider contract tests against OCE adapters;
- shadow policy comparison;
- no-privilege-expansion evidence;
- OCE outage/degraded-mode proof;
- federation/idempotency test.

## Evidence Manifest

Every phase freeze should include a machine-readable manifest listing test runs, generated reports, key commit SHAs, known blockers/deferred items, and canonical evidence refs.

## Invariants

1. Every phase leaves durable proof, not only source code.
2. Evidence maps to that phase's constitutional risks.
3. Negative/adversarial proof is required where relevant.
4. Freeze manifests make review reproducible.
5. Later phases may consume earlier evidence but cannot silently rewrite it.

## Exit Criteria

The flywheel reviewer can evaluate phase readiness from committed evidence manifests rather than trusting the build agent's summary.
