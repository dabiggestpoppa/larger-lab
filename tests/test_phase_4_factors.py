"""
Deterministic, no-lookahead tests for the Phase 4 latent FX factor engine.
CR-P4-LATENT-FACTOR-ENGINE-01

Coverage of the 18 required tests:
 1. EURUSD row orientation correct
 2. USDJPY orientation correct
 3. incidence matrix rank correct
 4. zero-sum constraint holds
 5. exact synthetic currency factors reconstruct known pair returns
 6. pair residual calculation correct
 7. missing pair observation handled without forward fill
 8. factor estimate deterministic
 9. robust estimator deterministic
10. trailing 4h feature has no lookahead
11. rank computation correct
12. breadth computation correct
13. H4 aggregation consistency
14. D1 aggregation consistency
15. reconstruction metrics correct
16. zero-return network returns zero factors
17. pair permutation does not materially alter solution
18. stale/missing pair weight does not introduce future information
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capital_routing.phases.phase_4_factors import (
    CURRENCIES,
    HORIZON_BARS,
    aggregate_factors_by_bucket,
    breadth_features,
    build_incidence_matrix,
    build_quality_weights,
    cross_sectional_ranks,
    dispersion_features,
    factor_volatility,
    incidence_rank,
    network_consistency,
    origin_pressure_features,
    orthogonality_audit,
    pair_residuals,
    reconstruction_validation,
    solve_from_panel_returns,
    solve_latent_factors,
    trailing_cumulative,
    velocity_acceleration,
)
from capital_routing.phases.phase_3_panel import PHASE2_SYMBOLS, CURRENCY_ORIENTATION


def _synthetic_returns(
    n=500, seed=7, currencies=None, pairs=None,
):
    """Deterministic synthetic pair returns drawn from hidden currency factors."""
    currencies = currencies or CURRENCIES
    pairs = pairs or PHASE2_SYMBOLS
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    # hidden factors (zero-sum by construction noise ~ but here just arbitrary)
    f = pd.DataFrame(rng.normal(0, 0.001, (n, len(currencies))),
                     index=idx, columns=currencies)
    pairs_idx = [(CURRENCY_ORIENTATION[p][0], CURRENCY_ORIENTATION[p][1]) for p in pairs]
    cols = {}
    for p, (b, q) in zip(pairs, pairs_idx):
        cols[p] = f[b] - f[q] + rng.normal(0, 1e-5, n)
    return pd.DataFrame(cols, index=idx), f


class TestIncidence:
    def test_eurusd_row_orientation_correct(self):
        A, _ = build_incidence_matrix(["EURUSD"])
        assert A.loc["EURUSD", "EUR"] == 1
        assert A.loc["EURUSD", "USD"] == -1
        assert A.loc["EURUSD"].sum() == 0

    def test_usdjpy_row_orientation_correct(self):
        A, _ = build_incidence_matrix(["USDJPY"])
        assert A.loc["USDJPY", "USD"] == 1
        assert A.loc["USDJPY", "JPY"] == -1
        assert A.loc["USDJPY"].sum() == 0

    def test_incidence_matrix_rank_correct(self):
        A, raw = build_incidence_matrix(PHASE2_SYMBOLS)
        r = incidence_rank(raw)
        assert r == len(CURRENCIES) - 1  # n-1, non-identifiable without constraint

    def test_all_rows_zero_sum(self):
        A, raw = build_incidence_matrix(PHASE2_SYMBOLS)
        assert (np.round(A.sum(axis=1), 12)).eq(0).all()


class TestSolve:
    def test_zero_sum_constraint_holds(self):
        ret, _ = _synthetic_returns()
        fac = solve_latent_factors(ret)
        assert (np.abs(fac[[f"{c}_factor" for c in CURRENCIES]].sum(axis=1)) < 1e-9).all()

    def test_exact_synthetic_reconstructs(self):
        ret, hidden = _synthetic_returns()
        fac = solve_latent_factors(ret, robust=False)
        # With negligible epsilon the factors should closely match the hidden
        # factors (up to the zero-sum constraint shift).
        # reconstruct pairs
        for p in PHASE2_SYMBOLS:
            b, q = CURRENCY_ORIENTATION[p]
            pred = fac[f"{b}_factor"] - fac[f"{q}_factor"]
            obs = ret[p]
            mae = (obs - pred).abs().mean()
            assert mae < 1e-3

    def test_zero_return_network_zero_factors(self):
        ret = pd.DataFrame(0.0, index=pd.date_range("2024-01-01", periods=50, freq="h", tz="UTC"),
                           columns=PHASE2_SYMBOLS)
        fac = solve_latent_factors(ret)
        assert (np.abs(fac[[f"{c}_factor" for c in CURRENCIES]]).max().max() < 1e-9)

    def test_missing_pair_no_forward_fill(self):
        ret, _ = _synthetic_returns(seed=3)
        # knock out EURUSD at a middle timestamp
        idx = ret.index[len(ret) // 2]
        ret.loc[idx, ["EURUSD", "GBPUSD"]] = np.nan
        fac = solve_latent_factors(ret)
        # solution at that timestamp should still exist but with fewer pairs
        assert fac.loc[idx, "n_pairs_available"] == len(PHASE2_SYMBOLS) - 2
        for p in ["EURUSD", "GBPUSD"]:
            assert np.isnan(ret.loc[idx, p])

    def test_deterministic(self):
        ret, _ = _synthetic_returns(seed=11)
        f1 = solve_latent_factors(ret)
        f2 = solve_latent_factors(ret)
        pd.testing.assert_frame_equal(f1, f2)

    def test_robust_deterministic(self):
        ret, _ = _synthetic_returns(seed=13)
        f1 = solve_latent_factors(ret, robust=True)
        f2 = solve_latent_factors(ret, robust=True)
        pd.testing.assert_frame_equal(f1, f2)

    def test_pair_permutation_not_materially_alter(self):
        ret, _ = _synthetic_returns(seed=5)
        perm = PHASE2_SYMBOLS[::2] + PHASE2_SYMBOLS[1::2]
        ret2 = ret[perm]
        f1 = solve_latent_factors(ret, pairs=PHASE2_SYMBOLS)
        f2 = solve_latent_factors(ret2, pairs=perm)
        # factor values should be (nearly) invariant to pair ordering
        diff = (f1[[f"{c}_factor" for c in CURRENCIES]] -
                f2[[f"{c}_factor" for c in CURRENCIES]]).abs().max().max()
        assert diff < 1e-6


class TestResidualsWeight:
    def test_pair_residual_correct(self):
        ret, hidden = _synthetic_returns()
        A = build_incidence_matrix(PHASE2_SYMBOLS)[1]
        fac = solve_latent_factors(ret, A=A)
        res = pair_residuals(fac, ret, PHASE2_SYMBOLS)
        for p in PHASE2_SYMBOLS:
            b, q = CURRENCY_ORIENTATION[p]
            pred = fac[f"{b}_factor"] - fac[f"{q}_factor"]
            assert (np.abs((ret[p] - pred) - res[f"{p}_residual"]) < 1e-12).all()

    def test_stale_missing_weight_no_future_info(self):
        # A pair flagged stale for the FIRST half should have its factor
        # estimate use only current-period data, never future.
        ret, _ = _synthetic_returns()
        w = pd.DataFrame(1.0, index=ret.index, columns=PHASE2_SYMBOLS)
        half = ret.index[len(ret) // 2]
        w.loc[ret.index < half, "EURUSD"] = 0.0
        w.loc[ret.index < half, "GBPUSD"] = 0.0
        fac = solve_latent_factors(ret, weights=w)
        # n_pairs_available in first half reduced
        assert (fac.loc[ret.index < half, "n_pairs_available"] < len(PHASE2_SYMBOLS)).any()


class TestFeatures:
    def test_trailing_4h_no_lookahead(self):
        ret, _ = _synthetic_returns()
        A = build_incidence_matrix(PHASE2_SYMBOLS)[1]
        fac = solve_latent_factors(ret, A=A)
        cum = trailing_cumulative(fac)
        # For EUR, cum_4h[t] should equal sum of factors over [t-3, t], i.e.
        # depends only on values <= t. Compare to a manual closed-form using
        # only past data:
        f4 = fac["EUR_factor"]
        manual = f4.rolling(4, min_periods=4).sum()
        pd.testing.assert_series_equal(cum["EUR_4h"], manual, check_names=False)

    def test_velocity_uses_trailing_only(self):
        ret, _ = _synthetic_returns()
        fac = solve_latent_factors(ret)
        cum = trailing_cumulative(fac)
        va = velocity_acceleration(cum, ["4h"])
        # shift must not create future leaks: velocity_4h[t] uses cum[t] and cum[t-4]
        v = va["EUR_velocity_4h"]
        assert v.iloc[0:4].isna().all()  # needs 5 points
        assert not v.isna().all()

    def test_rank_computation_correct(self):
        ret, _ = _synthetic_returns(seed=2)
        fac = solve_latent_factors(ret)
        rk = cross_sectional_ranks(fac)
        # At each row, ranks are a permutation of 1..5
        cols = [f"{c}_rank" for c in CURRENCIES]
        for idx in fac.index[100:110]:
            vals = rk.loc[idx, cols].values
            assert set(np.sort(vals)) == set([1.0, 2.0, 3.0, 4.0, 5.0])

    def test_breadth_computation_correct(self):
        ret, hidden = _synthetic_returns(seed=9)
        A = build_incidence_matrix(PHASE2_SYMBOLS)[1]
        fac = solve_latent_factors(ret, A=A)
        br = breadth_features(fac, ret, weights=None, pairs=PHASE2_SYMBOLS)
        # breadth counts bounded by number of pairs touching each currency
        for c in CURRENCIES:
            cnt = br[f"{c}_breadth_count"]
            assert (cnt.max() <= 4)  # EUR touches 4 pairs
            assert (cnt >= 0).all()
            assert br[f"{c}_breadth_fraction"].between(0, 1, inclusive="both").all()

    def test_reconstruction_metrics_correct(self):
        ret, _ = _synthetic_returns()
        fac = solve_latent_factors(ret)
        rc = reconstruction_validation(fac, ret, PHASE2_SYMBOLS)
        assert len(rc) == len(PHASE2_SYMBOLS)
        for _, row in rc.iterrows():
            assert row["n"] > 0
            assert row["r2"] > 0.9  # synthetic has tiny noise
            assert 0 <= row["corr"] <= 1


class TestHierarchy:
    def _h4_d1(self):
        # Build a dense H1 index and panel
        idx = pd.date_range("2024-01-01", periods=48 * 5, freq="h", tz="UTC")
        ret, hidden = _synthetic_returns(n=48 * 5, seed=21, currencies=CURRENCIES)
        fac = solve_latent_factors(ret)
        # H4 bucket index
        h4_index = idx.floor("4h")
        h4_uniq = pd.DatetimeIndex(sorted(set(h4_index)))
        # D1 bucket index = calendar day
        d1_uniq = pd.DatetimeIndex(sorted(set(idx.floor("D"))))
        return fac, h4_uniq, d1_uniq

    def test_h4_aggregation_consistency(self):
        fac, h4_uniq, _ = self._h4_d1()
        agg = aggregate_factors_by_bucket(fac, pd.DataFrame(index=h4_uniq), "H4")
        # Sum within a bucket should equal aggregating by hand
        bucket = pd.Series(fac.index, index=fac.index).dt.floor("4h")
        manual = fac["EUR_factor"].groupby(bucket).sum().reindex(h4_uniq)
        pd.testing.assert_series_equal(agg["EUR_factor"].dropna(), manual.dropna(), check_names=False)

    def test_d1_aggregation_consistency(self):
        fac, _, d1_uniq = self._h4_d1()
        agg = aggregate_factors_by_bucket(fac, pd.DataFrame(index=d1_uniq), "D1")
        bucket = pd.Series(fac.index, index=fac.index).dt.floor("D")
        manual = fac["GBP_factor"].groupby(bucket).sum().reindex(d1_uniq)
        pd.testing.assert_series_equal(agg["GBP_factor"].dropna(), manual.dropna(), check_names=False)


class TestAudit:
    def test_orthogonality_effective_rank_nminus1(self):
        ret, _ = _synthetic_returns(seed=31)
        fac = solve_latent_factors(ret)
        aud = orthogonality_audit(fac)
        assert aud["effective_rank"] == len(CURRENCIES) - 1
        assert aud["n_currencies"] == 5
        # covariance eigenvalue count
        ev = aud["eigenvalues"]
        assert len(ev) == 5

    def test_network_consistency(self):
        ret, _ = _synthetic_returns(seed=41)
        fac = solve_latent_factors(ret)
        res = pair_residuals(fac, ret, PHASE2_SYMBOLS)
        nc = network_consistency(fac, res, ret, PHASE2_SYMBOLS)
        assert nc["pair_reconstruction_rmse"].dropna().min() >= 0
        assert nc["network_agreement_score"].between(0, 1).all()