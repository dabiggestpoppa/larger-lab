# ADR-0005 — Amendment Interface-Schema Drift Guard Without New Dependencies

**Status:** Accepted (P0-A001)
**Phase:** P0-A001 amendment reconciliation
**Refs:** A-001 schemas (`research-capability-handoff.schema.json`,
`economic-experience.schema.json`), reconciliation prompt §12

## Context

The reconciliation prompt requires a qualification check ensuring the code-level
Research Mesh handoff and Economic Experience representations cannot silently
drift from the active A-001 JSON interface schemas, without introducing heavy
dependencies unless justified.

## Alternatives

1. **Add the `jsonschema` package and validate instance documents against the
   A-001 schemas.** Rejected for P0: a new runtime/test dependency in the
   most protection-sensitive area for a check that is structural; can be
   revisited at P1/P8 via amendment + ADR if instance-level validation becomes
   a real requirement.
2. **Commit frozen golden-JSON snapshots and byte-compare.** Rejected: brittle
   under intentional additive schema evolution and duplicates the schema files
   as another drift surface.
3. **Explicit compatibility assertions (accepted): parse the actual committed
   A-001 schema files at test time and assert the code-level enums, envelope
   versions, required-field sets, and firewall conditions agree with them.**

## Decision

`qcae/tests/unit/test_p0_a001_schema_drift.py` loads
`qcae/amendments/schemas/*.json` directly from the repo and asserts:

- every interface enum value set equals its code-level StrEnum counterpart
  (direction, mode, status, required_outputs, fallback_class, gap_type subset;
  qa_result, customer_acceptance, outcome, promotion_state, data_rights);
- the code envelope `interface_version` equals each schema's
  `schema_version` const ("1.0");
- required-field sets of the interface schemas are representable by the code
  records (non-empty provenance producer/created_at; economics block fields);
- the economic-experience allOf firewall (client-specific material cannot
  co-occur with promotion_state PROMOTED) is present in the schema file and
  mirrored by code validation;
- a self-verification case mutates a schema value in memory and asserts the
  guard detects the mismatch (guard detects drift).

The test fails when the amendment schemas change without a matching code
change — exactly the drift condition §12 targets.

## Reason

Structural compatibility is what P0 owns (typed boundary + vocabularies).
Instance validation belongs to P1's evidence spine and P8's workflow engine,
where records actually cross the boundary in anger. The chosen approach reuses
the repo's own committed schemas as the source of truth, adds zero
dependencies, and still fails closed on drift.

## Burden

- The guard must be extended when A-001 schemas gain fields (one test edit per
  amendment revision — proportional to amendment churn).
- Does not catch JSON-Schema semantics beyond enums/consts/required (e.g.
  format: date-time) at P0; noted as deferred to P1.

## Reversibility

High — swapping to full `jsonschema`-based validation later only extends the
test module; no core code depends on it.

## Canon/Amendment Compatibility

Implements reconciliation §12 directly; adds no authority and no new
vocabulary.
