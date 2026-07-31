# Part 3 — Claims, Contradictions, and Secret Redaction

## Goal

Record material documentation claims with provenance, identify contradictions without resolving them, and produce a redacted tracked-secret finding inventory.

## Inputs

- Verified Part 1 and Part 2 artifacts
- Root documentation, architecture indexes, selected progress/team records, and recent commit subjects
- Tracked text paths only for secret-pattern scanning

## Required Behavior

- Store source path, line or commit, retrieval time, category, and safe claim representation.
- Create contradiction IDs when material claims disagree.
- Detect secret fixtures and known credential shapes without retaining matched values.
- Sanitize remotes, excerpts, errors, logs, and serialized findings.
- Mark suspected active exposure as a blocker without attempting rotation.

## Test Obligations

- P0-DOC-001 claim provenance
- P0-SEC-001 redaction
- Contradictions remain unresolved and linked
- Findings contain category/location metadata but no secret material

## Exit

Part 3 closes when an adversarial fixture proves detection and redaction, every material claim has provenance, and contradictions are ready for Book 3 review.
