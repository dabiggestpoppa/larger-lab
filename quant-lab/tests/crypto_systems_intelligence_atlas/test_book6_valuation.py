"""Book 6 valuation — purpose-specific price authority and the Book 5 seam.

Ratified D6M-4 = A: there is no universal authoritative price-source class.

    PRICE_AUTHORITY = PURPOSE x SUBJECT x VALID_TIME x METHODOLOGY

The suite proves that a valuation cannot be struck without an explicit
numeraire and a cited price observation, that the admissible price class is
selected by PURPOSE, that divergent price classes are preserved rather than
averaged, and that nothing is ever written back into a frozen Book 5 record.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_support import NOW, T1
from crypto_systems_intelligence_atlas.book6_valuation import (
    BOOK5_WRITE_BACK_IS_REFUSED,
    NO_GLOBAL_PRICE_SOURCE_CLASS,
    PRICE_AUTHORITY_IS_PURPOSE_SPECIFIC,
    PRICE_AUTHORITY_MATRIX,
    Book5WriteBackRefusal,
    PriceObservation,
    PriceObservationClass,
    ValuationError,
    ValuationObservation,
    ValuationPurpose,
    check_price_divergence_is_preserved,
)

STALE_AFTER = 3600


def _price(
    price_class: PriceObservationClass = PriceObservationClass.MARKET_OBSERVATION,
    *,
    price: float = 1.0,
    observed_at=NOW,
    source_ref: str = "source:venue:1",
) -> PriceObservation:
    return PriceObservation(
        price_observation_id=f"price:{price_class.value.lower()}:1",
        price_class=price_class,
        source_ref=source_ref,
        source_claim_refs=("fixture:claim:measurement",),
        price=price,
        valid_time=observed_at,
        observed_at=observed_at,
        coverage=1.0,
    )


def _valuation(
    *,
    purpose: ValuationPurpose = ValuationPurpose.MARKET_VALUATION,
    price_class: PriceObservationClass = PriceObservationClass.MARKET_OBSERVATION,
    numeraire: str | None = "USD",
    observed_at=NOW,
    price: PriceObservation | None = None,
) -> ValuationObservation:
    payload: dict[str, object] = {
        "valuation_id": "val:1",
        "subject_ref": "fixture:subject:alpha",
        "native_quantity": 10.0,
        "native_unit": "TOKEN",
        "purpose": purpose,
        "price": price or _price(price_class, observed_at=observed_at),
        "conversion_methodology_ref": "book6-methodology@1",
        "valid_time": T1,
        "observed_at": observed_at,
        "coverage": 1.0,
        "staleness_bound_seconds": STALE_AFTER,
    }
    if numeraire is not None:
        payload["numeraire"] = numeraire
    return ValuationObservation(**payload)  # type: ignore[arg-type]


# -- numeraire is required, never implicit ------------------------------------


def test_numeraire_is_required() -> None:
    with pytest.raises(ValidationError):
        _valuation(numeraire=None)


def test_numeraire_cannot_be_an_empty_string() -> None:
    with pytest.raises(ValidationError):
        _valuation(numeraire="")


def test_usd_is_not_the_default_numeraire() -> None:
    field = ValuationObservation.model_fields["numeraire"]
    assert field.is_required()
    assert "USD" not in str(field.default)


def test_an_explicit_non_usd_numeraire_is_accepted() -> None:
    assert _valuation(numeraire="ETH").numeraire == "ETH"


def test_native_unit_and_quantity_are_always_declared() -> None:
    valuation = _valuation()
    assert valuation.native_unit == "TOKEN"
    assert valuation.native_quantity == 10.0


def test_no_common_value_without_a_price_observation() -> None:
    with pytest.raises(ValidationError):
        ValuationObservation(
            valuation_id="val:1",
            subject_ref="fixture:subject:alpha",
            native_quantity=10.0,
            native_unit="TOKEN",
            numeraire="USD",
            purpose=ValuationPurpose.MARKET_VALUATION,
            conversion_methodology_ref="book6-methodology@1",
            valid_time=T1,
            observed_at=NOW,
            coverage=1.0,
            staleness_bound_seconds=STALE_AFTER,
        )


def test_a_price_observation_must_carry_its_own_source_and_time() -> None:
    with pytest.raises(ValidationError):
        PriceObservation(
            price_observation_id="price:1",
            price_class=PriceObservationClass.MARKET_OBSERVATION,
            source_ref="",
            source_claim_refs=("fixture:claim:measurement",),
            price=1.0,
            valid_time=NOW,
            observed_at=NOW,
            coverage=1.0,
        )


def test_a_price_observation_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _price(price=0.0)


# -- D6M-4 = A: purpose-specific price authority ------------------------------


def test_every_purpose_has_an_authority_mapping() -> None:
    assert set(PRICE_AUTHORITY_MATRIX) == set(ValuationPurpose)
    for purpose, admissible in PRICE_AUTHORITY_MATRIX.items():
        assert admissible, purpose
        assert admissible <= set(PriceObservationClass), purpose


def test_every_price_class_is_admissible_for_at_least_one_purpose() -> None:
    for price_class in PriceObservationClass:
        assert any(
            price_class in admissible for admissible in PRICE_AUTHORITY_MATRIX.values()
        ), price_class


def test_no_price_class_is_admissible_for_every_purpose() -> None:
    """There is no global authoritative price source (NO_GLOBAL_PRICE_SOURCE)."""

    for price_class in PriceObservationClass:
        admitting = [
            purpose
            for purpose, admissible in PRICE_AUTHORITY_MATRIX.items()
            if price_class in admissible
        ]
        assert len(admitting) < len(ValuationPurpose), price_class


def test_price_authority_is_purpose_specific() -> None:
    for purpose, admissible in PRICE_AUTHORITY_MATRIX.items():
        for price_class in PriceObservationClass:
            if price_class in admissible:
                continue
            with pytest.raises(ValidationError, match="not admissible"):
                _valuation(purpose=purpose, price_class=price_class)


@pytest.mark.parametrize(
    ("purpose", "price_class"),
    [
        (ValuationPurpose.REDEMPTION_ACCOUNTING, PriceObservationClass.OFFICIAL_REDEMPTION_VALUE),
        (ValuationPurpose.MARKET_VALUATION, PriceObservationClass.MARKET_OBSERVATION),
        (ValuationPurpose.PROTOCOL_COLLATERAL_MARK, PriceObservationClass.ORACLE_MARK),
        (ValuationPurpose.VENUE_MARGIN_MARK, PriceObservationClass.VENUE_INDEX),
        (ValuationPurpose.ASSET_NAV, PriceObservationClass.ISSUER_NAV),
        (ValuationPurpose.POSITION_VALUATION, PriceObservationClass.MARKET_OBSERVATION),
        (ValuationPurpose.WRAPPED_ASSET_BASIS, PriceObservationClass.UNDERLYING_REFERENCE_PRICE),
    ],
    ids=lambda v: getattr(v, "value", str(v)),
)
def test_each_ratified_stress_purpose_admits_its_own_class(
    purpose: ValuationPurpose, price_class: PriceObservationClass
) -> None:
    assert _valuation(purpose=purpose, price_class=price_class).purpose is purpose


def test_redemption_value_is_not_a_market_observation() -> None:
    with pytest.raises(ValidationError, match="not admissible"):
        _valuation(
            purpose=ValuationPurpose.REDEMPTION_ACCOUNTING,
            price_class=PriceObservationClass.MARKET_OBSERVATION,
        )


def test_venue_index_is_not_a_collateral_mark() -> None:
    with pytest.raises(ValidationError, match="not admissible"):
        _valuation(
            purpose=ValuationPurpose.PROTOCOL_COLLATERAL_MARK,
            price_class=PriceObservationClass.VENUE_INDEX,
        )


def test_market_observation_is_not_an_issuer_nav() -> None:
    with pytest.raises(ValidationError, match="not admissible"):
        _valuation(
            purpose=ValuationPurpose.ASSET_NAV,
            price_class=PriceObservationClass.MARKET_OBSERVATION,
        )


def test_authority_constant_is_true() -> None:
    assert PRICE_AUTHORITY_IS_PURPOSE_SPECIFIC is True
    assert NO_GLOBAL_PRICE_SOURCE_CLASS is True


# -- divergence is preserved, never averaged ---------------------------------


def test_divergent_price_classes_are_preserved_side_by_side() -> None:
    observations = (
        _price(PriceObservationClass.OFFICIAL_REDEMPTION_VALUE, price=0.98, source_ref="s:1"),
        _price(PriceObservationClass.MARKET_OBSERVATION, price=1.02, source_ref="s:2"),
        _price(PriceObservationClass.ORACLE_MARK, price=1.00, source_ref="s:3"),
    )
    pairs = check_price_divergence_is_preserved(observations)
    assert len(pairs) == 3
    assert {cls for _, cls in pairs} == {
        PriceObservationClass.OFFICIAL_REDEMPTION_VALUE,
        PriceObservationClass.MARKET_OBSERVATION,
        PriceObservationClass.ORACLE_MARK,
    }


def test_there_is_no_consensus_price_combinator() -> None:
    from crypto_systems_intelligence_atlas import book6_valuation

    forbidden = {"average", "mean_price", "consensus_price", "blend", "merge_prices"}
    assert forbidden.isdisjoint(set(dir(book6_valuation)))


def test_no_module_level_price_singleton_exists() -> None:
    from crypto_systems_intelligence_atlas import book6_valuation

    for name in dir(book6_valuation):
        if not name.isupper() or not isinstance(getattr(book6_valuation, name), (str, dict)):
            continue
        value = getattr(book6_valuation, name)
        if isinstance(value, str) and "PRICE" in name:
            assert "AUTHORITATIVE_PRICE" not in value
        if isinstance(value, dict):
            assert all(isinstance(k, ValuationPurpose) for k in value), name


# -- staleness is bitemporal (Phase 32) -------------------------------------


def test_a_current_price_is_not_stale() -> None:
    valuation = _valuation()
    assert valuation.is_stale is False
    assert valuation.is_currently_fresh(valuation.observed_at) is True


def test_a_stale_price_makes_the_current_valuation_unavailable() -> None:
    valuation = _valuation(
        observed_at=NOW + timedelta(seconds=STALE_AFTER + 1),
        price=_price(
            PriceObservationClass.MARKET_OBSERVATION,
            observed_at=NOW,
        ),
    )
    assert valuation.is_stale is True
    assert valuation.is_currently_fresh(valuation.observed_at) is False


def test_a_price_inside_the_bound_is_not_stale() -> None:
    valuation = _valuation(
        observed_at=NOW + timedelta(seconds=STALE_AFTER - 1),
        price=_price(PriceObservationClass.MARKET_OBSERVATION, observed_at=NOW),
    )
    assert valuation.is_stale is False


def test_staleness_bound_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        ValuationObservation(
            valuation_id="val:1",
            subject_ref="fixture:subject:alpha",
            native_quantity=10.0,
            native_unit="TOKEN",
            numeraire="USD",
            purpose=ValuationPurpose.MARKET_VALUATION,
            price=_price(),
            conversion_methodology_ref="book6-methodology@1",
            valid_time=T1,
            observed_at=NOW,
            coverage=1.0,
            staleness_bound_seconds=0,
        )


def test_current_unavailable_is_not_historical_invalid() -> None:
    """Bitemporal: a stale CURRENT price does not invalidate historical truth."""

    historical = _valuation(
        observed_at=NOW + timedelta(days=30),
        price=_price(PriceObservationClass.MARKET_OBSERVATION, observed_at=NOW + timedelta(days=30)),
    )
    assert historical.valid_time == T1  # the measurement's own valid time is unchanged
    assert historical.is_currently_fresh(historical.observed_at) is True
    # the same structure read "now" is unavailable, and that unavailability is
    # a statement about the present, not about the historical observation.
    read_now = _valuation(
        observed_at=NOW + timedelta(days=3650),
        price=_price(PriceObservationClass.MARKET_OBSERVATION, observed_at=NOW),
    )
    assert read_now.is_currently_fresh(read_now.observed_at) is False
    assert historical.valuation_id == read_now.valuation_id


def test_an_unavailable_source_yields_no_price_observation_at_all() -> None:
    """A source-unavailable price is ABSENT, never a zero price."""

    with pytest.raises(ValidationError):
        PriceObservation(
            price_observation_id="price:1",
            price_class=PriceObservationClass.MARKET_OBSERVATION,
            source_ref="",
            source_claim_refs=("fixture:claim:measurement",),
            price=1.0,
            valid_time=NOW,
            observed_at=NOW,
            coverage=1.0,
        )
    with pytest.raises(ValidationError):
        _price(price=0.0)


# -- the Book 5 seam is read-only (Phase 18) ---------------------------------


def test_book_5_write_back_is_explicitly_refused() -> None:
    refusal = Book5WriteBackRefusal()
    assert refusal.target_kind == "BOOK5_CANONICAL_RECORD"
    assert set(refusal.refused_fields) == {"numeraire", "price", "common_value_scalar"}
    assert "BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE" in refusal.reason


def test_book_5_refusal_constant_is_true() -> None:
    assert BOOK5_WRITE_BACK_IS_REFUSED is True


def test_no_book6_api_writes_into_a_book_5_record() -> None:
    """The Book 5 seam is structurally write-free: no Book 6 module imports Book 5.

    Book 6 never holds a Book 5 canonical object, so there is no reference
    through which a numeraire, price or common-value scalar could be written
    back. The seam is READ-ONLY by construction, not by convention.
    """

    import ast
    import pathlib

    import crypto_systems_intelligence_atlas as pkg

    root = pathlib.Path(pkg.__file__).parent
    offenders: list[str] = []
    for path in sorted(root.glob("book6_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                target = node.names[0].name if node.names else ""
                if "book5" in module or "book5" in target:
                    offenders.append(f"{path.name}: from {module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "book5" in alias.name:
                        offenders.append(f"{path.name}: import {alias.name}")
    assert offenders == []


def test_no_book6_measurement_api_can_rewrite_a_book_4_edge() -> None:
    """Phase 19: the Book 4 dependency graph is read-only to Book 6."""

    import ast
    import pathlib

    import crypto_systems_intelligence_atlas as pkg

    #: Modules that hold the Book 4 dependency GRAPH. ``dependency_provenance``
    #: is a shared identity helper (Book 5 uses it too), not the graph.
    graph_modules = {"book4", "book4_boundary", "dependency"}

    root = pathlib.Path(pkg.__file__).parent
    offenders: list[str] = []
    for path in sorted(root.glob("book6_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").lstrip(".")
                if module in graph_modules or module.startswith("book4."):
                    offenders.append(f"{path.name}: from {module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in graph_modules or alias.name.startswith("book4."):
                        offenders.append(f"{path.name}: import {alias.name}")
    assert offenders == []


def test_no_book6_module_mutates_a_dependency_edge() -> None:
    from crypto_systems_intelligence_atlas import book6_core, book6_registry

    forbidden = ("add_edge", "remove_edge", "reweight", "repair_topology", "set_edge")
    for module in (book6_core, book6_registry):
        surface = [n for n in dir(module) if any(f in n.lower() for f in forbidden)]
        assert surface == [], f"{module.__name__} exposes {surface}"


def test_a_valuation_product_is_separate_from_the_native_book_5_quantity() -> None:
    valuation = _valuation()
    assert valuation.subject_ref != "BOOK5"
    assert valuation.native_unit == "TOKEN"
    assert not hasattr(valuation, "book5_record")


# -- engine authorization mirrors the matrix -------------------------------


def test_engine_authorizes_an_admissible_price() -> None:
    from crypto_systems_intelligence_atlas.book6_support import build_engine

    engine, *_ = build_engine()
    valuation = _valuation()
    assert engine.authorize_current_valuation(valuation, as_of=NOW) is valuation


def test_engine_rejects_an_inadmissible_price() -> None:
    from crypto_systems_intelligence_atlas.book6_support import build_engine

    engine, *_ = build_engine()
    forged = _valuation().model_copy(
        update={
            "purpose": ValuationPurpose.REDEMPTION_ACCOUNTING,
        }
    )
    with pytest.raises(ValuationError, match="not admissible"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_engine_rejects_a_forged_price_class_on_a_market_valuation() -> None:
    from crypto_systems_intelligence_atlas.book6_support import build_engine

    engine, *_ = build_engine()
    valuation = _valuation()
    forged = valuation.model_copy(
        update={
            "price": valuation.price.model_copy(
                update={"price_class": PriceObservationClass.ORACLE_MARK}
            )
        }
    )
    with pytest.raises(ValuationError, match="not admissible"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_engine_rejects_a_stripped_numeraire_that_reuses_an_admissible_price() -> None:
    """The numeraire is part of the authority key and is read at USE, not at build."""

    from crypto_systems_intelligence_atlas.book6_support import build_engine

    engine, *_ = build_engine()
    forged = _valuation(numeraire="USD").model_copy(update={"numeraire": ""})
    with pytest.raises(ValuationError, match="explicit numeraire at use"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_engine_rejects_a_price_with_a_stripped_source() -> None:
    from crypto_systems_intelligence_atlas.book6_support import build_engine

    engine, *_ = build_engine()
    valuation = _valuation()
    forged = valuation.model_copy(
        update={"price": valuation.price.model_copy(update={"source_ref": ""})}
    )
    with pytest.raises(ValuationError, match="cited price source"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_every_valuation_purpose_is_engine_enforced() -> None:
    from crypto_systems_intelligence_atlas.book6_support import build_engine

    engine, *_ = build_engine()
    for purpose in ValuationPurpose:
        admissible = PRICE_AUTHORITY_MATRIX[purpose]
        for price_class in PriceObservationClass:
            valuation = _valuation(
                purpose=purpose, price_class=next(iter(admissible))
            )
            engine.authorize_current_valuation(valuation, as_of=NOW)
            if price_class in admissible:
                continue
            forged = valuation.model_copy(
                update={"price": valuation.price.model_copy(update={"price_class": price_class})}
            )
            with pytest.raises(ValuationError):
                engine.authorize_current_valuation(forged, as_of=NOW)
