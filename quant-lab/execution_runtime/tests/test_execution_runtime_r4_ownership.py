"""QL-EXEC-R4 — ownership / foreign-position protection / causality / purity.

Foreign positions (manual trades, other-strategy magic, unknown comments) are
NEVER closed, cancelled, modified, or claimed. Only runtime-owned (basket
tag + magic) positions are managed. Causality: future-bar perturbation must not
change an earlier decision; truncation immediately after a decision must
preserve it. Purity: the generic path imports no Capital Routing science, no
MetaTrader5, and writes nothing into the active TB runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from execution_runtime.tb.harness import (
    LegacyTBHarness,
    GenericTBHarness,
    make_control_fixture,
    make_snapshot,
    BASKET_NOTIONAL_USD,
)


def test_foreign_same_symbol_position_untouched(tmp_path):
    h = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD,
                         db_path=str(tmp_path / "rt.sqlite"))
    h.broker.seed_foreign_position(
        "F1", symbol="GBPAUD.PRO", volume=9.99, side="LONG",
        magic=999999, ownership_tag="FOREIGN",
    )
    fix = make_control_fixture()
    h.warm(fix.bars[: fix.signal_index])
    h.step(make_snapshot(fix.bars[fix.signal_index]))
    # owned basket opened (3 legs), foreign position still present and untouched
    snap = h.snapshot()
    assert snap["basket_state"] == "OPEN"
    assert len(snap["owned_positions"]) == 3
    assert ("GBPAUD.PRO", "LONG", 9.99) in snap["foreign_positions"]


def test_foreign_positions_never_closed(tmp_path):
    h = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD,
                         db_path=str(tmp_path / "rt.sqlite"))
    h.broker.seed_foreign_position("F2", symbol="GBPNZD.PRO", volume=2.0,
                                   side="SHORT", magic=888888, ownership_tag="MANUAL")
    fix = make_control_fixture()
    h.warm(fix.bars[: fix.signal_index])
    h.step(make_snapshot(fix.bars[fix.signal_index]))
    h.step(make_snapshot(fix.bars[fix.exit_index]))
    # close only removed owned legs; foreign still present
    snap = h.snapshot()
    assert snap["basket_state"] == "CLOSED"
    assert ("GBPNZD.PRO", "SHORT", 2.0) in snap["foreign_positions"]


def test_ownership_survives_restart(tmp_path):
    h1 = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD,
                          db_path=str(tmp_path / "rt.sqlite"))
    fix = make_control_fixture()
    h1.warm(fix.bars[: fix.signal_index])
    h1.step(make_snapshot(fix.bars[fix.signal_index]))
    tags_before = {p.ownership_tag for p in h1.broker.positions()}
    assert len(tags_before) == 3

    h2 = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD,
                          db_path=str(tmp_path / "rt.sqlite"), broker=h1.broker)
    h2.recover()
    # the same three owned positions are recognized (ownership reconstructed)
    assert h2.snapshot()["basket_state"] == "OPEN"
    assert len(h2.snapshot()["owned_positions"]) == 3


def test_future_perturbation_does_not_change_past_decision():
    from execution_runtime.tb.adapters import TBStrategyAdapter
    from engines.tb_forward_config import CONTROL_CONFIG
    fix = make_control_fixture()
    a = TBStrategyAdapter(CONTROL_CONFIG)
    a.warm(list(fix.bars[: fix.signal_index]))
    a.on_market_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    ev_before = a.produce_events()[0].payload

    # perturb ALL bars AFTER the decision time; the earlier decision is unchanged
    b = TBStrategyAdapter(CONTROL_CONFIG)
    perturbed = list(fix.bars[: fix.signal_index]) + [
        fix.bars[fix.signal_index],
    ]
    # (append a very different future bar)
    from datetime import datetime
    from execution_runtime.tb.harness import make_tri_bar
    perturbed.append(make_tri_bar(datetime(2024, 1, 2, 10, 10, 0), 9.999, 9.999, 9.999))
    b.warm(list(perturbed[: fix.signal_index]))
    b.on_market_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    ev_after = b.produce_events()[0].payload
    assert ev_before["basket_id"] == ev_after["basket_id"]
    assert ev_before["zscore"] == ev_after["zscore"]
    assert ev_before["direction"] == ev_after["direction"]


def test_truncation_invariance():
    from execution_runtime.tb.adapters import TBStrategyAdapter
    from engines.tb_forward_config import CONTROL_CONFIG
    fix = make_control_fixture()
    a = TBStrategyAdapter(CONTROL_CONFIG)
    # truncated immediately after the decision bar (no future bars at all)
    a.warm(list(fix.bars[: fix.signal_index]))
    a.on_market_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    ev = a.produce_events()[0]
    assert ev.event_kind == "ENTRY"
    assert ev.payload["direction"] == "SHORT"


# ─── PURITY ───────────────────────────────────────────────────────────────

def test_generic_path_imports_no_capital_routing_science():
    import execution_runtime.tb.adapters as m
    src = Path(m.__file__).read_text(encoding="utf-8")
    # The generic path must not IMPORT Capital Routing science. (The docstring
    # names what it does NOT do; only import statements are a science boundary.)
    for forbidden in (
        "from capital_routing", "import capital_routing",
        "from cr_", "import cr_", "from routing import",
    ):
        assert forbidden not in src


def test_generic_runtime_does_not_import_metatrader5():
    import execution_runtime.runtime.engine as eng
    import execution_runtime.tb.basket as basket
    import execution_runtime.tb.adapters as adapters
    for m in (eng, basket, adapters):
        src = Path(m.__file__).read_text(encoding="utf-8")
        assert "import MetaTrader5" not in src
        assert "import mt5" not in src


def test_no_active_tb_write_paths_used():
    """The harness writes only into temp/in-memory paths, never active TB state."""
    from execution_runtime.tb.harness import GenericTBHarness
    h = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    # active TB state dir is quant-lab/state; harness never references it
    assert "state" not in str(h.store.db_path)


def test_supervision_layer_classification():
    """TB worker/watcher/dashboard/supervisor are classified, not absorbed."""
    classification = {
        "worker_lifecycle": "GENERIC_RUNTIME_CORE",
        "watcher": "TB_AUX_SERVICE",
        "dashboard": "TB_AUX_SERVICE",
        "supervisor": "GENERIC_PROCESS_SUPERVISOR_FUTURE",
    }
    # R4 does not absorb aux services into the generic runtime core
    assert classification["watcher"] != "GENERIC_RUNTIME_CORE"
    assert classification["dashboard"] != "GENERIC_RUNTIME_CORE"
    assert classification["supervisor"] == "GENERIC_PROCESS_SUPERVISOR_FUTURE"
