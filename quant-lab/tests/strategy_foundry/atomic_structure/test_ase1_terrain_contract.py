import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[4] / 'research' / 'atomic_structure' / '02_terrain'))
from run_ase1_terrain import (  # noqa: E402
    CHECKPOINTS,
    balance_bucket,
    fixed_session_date,
    kmeans_1d,
    run_loops,
    three_am_state,
)
from strategy_foundry.atomic_structure.atomic_structure import first_hit_from_anchor  # noqa: E402


def bars(rows):
    idx = pd.date_range('2024-01-02 03:00', periods=len(rows), freq='5min', tz='America/New_York')
    return pd.DataFrame(rows, columns=['open', 'high', 'low', 'close'], index=idx).assign(local=idx)


def test_fixed_session_date_boundary_semantics():
    idx = pd.Series(pd.to_datetime(['2024-01-02 18:55', '2024-01-02 19:00', '2024-01-03 02:55', '2024-01-03 03:00']).tz_localize('America/New_York'))
    out = fixed_session_date(idx)
    assert list(out) == [pd.Timestamp('2024-01-02').date(), pd.Timestamp('2024-01-03').date(), pd.Timestamp('2024-01-03').date(), pd.Timestamp('2024-01-03').date()]


def test_kmeans_and_assignment_are_deterministic():
    values = [10, 11, 12, 25, 26, 27, 50, 51, 52]
    first = kmeans_1d(values)
    second = kmeans_1d(values)
    assert np.allclose(first[0], second[0])
    assert np.allclose(first[1], second[1])
    assert np.array_equal(first[2], second[2])


def test_loop_completion_and_completion_reset():
    frame = bars([
        (1.0000, 1.0002, 0.9999, 1.0001),  # establishes UP at close
        (1.0001, 1.0011, 1.0000, 1.0010),  # completes 1 AU at high
        (1.0010, 1.0011, 1.0008, 1.0009),  # establishes DOWN after reset
        (1.0009, 1.0010, 1.0000, 1.0001),  # adverse but not a 1 AU completion
        (1.0001, 1.0002, 0.9990, 0.9991),  # opposite loop formation
    ])
    events = run_loops(frame, 1.0000, 10.0, '2024-01-02', 1, 'BALANCED_ASIA', 'BALANCED')
    assert events[0]['completion_state'] == 'COMPLETED_1_AU'
    assert events[0]['next_state'] == 'COMPLETION_RESET'
    assert events[1]['origin_state'] == 'COMPLETION_RESET'


def test_loop_failure_taxonomy_is_deterministic():
    frame = bars([
        (1.0000, 1.0002, 0.9999, 1.0001),  # UP direction
        (1.0001, 1.0002, 0.9998, 0.9999),  # origin breach before completion
        (0.9999, 1.0000, 0.9997, 0.9998),
    ])
    events = run_loops(frame, 1.0000, 10.0, '2024-01-02', 1, 'BALANCED_ASIA', 'BALANCED')
    assert events[0]['failure_type'] in {'ORIGIN_BREACH', 'RETRACE_INVALIDATION', 'OPPOSITE_LOOP_FORMATION', 'TERMINAL_12PM', 'DATA_INVALID'}
    assert events == run_loops(frame, 1.0000, 10.0, '2024-01-02', 1, 'BALANCED_ASIA', 'BALANCED')


def test_checkpoint_boundaries_are_frozen():
    assert CHECKPOINTS == {'6AM': 6, '9AM': 9, '12PM': 12}
    assert tuple(CHECKPOINTS.values()) == (6, 9, 12)


def test_first_hit_ordering_uses_first_completed_bar():
    frame = bars([
        (1.0, 1.0, 1.0, 1.0),
        (1.0, 1.0010, 1.0, 1.0005),
        (1.0005, 1.0020, 1.0005, 1.0015),
    ])
    result = first_hit_from_anchor(frame, frame.index[0], 1.0, 10.0)
    assert result['0.5AU_first'] == 'UP'
    assert result['1AU_first'] == 'UP'


def test_daily_reset_does_not_cross_session_boundary():
    assert fixed_session_date(pd.Series(pd.to_datetime(['2024-01-05 23:55', '2024-01-06 00:00']).tz_localize('America/New_York'))).tolist() == [pd.Timestamp('2024-01-06').date(), pd.Timestamp('2024-01-06').date()]


def test_causality_artifact_passes_all_prefix_checks():
    import json
    audit_path = Path(__file__).parents[4] / 'research' / 'atomic_structure' / '02_terrain' / 'ASE_CAUSALITY_AUDIT.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    assert audit['future_perturbation_invariance'] == 'PASS'
    assert audit['tail_truncation_invariance'] == 'PASS'
    assert audit['head_truncation_invariance'] == 'PASS'
    assert audit['prefix_consistency'] == 'PASS'


def test_daily_state_and_balance_buckets_are_closed_set():
    assert three_am_state(1.0, 1.001, 0.999, 1.0, 5.0) in {'BALANCED_ASIA', 'ONE_SIDED_UP', 'ONE_SIDED_DOWN', 'PARTIAL_LOOP', 'FULL_LOOP', 'OVER_COMPLETED', 'UNRESOLVED_DEFICIT'}
    assert {balance_bucket(x) for x in [-1, -.2, 0, .2, 1]} == {'DOWN_HEAVY', 'DOWN_LEAN', 'BALANCED', 'UP_LEAN', 'UP_HEAVY'}
