"""
CR-RISK-BLOCK1 R1.1 — Event-Risk Reconstruction (canonical risk ledger).

Every sealed A/B routing event is normalized into a common unit (1.00R) with an
explicit mapping between:

    market return  ->  volatility-normalized position  ->  PnL  ->  R-multiple
                                                                  ->  account % return

All inputs are frozen: the Phase 7.5 sealed trade book (P7_5_TRADES.csv, P0
book, 890 events) and the frozen Phase 3 strict common H1 panel. No synthetic
trade replacement; the alpha is untouched.

Unit system (documented formulas, see also R1_EXPOSURE_TRUTH_REPORT.md):

    mkt_bps_i  = dir_i * (log P_exit - log P_entry) * 1e4      # frozen Phase-7 window
    pos_i      = TARGET_VOL / rv_i                              # vol-normalized sizing unit
    pnl_bps_i  = mkt_bps_i * pos_i
    net_bps_i  = pnl_bps_i - cost_bps_i * pos_i                 # cost incl. spread+swap
    1R         = TARGET_VOL * sqrt(hold_h)                      # one-sigma hold move
    r_i        = net_bps_i / 1R
    account%_i = r_i * RISK_PER_R_PCT                           # 1.0% per R (reference)

Prices: entry/exit price LEVELS are read from the frozen H1 panel with the exact
same window logic as the execution grid, so `price_return_bps` must reproduce the
grid's `gross_return_bps` to float tolerance.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .phase_7_5_audit import FROZEN_CONFIGS
from .phase_7_execution import _window
from .phase_7_families import ONE_WAY_COST_BPS

TARGET_VOL = 10.0        # bps per hour — Phase 7.5 vol-normalization target
RISK_PER_R_PCT = 1.0     # reference account risk per 1R event (documented parameter)
PAIR = "USDJPY"

GRID_MERGE_COLS = [
    "event_id", "mfe_bps", "mae_bps", "dir_mfe_bps", "dir_mae_bps",
    "time_to_mfe_h", "time_to_mae_h", "rv_bps_per_h", "cost_bps",
    "gross_return_bps", "dir_return_bps", "dir_net_bps", "severity", "session",
]


def risk_unit_bps(hold_h):
    """1R in bps of PnL: one-sigma move over the full hold for the
    vol-normalized position. PnL_sigma = pos*rv*sqrt(hold) = TARGET_VOL*sqrt(hold)."""
    return TARGET_VOL * np.sqrt(np.asarray(hold_h, dtype=float))


def build_ledger(trades: pd.DataFrame, grids: Dict[str, pd.DataFrame],
                 panel: pd.DataFrame) -> pd.DataFrame:
    """Merge the sealed trade book with the frozen grid outcomes + panel prices.

    Returns one row per executed routing event (P0 book, all splits).
    """
    g = pd.concat(list(grids.values()), ignore_index=True)
    ld = trades.merge(g[GRID_MERGE_COLS], on="event_id", how="left")
    n_missing = int(ld["dir_net_bps"].isna().sum())
    if n_missing:
        raise ValueError(f"{n_missing} trades missing execution-grid data (frozen input broken)")

    # ---- entry/exit price levels from the frozen H1 panel, same window logic ----
    grid_ns = panel.index.values.astype("int64")
    closes = panel[f"{PAIR}_close"].to_numpy(dtype=float)
    closes_log = np.log(closes)
    entry_px = np.full(len(ld), np.nan)
    exit_px = np.full(len(ld), np.nan)
    ts = pd.to_datetime(ld["event_start"], utc=True)
    for i in range(len(ld)):
        cfg = FROZEN_CONFIGS[ld.iloc[i]["family"]]
        t0 = int(ts.iloc[i].value)
        entry, exit_i = _window(grid_ns, t0, cfg["delay_h"], cfg["hold_h"])
        if exit_i >= entry and np.isfinite(closes_log[entry]) and np.isfinite(closes_log[exit_i]):
            entry_px[i] = float(closes[entry])
            exit_px[i] = float(closes[exit_i])
    ld["entry_price"] = entry_px
    ld["exit_price"] = exit_px
    valid_px = np.isfinite(entry_px) & np.isfinite(exit_px)
    ld["price_return_bps"] = np.where(
        valid_px, (np.log(np.where(valid_px, exit_px, 1.0))
                   - np.log(np.where(valid_px, entry_px, 1.0))) * 1e4, np.nan)
    # consistency check vs the frozen grid return (same arrays => same value)
    diff = (ld["price_return_bps"] - ld["gross_return_bps"]).abs().max()
    if np.isfinite(diff) and diff > 1e-6:
        raise ValueError(f"price/grid return mismatch (max |diff| = {diff:.2e})")

    # ---- unit mapping ----
    hold = ld["hold_h"].to_numpy(dtype=float)
    ru = risk_unit_bps(hold)
    ld["risk_unit_bps"] = ru
    ld["r_multiple"] = ld["pnl_bps"].to_numpy(dtype=float) / ru
    ld["account_return_pct"] = ld["r_multiple"] * RISK_PER_R_PCT
    ld["mfe_r"] = ld["dir_mfe_bps"].to_numpy(dtype=float) / ru
    ld["mae_r"] = ld["dir_mae_bps"].to_numpy(dtype=float) / ru
    ld["rv_eff_bps_per_h"] = TARGET_VOL / ld["pos"].to_numpy(dtype=float)
    # cost transparency: spread+commission (2x one-way) vs swap component
    base = 2.0 * ONE_WAY_COST_BPS[PAIR]
    ld["spread_commission_bps"] = base
    ld["swap_bps"] = ld["cost_bps"].to_numpy(dtype=float) - base

    ld["event_ts"] = ts
    return ld


def unit_mapping_formulas() -> Dict[str, str]:
    """Human-readable formula registry (written into the report + decision)."""
    return {
        "market_return_bps": "dir * (log P_exit - log P_entry) * 1e4",
        "position_unit": "pos = TARGET_VOL / rv   (TARGET_VOL = 10 bps/h; clamp >= 1.0 when rv missing)",
        "pnl_bps": "mkt_bps * pos",
        "net_pnl_bps": "pnl_bps - cost_bps * pos   (cost = 2*one_way spread+comm + signed swap)",
        "risk_unit_1R_bps": "TARGET_VOL * sqrt(hold_h)  = 10 * sqrt(6) = 24.4949 for hold=6h",
        "r_multiple": "net_pnl_bps / risk_unit_bps",
        "account_return_pct": "r_multiple * RISK_PER_R_PCT   (RISK_PER_R_PCT = 1.0 reference)",
        "units": {
            "mkt_bps": "basis points of price (pair return)",
            "pos": "unitless vol-normalized notional",
            "pnl_bps": "basis points of notional per vol-normalized position",
            "1R": "basis points of PnL (one-sigma hold move)",
            "account_return": "percent of account equity (at reference 1% per R)",
        },
        "parameters": {"TARGET_VOL": TARGET_VOL, "RISK_PER_R_PCT": RISK_PER_R_PCT,
                       "pair": PAIR},
    }
