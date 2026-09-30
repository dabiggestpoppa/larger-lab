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
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from .book6_definitions import ComparabilityClass


class ComparabilityError(ValueError):
    """A comparison is not licensed by the ratified comparability doctrine."""


class CorpusVerdict(str, Enum):
    """The ratified outcome class of a corpus row."""

    NOT_COMPARABLE = "NOT_COMPARABLE"
    CONDITIONAL = "CONDITIONAL"
    AS_DISTINCT = "AS_DISTINCT"


@dataclass(frozen=True)
class CorpusRow:
    """One mechanized false-comparison row."""

    row_id: str
    left_metric: str
    right_metric: str
    why_naive_fails: str
    verdict: CorpusVerdict
    required_methodology: str | None


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
        "routing-attribution-methodology",
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
        "lineage-dedup-methodology",
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
        "valuation-methodology-with-numeraire",
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
        "net-migration-methodology",
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
        "native-unit-growth-methodology",
    ),
    CorpusRow(
        "FC-15",
        "chain.throughput.ALL_ATTEMPTED",
        "chain.throughput.SUCCESS_ONLY",
        "differing failed-transaction treatment",
        CorpusVerdict.CONDITIONAL,
        "success-semantics-methodology",
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

    A ``CONDITIONAL`` row still REFUSES here: the caller must present the named
    methodology, and no ratified methodology exists yet.
    """

    for row in FALSE_COMPARISON_CORPUS:
        if row.left_metric == left_metric_id and row.right_metric == right_metric_id:
            return row.verdict
        if row.left_metric == right_metric_id and row.right_metric == left_metric_id:
            return row.verdict
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
) -> str:
    """Authorize a comparison or refuse it, with an explicit reason.

    ``methodology_ref`` is required for every ``CONDITIONAL`` row. The same
    comparability class is additionally required unless the corpus row itself
    licenses the pairing: comparing across comparability classes is refused by
    default.
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
    return "AUTHORIZED"


__all__ = [
    "authorize_comparison",
    "ComparabilityError",
    "CONDITIONAL_ROW_IDS",
    "CorpusRow",
    "CorpusVerdict",
    "FALSE_COMPARISON_CORPUS",
    "gate_comparison",
    "NOT_COMPARABLE_ROW_IDS",
]
