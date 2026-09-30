"""Canonical Book 5 record registry (R3 Phase 7) — the narrowest offline
resolver that lets 5G derived views prove their references exist.

Doctrine (ratified plan v0.3; INV-5G-1 input lineage):

    every 5G output derives from canonical input records by pointer.

A pointer that cannot be resolved to a canonical record is not a pointer —
it is an arbitrary string, and no arbitrary string may become derived 5G
authority. This registry is an IN-MEMORY, DETERMINISTIC, OFFLINE resolver:
no database, no graph DB, no persistence architecture, no second epistemic
engine. It does not mint, store-as-truth, or mutate records; it accepts
already-canonical typed records only AFTER they pass:

    1. Book 2 provenance validation (typed input guard, live claim refs),
    2. record-context validation (R3 quantitative context seal —
       QuantitativeRecordContextBinding agreement/establishment — for the
       non-component record kinds),
    3. typed identity validation (unique identity per record class).

A record refused here can never be referenced by a 5G path or topology view:
references resolve ONLY through this registry, and UNKNOWN, DETACHED, and
WRONG-KIND references all fail closed.

R4 authority-decay seal: registration-time validation alone is not
authority. A registered entry whose Book 2 claims have since decayed out of
the canonical current graph-promotable states (CONTESTED, STALE, REJECTED,
SUPERSEDED) — or whose claims' evidence has since detached — is refused at
RESOLUTION time: every resolve re-runs the live Book 2 validation against
the explicit provenance resolver (NO STALE AUTHORITY THROUGH THE REGISTRY).
The record itself is immutable, so its entry is never "fixed": the faithful
resolution is to reject the ref the moment its Book 2 authority is no
current, and to accept it again the moment Book 2 restores that authority.
"""

from __future__ import annotations

from typing import Final, cast

from pydantic import BaseModel, ConfigDict

from .book5_lineage import DebtLiability
from .book5_provenance import Book5Provenance, Book5ProvenanceError
from .book5_records import (
    CapitalFlow,
    CapitalPosition,
    CapitalTransformation,
    ObservedCommonValueFact,
)

#: Reference-namespace prefixes per registered record class. A canonical
#: Book 5 record id carries its kind in its identity; a ref outside the
#: canonical namespaces can never resolve.
POSITION_REF_PREFIX: Final[str] = "pos:"
FLOW_REF_PREFIX: Final[str] = "flow:"
LIABILITY_REF_PREFIX: Final[str] = "liability:"
FACT_REF_PREFIX: Final[str] = "fact:"
TRANSFORMATION_REF_PREFIX: Final[str] = "transform:"
SITE_REF_PREFIX: Final[str] = "csia:site:"

_REF_PREFIXES: Final[dict[str, tuple[str, ...]]] = {
    "position": (POSITION_REF_PREFIX,),
    "flow": (FLOW_REF_PREFIX,),
    "liability": (LIABILITY_REF_PREFIX,),
    "observed_fact": (FACT_REF_PREFIX,),
    "transformation": (TRANSFORMATION_REF_PREFIX,),
    "economic_site": (SITE_REF_PREFIX,),
}


class Book5RegistryError(Book5ProvenanceError):
    """A record or reference cannot be canonical in the Book 5 registry."""


class RegisteredRecord(BaseModel):
    """Typed registry entry: the record's identity and its canonical kind."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_ref: str
    record_kind: str
    record_class: str


def _require_typed(record: object) -> tuple[object, str, str, str]:
    """Typed-input guard + identity extraction.

    Returns ``(record, ref, kind, class_name)``; anything else raises the
    typed :class:`Book5RegistryError` (raw dicts never enter the registry).
    """

    if isinstance(record, CapitalPosition):
        return record, record.position_id, "position", type(record).__name__
    if isinstance(record, CapitalFlow):
        return record, record.flow_id, "flow", type(record).__name__
    if isinstance(record, DebtLiability):
        return record, record.liability_id, "liability", type(record).__name__
    if isinstance(record, ObservedCommonValueFact):
        return record, record.fact_id, "observed_fact", type(record).__name__
    if isinstance(record, CapitalTransformation):
        return (
            record,
            record.transformation_id,
            "transformation",
            type(record).__name__,
        )
    raise Book5RegistryError(
        "registry accepts only typed canonical Book 5 records "
        "(CapitalPosition, CapitalFlow, DebtLiability, "
        "ObservedCommonValueFact, CapitalTransformation), got "
        f"{type(record).__name__}; raw payloads are refused"
    )


class Book5CanonicalRecordRegistry:
    """In-memory deterministic offline resolver for canonical Book 5 records.

    R3 Phase 7 contract:

    - registration is FAIL-CLOSED: a record enters only after typed
      identity validation, live Book 2 provenance validation, and (for the
      non-component quantitative kinds) the R3 context seal;
    - identities are unique per class; re-registration is refused;
    - reference resolution distinguishes UNKNOWN (never registered),
      DETACHED (registered class cannot appear in the requested role), and
      WRONG-KIND (registered, but the API requires a different kind) — all
      three REJECT;
    - R4: resolution is a LIVE Book 2 authority boundary — every resolve
      requires an explicit ``provenance`` (explicit None fails closed) and
      re-runs claim-currentness (plus the R3 context seal for the
      flow/liability/observed-fact kinds) against CURRENT Book 2 state, so
      an entry never outlives the authority of the claims that made it
      canonical (NO STALE AUTHORITY THROUGH THE REGISTRY);
    - categories: positions, flows, liabilities, observed facts,
      transformations, economic sites (path/topology semantics only).
    """

    def __init__(self) -> None:
        self._records: dict[str, object] = {}
        self._kinds: dict[str, str] = {}

    # -- registration ------------------------------------------------------

    def register(self, record: object, *, provenance: Book5Provenance) -> str:
        """Register a canonical record after full validation (R3 Phase 7).

        Order is deliberate: typed identity guard first (raw input fails
        closed as a typed error), then Book 2 live-state validation, then
        the quantitative context seal for flow/liability/observed-fact
        kinds, then namespace + uniqueness checks.
        """

        if provenance is None:  # explicit None fails closed
            raise Book5RegistryError(
                "registry registration requires an explicit Book5Provenance "
                "resolver; a registry entry that cannot be revalidated "
                "against live Book 2 state is not canonical"
            )
        typed, ref, kind, class_name = _require_typed(record)
        record = cast(object, typed)
        # 1. Book 2 provenance validation (live state)
        claim_refs = getattr(record, "book2_claim_refs", None)
        if not isinstance(claim_refs, tuple) or len(claim_refs) == 0:
            raise Book5RegistryError(
                f"registry refuses {kind} record {ref!r}: canonical Book 5 "
                "records require at least one Book 2 claim ref"
            )
        provenance.resolve_claim_refs(claim_refs)
        # 2. record-context validation (R3 non-component seal)
        if kind in {"flow", "liability", "observed_fact"}:
            provenance.validate_quantitative_record(record)
        # 3. typed identity validation
        self._require_namespace(ref, kind)
        if ref in self._records:
            raise Book5RegistryError(
                f"{kind} record {ref!r} already registered; identities are "
                "unique and registration is not mutable state"
            )
        self._records[ref] = record
        self._kinds[ref] = kind
        return ref

    def register_site(self, site: object) -> str:
        """Register an EconomicSite under its canonical site namespace.

        Sites carry no Book 2 claim refs of their own (they anchor Book 1
        identity, not economic observations), so validation here is typed
        identity + namespace only.
        """

        from .book5_core import EconomicSite

        if not isinstance(site, EconomicSite):
            raise Book5RegistryError(
                f"register_site accepts only a typed EconomicSite, got "
                f"{type(site).__name__}"
            )
        ref = site.site_id
        self._require_namespace(ref, "economic_site")
        if ref in self._records:
            raise Book5RegistryError(
                f"economic site {ref!r} already registered"
            )
        self._records[ref] = site
        self._kinds[ref] = "economic_site"
        return ref

    # -- resolution --------------------------------------------------------

    def resolve(
        self,
        ref: str,
        *,
        expected_kind: str | None = None,
        provenance: Book5Provenance | None = None,
    ) -> RegisteredRecord:
        """Resolve a reference to a registered canonical record (R4-sealed).

        - UNKNOWN: the ref was never registered → REJECT;
        - WRONG-KIND: the ref is registered but ``expected_kind`` differs
          → REJECT (an API that requires a specific kind never accepts a
          canonical record of another kind);
        - NO-AUTHORITY-CONTEXT: ``provenance`` is absent → REJECT (explicit
          None fails closed, mirroring the R2 mandatory-authority seal —
          there is no remembered-construction fallback and no default
          resolver);
        - STALE-AUTHORITY: the entry's Book 2 claims no longer resolve as
          canonical, current, and evidenced (claim decayed to CONTESTED,
          STALE, REJECTED, SUPERSEDED, or evidence detached) → REJECT; for
          the flow/liability/observed-fact kinds the R3 quantitative
          context seal re-runs live as well;
        - every surviving resolution returns the typed entry, and restored
          Book 2 authority (e.g. STALE → OBSERVED, CONTESTED →
          CORROBORATED) restores resolution of the same immutable record.
        """

        from .book5_provenance import require_str_hashable

        ref = require_str_hashable(ref, role="book5 record ref")
        if ref not in self._records:
            raise Book5RegistryError(
                f"5G derived reference {ref!r} does not resolve to a "
                "canonical Book 5 record (UNKNOWN); no arbitrary string may "
                "become derived 5G authority"
            )
        kind = self._kinds[ref]
        if expected_kind is not None and kind != expected_kind:
            raise Book5RegistryError(
                f"5G derived reference {ref!r} is a canonical {kind} record "
                f"but the requested role requires {expected_kind} "
                "(WRONG-KIND); refusing resolution"
            )
        if provenance is None:  # explicit None fails closed (R4)
            raise Book5RegistryError(
                f"resolving derived reference {ref!r} requires an explicit "
                "Book5Provenance resolver; a registry entry that cannot be "
                "revalidated against live Book 2 state is not derived "
                "authority (NO STALE AUTHORITY THROUGH THE REGISTRY)"
            )
        # R4 live revalidation: registration validated the claims ONCE;
        # resolution revalidates them against CURRENT Book 2 state every
        # time. Authority decays with its claims; it is never remembered.
        record = self._records[ref]
        claim_refs = getattr(record, "book2_claim_refs", None)
        if isinstance(claim_refs, tuple) and len(claim_refs) > 0:
            provenance.resolve_claim_refs(claim_refs)
            if kind in {"flow", "liability", "observed_fact"}:
                provenance.validate_quantitative_record(record)
            if kind == "position":
                # R5: a position's authority includes its NESTED principal
                # components. Registry current resolution validates each
                # through the SAME provenance validator used at every 5G
                # boundary (single implementation, no duplicated logic):
                # registry currentness -> record currentness -> binding
                # currentness -> binding basis currentness.
                for component in record.principal_components.components:
                    provenance.validate_principal_component(component)
        return RegisteredRecord(
            record_ref=ref, record_kind=kind, record_class=type(record).__name__
        )

    def registered_refs(self, kind: str | None = None) -> tuple[str, ...]:
        """Deterministic snapshot of registered refs, optionally by kind."""

        if kind is None:
            return tuple(sorted(self._records))
        return tuple(sorted(ref for ref, k in self._kinds.items() if k == kind))

    def registered_record(self, ref: str) -> object:
        """The registered typed record object (structural inspection only).

        Callers MUST NOT treat the returned object as revalidated state:
        live validation happens at the authority boundary, never by remember-
        ing a construction. Resolution + typedness is all this accessor proves.
        """

        if ref not in self._records:
            raise Book5RegistryError(f"unknown record {ref!r}")
        return self._records[ref]

    # -- internals ---------------------------------------------------------

    def _require_namespace(self, ref: str, kind: str) -> None:
        prefixes = _REF_PREFIXES.get(kind)
        if prefixes is None:
            raise Book5RegistryError(f"unknown registry kind {kind!r}")
        if not any(ref.startswith(prefix) for prefix in prefixes):
            raise Book5RegistryError(
                f"{kind} record ref {ref!r} is outside the canonical "
                f"{kind} reference namespace {prefixes}; refusing registration"
            )

    @property
    def registered_count(self) -> int:
        return len(self._records)


__all__ = [
    "Book5CanonicalRecordRegistry",
    "Book5RegistryError",
    "RegisteredRecord",
]
