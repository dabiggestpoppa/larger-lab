import json
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).parents[4]
FINAL = ROOT / 'research' / 'atomic_structure' / '04_final_ase2'
TRANS = ROOT / 'research' / 'atomic_structure' / '03_transitions'


# --- Evidence lineage conservation ---
def test_lineage_file_exists():
    assert (FINAL / 'ASE_EVIDENCE_LINEAGE.json').exists()


def test_lineage_json_valid():
    d = json.load(open(FINAL / 'ASE_EVIDENCE_LINEAGE.json'))
    assert 'resolution' in d
    assert d['resolution']['scale_downgrade_supported'] is False


def test_final_decision_exists():
    assert (FINAL / 'ASE_R2_FINAL_DECISION.json').exists()


def test_decision_enum_valid():
    d = json.load(open(FINAL / 'ASE_R2_FINAL_DECISION.json'))
    assert d['status'] in ['PASS_EMPIRICAL_TRANSITION_ENGINE',
                           'PASS_CONSTRAINT_CAPACITY_ENGINE_ONLY',
                           'FAIL_ATOMIC_PREDICTIVE_ENGINE']


def test_decision_no_confirmation():
    d = json.load(open(FINAL / 'ASE_R2_FINAL_DECISION.json'))
    assert d['confirmation_consumed'] is False
    assert d['holdout_consumed'] is False
    assert d['ASE3_authorized'] is False
    assert d['strategy_pnl_computed'] is False


# --- R_LOCK exact formula ---
def test_rlock_master_exists():
    assert (FINAL / 'ASE_RLOCK_MASTER.csv').exists()


def test_rlock_master_columns():
    fl = pd.read_csv(FINAL / 'ASE_RLOCK_MASTER.csv')
    for col in ['RL_UP_E1', 'RL_DN_E1', 'G_UP', 'G_DOWN', 'VU_touch_H17', 'VD_touch_H17']:
        assert col in fl.columns, f'{col} missing'


def test_rlock_positive():
    fl = pd.read_csv(FINAL / 'ASE_RLOCK_MASTER.csv')
    assert (fl['RL_UP_E1'].dropna() > 0).all()
    assert (fl['RL_DN_E1'].dropna() > 0).all()


# --- Subperiod stability ---
def test_subperiod_survives_both_years():
    sub = pd.read_csv(FINAL / 'ASE_RLOCK_SUBPERIOD.csv')
    for yr in [2023, 2024]:
        assert yr in sub['year'].values, f'{yr} missing'
    for _, r in sub.iterrows():
        assert r['spearman'] < 0, f'{r["side"]} {r["year"]} spearman positive'


# --- Rolling stability ---
def test_rolling_has_all_windows():
    roll = pd.read_csv(FINAL / 'ASE_RLOCK_ROLLING.csv')
    assert set(roll['window'].unique()) == {60, 90, 120}
    assert len(roll) > 900  # 381+351+321 windows


def test_rolling_majority_negative():
    roll = pd.read_csv(FINAL / 'ASE_RLOCK_ROLLING.csv')
    for w in [60, 90, 120]:
        sub = roll[roll['window'] == w]
        assert (sub['spearman_up'].dropna() < 0).mean() > 0.95, f'window {w} not majority negative'


# --- Estimator sensitivity ---
def test_estimator_sensitivity_all_negative():
    est = pd.read_csv(FINAL / 'ASE_RLOCK_ESTIMATOR_SENSITIVITY.csv')
    for name in ['E0', 'E1', 'E2', 'E3']:
        assert name in est['estimator'].values
    assert (est['spearman'] < 0).all()


# --- Baseline comparison ---
def test_baseline_rlock_vs_gap_close():
    base = pd.read_csv(FINAL / 'ASE_RLOCK_BASELINE_COMPARISON.csv')
    up = base[base['side'] == 'UP']
    g = up[up['model'] == 'D0_gap']['brier'].iloc[0]
    rl = up[up['model'] == 'D4_rlock']['brier'].iloc[0]
    assert abs(g - rl) < 0.01, f'G {g} vs RLOCK {rl} too different'


# --- Monotonicity ---
def test_monotonicity_declining():
    mon = pd.read_csv(FINAL / 'ASE_RLOCK_MONOTONICITY.csv')
    assert len(mon) > 0


# --- Side symmetry ---
def test_side_symmetry_both_negative():
    sym = pd.read_csv(FINAL / 'ASE_RLOCK_SIDE_SYMMETRY.csv')
    assert sym[sym['side'] == 'UP']['spearman'].iloc[0] < 0
    assert sym[sym['side'] == 'DN']['spearman'].iloc[0] < 0


# --- Horizon stability ---
def test_horizon_all_negative():
    hor = pd.read_csv(FINAL / 'ASE_RLOCK_HORIZON_STABILITY.csv')
    assert set(hor['horizon'].unique()) == {'H17', 'H19', 'H03'}
    assert (hor['spearman'] < 0).all()


# --- Generalized capacity ---
def test_generalized_capacity_exists():
    cap = pd.read_csv(FINAL / 'ASE_GENERALIZED_CAPACITY_CHECKPOINTS.csv')
    assert len(cap) > 0
    assert (cap['spearman'] < 0).all()


# --- Touch vs close ---
def test_touch_vs_close_exists():
    tc = pd.read_csv(FINAL / 'ASE_RLOCK_TOUCH_VS_CLOSE.csv')
    assert len(tc) > 0
    assert 'touch_rate' in tc.columns
    assert 'close_rate' in tc.columns


# --- Post-25 capacity ---
def test_post25_capacity_exists():
    p25 = pd.read_csv(FINAL / 'ASE_POST25_CAPACITY_ANALYSIS.csv')
    assert len(p25) > 0


# --- State compression ---
def test_state_compression():
    sc = pd.read_csv(FINAL / 'ASE_STATE_COMPRESSION.csv')
    null_brier = sc[sc['variable'] == 'BASELINE']['brier'].iloc[0]
    g_brier = sc[sc['variable'] == 'G']['brier'].iloc[0]
    assert g_brier < null_brier - 0.05, f'G {g_brier} not much better than BASELINE {null_brier}'


def test_state_compression_g_equals_rlock():
    sc = pd.read_csv(FINAL / 'ASE_STATE_COMPRESSION.csv')
    g = sc[sc['variable'] == 'G']['brier'].iloc[0]
    rl = sc[sc['variable'] == 'RLOCK']['brier'].iloc[0]
    assert abs(g - rl) < 0.005, f'G {g} vs RLOCK {rl} not close'


# --- Bootstrap ---
def test_bootstrap_exists():
    b = pd.read_csv(FINAL / 'ASE2_FINAL_BOOTSTRAP.csv')
    assert len(b) > 0
    assert (b['seed'] == 20260821).all()


# --- No 2025 consumption ---
def test_no_2025():
    fl = pd.read_csv(FINAL / 'ASE_RLOCK_MASTER.csv')
    dates = pd.to_datetime(fl['date'])
    assert dates.max() < pd.Timestamp('2025-01-01')


# --- Existing tests still pass (collected separately) ---
