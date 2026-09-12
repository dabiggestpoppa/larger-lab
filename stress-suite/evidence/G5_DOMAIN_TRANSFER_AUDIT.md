# G5 — DOMAIN TRANSFER AUDIT (S19)

## Concept source
Read-only ingestion of the Crypto Foundry research state (`agent/crypto-quant-foundry`): mechanism families include capacity/transfer/bottleneck semantics; the S19 fixture anchors on `ARBITRAGE_CAPITAL_BANDWIDTH` as a crypto-domain mechanism (no hardcoded invention; concept family real, treated as crypto evidence only).

## Firewall semantics
- Source-domain evidence supports `CRYPTO_VALIDATED_CONCEPT` only. It never yields `FX_VALIDATED_CONCEPT`.
- `DomainTransferHypothesis` is the only legal cross-domain object; it is not an FX strategy.
- `TransferInvariantMap` requires: source/target domain, source definition → target candidate definition, source observables → target observables, units/scales, state semantics, market-structure assumptions, mechanism invariants, known broken assumptions, required sensors, falsifiers. A name match is insufficient (name-collision control: same concept name, different mechanics → `ANALOGY_ONLY`, no transfer).

## Dispositions (test-only)
`ANALOGY_ONLY` / `TRANSFER_CANDIDATE` / `DATA_BLOCKED` / `TRANSFER_REJECTED` / `DOMAIN_VALIDATION_REQUIRED` / `DOMAIN_VALIDATED`. Only target-domain evidence can reach `DOMAIN_VALIDATED`.

## Controls
- A: same name, different observable mechanics → `ANALOGY_ONLY` / reject.
- B: strong structural mapping but target sensor unavailable → `DATA_BLOCKED` (fixture result: `TRANSFER_HYPOTHESIS_ONLY`, missing target-domain observable).
- C: mapping + target data + frozen target-domain protocol → `DOMAIN_VALIDATION_REQUIRED`.
- CEREBUS FX doctrine: a Crypto analogy cannot override a CEREBUS rule; when the transfer touches governed CEREBUS FX semantics, the manual prevails until explicit operator amendment. No FX strategy promotion from Crypto evidence strength (tested).

## Status
**PASS** — analogy ≠ transfer; invariant map required; missing observables block; doctrine firewalled.