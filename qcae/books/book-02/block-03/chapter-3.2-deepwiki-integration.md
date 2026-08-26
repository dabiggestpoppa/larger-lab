# Chapter 3.2 — DeepWiki Integration

## Mission

DeepWiki-style tooling is QCAE's repository-comprehension accelerator. It helps an agent navigate unfamiliar codebases, generate architectural hypotheses, follow relationships, and formulate better source questions.

It is **not** an evidence authority.

## 3.2.1 Natural Pairing

Book II deliberately pairs:

```text
Discovery surfaces → find candidate source
DeepWiki layer → understand candidate source
Direct source inspection → ground assertions
Capability Forensics → recover reusable unit
Proving Lab → demonstrate behavior
```

This is the "other half" of discovery: finding code without comprehension is insufficient; comprehension without source grounding is unsafe.

## 3.2.2 Allowed DeepWiki Roles

DeepWiki may assist with:

- high-level architecture orientation;
- module relationships;
- likely entry points;
- symbol/function explanation;
- data/control-flow hypotheses;
- locating relevant tests/docs;
- identifying terminology;
- generating follow-up source queries;
- explaining unfamiliar frameworks;
- summarizing history when source references are available.

## 3.2.3 Forbidden Authority Roles

DeepWiki output alone may not establish:

- capability verification;
- dependency completeness;
- license status;
- security safety;
- runtime correctness;
- benchmark validity;
- quant performance;
- acceptance of an acquisition.

## 3.2.4 Grounding Protocol

For each useful model assertion:

```text
DeepWiki assertion
      ↓
classify assertion type
      ↓
locate source anchor
      ↓
confirm / contradict / unresolved
      ↓
store grounded relationship or uncertainty
```

Possible statuses:

```text
MODEL_HYPOTHESIS
SOURCE_SUPPORTED
SOURCE_CONTRADICTED
SOURCE_AMBIGUOUS
NOT_LOCATED
```

## 3.2.5 Contradiction Rule

If DeepWiki explanation conflicts with source at the reviewed revision, source wins and the contradiction is retained as a quality signal.

## 3.2.6 Revision Alignment

Repository explanations can become stale. QCAE must record which repository revision the comprehension layer appears to describe. If revision alignment cannot be established, output is lower-confidence navigation assistance.

## 3.2.7 Question Generation

A major DeepWiki value is converting broad uncertainty into source-addressable questions:

- Where is state persisted?
- Which module owns retry semantics?
- Is this parser independent of the framework runtime?
- Which tests exercise this branch?
- What initializes this registry?
- Where does network access occur?

The answers are then grounded directly.

## 3.2.8 Context Compression

DeepWiki can act as a map so the QCAE agent need not repeatedly ingest an entire repository. But compressed explanation must always retain pointers back to authoritative source.

## 3.2.9 Cache Policy

Comprehension artifacts should be cached by repository + immutable revision. A new upstream revision should not silently reuse an old architectural explanation as current fact.

## 3.2.10 Fallback Behavior

QCAE must remain functional without DeepWiki.

Fallback stack:

```text
repository tree
manifests
code search/static analysis
symbol extraction
LLM over selected source
manual/source-driven navigation
```

DeepWiki improves speed and context efficiency; it is not a constitutional dependency.

## 3.2.11 Future Provider Abstraction

Implementation should target a generic `RepositoryComprehensionProvider` contract so DeepWiki can be replaced, supplemented, or disabled without rewriting QCAE core.

Conceptual methods:

```text
summarize_repository(revision)
explain_path(path, revision)
locate_concept(query, revision)
trace_relationship(symbol, revision)
answer_repository_question(question, revision)
```

Provider outputs must carry grounding references when available.

## 3.2.12 Sensitive/Internal Repositories

External comprehension services must never receive private source unless explicit policy permits it. Standalone QCAE must fail closed on uncertain source-egress authorization. Future OCE governs final identity/policy decisions.

Local comprehension remains the default safe fallback for protected code.

## 3.2.13 Quality Metrics

QCAE should eventually evaluate comprehension providers by:

- source-location precision;
- source-location recall;
- contradiction rate;
- stale-revision rate;
- useful-question yield;
- context/time saved;
- hallucinated-symbol rate.

## 3.2.14 Invariants

1. DeepWiki accelerates comprehension; it never becomes proof.
2. Source wins every contradiction.
3. Useful assertions are grounded or labeled hypotheses.
4. Revision alignment is explicit.
5. QCAE works without DeepWiki.
6. Provider coupling stays behind an interface.
7. Private source egress is policy-controlled and fail-closed.
8. Cached comprehension is revision-keyed.

## Exit Criteria

The future agent can use DeepWiki aggressively for navigation and reasoning while mechanically preventing DeepWiki prose from being promoted into technical evidence without direct source grounding.
