# Chapter 3.6 — Repository Archaeology

## Mission

Current source shows what exists now. Repository Archaeology explains how the relevant capability got there, what changed, what was removed, and whether current architecture is stable or accidental.

## 3.6.1 When Archaeology Is Worth Cost

Use targeted history when it can resolve:

- why an interface changed;
- whether a module is being deprecated;
- origin of a strange workaround;
- security-sensitive changes;
- fork divergence;
- abandoned/reintroduced capability;
- repeated bug patterns;
- migration direction;
- whether extraction boundary is becoming more or less stable.

Do not read history indiscriminately.

## 3.6.2 History Objects

Potential evidence:

- commits;
- tags/releases;
- changelogs;
- blame/history around target symbols;
- issues/PRs linked to changes;
- deprecation notes;
- migration docs.

## 3.6.3 Intent vs Fact

Commit/issue prose expresses maintainer intent. Source diff establishes what changed. Both are useful but distinct evidence types.

## 3.6.4 Stability Analysis

Track target atom churn separately from whole-repo churn.

A busy repository can contain a stable atom; a quiet repository can contain an unstable abandoned atom.

## 3.6.5 Fork Divergence

For forks, determine:

```text
common ancestor
divergence age
capability-relevant patches
upstream patches missing in fork
fork-only dependencies
merge feasibility
```

## 3.6.6 Regression Memory

Repeated fixes in the same area may reveal difficult edge cases that should become independent contract/adversarial tests later.

## 3.6.7 Removed Capability

Deleted code can still be valuable prior art. If a capability was removed, QCAE should seek why before considering resurrection.

## 3.6.8 Archaeology Output

```text
target atom/history scope
material changes
intent references
stability/churn findings
deprecation signals
fork divergence
historical bugs/edge cases
removed alternatives
forensic/proving implications
```

## 3.6.9 Invariants

1. Archaeology is targeted, not exhaustive by default.
2. Capability-local churn matters more than repository-wide commit count.
3. Maintainer prose and source diffs are distinguished.
4. Historical bugs feed future tests.
5. Removed code is not automatically safe or desirable to revive.
6. Fork divergence is capability-specific.

## Exit Criteria

QCAE can use repository history to reduce uncertainty about stability, hidden design intent, edge cases, and fork choice without mistaking historical narrative for runtime proof.
