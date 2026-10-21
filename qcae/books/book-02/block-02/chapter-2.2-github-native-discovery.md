# Chapter 2.2 — GitHub Native Discovery

## Mission

GitHub is QCAE's primary open-source code discovery surface, but QCAE must use it as a structured evidence-bearing index rather than a popularity leaderboard.

## 2.2.1 Discovery Surfaces

QCAE should distinguish:

- repository search;
- code search;
- topic/language metadata;
- dependency/manifests;
- releases/tags;
- commit history;
- issues/discussions when relevant;
- forks;
- organization/maintainer context;
- README/docs.

Each surface answers a different discovery question.

## 2.2.2 Repository Search

Useful for broad candidate generation from behavioral/domain vocabulary. Metadata is preliminary evidence only.

Stars, forks, watchers, and recency may help prioritize inspection but must never substitute for capability evidence.

## 2.2.3 Code Search

Code search is critical when repository titles/descriptions do not reveal the capability.

Search targets may include:

- function/class names;
- protocol identifiers;
- standard names;
- file formats;
- error messages;
- algorithm terms;
- imports/dependencies;
- schema keys;
- tests/fixtures;
- interface symbols.

This is how QCAE finds atoms embedded in unrelated larger projects.

## 2.2.4 Structural Signals

Cheap preliminary signals include:

```text
license file
package manifests
CI configuration
test directories
release history
documentation structure
examples
benchmarks
security policy
changelog
```

These signals determine investigation priority; they do not prove correctness.

## 2.2.5 Immutable Review Anchor

When a candidate enters deeper intelligence, QCAE should anchor analysis to an immutable commit SHA whenever possible.

A moving branch is unsuitable as the sole identity of evidence.

## 2.2.6 Fork Intelligence

Forks can reveal:

- maintained descendants of abandoned projects;
- patches not merged upstream;
- specialized capability extractions;
- ecosystem fragmentation.

QCAE should avoid assuming the original repository is the best implementation merely because it has the canonical name.

## 2.2.7 Organization Context

Maintainer organization can provide useful context, but institutional reputation is not proof of capability correctness. It may influence maintenance-risk priors, never bypass verification.

## 2.2.8 Activity Interpretation

Recency must be interpreted contextually.

A stable parser for a mature standard may need few commits. A fast-moving API client with no recent maintenance may be risky.

Therefore:

> activity is capability-contextual evidence, not a universal health score.

## 2.2.9 Popularity Bias Firewall

QCAE must not rank candidates primarily by stars.

Popularity can be recorded as a weak operational signal for:

- ecosystem breadth;
- likelihood of community knowledge;
- issue visibility;
- potential bus-factor mitigation.

It cannot establish:

- correctness;
- security;
- architectural fit;
- contract coverage;
- quant edge.

## 2.2.10 README Firewall

README claims are `CLAIMED` evidence.

They may generate atom hypotheses and test plans, but promotion requires stronger evidence.

## 2.2.11 GitHub Candidate Snapshot

Discovery should capture:

```text
owner/repo
commit_sha/default_branch
repository metadata
license claim
languages
archived status
fork relationship
release signals
activity signals
manifest paths
test/docs/benchmark presence
query provenance
matched source symbols when code search found the candidate
```

## 2.2.12 Search Pagination and Coverage

QCAE must not confuse the first page with the search universe. Discovery adapters should support controlled pagination and track:

- pages/results inspected;
- duplicate rate;
- novelty rate;
- query saturation;
- API/rate budget.

## 2.2.13 Rate/Budget Awareness

GitHub discovery must operate within explicit request/time budgets and resume safely. A partial search must be marked partial rather than represented as exhaustive.

## 2.2.14 Candidate Prefilters

Cheap hard prefilters may reject or defer candidates when obvious evidence shows:

- archived and incompatible with required maintenance profile;
- explicit incompatible license;
- wrong runtime/platform under a hard constraint;
- capability mismatch;
- source unavailable where source review is mandatory.

Do not over-filter based on weak metadata.

## 2.2.15 GitHub Is Not the Universe

Failure to find a GitHub repository does not imply no capability exists. The Discovery Planner must continue to package ecosystems, research, standards, internal code, or other allowed sources according to plan.

## 2.2.16 Invariants

1. GitHub is a source, not an authority.
2. Code search is first-class alongside repository search.
3. Evidence is anchored to immutable revisions for deeper work.
4. Stars are weak signals, never proof.
5. README statements remain claims.
6. Forks are independent candidate paths when materially divergent.
7. Partial searches are labeled partial.
8. Candidate snapshots preserve query/source provenance.

## Exit Criteria

An implementation agent can build a GitHub discovery adapter that generates and normalizes candidates without allowing GitHub ranking, stars, or README prose to define capability truth.
