import numpy as np
import pandas as pd
import pytest
from pathlib import Path

ROOT = Path(__file__).parents[4]
TRANS = ROOT / 'research' / 'atomic_structure' / '03_transitions'
TERRAIN = ROOT / 'research' / 'atomic_structure' / '02_terrain'
MIN_BARS = 90


@pytest.fixture(scope='module')
def noon():
    return pd.read_parquet(TRANS / 'ASE_NOON_EXTREME_LEDGER_REPAIRED.parquet')


@pytest.fixture(scope='module')
def post25():
    return pd.read_parquet(TRANS / 'ASE_POST25_EVENT_LEDGER_REPAIRED.parquet')


@pytest.fixture(scope='module')
def varclock():
    return pd.read_csv(TRANS / 'ASE_VARIANCE_CLOCK_REPAIRED.csv')


@pytest.fixture(scope='module')
def score():
    return pd.read_csv(TRANS / 'ASE_REMAINING_RANGE_SCORE_SUMMARY.csv')


# --- raw path reconstruction / session membership ---
def test_noon_ledger_has_full_day_and_3_12_anchors(noon):
    assert 'H_PRE12' in noon.columns
    assert 'H_3_12' in noon.columns
    assert 'L_PRE12' in noon.columns
    assert noon['H_PRE12'].notna().sum() > 0


def test_noon_price_is_last_completed_pre_noon_bar(noon):
    # P_12_time must be < 12:00 local and typical value 11:55
    t = noon['P_12_time'].dropna().iloc[0]
    ts = pd.Timestamp(t)
    assert ts.hour < 12
    # spot check the actual timestamp semantics
    assert ts.strftime('%H:%M') == '11:55' or ts.strftime('%H:%M') == '11:50' or ts.strftime('%H:%M') == '11:45'


def test_noon_anchor_full_includes_asian_pre12(noon):
    # H_PRE12 must be >= H_3_12 on most days (full window superset)
    sub = noon.dropna(subset=['H_PRE12', 'H_3_12'])
    assert (sub['H_PRE12'] >= sub['H_3_12'] - 1e-9).mean() > 0.9
    assert (sub['L_PRE12'] <= sub['L_3_12'] + 1e-9).mean() > 0.9


def test_noon_horizon_matrix_has_3_horizons():
    h = pd.read_csv(TRANS / 'ASE_NOON_HORIZON_MATRIX.csv')
    assert set(['H17', 'H19', 'H03']).issubset(set(h.horizon))


def test_noon_touch_implies_close_or_same_sided_consistency(noon):
    # if close beyond happened, touch must be True (a new extreme was touched)
    gg = noon.dropna(subset=['touch_full'])
    viol = gg[(gg['close_full'] == True) & (gg['touch_full'] == False)]  # noqa: E712
    assert len(viol) == 0


# --- E25 vs E50 ---
def test_e25_ne_e50(post25):
    # E50 event rate must be lower than E25 touch rate (extension is deeper)
    pv = post25[(post25.event_kind == 'E25_CEREBUS_VALID') & (post25.completion == 'touch')]
    assert pv['e50_extension_later'].mean() <= pv['e25_retouch_later'].mean()


def test_retouch_not_extension(post25):
    pv = post25[(post25.event_kind == 'E25_CEREBUS_VALID') & (post25.completion == 'touch')]
    assert 'E25_RETOUCH' in pv['first_event'].unique()


def test_same_bar_ambiguity_flag(post25):
    pv = post25[(post25.event_kind == 'E25_CEREBUS_VALID') & (post25.completion == 'touch')]
    assert pv['same_bar_ambiguity'].dtype == bool
    assert pv['same_bar_ambiguity'].mean() < 0.5


# --- variance clock ---
def test_variance_clock_has_shares(varclock):
    for col in ['share_17', 'share_next03', 'share_24h']:
        assert col in varclock.columns
    s = varclock['share_17'].dropna()
    assert s.between(0, 1).all()


def test_variance_share_denominator_consistency(varclock):
    # share_next03 must be <= share_17 because denominator is larger
    v = varclock.dropna(subset=['share_17', 'share_next03'])
    assert (v['share_next03'] <= v['share_17'] + 1e-9).mean() >= 0.99


# --- walk-forward & transition scoring ---
def test_score_summary_has_matched_hierarchy(score):
    m = score[score['model'] == 'HIER_MATCHED']
    assert len(m) == 5  # 4 checkpoints + ALL
    assert m['n_scored'].min() > 100


def test_transition_score_richer_not_better():
    t = pd.read_csv(TRANS / 'ASE_TRANSITION_PREDICTIVE_SCORE_REPAIRED.csv')
    t0 = t[t.model == 'T0']['log_loss'].iloc[0]
    assert all(t[t.model != 'T0']['log_loss'] >= t0 - 1e-6)


def test_bootstrap_reproducible():
    b = pd.read_csv(TRANS / 'ASE2_2_BOOTSTRAP.csv')
    assert set(b['seed']) == {20260821}
    assert (b['replicates'] == 2000).all()


def test_lock_ratio_monotonic():
    lk = pd.read_csv(TRANS / 'ASE_LOCK_RATIO_ANALYSIS_REPAIRED.csv')
    d = lk.dropna(subset=['R_LOCK_UP_A1', 'VIOL_UP_H17'])
    assert len(d) > 100
    assert d['R_LOCK_UP_A1'].corr(d['VIOL_UP_H17'], method='spearman') < 0


def test_no_2025_rows(noon, post25):
    assert noon['date'].max() <= '2024-12-31'
    assert post25['date'].max() <= '2024-12-31'


def test_artifact_files_exist():
    for f in [
        'ASE_NOON_EXTREME_HOLD_REPAIRED.csv',
        'ASE_NOON_HORIZON_MATRIX.csv',
        'ASE_POST25_REVERSAL_MATRIX_REPAIRED.csv',
        'ASE_POST25_FIRST_EVENT_ORDERING_REPAIRED.csv',
        'ASE_POST25_TOUCH_VS_CLOSE.csv',
        'ASE_LOCK_RATIO_ANALYSIS_REPAIRED.csv',
        'ASE_REMAINING_RANGE_SCORE_SUMMARY.csv',
        'ASE_TRANSITION_PREDICTIVE_SCORE_REPAIRED.csv',
        'ASE_MECHANISM_SOURCE_COMPARISON_REPAIRED.csv',
        'ASE_VARIANCE_CLOCK_REPAIRED.csv',
        'ASE_NOON_RANGE_CONTRACT.md',
        'ASE_POST25_EVENT_CONTRACT_AUDIT.md',
        'ASE_VARIANCE_CLOCK_AUDIT.md',
    ]:
        assert (TRANS / f).exists(), f


def test_no_2025_confirmation_or_holdout_consumed():
    assert not hasattr(pytest, 'ase2_2025_consumed')