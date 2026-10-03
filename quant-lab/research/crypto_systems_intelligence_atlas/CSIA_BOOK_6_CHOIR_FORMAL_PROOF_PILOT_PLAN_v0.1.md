# CSIA Book 6 — Choir Formal Proof Pilot Plan v0.1

**Status:** RESEARCH PROPOSAL / PLANNING ONLY  
**Branch:** `agent/crypto-systems-intelligence-atlas-plan`  
**Planning anchor:** `6f651dee879c73f708796a14c15bb216d9e48125` (post-ratification implementation review v0.4: HOLD)  
**External donor:** [Choir](https://github.com/Weber-GeoML/Choir/tree/762d1ce47ee23871075fea22a2b510c1fd054fed), pinned at `762d1ce47ee23871075fea22a2b510c1fd054fed`, Apache-2.0, pre-alpha.  
**Authority:** none created by this plan. GAP-6 remains unratified; Book 6 comparison implementation, Book 7 implementation, and live acquisition remain unauthorized.

## Purpose

Test whether a ratified CSIA rule can be translated into a small machine-checked theorem and carried back as bounded evidence. Choir is a donor for task decomposition, contributor isolation, proof checking, and review discipline. CSIA continues to own its contracts, authority, evidence, and implementation gate. A green proof about an abstract specification does not establish that production code implements it.

## One candidate, after GAP-6 is decided

The candidate is the Book 6 baseline selector's temporal ordering. Use the eventual **ratified** GAP-6 text, if any, rather than treating the proposed 6E resolution as accepted. Its currently proposed form derives `effective_start/end` from interval bounds for interval observations and from `valid_time` for instantaneous observations, without changing `MeasurementObservation`.

Translate only these obligations into a prover-neutral specification, then choose one supported prover for a bounded pilot:

1. Eligibility and current-record/authority filtering occur before temporal ordering. If the accepted runtime cannot identify a superseded record, record that premise as OPEN instead of assuming it.
2. A candidate is prior only when `candidate.effective_end < comparison.effective_start`; equal-time candidates are excluded.
3. Among eligible prior candidates, ordering is deterministic and independent of caller or insertion order and `observed_at`. The final lexical tie direction must be quoted from the ratified rule.
4. On interval-only inputs, derived-key selection equals the previously ratified interval selection.
5. Instantaneous inputs retain absent window bounds; no coercion, fabricated interval, or observation mutation is used.
6. Incompatible metric definitions or window classes cannot become comparable through the ordering projection.

A proof may establish these statements **conditional on explicit premises**. Report any premise that lacks an accepted CSIA source as an open bridge, not as a proved institutional fact.

## Minimal proof task and evidence mapping

| Stage | Output | Owner |
|---|---|---|
| Freeze intake | Ratified clause IDs, exact commit/blob hashes, accepted runtime version, definitions and open premises | CSIA operator/governance |
| Formalize | One source-to-formal mapping with named assumptions and the six bounded obligations | Pilot author; operator reviews statement meaning |
| Prove | Small dependency graph of proof tasks; workers may submit bounded PRs | Choir-style worker workflow |
| Verify | Clean prover build, no unapproved axioms/placeholders, pinned toolchain and checker result | Deterministic proof gate |
| Reconcile | Map each checked theorem to its source clause and state which runtime paths were exercised separately | CSIA evidence review |

The pilot evidence receipt should bind the source rule SHA, formal statement SHA, assumptions, prover/toolchain version, proof commit, checker result, and separate implementation-conformance results. `PROVED_SPEC` and `IMPLEMENTATION_MATCHES_SPEC` are distinct claims. Neither result ratifies a policy or grants execution authority.

## Entry and exit

**Entry:** GAP-6 has a recorded operator decision; the exact selector statement, lexical tie direction, record-state eligibility, and current rule anchors are stable; a separate bounded pilot authorization exists. Compare OCE/CSIA's existing task, receipt, and gate owners before adopting any Choir component. Pin and inspect the donor version; do not install its plugin into an active CSIA build merely to run this planning exercise.

**Exit:** one independently checkable theorem bundle and one source-to-proof evidence map, or a falsified/underdetermined premise with a minimal counterexample. Demonstrate a statement-weakening or missing-check negative control. Record checker applicability and any advisory or not-applicable paths; do not treat a green aggregate badge as proof of every obligation.

**Next decision:** after GAP-6 ratification and a separate pilot authorization, choose a disposable proof workspace and one prover. No Book 6 runtime edits, new authority class, merge, or live acquisition follows from this document.
