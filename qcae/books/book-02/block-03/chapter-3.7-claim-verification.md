# Chapter 3.7 — Claim Verification

## Mission

Convert discovery/README/DeepWiki claims into a source-grounded ledger of supported, contradicted, ambiguous, and still-unverified assertions.

This is **source-level verification**, not runtime/contract proof.

## 3.7.1 Claim Sources

Claims may originate from:

- README;
- docs;
- package metadata;
- paper;
- curated sensor description;
- DeepWiki explanation;
- comments;
- issue/PR discussion;
- discovery model inference.

## 3.7.2 Claim Types

```text
CAPABILITY
INTERFACE
DEPENDENCY
ARCHITECTURE
PERFORMANCE
SECURITY
COMPATIBILITY
MAINTENANCE
QUANT_RESULT
LICENSE
```

Different claim types require different later proof.

## 3.7.3 Source-Level Status

```text
SOURCE_SUPPORTED
SOURCE_CONTRADICTED
SOURCE_PARTIAL
SOURCE_AMBIGUOUS
NOT_LOCATED
NOT_SOURCE_VERIFIABLE
```

A performance claim may be `NOT_SOURCE_VERIFIABLE` even if benchmark code exists; execution is required.

## 3.7.4 Evidence Anchors

Supported/contradicted source claims require exact revision/path/symbol-region anchors where practical.

## 3.7.5 Claim Decomposition

Broad claims should be decomposed.

"Production-ready order book engine" may become:

- supports L2 updates;
- preserves event sequence;
- handles snapshots;
- supports reconnect;
- benchmark claims X throughput;
- test coverage exists for Y.

This makes later proving possible.

## 3.7.6 Absence Discipline

Not finding source support is not always contradiction. Use `NOT_LOCATED` unless source evidence positively conflicts with the claim.

## 3.7.7 Performance Firewall

Source can show that a benchmark exists or that code is intended to be optimized. It cannot establish measured performance without executing a controlled benchmark.

## 3.7.8 Security Firewall

Source inspection may locate dangerous primitives or obvious controls. It cannot establish overall safety. Book III owns security verification.

## 3.7.9 Quant Firewall

No source-level artifact can establish live/research edge merely because strategy logic and backtest code exist. Quant claims remain unverified until Book III Block 7.

## 3.7.10 Contradiction Priority

Material contradictions should immediately influence escalation priority.

Examples:

- README says standalone, source requires framework runtime;
- docs say local-only, source calls remote API;
- package claims optional dependency, import is unconditional;
- paper claims no look-ahead, code appears to use future values.

Contradictions become explicit Block 4/Book III targets.

## 3.7.11 Claim Ledger

```text
claim_id
candidate_id
claim_text
claim_type
origin
source_revision
status
evidence_anchors
materiality
required_next_proof
notes
```

## 3.7.12 Block 3 Terminal Package

At the end of repository intelligence, QCAE should have:

```text
structural map
atom localization
dependency envelope
history findings
claim ledger
uncertainty ledger
forensic targets
```

This is the input to Block 4.

## 3.7.13 Invariants

1. Claims are decomposed into testable assertions where possible.
2. Source support is not runtime proof.
3. Absence of located evidence is not automatically contradiction.
4. Performance/security/quant claims retain later proof requirements.
5. Contradictions are durable evidence and prioritized.
6. Every material claim retains origin and revision context.

## Exit Criteria

QCAE can finish repository comprehension knowing exactly which candidate assertions source supports, contradicts, or leaves unresolved, and what evidence the next stages must obtain.
