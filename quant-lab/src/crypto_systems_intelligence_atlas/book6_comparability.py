"""Book 6 comparability — the false-comparison corpus encoded as refusals.

A comparison layer that only permits comparisons launders false equivalence. The
ratified corpus (comparability v0.1 §6; validation stress matrix v0.1 §6) is
therefore encoded here as data with an enforcement gate, not as prose:

- ``NOT_COMPARABLE`` — the comparison has no licensed form and is refused;
- ``CONDITIONAL`` — comparable only under a named methodology, which must be
  supplied explicitly or the comparison is still refused;
- ``AS_DISTINCT`` — legitimate only as separate metrics.

There is no generic "everything numeric is comparable" path
(ratified plan v0.2 §7).

Book 6 Hardening R1 (R1-D1) closed the gap this module still had: a
``CONDITIONAL`` row checked only ``if not methodology_ref``, so
``methodology_ref="fake:anything"`` authorized the FC-05 comparison. The named
methodology is now a fully-qualified identity that must resolve in the Book 6
methodology registry AND be authorized by that methodology for that exact
corpus row.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from .book6_definitions import ComparabilityClass
from .book6_definitions import MeasurementMethodology
from .book6_methodology import (
    Book6MethodologyRegistry,
    MethodologyRegistryError,
    methodology_fingerprint,
)


class ComparabilityError(ValueError):
    """A comparison is not licensed by the ratified comparability doctrine."""


class CorpusVerdict(str, Enum):
    """The ratified outcome class of a corpus row."""

    NOT_COMPARABLE = "NOT_COMPARABLE"
    CONDITIONAL = "CONDITIONAL"
    AS_DISTINCT = "AS_DISTINCT"


@dataclass(frozen=True)
class CorpusRow:
    """One mechanized false-comparison row.

    R1 made ``required_methodology`` a versioned identity compared for EXACT
    equality. That was still a NAME, and R2-D1 showed that a name plus a
    self-declared row-authority list is enough for one caller-created object to
    license its own comparison.

    R2 therefore stores the full canonical methodology SPECIFICATION on the row.
    It is ratified corpus data, not runtime caller input, so a comparison can
    compare the registered methodology's content digest against content the
    operator ratified. ``required_methodology`` and
    ``required_methodology_fingerprint`` are derived from it, so they cannot
    drift apart.
    """

    row_id: str
    left_metric: str
    right_metric: str
    why_naive_fails: str
    verdict: CorpusVerdict
    required_methodology_spec: MeasurementMethodology | None = None

    @property
    def required_methodology(self) -> str | None:
        """The exact methodology identity this row requires (``ref@version``)."""

        if self.required_methodology_spec is None:
            return None
        return self.required_methodology_spec.identity

    @property
    def required_methodology_fingerprint(self) -> str | None:
        """The canonical content digest this row requires."""

        if self.required_methodology_spec is None:
            return None
        return methodology_fingerprint(self.required_methodology_spec)



def _canonical_spec(
    ref: str,
    formula: str,
    *,
    version: str = "1",
    window_rule: str = "declared window class of both compared metrics",
    filters: tuple[str, ...] = ("no-cross-window-comparison",),
    denominator_rule: str = "explicit measured denominator or not applicable",
    source_selection: str = "first-party Book 2-backed source",
    identity_rule: str = "subject identity rule declared per metric",
    row_id: str,
) -> MeasurementMethodology:
    """Build the canonical specification a CONDITIONAL corpus row requires.

    This lives in the ratified corpus rather than in a test fixture precisely so
    that it is NOT caller input: R2-D1 reproduced by registering a methodology
    with the right name and a garbage formula, which R1 could not distinguish
    from the real thing.
    """

    return MeasurementMethodology(
        methodology_ref=ref,
        version=version,
        formula=formula,
        window_rule=window_rule,
        filters=filters,
        denominator_rule=denominator_rule,
        source_selection=source_selection,
        identity_rule=identity_rule,
        authorized_corpus_row_ids=(row_id,),
    )



#: The fifteen ratified corpus rows (validation stress matrix v0.1 §6). Each is
#: a refusal or a gated comparison; none yields a bare comparable number.
FALSE_COMPARISON_CORPUS: Final[tuple[CorpusRow, ...]] = (
    CorpusRow(
        "FC-01",
        "chain.executed_transactions.L1",
        "chain.executed_transactions.ROLLUP",
        "different layers; a rollup batch is not an L1 user transaction",
        CorpusVerdict.NOT_COMPARABLE,
        None,
    ),
    CorpusRow(
        "FC-02",
        "chain.executed_transactions.INSTRUCTION_FAMILY",
        "chain.executed_transactions.EVM_TX",
        "an instruction is a program call, not a transaction",
        CorpusVerdict.NOT_COMPARABLE,
        None,
    ),
    CorpusRow(
        "FC-03",
        "chain.active_accounts",
        "chain.active_wallets",
        "account identity vs wallet-cluster identity; different sybil exposure",
        CorpusVerdict.AS_DISTINCT,
        None,
    ),
    CorpusRow(
        "FC-04",
        "chain.validator_count.POS",
        "chain.validator_count.BFT_FEDERATION",
        "consensus models differ; the count is not the same construct",
        CorpusVerdict.NOT_COMPARABLE,
        None,
    ),
    CorpusRow(
        "FC-05",
        "protocol.volume.DEX_NATIVE",
        "protocol.volume.AGGREGATOR_ROUTED",
        "routed volume includes the underlying venue volume; overlap unknown",
        CorpusVerdict.CONDITIONAL,
        _canonical_spec(
            "routing-attribution-methodology",
            "venue_routed_volume = venue_volume - overlap_with_other_venues, "
            "where overlap is resolved by per-fill route attribution",
            row_id="FC-05",
        ),
    ),
    CorpusRow(
        "FC-06",
        "capital.supplied_principal",
        "capital.tvL_like_total",
        "a lending total is not a single construct comparable to supplied principal",
        CorpusVerdict.AS_DISTINCT,
        None,
    ),
    CorpusRow(
        "FC-07",
        "capital.staked_principal",
        "capital.restaked_claims",
        "restaked claims may re-express underlying stake",
        CorpusVerdict.CONDITIONAL,
        _canonical_spec(
            "lineage-dedup-methodology",
            "restaked_principal = stake_represented_by_claim - "
            "stake_already_counted_at_the_same_origin",
            row_id="FC-07",
        ),
    ),
    CorpusRow(
        "FC-08",
        "capital.perp_notional",
        "capital.collateral_capital",
        "exposure domain vs principal domain (Book 5 ALG-5/9)",
        CorpusVerdict.NOT_COMPARABLE,
        None,
    ),
    CorpusRow(
        "FC-09",
        "token.native_supply",
        "capital.common_value_supply",
        "a native-unit count is not a numeraire value",
        CorpusVerdict.CONDITIONAL,
        _canonical_spec(
            "valuation-methodology-with-numeraire",
            "common_value_supply = native_supply * price_observation, with the "
            "numeraire and the admissible price class stated explicitly",
            row_id="FC-09",
        ),
    ),
    CorpusRow(
        "FC-10",
        "developer.commits",
        "developer.deployed_apps",
        "off-chain activity is not structural deployment",
        CorpusVerdict.NOT_COMPARABLE,
        None,
    ),
    CorpusRow(
        "FC-11",
        "protocol.fees_paid",
        "protocol.protocol_revenue",
        "fees paid is not revenue after participant cuts",
        CorpusVerdict.AS_DISTINCT,
        None,
    ),
    CorpusRow(
        "FC-12",
        "capital.gross_bridge_flow",
        "capital.net_capital_migration",
        "gross includes round trips; net is not gross minus fees",
        CorpusVerdict.CONDITIONAL,
        _canonical_spec(
            "net-migration-methodology",
            "net_migration = inbound_bridged - outbound_bridged, counted once "
            "per unique address and net of round trips",
            row_id="FC-12",
        ),
    ),
    CorpusRow(
        "FC-13",
        "token.holders",
        "protocol.users",
        "a token is not its protocol (Axiom 2)",
        CorpusVerdict.NOT_COMPARABLE,
        None,
    ),
    CorpusRow(
        "FC-14",
        "capital.common_value_total",
        "capital.native_quantity_growth",
        "price appreciation masquerading as native growth",
        CorpusVerdict.CONDITIONAL,
        _canonical_spec(
            "native-unit-growth-methodology",
            "native_growth = quantity_t1 - quantity_t0 measured in the native "
            "unit, holding the price constant",
            row_id="FC-14",
        ),
    ),
    CorpusRow(
        "FC-15",
        "chain.throughput.ALL_ATTEMPTED",
        "chain.throughput.SUCCESS_ONLY",
        "differing failed-transaction treatment",
        CorpusVerdict.CONDITIONAL,
        _canonical_spec(
            "success-semantics-methodology",
            "throughput = count(transactions where status == SUCCESS), with the "
            "success predicate and the included set stated explicitly",
            row_id="FC-15",
        ),
    ),
)

#: Corpus rows whose comparison is structurally impossible, for evidence.
NOT_COMPARABLE_ROW_IDS: Final[tuple[str, ...]] = tuple(
    row.row_id for row in FALSE_COMPARISON_CORPUS if row.verdict is CorpusVerdict.NOT_COMPARABLE
)
CONDITIONAL_ROW_IDS: Final[tuple[str, ...]] = tuple(
    row.row_id for row in FALSE_COMPARISON_CORPUS if row.verdict is CorpusVerdict.CONDITIONAL
)


def gate_comparison(left_metric_id: str, right_metric_id: str) -> CorpusVerdict:
    """Return the corpus verdict for a metric pair (no methodology supplied).

    A ``CONDITIONAL`` row still REFUSES here: the caller must present the exact
    named methodology identity, and none is registered by default.
    """

    return corpus_row_for(left_metric_id, right_metric_id).verdict


def corpus_row_for(left_metric_id: str, right_metric_id: str) -> CorpusRow:
    """Return the corpus row governing a metric pair, symmetrically, or refuse."""

    for row in FALSE_COMPARISON_CORPUS:
        if row.left_metric == left_metric_id and row.right_metric == right_metric_id:
            return row
        if row.left_metric == right_metric_id and row.right_metric == left_metric_id:
            return row
    raise ComparabilityError(
        f"no corpus row governs {left_metric_id!r} vs {right_metric_id!r}"
    )


def authorize_comparison(
    left_metric_id: str,
    right_metric_id: str,
    *,
    methodology_ref: str | None,
    left_class: ComparabilityClass,
    right_class: ComparabilityClass,
    methodologies: Book6MethodologyRegistry,
) -> str:
    """Authorize a comparison or refuse it, with an explicit reason.

    R1 (R1-D1): for a ``CONDITIONAL`` row a non-empty ``methodology_ref`` is no
    longer sufficient. The reference must be the EXACT methodology identity the
    corpus row requires, that methodology must be registered and current in the
    Book 6 methodology registry, and the methodology must itself declare
    authority for that corpus row. Registration alone is still not authority, so
    a later supersession or local invalidation makes the comparison refuse again.

    R2 (R2-D1) adds the condition R1 was missing. R1 compared an IDENTITY and
    a SELF-DECLARED row list, and one caller-created ``MeasurementMethodology``
    could satisfy both at once - right name, garbage formula, ``FC-05`` in its
    own row set, comparison ``AUTHORIZED``. The row therefore now pins the full
    canonical methodology SPECIFICATION and this gate compares the registered
    methodology's CONTENT digest against it. The authority relationship is no
    longer something a caller can assert by including its own row id.
    """

    verdict = gate_comparison(left_metric_id, right_metric_id)
    if verdict is CorpusVerdict.NOT_COMPARABLE:
        raise ComparabilityError(
            f"{left_metric_id} vs {right_metric_id} is NOT_COMPARABLE under the "
            f"ratified corpus; the comparison is refused"
        )
    if verdict is CorpusVerdict.AS_DISTINCT:
        raise ComparabilityError(
            f"{left_metric_id} vs {right_metric_id} is licensed only as separate "
            f"metrics, never as a comparison"
        )
    row = corpus_row_for(left_metric_id, right_metric_id)
    if not methodology_ref:
        raise ComparabilityError(
            f"{left_metric_id} vs {right_metric_id} is comparable only under a "
            f"named methodology; none was supplied"
        )
    if left_class is not right_class:
        raise ComparabilityError(
            f"{left_metric_id} and {right_metric_id} declare different "
            f"comparability classes ({left_class.value} vs {right_class.value})"
        )
    assert row.required_methodology is not None  # guaranteed for CONDITIONAL
    assert row.required_methodology_spec is not None
    try:
        methodologies.require_comparison_authority(
            methodology_identity_ref=methodology_ref,
            corpus_row_id=row.row_id,
            required_spec=row.required_methodology_spec,
        )
    except MethodologyRegistryError as exc:
        raise ComparabilityError(
            f"{left_metric_id} vs {right_metric_id} requires methodology "
            f"{row.required_methodology}: {exc}"
        ) from exc
    return "AUTHORIZED"


__all__ = [
    "authorize_comparison",
    "ComparabilityError",
    "CONDITIONAL_ROW_IDS",
    "corpus_row_for",
    "CorpusRow",
    "CorpusVerdict",
    "FALSE_COMPARISON_CORPUS",
    "gate_comparison",
    "NOT_COMPARABLE_ROW_IDS",
]
