# Chapter 16.6 — Repository Comprehension Tests

## Mission

Measure whether repository intelligence can correctly locate architecture, target capability code, dependencies, state, tests, and uncertainty while preventing DeepWiki/LLM explanations from becoming ungrounded truth.

## Fixtures

Use small synthetic repos plus selected real pinned repositories with known architecture. Include misleading README text, dynamic imports, generated code, vendored code, multiple implementations, and stale documentation.

## Metrics

Track source-location precision/recall, hallucinated-symbol rate, dependency completeness, state/interface detection, grounding coverage, contradiction detection, and cost/context efficiency.

## DeepWiki Differential

Run selected fixtures with and without the comprehension provider. DeepWiki should improve speed/recall without changing the source-grounding standard or becoming required for correctness.

## Invariants

1. Material structural claims are source-grounded.
2. Hallucinated paths/symbols fail qualification.
3. Stale model/docs are detected rather than trusted.
4. Dynamic uncertainty remains explicit.
5. QCAE remains functional without DeepWiki.

## Exit Criteria

Repository intelligence reliably produces a grounded forensic handoff rather than an impressive but unverifiable summary.
