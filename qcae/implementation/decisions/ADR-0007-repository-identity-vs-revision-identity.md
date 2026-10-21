# ADR-0007 — Repository Identity vs Revision Identity

**Status:** Accepted (P1-R1)
**Phase:** P1-R1 — Registry Completion + Freeze Truth Repair
**Canon refs:** Book I 1.3.16 (stable internal IDs; external identifiers are
attributes), 1.3.17 (canonical source identity: "repository owner/name +
immutable commit"), Book II Block 3 (all repository intelligence is
revision-scoped; `repo_revision` is the analysis anchor), Book V 13.3
(versioned, append-oriented persistence), Book IV 9.5 (temporal lineage:
new revisions create new scope, old evidence is never mutated)

## Context

The P1-R1-C02 `RepositoryRecord` documents identity as
`(source_kind, canonical_locator)` with `repository_id` as the stable handle,
but its SQLite table uses `PRIMARY KEY (repository_id)`. A second revision of
the same repository therefore cannot share its parent's stable ID — the schema
would force a new unrelated `repository_id` per commit SHA, exactly the
"treat a new commit as an unrelated repository" defect the operator flagged.

## Alternatives

1. **Keep PK(repository_id), mint a fresh ID per revision.** Rejected:
   breaks deduplication (1.3.17), makes "all known revisions of this
   repository" unanswerable, and severs revision lineage from identity.
2. **Composite PK (source_kind, canonical_locator, revision), no stable ID.**
   Rejected: locator strings change (package ownership migrates, canon 2.4:
   "a package may change repository ownership"); identity keyed on mutable
   attributes is fragile and contradicts 1.3.16.
3. **Two-level model (DECIDED): `repository_id` names the container; each
   observation is an immutable revision record keyed by
   `repository_id + revision` with its own stable `repository_revision_id`
   (`<repository_id>@<revision>`).**

## Decision

- **Repository identity:** `repository_id` — stable internal handle for the
  source container (canon 1.3.16), with current `source_kind` +
  `canonical_locator` as attributes of the *identity*, updatable only by
  explicit supersession.
- **Revision identity:** `repository_revision_id = repository_id + "@" +
  revision` — immutable, content-digest-verified observation record.
- **One identity → many immutable revision records.** A new commit SHA is a
  new *revision of a known repository*, never a new repository.
- **"Latest" is observation-time-based** (`last_observed_at`, then
  `first_seen_at` tie-break, then `repository_revision_id` as final
  deterministic tie-break): never derived from revision-string lexical order —
  Git SHAs are not chronological and package versions are not always
  lexicographic. If observation timestamps are absent, callers must request
  an exact revision; the API does not guess.
- **Schema evolution uses the P1 migration framework** (v2 → v3): a new
  `repository_revision` table (PK `repository_revision_id`, FK-like reference
  to `repository_id`, per-row payload digest); the existing
  `repository_record` table keeps its role as the identity/current-observation
  registry. No destructive overwrite.

## Reason

It is the only alternative satisfying all four operator invariants: stable
identity, multiple immutable revisions, revision-exact lookup, and non-lexical
"latest". It matches canon's own vocabulary (`repo_revision` in Book II 3.3.7;
"repository owner/name + immutable commit" in 1.3.17) rather than inventing
semantics.

## Reversibility

High. The revision table is additive; a future schema change can reshape it
via another forward migration. No domain object embeds the encoding except
`repository_revision_id`, whose `id@revision` form is human-readable and
mechanically splittable.

## Candidate identity (resolved within this ADR, per operator §6)

**Interpretation A: `candidate_id` intentionally identifies one candidate
revision record.** Canon 1.3.3 defines the Implementation Candidate as "a
particular implementation proposed to satisfy an atom" and 1.3.17 anchors
deduplication on "immutable commit"; a new upstream revision is a *new
particular implementation* and therefore a new candidate record. The
`source_ref` attribute (repo/package coordinate) provides the stable grouping
key across candidate revision records, so "all candidate revisions from one
source" remains answerable via `list_candidates_by_source`. This is coherent
with the existing P0/P1 semantics; no redesign required — only an explicit
test pinning the rule.

## P3/P4 implications

- P3 discovery *updates* an existing repository identity by appending
  revision records — never re-registering the repository.
- P4 comprehension artifacts key on `repository_revision_id` (Book II 3.3.7
  `repo_revision`), matching the revision-scoped intelligence doctrine.
- Relationship edges (P1-R1-C03R2) reference revision records, so
  "revision X implements atom Y" cannot silently mean "all revisions do".

## Canon compatibility

No contradiction with Books I–VI or amendment A-001. The two-level model
implements rather than amends 1.3.16/1.3.17 and Book II's revision-scoping.
