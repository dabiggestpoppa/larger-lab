# Chapter 9.5 — Lineage & Contradictions

## Mission

Represent how QCAE beliefs evolve without overwriting conflicting evidence or losing which conclusion depended on which source.

## Lineage Edges

`SUPPORTS`, `CONTRADICTS`, `DERIVED_FROM`, `SUPERSEDES`, `REPRODUCES`, `FAILS_TO_REPRODUCE`, `DEPENDS_ON`, `VALID_UNDER`.

## Contradiction Handling

A contradiction creates a resolution task. It does not permit the latest model response to choose a winner without evidence.

## Source Hierarchy

Authority remains question-specific: direct source can override prose about code; controlled runtime evidence can override claims about runtime; CEREBUS manual governs CEREBUS doctrine. Preserve both conflicting objects and the resolution rationale.

## Temporal Lineage

New upstream revisions do not mutate old evidence. They create new subject revisions connected through lineage.

## Invariants

1. Evidence evolution is graph-like, not destructive replacement.
2. Contradictions remain visible.
3. Resolution uses appropriate evidence authority for the question.
4. New revisions create new evidence scope.
5. Conclusions retain dependency lineage.

## Exit Criteria

A reviewer can trace any current belief backward through the evidence and see prior contradictions/superseded conclusions.
