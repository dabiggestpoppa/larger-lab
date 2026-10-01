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

Book 6 Hardening R2 (R2-D1) closes the hole R1 left. An identity alone was still
a **namespace claim**: a caller could construct one ``MeasurementMethodology``
with ``formula="garbage"`` and ``authorized_corpus_row_ids=("FC-05",)``,
register it, and thereby license the comparison. R1 required exact identity,
registration and row authority, but all three came from the SAME caller-created
object, so the three checks agreed with each other and with the attacker.

R2 binds identity to CONTENT with a canonical fingerprint over every semantic
field, and adds a second, independent canonical source for the case where
self-authorization is most dangerous:

1. **Registry binding** - first registration binds ``identity -> fingerprint``.
   Any later object presented under that identity must match exactly, which
   closes content mutation (a ``model_copy`` of a formula, an input-methodology
   ref set, a row-authority set) on EVERY surface, not only comparisons.
2. **Corpus-pinned canonical specification** - the ratified false-comparison
   corpus carries the full canonical methodology specification for each
   ``CONDITIONAL`` row, not merely its name. A comparison therefore compares
   the registered methodology's fingerprint against content the operator
   ratified, so even a FIRST registration cannot self-authorize.

Neither mechanism uses Python object identity or a hidden global singleton:
both would make the seal depend on process state rather than on the
methodology's meaning, which is exactly what R2 closes.

This is NOT a second epistemic engine. Methodology registration is structural
Book 6 authority — the same class of thing as registering a metric definition.
It confers no Book 2 claim state, mints no claim, and never evaluates evidence.
Book 2 remains the only epistemic engine.
"""

from __future__ import annotations

import hashlib
import json
from typing import Final

from .book6_definitions import MeasurementMethodology


class MethodologyRegistryError(ValueError):
    """A methodology reference is unknown, not current, unauthorized, or altered."""


#: The separator between a methodology ref and its version. Versioned
#: methodology identity is the whole point: "monthly active addresses" under
#: two different methodologies are two different observations.
METHODOLOGY_IDENTITY_SEPARATOR: Final[str] = "@"


#: Every semantic field of a methodology, in canonical order. The fingerprint is
#: taken over exactly these - no more, no less - so "equivalent content, same
#: digest; different content, different digest" is a property of this list rather
#: than of hand-maintained bookkeeping.
METHODOLOGY_CANONICAL_FIELDS: Final[tuple[str, ...]] = (
    "methodology_ref",
    "version",
    "formula",
    "parameters",
    "window_rule",
    "filters",
    "denominator_rule",
    "source_selection",
    "identity_rule",
    "input_methodology_refs",
    "authorized_corpus_row_ids",
)


def canonical_methodology_spec(methodology: MeasurementMethodology) -> str:
    """Serialize a methodology's full semantic content deterministically.

    Unordered fields (``filters``, ``input_methodology_refs``,
    ``authorized_corpus_row_ids``, ``parameters``) are SORTED, because their
    order carries no meaning and an order-sensitive digest would let a cosmetic
    reordering masquerade as a different methodology.
    """

    values: dict[str, object] = {
        "methodology_ref": methodology.methodology_ref,
        "version": methodology.version,
        "formula": methodology.formula,
        "parameters": sorted(methodology.parameters),
        "window_rule": methodology.window_rule,
        "filters": sorted(methodology.filters),
        "denominator_rule": methodology.denominator_rule,
        "source_selection": methodology.source_selection,
        "identity_rule": methodology.identity_rule,
        "input_methodology_refs": sorted(methodology.input_methodology_refs),
        "authorized_corpus_row_ids": sorted(methodology.authorized_corpus_row_ids),
    }
    if set(values) != set(METHODOLOGY_CANONICAL_FIELDS):  # pragma: no cover
        raise MethodologyRegistryError(
            "canonical methodology fields drifted from the specification"
        )
    return json.dumps(
        [values[field] for field in METHODOLOGY_CANONICAL_FIELDS],
        separators=(",", ":"),
        ensure_ascii=True,
    )


def methodology_fingerprint(methodology: MeasurementMethodology) -> str:
    """A stable content digest for a methodology specification.

    Deliberately NOT Python object identity (``id()`` / ``is``) and deliberately
    NOT a hidden global singleton: both would make the seal depend on process
    state rather than on the methodology's meaning, which is precisely the
    defect R2 is closing.
    """

    return hashlib.sha256(
        canonical_methodology_spec(methodology).encode("utf-8")
    ).hexdigest()


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
        #: R2-D1: identity -> canonically bound CONTENT digest, fixed at first
        #: registration. A later object bearing the same identity but different
        #: content is refused, so content may not drift under a fixed name.
        self._fingerprints: dict[str, str] = {}

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
        self._fingerprints[identity] = methodology_fingerprint(methodology)
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

    # -- canonical content binding (R2-D1) ---------------------------------

    def bound_fingerprint(self, identity: str) -> str:
        """The content digest canonically bound to a methodology identity."""

        resolved = self.resolve_methodology(identity)
        try:
            return self._fingerprints[resolved.identity]
        except KeyError as exc:  # pragma: no cover - resolve implies binding
            raise MethodologyRegistryError(
                f"methodology {resolved.identity} has no bound content"
            ) from exc

    def assert_content_matches(self, identity: str, candidate: MeasurementMethodology) -> None:
        """Refuse unless ``candidate`` is the content bound to ``identity``.

        This is the seal that closes content mutation on EVERY surface. A
        ``model_copy`` of a formula, a window rule, an input-methodology set or
        a row-authority set produces an object whose digest differs from the
        bound one, and is refused here rather than at some later decision point.
        """

        bound = self.bound_fingerprint(identity)
        presented = methodology_fingerprint(candidate)
        if bound != presented:
            raise MethodologyRegistryError(
                f"methodology {identity} content does not match the canonically "
                f"bound specification: expected {bound[:12]}, presented "
                f"{presented[:12]}; an identity names one exact methodology and "
                f"may not carry altered semantics"
            )

    def require_canonical_methodology(
        self, candidate: MeasurementMethodology
    ) -> MeasurementMethodology:
        """Resolve a presented methodology and re-verify its CONTENT, live.

        The authority-bearing path for every Book 6 surface that receives a
        methodology OBJECT rather than a bare ref: metric definitions,
        measurements, normalization rules, valuations, state rules. Structural
        registration alone would accept an altered copy, because
        ``model_copy`` does not re-run validators.
        """

        canonical = self.resolve_methodology(candidate.identity)
        self.assert_content_matches(canonical.identity, candidate)
        return canonical

    def require_comparison_authority(
        self,
        *,
        methodology_identity_ref: str,
        corpus_row_id: str,
        required_spec: MeasurementMethodology,
    ) -> MeasurementMethodology:
        """Authorize a CONDITIONAL corpus row, or refuse.

        Three independent conditions, all required (R2 supersedes R1's two):

        1. the supplied methodology identity EQUALS the exact identity the
           ratified corpus row requires - no substring match, no alias;
        2. the registered methodology's CONTENT digest equals the digest of the
           canonical specification the ratified corpus row pins - so a
           caller-created object with the right name and a garbage formula
           cannot self-authorize; and
        3. the ratified canonical specification ITSELF lists ``corpus_row_id``
           in ``authorized_corpus_row_ids``.

        R1 had only 1 and 3, both of which a single caller-created object could
        satisfy simultaneously; that was R2-D1. Condition 2 compares against
        content the operator ratified, not content the caller supplied.

        Condition 3 is deliberately checked against ``required_spec`` rather
        than against the REGISTERED methodology. Checking the registered object
        would have been dead code: condition 2 already pins the registered row
        set to the corpus row set, so a mutated row set always fails at 2 and
        never reaches 3. As written, 3 is a live self-consistency check on the
        ratified corpus - it fails if a corpus row ever pins a methodology
        specification that does not license that very row.
        """

        required_identity = required_spec.identity
        if methodology_identity_ref != required_identity:
            raise MethodologyRegistryError(
                f"corpus row {corpus_row_id} requires methodology "
                f"{required_identity}, not {methodology_identity_ref}; a "
                f"different methodology does not license this comparison"
            )
        if corpus_row_id not in required_spec.authorized_corpus_row_ids:
            raise MethodologyRegistryError(
                f"the canonical methodology specification ratified for corpus "
                f"row {corpus_row_id} is not authorized for corpus row "
                f"{corpus_row_id} itself; it declares "
                f"{list(required_spec.authorized_corpus_row_ids) or 'no rows'}. "
                f"A corpus row may not license itself through a methodology "
                f"that does not name it"
            )
        methodology = self.resolve_methodology(methodology_identity_ref)
        required_fingerprint = methodology_fingerprint(required_spec)
        actual = methodology_fingerprint(methodology)
        if actual != required_fingerprint:
            raise MethodologyRegistryError(
                f"methodology {methodology_identity_ref} content does not match "
                f"the canonical specification ratified for corpus row "
                f"{corpus_row_id}: expected {required_fingerprint[:12]}, "
                f"registered {actual[:12]}; an identity may not carry altered "
                f"semantics"
            )
        return methodology


#: Canonical invariants asserted by the R1/R2 implementation.
METHODOLOGY_REGISTRY_PRESENT: Final[bool] = True
NO_FREE_STRING_METHODOLOGY_AUTHORITY: Final[bool] = True
METHODOLOGY_IDENTITY_IS_VERSIONED: Final[bool] = True
#: R2-D1: one identity names one exact methodology specification.
METHODOLOGY_IDENTITY_BINDS_CONTENT: Final[bool] = True
#: R2-D1: an identity is not an arbitrary namespace claim.
METHODOLOGY_SELF_AUTHORIZATION_REJECTED: Final[bool] = True


__all__ = [
    "Book6MethodologyRegistry",
    "canonical_methodology_spec",
    "METHODOLOGY_CANONICAL_FIELDS",
    "METHODOLOGY_IDENTITY_BINDS_CONTENT",
    "METHODOLOGY_IDENTITY_IS_VERSIONED",
    "METHODOLOGY_IDENTITY_SEPARATOR",
    "METHODOLOGY_REGISTRY_PRESENT",
    "METHODOLOGY_SELF_AUTHORIZATION_REJECTED",
    "MethodologyRegistryError",
    "NO_FREE_STRING_METHODOLOGY_AUTHORITY",
    "methodology_fingerprint",
    "methodology_identity",
    "parse_methodology_identity",
]
