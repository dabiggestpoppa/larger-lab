# CSIA Book 4 Fail-Closed Audit — Admission & Classification Paths

- **Date:** 2026-09-26
- **Target:** every Book 4 decision point that admits or classifies
  record-supplied payloads. The R3 probing round found one instance of the
  pattern (raw dict bindings crashing `RedundancyBook.add` with
  `AttributeError`); this audit sweeps the entire Book 4 surface for the same
  fail-closed gap.
- **Baseline HEAD:** `ebfd8cec0293ba8b40a2aa0b18ebd6450a395b20` (R3 complete)
- **Probe suite:** `test_book4_fail_closed_audit.py` — 21 executable probes

## Decision-Point Inventory (all swept)

| Decision point | Verdict before fixes | Verdict after |
|---|---|---|
| `DependencyBook.add` | raw dict record crashed (`AttributeError`) | REFUSES (`typed DependencyRecord`) |
| `DependencyPathBook.add` | raw dict record crashed | REFUSES (`typed DependencyPath`) |
| `ProtocolRoleBook.add` | raw dict record crashed | REFUSES (`typed RoleAssignment`) |
| `SubstitutabilityBook.add` | raw dict record crashed | REFUSES (`typed SubstitutabilityAssessment`) |
| `RedundancyBook.add` | record-type guard already present (R3) | unchanged, verified |
| `FailureDomainBook.add` | raw dict record crashed | REFUSES (`typed FailureDomain`) |
| `HardRuntimeGate.classify` | raw evidence record crashed on first attribute read | REFUSES (`typed HardRuntimeEvidence`) |
| `HardRuntimeGate.classify` bindings | type gate present (R2 audit) | verified |
| `HardRuntimeGate.classify` fact enum | fact drifted outside `HardRuntimeFact` crashed on set insertion / `.value` | refusal reason, UNKNOWN |
| `FailureDomainBook.classify` | raw dict binding crashed (`binding.claim_ref`) | REFUSES (`typed IndependenceClaimBinding`) |
| `FailureDomainBook.classify` empty systems | **CONFIRMED CRASH: `IndexError: tuple index out of range`** on `affected_system_refs[0]` after model_copy stripping | REFUSES (non-empty affected systems) |
| `Book4Provenance.resolve_claim` | non-string claim id passed through to `ClaimStore.require` | REFUSES (canonical string refs) |
| `Book4Provenance.validate_refs` | non-string / unhashable items reached set ops | REFUSES at entry |
| `Book4Provenance.validate_snapshot_lineage` | same | REFUSES at entry |

## Gap Pattern Confirmed (2 crash classes, 1 latent-crash class)

1. **Raw-dict record/binding injection** — pydantic `model_copy(update=...)`
   skips every model validator and performs no coercion, so arbitrary
   payloads reach decision points. Every admission method and classify path
   that read attributes off such payloads crashed with `AttributeError`.
   Fixed: every Book 4 admission method now type-checks the record; both
   classify paths type-check binding payloads; untyped payloads are refused
   with `Book4ProvenanceError`, never crashed on.
2. **Structural stripping** — `FailureDomainBook.classify` indexed
   `affected_system_refs[0]` before any guard; a record whose tuple was
   stripped via `model_copy` produced `IndexError`. Fixed: explicit
   non-empty affected-system guard, fail closed.
3. **Payload-type drift at provenance chokepoints** — non-string or
   unhashable claim/snapshot refs (nested tuples, dicts) flowed into
   `ClaimStore.require` and set operations. Fixed: shared
   `require_str_hashable` guard at `Book4Provenance` entry points
   (`resolve_claim`, `validate_refs`, `validate_snapshot_lineage`), so every
   downstream admission method inherits the check.
4. **Enum drift** — a `HardRuntimeFactContextBinding` whose `fact` was
   drifted outside the `HardRuntimeFact` enum previously crashed set
   insertion; the gate now emits a refusal reason and returns UNKNOWN.

## Post-Fix State

- CSIA: **528 PASS** (507 + 21 audit probes, kept as permanent regression
  tests); all prior R1/R2/R3 probes green unchanged.
- Ruff: PASS. mypy: PASS (37 source files).
- Sensor: **2325 PASS / 14 FAIL / 4 SKIPPED** — failure set byte-identical to
  the R3 equivalence record; `BOOK4_INTRODUCED_SENSOR_FAILURES = 0`.
- Freeze: diff vs `ebfd8cec` touches Book 4 source + test files only; zero
  Book 1/2/3 source changes, zero Sensor changes.
- Status: BOOK_4_ACCEPTANCE remains NOT_SELF_ACCEPTED; BOOK_5 NOT_STARTED;
  LIVE_ACQUISITION_AUTHORITY FALSE.

## Note

This audit was run in direct response to the operator's fail-closed audit
request following R3. It closes the one remaining known crash-class gap in
Book 4 decision points; the guards live at decision points (authoritative)
with constructor validators retained as defense in depth.
