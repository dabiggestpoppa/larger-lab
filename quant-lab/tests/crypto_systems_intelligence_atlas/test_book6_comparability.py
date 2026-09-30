"""Book 6 comparability — the ratified false-comparison corpus as refusals.

A comparison layer that permits everything launders false equivalence. All
fifteen ratified corpus rows are exercised mechanically: none yields a bare
comparable number, every ``CONDITIONAL`` row is refused without its named
methodology, and there is no generic "everything numeric is comparable" path
(ratified comparability matrix v0.1; plan v0.2 §7).
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book6_comparability import (
    CONDITIONAL_ROW_IDS,
    FALSE_COMPARISON_CORPUS,
    NOT_COMPARABLE_ROW_IDS,
    ComparabilityError,
    CorpusVerdict,
    authorize_comparison,
    gate_comparison,
)
from crypto_systems_intelligence_atlas.book6_definitions import ComparabilityClass

#: The fifteen comparisons the operator required to be guarded, mapped to the
#: corpus row that mechanizes each refusal.
RATIFIED_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("FC-01", "chain.executed_transactions.L1", "chain.executed_transactions.ROLLUP"),
    (
        "FC-02",
        "chain.executed_transactions.INSTRUCTION_FAMILY",
        "chain.executed_transactions.EVM_TX",
    ),
    ("FC-03", "chain.active_accounts", "chain.active_wallets"),
    ("FC-04", "chain.validator_count.POS", "chain.validator_count.BFT_FEDERATION"),
    ("FC-05", "protocol.volume.DEX_NATIVE", "protocol.volume.AGGREGATOR_ROUTED"),
    ("FC-06", "capital.supplied_principal", "capital.tvL_like_total"),
    ("FC-07", "capital.staked_principal", "capital.restaked_claims"),
    ("FC-08", "capital.perp_notional", "capital.collateral_capital"),
    ("FC-09", "token.native_supply", "capital.common_value_supply"),
    ("FC-10", "developer.commits", "developer.deployed_apps"),
    ("FC-11", "protocol.fees_paid", "protocol.protocol_revenue"),
    ("FC-12", "capital.gross_bridge_flow", "capital.net_capital_migration"),
    ("FC-13", "token.holders", "protocol.users"),
    ("FC-14", "capital.common_value_total", "capital.native_quantity_growth"),
    ("FC-15", "chain.throughput.ALL_ATTEMPTED", "chain.throughput.SUCCESS_ONLY"),
)

SAME = ComparabilityClass.CHAIN_WITHIN_FAMILY
OTHER = ComparabilityClass.PROTOCOL_WITHIN_MODEL


# -- corpus shape -------------------------------------------------------------


def test_corpus_has_the_fifteen_ratified_rows() -> None:
    assert len(FALSE_COMPARISON_CORPUS) == 15


def test_every_required_operator_comparison_has_a_row() -> None:
    by_id = {row.row_id: (row.left_metric, row.right_metric) for row in FALSE_COMPARISON_CORPUS}
    for row_id, left, right in RATIFIED_PAIRS:
        assert by_id[row_id] == (left, right), row_id


def test_row_ids_are_unique_and_well_formed() -> None:
    ids = [row.row_id for row in FALSE_COMPARISON_CORPUS]
    assert len(set(ids)) == len(ids)
    assert all(len(row_id) == 5 and row_id.startswith("FC-") for row_id in ids)


def test_every_row_states_why_the_naive_comparison_fails() -> None:
    for row in FALSE_COMPARISON_CORPUS:
        assert len(row.why_naive_fails) > 10, row.row_id


def test_conditional_rows_declare_a_required_methodology() -> None:
    for row in FALSE_COMPARISON_CORPUS:
        if row.verdict is CorpusVerdict.CONDITIONAL:
            assert row.required_methodology, row.row_id
        else:
            assert row.required_methodology is None, row.row_id


def test_no_row_is_a_bare_comparable_verdict() -> None:
    assert {row.verdict for row in FALSE_COMPARISON_CORPUS} <= {
        CorpusVerdict.NOT_COMPARABLE,
        CorpusVerdict.CONDITIONAL,
        CorpusVerdict.AS_DISTINCT,
    }


def test_index_tuples_partition_the_corpus() -> None:
    assert set(NOT_COMPARABLE_ROW_IDS).isdisjoint(CONDITIONAL_ROW_IDS)
    assert len(NOT_COMPARABLE_ROW_IDS) + len(CONDITIONAL_ROW_IDS) <= 15


# -- the gate refuses, it does not compute ------------------------------------


@pytest.mark.parametrize(("row_id", "left", "right"), RATIFIED_PAIRS, ids=[p[0] for p in RATIFIED_PAIRS])
def test_every_ratified_pair_is_gated(row_id: str, left: str, right: str) -> None:
    assert gate_comparison(left, right) in set(CorpusVerdict)


@pytest.mark.parametrize(("row_id", "left", "right"), RATIFIED_PAIRS, ids=[p[0] for p in RATIFIED_PAIRS])
def test_every_ratified_pair_is_refused_without_its_methodology(
    row_id: str, left: str, right: str
) -> None:
    verdict = gate_comparison(left, right)
    with pytest.raises(ComparabilityError):
        authorize_comparison(
            left, right, methodology_ref=None, left_class=SAME, right_class=SAME
        )
    if verdict is not CorpusVerdict.CONDITIONAL:
        with pytest.raises(ComparabilityError):
            authorize_comparison(
                left,
                right,
                methodology_ref="some-methodology",
                left_class=SAME,
                right_class=SAME,
            )


@pytest.mark.parametrize(
    "row_id",
    [pair[0] for pair in RATIFIED_PAIRS if pair[0] in CONDITIONAL_ROW_IDS],
)
def test_conditional_pairs_authorize_only_under_a_named_methodology(row_id: str) -> None:
    row = next(r for r in FALSE_COMPARISON_CORPUS if r.row_id == row_id)
    assert (
        authorize_comparison(
            row.left_metric,
            row.right_metric,
            methodology_ref=row.required_methodology,
            left_class=SAME,
            right_class=SAME,
        )
        == "AUTHORIZED"
    )


@pytest.mark.parametrize(
    "row_id",
    [pair[0] for pair in RATIFIED_PAIRS if pair[0] in NOT_COMPARABLE_ROW_IDS],
)
def test_not_comparable_pairs_stay_refused_even_with_a_methodology(row_id: str) -> None:
    row = next(r for r in FALSE_COMPARISON_CORPUS if r.row_id == row_id)
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            row.left_metric,
            row.right_metric,
            methodology_ref="some-methodology",
            left_class=SAME,
            right_class=SAME,
        )


def test_as_distinct_pairs_are_never_a_comparison() -> None:
    with pytest.raises(ComparabilityError, match="separate metrics"):
        authorize_comparison(
            "chain.active_accounts",
            "chain.active_wallets",
            methodology_ref="identity-methodology",
            left_class=SAME,
            right_class=SAME,
        )


# -- specific ratified refusals ----------------------------------------------


def test_ethereum_l1_transactions_are_not_rollup_transactions() -> None:
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            "chain.executed_transactions.L1",
            "chain.executed_transactions.ROLLUP",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_solana_instructions_are_not_evm_transactions() -> None:
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            "chain.executed_transactions.INSTRUCTION_FAMILY",
            "chain.executed_transactions.EVM_TX",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_perp_notional_is_not_collateral() -> None:
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            "capital.perp_notional",
            "capital.collateral_capital",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_token_holders_are_not_protocol_users() -> None:
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            "token.holders",
            "protocol.users",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_validator_counts_do_not_cross_consensus_models() -> None:
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            "chain.validator_count.POS",
            "chain.validator_count.BFT_FEDERATION",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_github_commits_are_not_deployed_developer_activity() -> None:
    with pytest.raises(ComparabilityError, match="NOT_COMPARABLE"):
        authorize_comparison(
            "developer.commits",
            "developer.deployed_apps",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_fees_are_not_revenue() -> None:
    with pytest.raises(ComparabilityError, match="separate metrics"):
        authorize_comparison(
            "protocol.fees_paid",
            "protocol.protocol_revenue",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_supplied_principal_is_not_a_tvl_like_total() -> None:
    with pytest.raises(ComparabilityError, match="separate metrics"):
        authorize_comparison(
            "capital.supplied_principal",
            "capital.tvL_like_total",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_nominal_value_growth_is_not_native_growth() -> None:
    with pytest.raises(ComparabilityError, match="named methodology"):
        authorize_comparison(
            "capital.common_value_total",
            "capital.native_quantity_growth",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_dex_volume_needs_a_routing_attribution_methodology() -> None:
    with pytest.raises(ComparabilityError, match="named methodology"):
        authorize_comparison(
            "protocol.volume.DEX_NATIVE",
            "protocol.volume.AGGREGATOR_ROUTED",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_restaked_claims_need_a_lineage_dedup_methodology() -> None:
    with pytest.raises(ComparabilityError, match="named methodology"):
        authorize_comparison(
            "capital.staked_principal",
            "capital.restaked_claims",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_stablecoin_supply_is_not_reserve_value() -> None:
    with pytest.raises(ComparabilityError, match="named methodology"):
        authorize_comparison(
            "token.native_supply",
            "capital.common_value_supply",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_gross_bridge_flow_needs_a_net_migration_methodology() -> None:
    with pytest.raises(ComparabilityError, match="named methodology"):
        authorize_comparison(
            "capital.gross_bridge_flow",
            "capital.net_capital_migration",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


def test_failed_transaction_treatment_needs_a_success_semantics_methodology() -> None:
    with pytest.raises(ComparabilityError, match="named methodology"):
        authorize_comparison(
            "chain.throughput.ALL_ATTEMPTED",
            "chain.throughput.SUCCESS_ONLY",
            methodology_ref=None,
            left_class=SAME,
            right_class=SAME,
        )


# -- the gate is symmetric and has no wildcard -------------------------------


def test_the_gate_is_symmetric() -> None:
    for row in FALSE_COMPARISON_CORPUS:
        assert gate_comparison(row.left_metric, row.right_metric) is row.verdict
        assert gate_comparison(row.right_metric, row.left_metric) is row.verdict


def test_an_ungoverned_pair_is_refused_not_defaulted() -> None:
    with pytest.raises(ComparabilityError, match="no corpus row governs"):
        gate_comparison("chain.whatever", "chain.something_else")


def test_a_wildcard_comparison_is_refused() -> None:
    with pytest.raises(ComparabilityError, match="no corpus row governs"):
        gate_comparison("*", "*")


def test_comparability_classes_must_match_even_under_a_named_methodology() -> None:
    with pytest.raises(ComparabilityError, match="different comparability classes"):
        authorize_comparison(
            "protocol.volume.DEX_NATIVE",
            "protocol.volume.AGGREGATOR_ROUTED",
            methodology_ref="routing-attribution-methodology",
            left_class=SAME,
            right_class=OTHER,
        )


def test_engine_comparison_goes_through_the_same_gate() -> None:
    from crypto_systems_intelligence_atlas.book6_core import ComparabilityError as EngineError
    from crypto_systems_intelligence_atlas.book6_support import (
        build_engine_with_definitions,
        definition,
    )

    engine = build_engine_with_definitions(
        definition("protocol.volume.DEX_NATIVE"),
        definition("protocol.volume.AGGREGATOR_ROUTED"),
    )
    assert EngineError is ComparabilityError
    with pytest.raises(ComparabilityError):
        engine.authorize_comparison(
            "protocol.volume.DEX_NATIVE", "protocol.volume.AGGREGATOR_ROUTED", methodology_ref=None
        )
    assert (
        engine.authorize_comparison(
            "protocol.volume.DEX_NATIVE",
            "protocol.volume.AGGREGATOR_ROUTED",
            methodology_ref="routing-attribution-methodology",
        )
        == "AUTHORIZED"
    )
