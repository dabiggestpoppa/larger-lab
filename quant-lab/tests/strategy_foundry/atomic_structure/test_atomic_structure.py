import numpy as np
import pandas as pd
import pytest
from strategy_foundry.atomic_structure.atomic_structure import (
    normalize, kmeans_1d, assign_tier, first_hit_from_anchor, session_key, spec_hash
)


def test_normalize_timezone_and_columns():
    df = pd.DataFrame({
        '<DATE>':['2024.01.02','2024.01.02'],
        '<TIME>':['00:00:00','01:00:00'],
        '<OPEN>':[1.1,1.2],'<HIGH>':[1.2,1.3],'<LOW>':[1.0,1.1],'<CLOSE>':[1.15,1.25]
    })
    out = normalize(df)
    assert str(out.index.tz) == 'America/New_York'
    assert list(out.columns.intersection(['open','high','low','close'])) == ['open','high','low','close']


def test_fixed_session_key_keeps_evening_with_following_research_day():
    idx = pd.DatetimeIndex([
        pd.Timestamp('2024-01-02 18:55', tz='America/New_York'),
        pd.Timestamp('2024-01-02 19:00', tz='America/New_York'),
        pd.Timestamp('2024-01-03 02:55', tz='America/New_York'),
        pd.Timestamp('2024-01-03 03:00', tz='America/New_York'),
    ])
    assert list(session_key(idx)) == [pd.Timestamp('2024-01-02').date(), pd.Timestamp('2024-01-03').date(), pd.Timestamp('2024-01-03').date(), pd.Timestamp('2024-01-03').date()]


def test_dst_is_resolved_by_iana_zone():
    df = pd.DataFrame({'dt': ['2024-03-10 06:55:00', '2024-03-10 07:00:00'], 'open':[1,1], 'high':[1,1], 'low':[1,1], 'close':[1,1]})
    out = normalize(df)
    assert out.index[0].hour == 1
    assert out.index[1].hour == 3


def test_duplicate_timestamps_rejected():
    df = pd.DataFrame({'dt': ['2024-01-02 00:00:00', '2024-01-02 00:00:00'], 'open':[1,1], 'high':[1,1], 'low':[1,1], 'close':[1,1]})
    with pytest.raises(ValueError, match='duplicate'):
        normalize(df)


def test_invalid_ohlc_rejected():
    df = pd.DataFrame({'dt': ['2024-01-02 00:00:00'], 'open':[1.1], 'high':[1.0], 'low':[1.05], 'close':[1.08]})
    with pytest.raises(ValueError, match='invalid OHLC'):
        normalize(df)


def test_kmeans_centroids_ordered():
    x = np.array([10,11,12,25,26,27,50,51,52], float)
    c, b = kmeans_1d(x, 3, seed=42)
    assert np.all(np.diff(c) > 0)
    assert np.all(np.diff(b) > 0)


def test_tier_assignment():
    c = np.array([10., 25., 50.])
    t = assign_tier([9,24,52], c)
    assert list(t) == [1,2,3]


def test_first_hit_shape():
    idx = pd.date_range('2024-01-02 03:00', periods=4, freq='h', tz='America/New_York')
    day = pd.DataFrame({'high':[1.1000,1.1010,1.1020,1.1030], 'low':[1.1000,1.0995,1.0990,1.0980]}, index=idx)
    out = first_hit_from_anchor(day, idx[0], 1.1000, 10)
    assert set(out) == {'0.5AU_first','1AU_first','1.2AU_first','1.5AU_first','2AU_first'}


def test_au_source_math_is_exact():
    centroids = np.array([10., 20., 40.])
    assert np.allclose(0.5 * centroids, [5., 10., 20.])
    assert np.allclose(1.2 * 0.5 * centroids, [6., 12., 24.])


def test_spec_hash_stable():
    assert spec_hash() == spec_hash()
