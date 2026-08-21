import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[4] / 'research' / 'atomic_structure'
OUT = ROOT / '03_transitions'


def test_raw_path_and_event_counts():
    paths = pd.read_parquet(OUT / 'ASE_SESSION_PATH_LEDGER.parquet')
    noon = pd.read_parquet(OUT / 'ASE_NOON_EXTREME_LEDGER.parquet')
    post25 = pd.read_parquet(OUT / 'ASE_POST25_EVENT_LEDGER.parquet')
    assert len(paths) == 442
    assert len(noon) == 442
    assert len(post25) == 433


def test_noon_touch_and_close_are_distinct_fields():
    x = pd.read_parquet(OUT / 'ASE_NOON_EXTREME_LEDGER.parquet')
    required = {'H_AM','L_AM','P_12','NEW_HIGH_AFTER_12_TOUCH','NEW_LOW_AFTER_12_TOUCH','NEW_HIGH_AFTER_12_CLOSE','NEW_LOW_AFTER_12_CLOSE'}
    assert required.issubset(x.columns)


def test_atr_excludes_current_day():
    x = pd.read_parquet(OUT / 'ASE_ATR_SERIES.parquet')
    assert x.current_day_excluded.eq(True).all()
    assert x.loc[0, 'ATR20'] != x.loc[0, 'ATR20']


def test_walkforward_has_prior_cell_metadata():
    x = pd.read_csv(OUT / 'ASE_REMAINING_RANGE_WALKFORWARD.csv')
    assert len(x) == 1764
    assert (x.cell_n >= 1).all()
    assert x.date.nunique() == 441


def test_partition_guards_and_no_pnl():
    d = json.loads((ROOT / 'ASE_R2_1_DECISION.json').read_text())
    assert d['confirmation_consumed'] is False
    assert d['holdout_consumed'] is False
    assert d['strategy_pnl_computed'] is False
    assert d['optimization_performed'] is False
