# Chapter 2.5 — Research Discovery

## Mission

QCAE must discover capability from research literature, standards, specifications, reference implementations, benchmarks, and technical reports—not only production repositories.

This is especially important for quantitative methods, algorithms, protocols, and emerging techniques where the best reusable asset may be the specification or method rather than existing code.

## 2.5.1 Research Source Classes

```text
peer-reviewed papers
preprints
standards/specifications
technical reports
reference implementations
benchmark suites
theses/dissertations
research datasets
reproducibility packages
```

Source class affects evidence interpretation but does not automatically determine quality.

## 2.5.2 Research as Capability Prior Art

A paper may contribute:

- algorithm definition;
- mathematical derivation;
- assumptions;
- benchmark methodology;
- testable claims;
- reference data;
- implementation hints.

It may support `REIMPLEMENT_FROM_PAPER` without supporting direct code acquisition.

## 2.5.3 Specification Priority

When a capability implements a formal standard/protocol, the normative specification should generally outrank one implementation's behavior as the semantic reference.

Implementation quirks may still matter for compatibility, but QCAE should distinguish normative semantics from accidental implementation behavior.

## 2.5.4 Paper-to-Code Mapping

QCAE should attempt to connect:

```text
Paper
→ official/reference implementation
→ third-party implementations
→ benchmark datasets
→ later corrections/errata
→ derivative methods
```

This creates a richer candidate family than treating each repository independently.

## 2.5.5 Claim Firewall

Published performance is a claim until independently reproduced under the relevant contract.

For quant research this is absolute:

- reported Sharpe is not accepted Sharpe;
- reported CAGR is not accepted CAGR;
- reported robustness is not accepted robustness;
- a paper's statistical significance is not live-trading authority.

Book III defines proof.

## 2.5.6 Research Freshness vs Foundational Work

Newer is not automatically better. Discovery should include foundational sources when later implementations depend on them and newer work when it materially changes assumptions, algorithms, or empirical evidence.

## 2.5.7 Citation Signals

Citation count may help locate influential work but cannot prove correctness or relevance. QCAE should favor direct semantic fit and reproducibility evidence over prestige metrics.

## 2.5.8 Reproducibility Assets

High-value discovery signals include:

- source code;
- fixed datasets;
- seeds;
- environment files;
- experiment scripts;
- benchmark definitions;
- test vectors.

These raise investigation priority because later proof becomes cheaper.

## 2.5.9 Assumption Extraction

Research discovery should record stated assumptions early:

- stationarity;
- distribution assumptions;
- market microstructure assumptions;
- latency assumptions;
- transaction cost treatment;
- sampling frequency;
- hardware requirements;
- dataset restrictions.

This can eliminate a method before expensive implementation work.

## 2.5.10 Quant-Specific Discovery

For trading/research atoms, QCAE should seek both:

```text
method source
```

and

```text
criticism/replication/failure evidence
```

Discovery is stronger when it actively searches for reasons the claimed edge may not survive.

## 2.5.11 Research Candidate Record

Capture:

```text
paper/spec identifier
version/date
authors/maintainer
capability atom hypothesis
normative vs descriptive role
stated assumptions
claimed results
code/data links
corrections/errata
replication links
license/access notes
query provenance
```

## 2.5.12 Research-to-Acquisition Outcomes

Possible outcomes include:

- REIMPLEMENT_FROM_SPEC;
- REIMPLEMENT_FROM_PAPER;
- EXTRACT_ALGORITHM;
- EXTRACT_TESTS;
- USE_AS_REFERENCE;
- REJECT as irrelevant/invalid under contract.

## 2.5.13 Invariants

1. Research sources are first-class capability sources.
2. Published claims remain claims until reproduced.
3. Normative specifications are distinguished from implementations.
4. Assumptions are captured as early as possible.
5. Quant discovery actively seeks replication and failure evidence.
6. Citation/prestige metrics never replace semantic or empirical validation.
7. Research provenance remains connected to resulting implementations.

## Exit Criteria

QCAE can discover a method even when no suitable repository exists, preserve the method's assumptions and provenance, connect paper/specification to implementations, and route it toward independent reimplementation/proof rather than treating publication as validation.
