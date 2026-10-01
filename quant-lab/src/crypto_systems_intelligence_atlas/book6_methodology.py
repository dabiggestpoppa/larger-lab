"""Book 6 methodology registry — closing free-string methodology authority.

Book 6 Hardening R1 (R1-D5 / R1-D1): the implementation authorization required
five SEPARATED stores —

    definition registry | methodology registry | measurement records
    | normalization rules | state rules

— and the methodology store was **absent**. Every methodology reference in the
kernel was therefore a bare ``str``: ``"methodology:whatever"`` authorized an
economic or descriptive output purely by being non-empty. R1-D1 is the concrete
consequence — ``authorize_comparison`` checked only ``if not methodology_ref``,
so ``methodology_ref="fake:anything"`` authorized the FC-05 DEX-native vs
aggregator-routed comparison.

The repair makes methodology identity structural:

    METHODOLOGY_IDENTITY = methodology_ref + "@" + version

and requires every authority-bearing surface to RESOLVE that identity here
before it may authorize anything:

- ``MetricDefinition.methodology``
- ``MeasurementObservation.methodology_ref`` + ``methodology_version``
- ``NormalizationRule.methodology_ref``
- comparison ``methodology_ref`` (exact corpus-row identity)
- ``ValuationObservation.conversion_methodology_ref``
- ``StateRule.methodology_ref``

This is NOT a second epistemic engine. Methodology registration is structural
Book 6 authority — the same class of thing as registering a metric definition.
It confers no Book 2 claim state, mints no claim, and never evaluates evidence.
Book 2 remains the only epistemic engine.
"""

from __future__ import annotations

from typing import Final

from .book6_definitions import MeasurementMethodology


class MethodologyRegistryError(ValueError):
    """A methodology reference is unknown, not current, or unauthorized."""


#: The separator between a methodology ref and its version. Versioned
#: methodology identity is the whole point: "monthly active addresses" under
#: two different methodologies are two different observations.
METHODOLOGY_IDENTITY_SEPARATOR: Final[str] = "@"


def methodology_identity(methodology_ref: str, version: str) -> str:
    """Build the canonical, fully-qualified methodology identity."""

    if not methodology_ref or not version:
        raise MethodologyRegistryError(
            "methodology identity requires both a ref and a version; an "
            "unversioned methodology is not a methodology identity"
        )
    return f"{methodology_ref}{METHODOLOGY_IDENTITY_SEPARATOR}{version}"


def parse_methodology_identity(identity: str) -> tuple[str, str | None]:
    """Split an identity into ``(ref, version)``; version is ``None`` if absent.

    Splits on the LAST separator so a ref may itself contain one. There is no
    substring matching, aliasing, or "close enough" resolution anywhere in this
    module: an identity either resolves to a registered methodology or refuses.
    """

    if not identity:
        raise MethodologyRegistryError("an empty string is not a methodology identity")
    ref, separator, version = identity.rpartition(METHODOLOGY_IDENTITY_SEPARATOR)
    if not separator:
        return identity, None
    if not ref or not version:
        raise MethodologyRegistryError(
            f"malformed methodology identity {identity!r}; expected "
            f"'<ref>{METHODOLOGY_IDENTITY_SEPARATOR}<version>'"
        )
    return ref, version


class Book6MethodologyRegistry:
    """Deterministic, offline, in-memory store of versioned methodologies.

    Inherits the Book 4 / Book 5 lesson literally:

        REGISTERED THEN != AUTHORITATIVE NOW

    ``register_methodology`` accepts a methodology without judging it.
    ``resolve_methodology`` re-checks registration, supersession and local
    invalidation at the moment of use, so a methodology that was invalidated or
    superseded stops authorizing anything while the record stays queryable as
    history.
    """

    def __init__(self) -> None:
        self._by_identity: dict[str, MeasurementMethodology] = {}
        self._order: list[str] = []
        self._current_by_ref: dict[str, str] = {}
        self._superseded: dict[str, tuple[MeasurementMethodology, ...]] = {}
        self._invalidated: dict[str, str] = {}

    # -- registration (proves nothing about current authority) ---------------

    def register_methodology(self, methodology: MeasurementMethodology) -> MeasurementMethodology:
        """Register a methodology version. Registration is not authority."""

        identity = methodology.identity
        if identity in self._by_identity:
            raise MethodologyRegistryError(
                f"methodology {identity} is already registered; a new version is "
                f"a new identity and is installed with supersede_methodology()"
            )
        self._by_identity[identity] = methodology
        self._order.append(identity)
        current = self._current_by_ref.get(methodology.methodology_ref)
        if current is not None:
            self._superseded[current] = self._superseded.get(current, ()) + (
                self._by_identity[current],
            )
        self._current_by_ref[methodology.methodology_ref] = identity
        return methodology

    def supersede_methodology(
        self, methodology: MeasurementMethodology
    ) -> MeasurementMethodology:
        """Install a NEW VERSION of a methodology ref, retaining the prior one.

        The prior version stays queryable through ``superseded_versions`` and is
        no longer current, so any decision still naming it fails closed.
        """

        ref = methodology.methodology_ref
        if ref not in self._current_by_ref:
            raise MethodologyRegistryError(
                f"methodology ref {ref} is not registered; supersession requires "
                f"a prior version of the same ref"
            )
        return self.register_methodology(methodology)

    def invalidate_methodology(self, identity: str, *, reason: str) -> str:
        """Mark a registered methodology as locally invalid, with a reason.

        This is the R1-D1 A6 path: a methodology may be invalidated AFTER it was
        legitimately registered, and a comparison naming it must then refuse
        even though the identity still resolves structurally.
        """

        if identity not in self._by_identity:
            raise MethodologyRegistryError(
                f"methodology {identity} is not registered and cannot be invalidated"
            )
        if not reason:
            raise MethodologyRegistryError("an invalidation must record a reason")
        self._invalidated[identity] = reason
        return identity

    def clear_invalidation(self, identity: str) -> None:
        """Reverse a local invalidation. Explicit, and recorded as a no-op if absent."""

        self._invalidated.pop(identity, None)

    # -- structural accessors (never authority) ------------------------------

    def registered_methodology(self, identity: str) -> MeasurementMethodology:
        """Return a registered methodology by identity, or refuse.

        Structural only: an invalidated or superseded identity still resolves
        here as history. Use ``resolve_methodology`` for authority.
        """

        try:
            return self._by_identity[identity]
        except KeyError as exc:
            raise MethodologyRegistryError(
                f"methodology {identity} is not registered"
            ) from exc

    def registered_methodology_identities(self) -> tuple[str, ...]:
        """Deterministic structural snapshot, registration-ordered."""

        return tuple(self._order)

    def superseded_versions(self, identity: str) -> tuple[MeasurementMethodology, ...]:
        """Prior versions of a methodology identity, retained as history."""

        return self._superseded.get(identity, ())

    def invalidation_reason(self, identity: str) -> str | None:
        return self._invalidated.get(identity)

    def current_identity(self, methodology_ref: str) -> str:
        """The current version identity for a bare methodology ref."""

        try:
            return self._current_by_ref[methodology_ref]
        except KeyError as exc:
            raise MethodologyRegistryError(
                f"methodology ref {methodology_ref} has no registered version"
            ) from exc

    # -- authority-bearing resolution ---------------------------------------

    def resolve_methodology(self, identity: str) -> MeasurementMethodology:
        """Resolve a methodology identity to a current, registered methodology.

        Accepts a full ``ref@version`` identity or a bare ``ref`` (resolved to
        its current version). Fails closed on unknown, superseded, or locally
        invalidated methodology. No substring matching, no alias-by-convention.
        """

        ref, version = parse_methodology_identity(identity)
        if version is None:
            resolved_identity = self.current_identity(ref)
        else:
            resolved_identity = methodology_identity(ref, version)
        if resolved_identity in self._invalidated:
            raise MethodologyRegistryError(
                f"methodology {resolved_identity} was invalidated locally: "
                f"{self._invalidated[resolved_identity]}"
            )
        methodology = self.registered_methodology(resolved_identity)
        current = self._current_by_ref.get(methodology.methodology_ref)
        if current is not None and current != resolved_identity:
            raise MethodologyRegistryError(
                f"methodology {resolved_identity} is superseded by {current}; a "
                f"superseded methodology version authorizes nothing"
            )
        return methodology

    def methodology_is_current(self, identity: str) -> bool:
        """Live currentness check that never raises (structural query)."""

        try:
            self.resolve_methodology(identity)
        except MethodologyRegistryError:
            return False
        return True

    def require_comparison_authority(
        self, *, methodology_identity_ref: str, corpus_row_id: str, required_identity: str
    ) -> MeasurementMethodology:
        """Authorize a CONDITIONAL corpus row, or refuse.

        Two independent conditions, both required:

        1. the supplied methodology identity EQUALS the exact identity the
           ratified corpus row requires — no substring match, no alias; and
        2. that methodology itself declares authority for this row via
           ``authorized_corpus_row_ids``.

        Condition 1 alone is a name. Condition 2 alone is a claim with no
        ratified name behind it. Only together is it authority, which is what
        makes A5 ("PASS only if the methodology itself is authorized for that
        corpus row") mechanically true.
        """

        if methodology_identity_ref != required_identity:
            raise MethodologyRegistryError(
                f"corpus row {corpus_row_id} requires methodology "
                f"{required_identity}, not {methodology_identity_ref}; a "
                f"different methodology does not license this comparison"
            )
        methodology = self.resolve_methodology(methodology_identity_ref)
        if corpus_row_id not in methodology.authorized_corpus_row_ids:
            raise MethodologyRegistryError(
                f"methodology {methodology_identity_ref} is not authorized for "
                f"corpus row {corpus_row_id}; it declares "
                f"{list(methodology.authorized_corpus_row_ids) or 'no rows'}"
            )
        return methodology


#: Canonical invariants asserted by the R1 implementation.
METHODOLOGY_REGISTRY_PRESENT: Final[bool] = True
NO_FREE_STRING_METHODOLOGY_AUTHORITY: Final[bool] = True
METHODOLOGY_IDENTITY_IS_VERSIONED: Final[bool] = True


__all__ = [
    "Book6MethodologyRegistry",
    "METHODOLOGY_IDENTITY_IS_VERSIONED",
    "METHODOLOGY_IDENTITY_SEPARATOR",
    "METHODOLOGY_REGISTRY_PRESENT",
    "MethodologyRegistryError",
    "NO_FREE_STRING_METHODOLOGY_AUTHORITY",
    "methodology_identity",
    "parse_methodology_identity",
]
