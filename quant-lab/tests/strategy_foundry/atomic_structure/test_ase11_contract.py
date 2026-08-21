import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[4] / 'research' / 'atomic_structure' / '02_terrain'))
from run_ase1_terrain import AR_MAX_PIPS, generation_a_classify, gated_kmeans
from strategy_foundry.atomic_structure.atomic_structure import add_tiers


def test_generation_a_boundary_fixture():
    assert [generation_a_classify(v) for v in (10, 18, 19.9)] == [('T1', False)] * 3
    assert [generation_a_classify(v) for v in (20, 25, 29.9)] == [('T2', False)] * 3
    assert [generation_a_classify(v) for v in (30, 38, 44.9, 45)] == [('T3', False)] * 4
    assert generation_a_classify(50) == (None, True)
    assert generation_a_classify(218.4) == (None, True)
    assert AR_MAX_PIPS == 45.0


def test_gated_kmeans_excludes_nogo_but_retains_membership_input():
    centroids, bounds, labels, calibration = gated_kmeans([10, 20, 30, 45, 50, 218.4])
    assert len(calibration) == 4
    assert len(labels) == 4
    assert np.all(centroids[:-1] < centroids[1:])


def test_four_tier_fields_are_separate():
    frame = pd.DataFrame({'asian_range': [10.0, 25.0, 35.0, 50.0]})
    result = add_tiers(frame, [13.7, 22.5, 34.6])
    assert set(['session_ar_tier', 'ar_no_go_state', 'au_raw', 'au_operational', 'trigger_raw', 'trigger_operational']).issubset(result.columns)
    assert result.session_ar_tier.tolist() == ['T1', 'T2', 'T3', None]
    assert result.ar_no_go_state.tolist() == [False, False, False, True]
    assert result.au_operational.tolist()[:3] == [10.0, 12.0, 15.0]
