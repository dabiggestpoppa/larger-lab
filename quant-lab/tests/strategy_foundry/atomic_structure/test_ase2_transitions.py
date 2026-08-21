import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parents[4] / 'research' / 'atomic_structure'
OUT = ROOT / '03_transitions'


def test_transition_probabilities_sum_by_condition():
    x = pd.read_csv(OUT / 'ASE_STATE_TRANSITION_MATRIX.csv')
    sums = x.groupby(['conditioning', 'current_state'])['probability'].sum()
    assert ((sums - 1).abs() < 1e-9).all()


def test_transition_counts_are_positive_and_observed_only():
    x = pd.read_csv(OUT / 'ASE_STATE_TRANSITION_COUNTS.csv')
    assert (x['count'] > 0).all()
    assert x['sample_n'].max() <= 442


def test_no_future_features_are_declared():
    d = json.loads((ROOT / 'ASE_R2_DECISION.json').read_text())
    assert d['confirmation_consumed'] is False
    assert d['holdout_consumed'] is False
    assert d['strategy_pnl_computed'] is False


def test_required_outputs_exist_and_have_rows():
    names = [
        'ASE_NEXT_LOOP_DIRECTION.csv', 'ASE_FAILURE_TRANSITIONS.csv',
        'ASE_REMAINING_RANGE_BASELINES.csv', 'ASE_REMAINING_RANGE_QUANTILES.csv',
        'ASE_TIME_TO_COMPLETION.csv', 'ASE_SURVIVAL_CURVES.csv',
        'ASE_UNCERTAINTY_LAYERING.csv', 'ASE_VARIANCE_CLOCK.csv',
        'ASE_NOON_EXTREME_HOLD.csv',
        'ASE_POST25_REVERSAL_MATRIX.csv', 'ASE_POST25_STATE_TRANSITION.csv',
        'ASE_POST25_FIRST_EVENT_ORDERING.csv', 'ASE_BOOTSTRAP_INFERENCE.csv',
    ]
    for name in names:
        frame = pd.read_csv(OUT / name)
        assert not frame.empty, name


def test_path_outputs_are_explicitly_labeled():
    assert 'new_high_touch' in (OUT / 'ASE_NOON_EXTREME_HOLD.csv').read_text(encoding='utf-8')
    assert 'source_claim' in (OUT / 'ASE_MECHANISM_SOURCE_COMPARISON.csv').read_text(encoding='utf-8')
