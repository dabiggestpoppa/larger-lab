# Chapter 18.4 — Minimum Viable Standalone Release

## Mission

Define the first release that is genuinely useful on its own before broad autonomy, quant expansion, or OCE wiring.

## MVSR Scope

The Minimum Viable Standalone Release (MVSR) should support one complete generic capability-acquisition vertical slice:

```text
natural-language request
→ normalized Capability Contract
→ internal baseline lookup
→ GitHub discovery
→ candidate normalization/ranking
→ repository structural/source analysis
→ capability forensics
→ license/security screening
→ isolated build/test
→ independent contract test
→ acquisition recommendation
→ Capability Receipt
→ persistent registry/memory
```

## Required Runtime

MVSR includes:

- local CLI/API;
- local job queue/state;
- local policy engine;
- evidence store;
- sandbox backend;
- GitHub adapter;
- local repository/source analyzer;
- receipt/registry services;
- resume after restart;
- negative knowledge.

## Not Required for MVSR

The first standalone release does **not** require:

- DeepWiki;
- every package ecosystem;
- full quant validation;
- autonomous reverse acquisition;
- OCE integration;
- distributed microservices;
- cloud deployment.

Those remain later milestones.

## Acceptance Demonstrations

MVSR must successfully complete at least:

1. one focused dependency/wrapper case;
2. one reject case;
3. one extraction/reimplementation-style case;
4. restart/resume during an active job;
5. one malicious/unsafe candidate stopped before unsafe execution.

## Invariants

1. MVSR is useful end-to-end, not a collection of disconnected modules.
2. Standalone operation requires no OCE service.
3. DeepWiki is optional at this milestone.
4. Evidence/receipts/negative memory are present from first release.
5. Unknown code runs only through qualified sandbox controls.
6. Local-first operation is the default deployment posture.

## Exit Criteria

QCAE can independently acquire or reject a real generic capability with a durable receipt and no hidden dependence on future phases.
