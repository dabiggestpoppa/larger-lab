"""PFT-B3 causality conformance (build prompt sections 12, 36, 43).

For every rolling kernel the two causal invariants must hold:

TRUNCATION INVARIANCE
    Computing the kernel on data[0:T] and on the full series must yield
    bit-identical outputs for every slot t < T.

FUTURE PERTURBATION INVARIANCE
    Modifying any data at slots >= T must not change outputs at slots
    < T.

These prove no kernel reads future information. A synthetic-panel
pipeline test additionally proves the wiring (returns -> kernels ->
FSM -> cap -> fade) is causal end to end, and that rerunning the
pipeline is deterministic. No protected data is touched and no PnL is
computed.
"""

import numpy as np
import pandas as pd
import pytest

from strategy_foundry.pft.engine import k1 as k1_mod
from strategy_foundry.pft.engine import k2 as k2_mod
from strategy_foundry.pft.engine import k3 as k3_mod
from strategy_foundry.pft.engine import k4 as k4_mod
from strategy_foundry.pft.engine import parkinson
from strategy_foundry.pft.engine import pipeline as pipe_mod
from strategy_foundry.pft.engine import portfolio as port_mod
from strategy_foundry.pft.engine import returns as ret_mod


# ---------------------------------------------------------------------------
# Invariance drivers
# ---------------------------------------------------------------------------


def _compare_slices(full_out, trunc_out, cutoff, label):
    """Compare outputs through `cutoff`, recursing into dicts/tuples."""
    if isinstance(full_out, dict):
        for k in full_out:
            _compare_slices(full_out[k], trunc_out[k], cutoff, f"{label}.{k}")
    elif isinstance(full_out, (tuple, list)):
        for i, (f, t) in enumerate(zip(full_out, trunc_out)):
            _compare_slices(f, t, cutoff, f"{label}[{i}]")
    else:
        f = np.asarray(full_out)
        t = np.asarray(trunc_out)
        if f.ndim == 0:
            assert f == t, label
        else:
            np.testing.assert_array_equal(f[:cutoff], t[:cutoff], err_msg=label)


def truncation_invariance(fn, *arrays, cutoff=400):
    """fn(array, ...) per-slot outputs; truncated vs full must match through cutoff."""
    full = fn(*arrays)
    truncated = fn(*[a[:cutoff] for a in arrays])
    _compare_slices(full, truncated, cutoff, "truncation invariance violated")


def perturbation_invariance(fn, *arrays, cutoff=400):
    """Mutate all inputs after cutoff; outputs before cutoff must not change."""
    base = fn(*arrays)
    pert = [a.copy() for a in arrays]
    rng = np.random.RandomState(7)
    for p in pert:
        p[cutoff:] = rng.normal(size=p[cutoff:].shape)
    alt = fn(*pert)
    _compare_slices(base, alt, cutoff, "future perturbation invariance violated")


def _rand_ohlc(n, seed=3, scale=1.0):
    rng = np.random.RandomState(seed)
    close = np.cumprod(1.0 + rng.normal(0, 0.002 * scale, n)) * 100.0
    spread = np.abs(rng.normal(0, 0.001 * scale, n))
    high = close + spread
    low = close - spread
    return high, low, close


def _ones_valid(n):
    return np.ones(n, dtype=bool)


# ---------------------------------------------------------------------------
# Returns / Parkinson / K2
# ---------------------------------------------------------------------------


class TestReturnsCausal:
    def test_truncation(self):
        prices = _rand_ohlc(600)[2]
        truncation_invariance(ret_mod.log_return, prices)

    def test_perturbation(self):
        prices = _rand_ohlc(600)[2]
        perturbation_invariance(ret_mod.log_return, prices)

    def test_stale_mask_invariance(self):
        n = 600
        prices = _rand_ohlc(n)[2]
        stale = np.zeros(n, dtype=bool)
        stale[300:320] = True
        truncation_invariance(ret_mod.log_return, prices, stale)


class TestParkinsonCausal:
    def test_truncation(self):
        high, low, _ = _rand_ohlc(600)
        truncation_invariance(parkinson.parkinson_14h, high, low)

    def test_perturbation(self):
        high, low, _ = _rand_ohlc(600)
        perturbation_invariance(parkinson.parkinson_14h, high, low)


class TestK2Causal:
    def test_gamma_raw(self):
        high, low, close = _rand_ohlc(600)
        truncation_invariance(k2_mod.gamma_raw, high, low, close)
        perturbation_invariance(k2_mod.gamma_raw, high, low, close)

    def test_gamma_sma3(self):
        high, low, close = _rand_ohlc(600)
        g, gv, _ = k2_mod.gamma_raw(high, low, close)
        truncation_invariance(k2_mod.gamma_sma3, g, gv)
        perturbation_invariance(k2_mod.gamma_sma3, g, gv)

    def test_acceleration(self):
        high, low, _ = _rand_ohlc(600)
        s, sv, _ = parkinson.parkinson_14h(high, low)
        truncation_invariance(k2_mod.acceleration, s, sv)
        perturbation_invariance(k2_mod.acceleration, s, sv)

    def test_k2_weight(self):
        n = 600
        gb = np.random.RandomState(1).normal(0, 0.15, n)
        ac = np.random.RandomState(2).normal(0, 0.05, n)
        gbv = _ones_valid(n)
        acv = _ones_valid(n)
        truncation_invariance(k2_mod.k2_weight, gb, gbv, ac, acv)
        perturbation_invariance(k2_mod.k2_weight, gb, gbv, ac, acv)


# ---------------------------------------------------------------------------
# K1 (DMD) — the heaviest kernel; window 720
# ---------------------------------------------------------------------------


class TestK1Causal:
    def _obs(self, n=2000):
        rng = np.random.RandomState(11)
        psi = rng.normal(0, 1, (n, 6))
        r_i = rng.normal(0, 1, n)
        stale = np.zeros(n, dtype=bool)
        return psi, r_i, stale

    def test_truncation(self):
        psi, r_i, stale = self._obs()
        cutoff = 1500
        full = k1_mod.k1_kernel(psi, r_i, stale)
        trunc = k1_mod.k1_kernel(psi[:cutoff], r_i[:cutoff], stale[:cutoff])
        for key in ("w3", "K1_VALID", "delta_phi"):
            np.testing.assert_array_equal(full[key][:cutoff], trunc[key])
        np.testing.assert_array_equal(full["reason"][:cutoff], trunc["reason"])

    def test_perturbation(self):
        psi, r_i, stale = self._obs()
        cutoff = 1500
        base = k1_mod.k1_kernel(psi, r_i, stale)
        psi_pert = psi.copy()
        psi_pert[cutoff:] = np.random.RandomState(9).normal(0, 5, psi_pert[cutoff:].shape)
        r_i_pert = r_i.copy()
        r_i_pert[cutoff:] = 99.0
        alt = k1_mod.k1_kernel(psi_pert, r_i_pert, stale)
        for key in ("w3", "K1_VALID", "delta_phi"):
            np.testing.assert_array_equal(base[key][:cutoff], alt[key][:cutoff])
        np.testing.assert_array_equal(base["reason"][:cutoff], alt["reason"][:cutoff])


# ---------------------------------------------------------------------------
# K3 (z-score, distances, OLS)
# ---------------------------------------------------------------------------


class TestK3Causal:
    def _series(self, n=800):
        rng = np.random.RandomState(5)
        r = {a: rng.normal(0, 0.01, n) for a in "WECI"}
        valid = {a: _ones_valid(n) for a in "WECI"}
        return r, valid

    def test_zscore(self):
        r, valid = self._series()
        for a in "WECI":
            truncation_invariance(k3_mod.zscore_720, r[a], valid[a])
            perturbation_invariance(k3_mod.zscore_720, r[a], valid[a])

    def test_vr_distances(self):
        r, valid = self._series()
        z = {a: k3_mod.zscore_720(r[a], valid[a])[0] for a in "WECI"}
        full_d, full_v = k3_mod.vr_distances(z)
        z_t = {a: k3_mod.zscore_720(r[a][:400], valid[a][:400])[0] for a in "WECI"}
        trunc_d, trunc_v = k3_mod.vr_distances(z_t)
        np.testing.assert_array_equal(full_d[:400], trunc_d)
        np.testing.assert_array_equal(full_v[:400], trunc_v)
        # perturb future z-scores (feed z directly with future altered)
        z_p = {a: z[a].copy() for a in "WECI"}
        for a in "WECI":
            z_p[a][500:] = 999.0
        pert_d, pert_v = k3_mod.vr_distances(z_p)
        np.testing.assert_array_equal(full_d[:400], pert_d[:400])
        np.testing.assert_array_equal(full_v[:400], pert_v[:400])

    def test_ols(self):
        rng = np.random.RandomState(6)
        n = 800
        dwe = rng.uniform(0.5, 2.0, n)
        dwc = rng.uniform(0.3, 1.5, n)
        dec = 1.0 + 2.0 * dwe - 0.5 * dwc + rng.normal(0, 0.01, n)
        valid = _ones_valid(n)
        truncation_invariance(k3_mod.k3_ols, dec, dwe, dwc, valid)
        perturbation_invariance(k3_mod.k3_ols, dec, dwe, dwc, valid)

    def test_alpha(self):
        rng = np.random.RandomState(8)
        n = 800
        dec = rng.normal(1.0, 0.1, n)
        dhat = rng.normal(1.0, 0.1, n)
        r_e = rng.normal(0, 0.01, n)
        r_c = rng.normal(0, 0.01, n)
        mult = rng.choice([0.0, 0.6, 1.8], n)
        valid = _ones_valid(n)
        truncation_invariance(k3_mod.k3_alpha, dec, dhat, r_e, r_c, mult, valid)
        perturbation_invariance(k3_mod.k3_alpha, dec, dhat, r_e, r_c, mult, valid)


# ---------------------------------------------------------------------------
# K4 (RV6, commutator, w_total)
# ---------------------------------------------------------------------------


class TestK4Causal:
    def test_rv6(self):
        r_ec = _rand_ohlc(600)[2]
        r_ec = np.diff(np.log(r_ec), prepend=0.0)
        truncation_invariance(k4_mod.rv6, r_ec, _ones_valid(600))
        perturbation_invariance(k4_mod.rv6, r_ec, _ones_valid(600))

    def test_commutator(self):
        n = 600
        a = np.random.RandomState(1).normal(0, 0.01, n)
        b = np.random.RandomState(2).normal(0, 0.01, n)
        av = _ones_valid(n)
        bv = _ones_valid(n)
        truncation_invariance(k4_mod.commutator, a, b, av, bv)
        perturbation_invariance(k4_mod.commutator, a, b, av, bv)

    def test_w_total(self):
        n = 600
        alpha = np.random.RandomState(3).normal(0, 0.001, n)
        truncation_invariance(k4_mod.w_total, alpha, _ones_valid(n))
        perturbation_invariance(k4_mod.w_total, alpha, _ones_valid(n))


# ---------------------------------------------------------------------------
# Portfolio layer (FSM / cap / fade / DD / leg stop)
# ---------------------------------------------------------------------------


class TestPortfolioCausal:
    def test_cluster_fsm(self):
        n = 600
        rng = np.random.RandomState(4)
        wt = rng.normal(0, 0.1, n)
        w1 = rng.normal(0, 0.1, n)
        w2 = rng.normal(0, 0.1, n)
        w3 = rng.normal(0, 0.1, n)
        truncation_invariance(port_mod.cluster_fsm, wt, w1, w2, w3)
        perturbation_invariance(port_mod.cluster_fsm, wt, w1, w2, w3)

    def test_gross_cap(self):
        rng = np.random.RandomState(5)
        w = rng.normal(0, 0.5, (600, 3))
        truncation_invariance(port_mod.gross_cap, w)
        perturbation_invariance(port_mod.gross_cap, w)

    def test_fade(self):
        rng = np.random.RandomState(6)
        targets = rng.normal(0, 0.4, (600, 3))
        full = port_mod.fade_sequence(targets)
        trunc = port_mod.fade_sequence(targets[:400])
        for key in ("w_fade", "phase"):
            np.testing.assert_array_equal(full[key][:400], trunc[key])
        np.testing.assert_array_equal(full["reason"][:400], trunc["reason"])
        # perturb future targets
        targets_p = targets.copy()
        targets_p[400:] = rng.normal(0, 2.0, (200, 3))
        alt = port_mod.fade_sequence(targets_p)
        np.testing.assert_array_equal(full["w_fade"][:400], alt["w_fade"][:400])

    def test_drawdown(self):
        nav = np.cumprod(1.0 + np.random.RandomState(7).normal(0, 0.01, 600))
        w = np.ones((600, 1)) * 0.3
        full = port_mod.drawdown_overlay(w, nav)
        trunc = port_mod.drawdown_overlay(w[:400], nav[:400])
        for key in ("w_dd", "dd", "terminal"):
            np.testing.assert_array_equal(full[key][:400], trunc[key])

    def test_leg_stop(self):
        n = 600
        rng = np.random.RandomState(8)
        equity = 100.0 + np.cumsum(rng.normal(0, 0.05, (n, 1)), axis=0)
        nav = np.full(n, 100.0)
        full = port_mod.leg_stop(equity, nav)
        trunc = port_mod.leg_stop(equity[:400], nav[:400])
        for key in ("target", "trigger_hits"):
            np.testing.assert_array_equal(full[key][:400], trunc[key])
        np.testing.assert_array_equal(full["banned_until"], trunc["banned_until"])


# ---------------------------------------------------------------------------
# Pipeline wiring: synthetic panel, determinism, end-to-end causality
# ---------------------------------------------------------------------------


def _synthetic_panel(n=1300, seed=0):
    """Small synthetic panel with the exact column contract of build_panel.

    All slots are DEVELOPMENT; slots are hourly UTC; every asset observed
    (no stale slots) so the pipeline's full path is exercised.
    """
    rng = np.random.RandomState(seed)
    idx = pd.date_range("2023-06-01", periods=n, freq="1h", tz="UTC")
    panel = pd.DataFrame(index=idx)
    for asset in ("W", "E", "C", "I", "EC"):
        close = np.cumprod(1.0 + rng.normal(0, 0.001, n)) * 100.0
        spread = np.abs(rng.normal(0, 0.0005, n))
        high = close + spread
        low = close - spread
        panel[f"{asset}.close_carried"] = close
        panel[f"{asset}.high_carried"] = high
        panel[f"{asset}.low_carried"] = low
        panel[f"{asset}.observed"] = True
        panel[f"{asset}.stale"] = False
        panel[f"{asset}.stale_age_hours"] = 0.0
    panel["canonical_ny"] = idx.tz_convert("America/New_York")
    panel["partition"] = "DEVELOPMENT"
    return panel


class TestPipelineCausal:
    def test_deterministic_rerun(self):
        panel = _synthetic_panel()
        out1 = pipe_mod.run_pre_economic(panel)
        out2 = pipe_mod.run_pre_economic(panel)
        l1 = out1["ledger"].select_dtypes(include=[np.number])
        l2 = out2["ledger"].select_dtypes(include=[np.number])
        pd.testing.assert_frame_equal(l1, l2)
        pd.testing.assert_frame_equal(out1["invalid_state_ledger"],
                                      out2["invalid_state_ledger"])

    def test_future_perturbation_invariance(self):
        panel = _synthetic_panel()
        cutoff = 1000
        base = pipe_mod.run_pre_economic(panel)["ledger"]
        pert = panel.copy()
        for asset in ("W", "E", "C", "I", "EC"):
            rng = np.random.RandomState(99)
            pert.loc[pert.index[cutoff:], f"{asset}.close_carried"] = \
                pert.loc[pert.index[cutoff:], f"{asset}.close_carried"] * (
                    1.0 + rng.normal(0, 0.5, len(pert.index) - cutoff))
        alt = pipe_mod.run_pre_economic(pert)["ledger"]
        cols = [c for c in base.columns if c not in ("fade_reason", "K1_reason",
                                                     "K3_OLS_reason", "fsm_state",
                                                     "topology_raw", "topology_frozen")]
        for c in cols:
            b = pd.to_numeric(base[c], errors="coerce").to_numpy()[:cutoff]
            a = pd.to_numeric(alt[c], errors="coerce").to_numpy()[:cutoff]
            np.testing.assert_array_equal(b, a, err_msg=f"pipeline leaked future in {c}")

    def test_truncation_invariance(self):
        panel = _synthetic_panel()
        cutoff = 1000
        full = pipe_mod.run_pre_economic(panel)["ledger"]
        trunc = pipe_mod.run_pre_economic(panel.iloc[:cutoff])["ledger"]
        cols = [c for c in full.columns if c not in ("fade_reason", "K1_reason",
                                                     "K3_OLS_reason", "fsm_state",
                                                     "topology_raw", "topology_frozen")]
        for c in cols:
            b = pd.to_numeric(full[c], errors="coerce").to_numpy()[:cutoff]
            a = pd.to_numeric(trunc[c], errors="coerce").to_numpy()
            np.testing.assert_array_equal(b, a, err_msg=f"pipeline truncation violated {c}")
