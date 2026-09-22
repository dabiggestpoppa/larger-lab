# G8 — pre-repair red evidence (STRESS-G8R0)

Transcript of the audit-closure defects reproduced against the pre-repair
head, before any repair was applied. Regenerate with:

```
cd stress-suite && PYTHONIOENCODING=utf-8 python scenarios/g8_pre_repair_red_transcript.py
```

The harness extracts the named commit read-only into a temporary directory,
runs the probes against THAT code in a subprocess, and discards it. It never
moves HEAD and never writes to the working tree.

pre-repair commit: `6c015f86408a56721f8999e4aa39b218fab0fd4d`
pre-repair subject: `STRESS-G8R: archive G8 evidence package`

## Probes against the pre-repair code

```
R-G8-01: mandated_observed=20/20  uncovered_reported=0  NOT_COMPARABLE(mandated)=2  gate=PASS_G8_CROSS_SCENARIO_COHERENCE  (F7 excluded from this probe: it needs the archived evidence tree)
R-G8-01: mandated NOT_COMPARABLE pairs in F2: [["G2:S05", "G5:S16", "NOT_COMPARABLE"], ["G5:S16", "G6:S22", "NOT_COMPARABLE"]]
R-G8-02: _profit_never_reduced({'profit': 10, 'items': [{'disposition': 'VALIDATED'}]}) -> True
R-G8-02: inspect.getsource(_profit_never_reduced) tail: ["for i in items) or True"]
R-G8-03: _has_provenance({'evidence_provenance': 'UNKNOWN', 'evidence_lineage': 'UNKNOWN'}) -> True
R-G8-04: _g4_runtime_neutral('S13') -> True ; _g4_runtime_neutral('S99_NO_SUCH_SCENARIO') -> True
R-G8-04: inspect.getsource(_g4_runtime_neutral): "def _g4_runtime_neutral(sid: str) -> Optional[bool]:\n    return True if sid != \"S13\" else True"
R-G8-05: _refusal_observed(single refusal phase, nothing else) -> True
R-G8-05: _refusal_observed(refusal AFTER an escalation phase) -> True
R-G8-05: P8 declared in the G6 observation as: ["True"]
R-G8-05: _availability_derived({'operator_availability': 'UNAVAILABLE'}) -> True
R-G8-06: the P6 derivation in the G3 observation builder: ["p6 = (True if (raw_reviewers > 1 and sources == 1) else None)"]
R-G8-07: inspect.signature(emit) -> (measured_full: 'int') -> 'Dict[str, Any]'
R-G8-07: emit(1)['receipt'] -> collected=1 passed=1 failed=0 inherited=938 new_g8_test_count=-937; receipt records a test-results artifact -> False; receipt records an artifact digest -> False
R-G8-07: emit(9999)['receipt'] -> collected=9999 passed=9999 failed=0 inherited=938 new_g8_test_count=9061; receipt records a test-results artifact -> False; receipt records an artifact digest -> False
R-G8-08: this (archive) checkout: bytes=354913 sha256=af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb
R-G8-08: synthetic LF:   bytes=354913 sha256=af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb
R-G8-08: synthetic CRLF: bytes=366841 sha256=72ba79d7064404b463dfcf7d937a3a4c03565f6bad12f0ffa4fb8f6d5f011233
R-G8-08: the S16 fixture declares: 72ba79d7064404b463dfcf7d937a3a4c03565f6bad12f0ffa4fb8f6d5f011233
R-G8-08: fixture digest == LF digest -> False ; == CRLF digest -> True
R-G8-09: contract status: "FROZEN_AT_STRESS-G8P0 + DECLARED_REVISIONS"
R-G8-09: contract version: "1.1.0"
R-G8-09: contract freeze_note: "This contract is authored BEFORE any cross-scenario comparison runs. It declares the equivalence vector, the normalization rules, the comparison families, the discriminator rules, the outcome-class vocabulary and the classification vocabulary. No verdict rule below depends on which scenario produced a token; verdict logic is a pure function of the declared fields. The later planning package (A-012 / MF-A002 / OPH / Cadence / continuation extension) is deliberately NOT an input to this contract and cannot define an expected G8 outcome."
R-G8-09: contract declares contract_chronology -> False
```

## Git evidence for R-G8-09 (contract chronology)

```
$ git log --all --oneline -- stress-suite/evidence/G8_EQUIVALENCE_CONTRACT.json
f5482e3e STRESS-G8P0: freeze equivalence and contradiction audit contract
```

One commit ever touched the contract, and that commit's blob
already carries the revisions motivated by the first run's own
findings, so Git cannot show that those verdict rules were frozen
before the first comparison ran. The claim recorded in the
pre-repair contract (`FROZEN_AT_STRESS-G8P0`, `authored BEFORE any
cross-scenario comparison runs`) is therefore retracted as
unsupported and replaced by the staged chronology record in
`contract_chronology`.
