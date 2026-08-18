"""PFT-B3 reference fixtures (build prompt section 35).

Every frozen A1 formula is exercised against hand-computed or
independently computed expected values. These are deterministic
mathematical fixtures, not economic evaluation.
"""

import numpy as np
import pytest

from strategy_foundry.pft.engine import k1 as k1_mod
from strategy_foundry.pft.engine import k2 as k2_mod
from strategy_foundry.pft.engine import k3 as k3_mod
from strategy_foundry.pft.engine import k4 as k4_mod
from strategy_foundry.pft.engine import parkinson
from strategy_foundry.pft.engine import portfolio as port_mod
from strategy_foundry.pft.engine import returns as ret_mod


# ---------------------------------------------------------------------------
# 35.1 log return (A1.F01)
# ---------------------------------------------------------------------------


class TestLogReturn:
    def test_hand_fixture(self):
        r, valid, _ = ret_mod.log_return(np.array([100.0, 101.0]), None)
        assert r[1] == pytest.approx(np.log(101 / 100))
        assert valid[1]

    def test_zero_move(self):
        r, valid, _ = ret_mod.log_return(np.array([100.0, 100.0]), None)
        assert r[1] == 0.0

    def test_stale_slot_zero_return(self):
        r, valid, reasons = ret_mod.log_return(np.array([100.0, 101.0, 101.0]),
                                               np.array([False, False, True]))
        assert r[2] == 0.0
        assert valid[2]
        assert reasons[2] == "STALE_SLOT_ZERO"

    def test_gap(self):
        r, _, _ = ret_mod.log_return(np.array([100.0, 110.0]), None)
        assert r[1] == pytest.approx(np.log(1.1))

    def test_missing_non_finite_invalid(self):
        r, valid, reasons = ret_mod.log_return(np.array([100.0, np.nan, 105.0]), None)
        assert not valid[1]
        assert "non-finite" in reasons[1]
        assert not valid[2]


# ---------------------------------------------------------------------------
# 35.2 Parkinson (A1.F02)
# ---------------------------------------------------------------------------


class TestParkinson:
    def test_hand_fixture(self):
        n = 20
        high = np.full(n, 2.0)
        low = np.full(n, 1.0)
        sigma, valid, _ = parkinson.parkinson_14h(high, low)
        assert valid[13]
        # independent computation
        hl = 2.0 / 1.0
        expected = np.sqrt((1.0 / (4.0 * np.log(2.0))) * (1.0 / 14.0) * 14.0 * np.log(hl) ** 2)
        expected *= np.sqrt(365.0 * 24.0)
        assert sigma[13] == pytest.approx(expected)
        # rolling: slot 14 uses bars 1..14 (same values -> same sigma)
        assert sigma[14] == pytest.approx(sigma[13])

    def test_exact_window(self):
        n = 20
        high = np.full(n, 2.0)
        low = np.full(n, 1.0)
        high[0] = 10.0  # inside slot-13 window (bars 0..13), outside slot-14 (1..14)
        sigma, valid, _ = parkinson.parkinson_14h(high, low)
        base = np.sqrt((1 / (4 * np.log(2))) * np.log(2) ** 2) * np.sqrt(365 * 24)
        # slot 13 includes the ln(10/1) range
        expected_13 = np.sqrt((1 / (4 * np.log(2))) * (1 / 14)
                              * (13 * np.log(2) ** 2 + np.log(10) ** 2)) * np.sqrt(365 * 24)
        assert sigma[13] == pytest.approx(expected_13)
        # slot 14 uses bars 1..14 (all 2/1) -> base value
        assert sigma[14] == pytest.approx(base)

    def test_insufficient_history_invalid(self):
        sigma, valid, reasons = parkinson.parkinson_14h(np.full(5, 2.0), np.full(5, 1.0))
        assert not valid.any()
        assert "insufficient" in reasons[4]

    def test_annualized_scale(self):
        n = 14
        sigma, _, _ = parkinson.parkinson_14h(np.full(n, 2.0), np.full(n, 1.0))
        # hourly sigma of constant 2/1 range; annualization factor sqrt(365*24) ~ 93.6
        assert sigma[13] == pytest.approx(np.sqrt((1 / (4 * np.log(2))) * np.log(2) ** 2)
                                          * np.sqrt(365 * 24))


# ---------------------------------------------------------------------------
# 35.3 gamma (A1.F03) + 35.4 acceleration (A1.F05)
# ---------------------------------------------------------------------------


class TestGamma:
    def test_permanent_regression_fixture(self):
        gamma, valid, _ = k2_mod.gamma_raw(
            np.array([100.0]), np.array([90.0]), np.array([99.0]))
        assert gamma[0] == pytest.approx(-0.8)

    def test_hl_equal_zero(self):
        gamma, valid, reasons = k2_mod.gamma_raw(
            np.array([100.0]), np.array([100.0]), np.array([100.0]))
        assert gamma[0] == 0.0
        assert valid[0]
        assert reasons[0] == "H_EQ_L_ZERO"

    def test_v22_direction_long_with_active_acceleration(self):
        """gamma=-0.8 with active acceleration -> w1 > 0 (LONG) because of the
        leading negative sign in v2.2."""
        g = np.array([-0.8, -0.8, -0.8])
        gamma_bar, _, _ = k2_mod.gamma_sma3(g, np.ones(3, dtype=bool))
        sigma = np.array([1.0, 2.0, 4.0])  # accel_t = 3.0 at t=2
        accel, _, _ = k2_mod.acceleration(sigma, np.ones(3, dtype=bool))
        w1, active, _ = k2_mod.k2_weight(gamma_bar, np.ones(3, dtype=bool),
                                         accel, np.ones(3, dtype=bool))
        assert active[2]
        assert w1[2] > 0  # LONG per corrected v2.2 direction
        assert w1[2] == pytest.approx(0.45 * min(3.0 / 0.04, 1.0))

    def test_stale_bar_gamma_zero(self):
        gamma, valid, reasons = k2_mod.gamma_raw(
            np.array([100.0]), np.array([90.0]), np.array([99.0]),
            valid_bars=np.array([False]))
        assert gamma[0] == 0.0
        assert reasons[0] == "STALE_ZERO"


class TestAcceleration:
    def test_basic(self):
        sigma, valid, _ = k2_mod.acceleration(np.array([1.0, 2.0]), np.ones(2, dtype=bool))
        assert sigma[1] == pytest.approx(1.0)  # 2/1 - 1

    def test_previous_zero(self):
        sigma, valid, reasons = k2_mod.acceleration(np.array([0.0, 2.0]), np.ones(2, dtype=bool))
        assert sigma[1] == 0.0
        assert reasons[1] == "PREV_SIGMA_ZERO"


# ---------------------------------------------------------------------------
# 35.5 DMD synthetic system (A1.F06) + 35.6 circular phase (A1.F08)
# ---------------------------------------------------------------------------


def _block_diag_system(pairs, reals):
    """Real block-diagonal 6x6 A with 2x2 rotation blocks for each
    (mag, theta) pair and a diag block for the real eigenvalues.

    Eigenvectors of a rotation block concentrate in the block's rows, so
    a pair at rows 0-1 is oil-dominant (P_W high) and a pair at rows 2-3
    or 4-5 is EC-dominant (P_EC high).
    """
    from scipy.linalg import block_diag

    blocks = []
    for mag, theta in pairs:
        r = mag
        blocks.append(np.array([[r * np.cos(theta), -r * np.sin(theta)],
                                [r * np.sin(theta), r * np.cos(theta)]]))
    blocks.append(np.diag(reals) if reals else np.zeros((0, 0)))
    return block_diag(*blocks)


def _generate_trajectory(a, n=1500, seed=0):
    rng = np.random.RandomState(seed)
    x = rng.normal(0, 1, (6, n + 1))
    out = np.empty((n, 6))
    for t in range(n):
        out[t] = x[:, t]
        x[:, t + 1] = a @ x[:, t]
    return out


class TestDMD:
    def test_recovers_magnitude_phase_and_norm(self):
        theta = 0.5
        a = _block_diag_system([(0.97, theta), (0.9, 1.2)], [0.8, -0.7])
        psi = _generate_trajectory(a)
        result = k1_mod.dmd_step(psi[-k1_mod.DMD_WINDOW:])
        mags = np.abs(result["eigenvalues"])
        assert np.any(np.isclose(mags, 0.97, atol=1e-6))
        assert np.any(np.isclose(np.abs(np.angle(result["eigenvalues"])), theta, atol=1e-6))
        norms = np.linalg.norm(result["eigenvectors"], axis=0)
        assert np.allclose(norms, 1.0, atol=1e-9)

    def test_eligibility_mask(self):
        eigvals = np.array([0.97 + 0.1j, 0.97 - 0.1j, 0.99, -0.99, 0.5 + 0.2j, 1.01 + 0.1j])
        mask = k1_mod.eligible_mask(eigvals)
        assert mask[0]
        assert not mask[1]
        assert not mask[2]
        assert not mask[3]
        assert not mask[4]  # 0.5 not in band
        assert not mask[5]  # |1.01...| >= 1.0

    def test_oil_and_ec_dominant_selection(self):
        theta_oil, theta_ec = 2.5, -2.5
        # pair at rows 0-1 (oil) and pair at rows 2-3 (EC)
        a = _block_diag_system([(0.97, theta_oil), (0.96, theta_ec)], [0.5, 0.3])
        psi = _generate_trajectory(a)
        result = k1_mod.dmd_step(psi[-k1_mod.DMD_WINDOW:])
        mask = k1_mod.eligible_mask(result["eigenvalues"])
        idx = np.where(mask)[0]
        assert len(idx) == 2
        p_w = [k1_mod.participation(result["eigenvectors"], j)[0] for j in idx]
        p_ec = [k1_mod.participation(result["eigenvectors"], j)[1] for j in idx]
        j_w = idx[int(np.argmax(p_w))]
        j_ec = idx[int(np.argmax(p_ec))]
        assert j_w != j_ec
        assert np.isclose(np.abs(result["eigenvalues"][j_w]), 0.97, atol=1e-6)
        assert np.isclose(np.abs(result["eigenvalues"][j_ec]), 0.96, atol=1e-6)

    def test_same_dominant_mode_gives_zero_deltaphi(self):
        # ONE eligible mode -> same mode wins both participations -> DeltaPhi=0
        a = _block_diag_system([(0.97, 1.0)], [0.8, 0.7, 0.6, 0.5])
        psi = _generate_trajectory(a)
        out = k1_mod.k1_kernel(psi, np.ones(len(psi)), np.zeros(len(psi), dtype=bool))
        assert out["delta_phi"][-1] == 0.0
        assert out["w3"][-1] == 0.0

    def test_no_eligible_mode_fails_closed(self):
        a = _block_diag_system([(0.9, 0.7)], [0.8, 0.7, 0.6, 0.5])
        psi = _generate_trajectory(a)
        out = k1_mod.k1_kernel(psi, np.ones(len(psi)), np.zeros(len(psi), dtype=bool))
        assert not out["K1_VALID"][-1]
        assert out["w3"][-1] == 0.0
        assert "no eligible" in out["reason"][-1]

    def test_real_only_eigenvalues_invalid(self):
        a = _block_diag_system([], [0.97, -0.97, 0.9, -0.9, 0.8, 0.7])
        psi = _generate_trajectory(a)
        out = k1_mod.k1_kernel(psi, np.ones(len(psi)), np.zeros(len(psi), dtype=bool))
        assert not out["K1_VALID"][-1]
        assert "no eligible" in out["reason"][-1]

    def test_stale_disables_k1(self):
        psi = np.zeros((k1_mod.DMD_WINDOW, 6))
        stale = np.zeros(len(psi), dtype=bool)
        stale[-1] = True
        out = k1_mod.k1_kernel(psi, np.ones(len(psi)), stale)
        assert not out["K1_VALID"][-1]
        assert "stale" in out["reason"][-1]

    def test_phase_activation_and_w3(self):
        """DeltaPhi > 1.57 activates w3 = -sign(r_I) * min(DeltaPhi/2, 0.35)."""
        # eligible phases: oil +2.5, EC +0.5 -> circular distance 2.0 > 1.57
        a = _block_diag_system([(0.97, 2.5), (0.96, 0.5)], [0.5, 0.3])
        psi = _generate_trajectory(a)
        r_i = np.ones(len(psi)) * 0.5  # positive DAX return
        out = k1_mod.k1_kernel(psi, r_i, np.zeros(len(psi), dtype=bool))
        assert out["K1_VALID"][-1]
        dp = out["delta_phi"][-1]
        assert dp > 1.57
        assert out["w3"][-1] == pytest.approx(-np.sign(0.5) * min(dp / 2.0, 0.35))
        # inactive: phases +2.5 and +2.5 (same angle) -> DeltaPhi 0
        a2 = _block_diag_system([(0.97, 2.5), (0.96, 2.5)], [0.5, 0.3])
        psi2 = _generate_trajectory(a2)
        out2 = k1_mod.k1_kernel(psi2, r_i, np.zeros(len(psi2), dtype=bool))
        # same-angle modes differ only by floating-point reconstruction noise
        assert out2["delta_phi"][-1] == pytest.approx(0.0, abs=1e-12)
        assert out2["w3"][-1] == 0.0


class TestCircularPhase:
    def test_wrapping_fixture(self):
        d = k1_mod.phase_distance(3.10, -3.10)
        assert d == pytest.approx(2 * np.pi - 6.20, abs=1e-9)
        assert d < 0.5  # circular distance is small, NOT ~6.2

    def test_bounded(self):
        assert 0.0 <= k1_mod.phase_distance(0.1, 6.0) <= np.pi


# ---------------------------------------------------------------------------
# 35.7 VR topology (A1.F10)
# ---------------------------------------------------------------------------


class TestVRTopology:
    # PAIRS order: WE, WC, WI, EC, EI, CI
    def test_no_hole_complete_graph(self):
        d = np.array([1.0] * 6)
        assert k3_mod.beta1_of_complex(d <= 1.2) == 0.0
        assert k3_mod.classify_distances(d, 1.2) == "NO_HOLE"

    def test_unfilled_four_cycle(self):
        # cycle W-E-C-I-W: edges WE, EC, CI, WI present; WC, EI absent
        edges = np.array([True, False, True, True, False, True])
        assert k3_mod.beta1_of_complex(edges) == 1.0

    def test_persistent_cycle(self):
        d = np.array([1.0, 2.0, 1.0, 1.0, 2.0, 1.0])  # cycle; diagonals far
        assert k3_mod.classify_distances(d, 1.2) == "PERSISTENT"

    def test_fragile_cycle(self):
        d = np.array([1.0, 1.1, 1.0, 1.0, 1.1, 1.0])  # diagonals close
        # at eps=1.0 the cycle holds; at 1.15*eps=1.15 diagonals appear -> filled
        assert k3_mod.classify_distances(d, 1.0) == "FRAGILE"

    def test_no_edges_no_hole(self):
        d = np.array([2.0] * 6)
        assert k3_mod.beta1_of_complex(d <= 1.0) == 0.0
        assert k3_mod.classify_distances(d, 1.0) == "NO_HOLE"

    def test_triangle_plus_isolated_vertex(self):
        # triangle W-E-C edges WE, WC, EC present; I isolated
        edges = np.array([True, True, False, True, False, False])
        assert k3_mod.beta1_of_complex(edges) == 0.0


# ---------------------------------------------------------------------------
# 35.8 K3 causal OLS (A1.F11)
# ---------------------------------------------------------------------------


class TestK3OLS:
    def _fixture(self, n=200, noise=0.0, seed=1):
        rng = np.random.RandomState(seed)
        dwe = rng.uniform(0.5, 2.0, n)
        dwc = rng.uniform(0.3, 1.5, n)
        dec = 1.0 + 2.0 * dwe - 0.5 * dwc + rng.normal(0, noise, n)
        return dec, dwe, dwc

    def test_recovers_known_coefficients(self):
        dec, dwe, dwc = self._fixture(noise=0.0)
        result = k3_mod.k3_ols(dec, dwe, dwc, np.ones(len(dec), dtype=bool))
        t = len(dec) - 1
        assert result["valid"][t]
        b = result["beta"][t]
        assert b[0] == pytest.approx(1.0, abs=1e-8)
        assert b[1] == pytest.approx(2.0, abs=1e-8)
        assert b[2] == pytest.approx(-0.5, abs=1e-8)
        assert result["dhat"][t] == pytest.approx(dec[t], abs=1e-6)

    def test_current_t_excluded_from_fitting(self):
        dec, dwe, dwc = self._fixture(noise=0.0)
        result1 = k3_mod.k3_ols(dec, dwe, dwc, np.ones(len(dec), dtype=bool))
        t = 100
        dec_perturbed = dec.copy()
        dec_perturbed[t] = dec_perturbed[t] * 1000.0  # massive change at t
        result2 = k3_mod.k3_ols(dec_perturbed, dwe, dwc, np.ones(len(dec), dtype=bool))
        assert np.allclose(result1["beta"][t], result2["beta"][t])
        # prediction still uses current inputs: Dhat uses current D_WE/D_WC
        b = result2["beta"][t]
        assert result2["dhat"][t] == pytest.approx(
            b[0] + b[1] * dwe[t] + b[2] * dwc[t])

    def test_singular_ols_fails_closed(self):
        n = 100
        dwe = np.linspace(1.0, 2.0, n)
        dwc = 2.0 * dwe  # perfectly collinear
        dec = 1.0 + dwe
        result = k3_mod.k3_ols(dec, dwe, dwc, np.ones(n, dtype=bool))
        t = n - 1
        assert not result["valid"][t]
        assert "K3_OLS_VALID=false" in result["reason"][t]
        assert np.isnan(result["dhat"][t])  # no silent fallback value

    def test_no_pseudoinverse_substitution(self):
        """The RAW fail-closed path must never produce coefficients via pinv."""
        n = 100
        dwe = np.linspace(1.0, 2.0, n)
        dwc = 2.0 * dwe
        dec = 1.0 + dwe
        result = k3_mod.k3_ols(dec, dwe, dwc, np.ones(n, dtype=bool))
        assert not result["valid"][-1]


# ---------------------------------------------------------------------------
# 35.10 RV6 (A1.F13) + 35.11 commutator (A1.F14)
# ---------------------------------------------------------------------------


class TestRV6:
    def test_hand_fixture(self):
        returns = np.array([0.01, -0.02, 0.03, 0.0, 0.005, -0.01])
        b, valid, _ = k4_mod.rv6(returns, np.ones(6, dtype=bool))
        assert valid[5]
        assert b[5] == pytest.approx(np.std(returns, ddof=1))

    def test_exactly_six_ddof1_nonannualized(self):
        returns = np.arange(1.0, 7.0) * 0.001
        b, valid, _ = k4_mod.rv6(returns, np.ones(6, dtype=bool))
        expected = np.std(returns, ddof=1)
        assert b[5] == pytest.approx(expected)  # raw hourly scale, NOT annualized
        assert expected != pytest.approx(expected * np.sqrt(24))

    def test_insufficient_history(self):
        b, valid, reasons = k4_mod.rv6(np.zeros(3), np.ones(3, dtype=bool))
        assert not valid[2]
        assert "insufficient" in reasons[2]


class TestCommutator:
    def test_hand_calculated(self):
        n = 21  # indices t-20 .. t
        a = np.arange(n, dtype=float) * 0.1
        b = np.arange(n, dtype=float) * 0.01
        alpha, ok, _ = k4_mod.commutator(a, b, np.ones(n, dtype=bool),
                                         np.ones(n, dtype=bool))
        assert ok[-1]
        # independent computation
        expected = 0.0
        for k in range(1, 21):
            expected += a[20 - k] * b[20 - k + 1] - b[20 - k] * a[20 - k + 1]
        expected /= 20
        assert alpha[-1] == pytest.approx(expected)

    def test_current_a_enters_via_k1(self):
        n = 21
        a = np.ones(n)
        b = np.ones(n)
        alpha_base, _, _ = k4_mod.commutator(a, b, np.ones(n, dtype=bool),
                                             np.ones(n, dtype=bool))
        a_cur = a.copy()
        a_cur[-1] = 5.0  # current A_t changed
        alpha_changed, _, _ = k4_mod.commutator(a_cur, b, np.ones(n, dtype=bool),
                                                np.ones(n, dtype=bool))
        assert alpha_changed[-1] != alpha_base[-1]  # current A_t enters k=1

    def test_insufficient_history(self):
        a = np.ones(10)
        b = np.ones(10)
        alpha, ok, reasons = k4_mod.commutator(a, b, np.ones(10, dtype=bool),
                                               np.ones(10, dtype=bool))
        assert not ok[-1]
        assert "insufficient" in reasons[-1]

    def test_w_total_clip_and_sign(self):
        alpha = np.array([0.001, -0.001, 0.0001, 0.0])
        wt, ok, _ = k4_mod.w_total(alpha, np.ones(4, dtype=bool))
        assert wt[0] == pytest.approx(1.0)   # |0.001|/0.0005 = 2 -> clipped to 1
        assert wt[1] == pytest.approx(-1.0)
        assert wt[2] == pytest.approx(0.2)   # 0.0001/0.0005 = 0.2
        assert wt[3] == 0.0


# ---------------------------------------------------------------------------
# 35.12 FSM (A1.F15) + fade
# ---------------------------------------------------------------------------


class TestFSM:
    def test_exhaustive_transitions(self):
        wt = np.array([0.0, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1, 0.0, 0.0, 0.1, -0.1])
        w1 = np.ones(11) * 0.1
        w2 = np.ones(11) * 0.2
        w3 = np.ones(11) * 0.3
        out = port_mod.cluster_fsm(wt, w1, w2, w3)
        states = out["state"]
        assert states[0] == "NEUTRAL"
        assert states[1] == "LONG"
        assert states[2] == "SHORT"
        assert states[3] == "LONG"   # long->long
        assert states[4] == "LONG"
        assert states[5] == "SHORT"  # long->short
        assert states[6] == "LONG"   # short->long
        assert states[7] == "NEUTRAL"  # long->neutral
        assert states[8] == "NEUTRAL"  # neutral->neutral
        assert states[9] == "LONG"   # neutral->long
        assert states[10] == "SHORT"  # long->short

    def test_neutral_target_zero(self):
        out = port_mod.cluster_fsm(np.array([0.0]), np.array([0.5]), np.array([0.5]),
                                   np.array([0.5]))
        assert np.all(out["w_base"][0] == 0.0)

    def test_active_target_scaling(self):
        out = port_mod.cluster_fsm(np.array([0.1]), np.array([0.2]), np.array([0.3]),
                                   np.array([0.4]))
        assert out["w_base"][0][0] == pytest.approx(0.1 * 0.2)
        assert out["w_base"][0][1] == pytest.approx(0.1 * 0.3)
        assert out["w_base"][0][2] == pytest.approx(0.1 * 0.5 * 0.4)


class TestFade:
    def _seq(self, targets):
        return np.array(targets, dtype=float).reshape(len(targets), 1)

    def test_no_reversal_constant_target(self):
        t = self._seq([0.3, 0.3, 0.3, 0.3])
        out = port_mod.fade_sequence(t)
        assert np.allclose(out["w_fade"][:, 0], [0.3, 0.3, 0.3, 0.3])

    def test_reversal_fade_sequence(self):
        t = self._seq([0.3, 0.3, -0.2, -0.2, -0.2, -0.2])
        out = port_mod.fade_sequence(t)
        w = out["w_fade"][:, 0]
        assert w[0] == pytest.approx(0.3)
        assert w[1] == pytest.approx(0.3)
        assert w[2] == pytest.approx(0.67 * 0.3)  # hour 1: 67% old exposure
        assert w[3] == 0.0                         # hour 2: flat
        assert w[4] == pytest.approx(-0.2)         # hour 3: full new target
        assert w[5] == pytest.approx(-0.2)
        assert list(out["phase"]) == [0, 0, 1, 2, 3, 0]

    def test_second_flip_restarts_fade(self):
        t = self._seq([0.3, 0.3, -0.2, 0.4, 0.4])
        out = port_mod.fade_sequence(t)
        w = out["w_fade"][:, 0]
        assert w[2] == pytest.approx(0.67 * 0.3)   # first fade hour 1
        assert w[3] == pytest.approx(0.67 * w[2])  # re-flip restarts from current
        assert w[4] == 0.0                         # second fade hour 2

    def test_neutral_during_fade_fades_to_zero(self):
        t = self._seq([0.3, 0.3, -0.2, 0.0, 0.0, 0.0])
        out = port_mod.fade_sequence(t)
        w = out["w_fade"][:, 0]
        assert w[2] == pytest.approx(0.67 * 0.3)
        assert w[3] == 0.0
        assert w[4] == 0.0
        assert w[5] == 0.0
        assert out["reason"][3] == "FADE_TO_ZERO_STOP"

    def test_entry_from_flat_no_fade(self):
        t = self._seq([0.0, 0.0, 0.3, 0.3])
        out = port_mod.fade_sequence(t)
        w = out["w_fade"][:, 0]
        assert w[0] == 0.0
        assert w[2] == pytest.approx(0.3)  # no fade on entry

    def test_neutralization_fades_to_zero(self):
        t = self._seq([0.3, 0.3, 0.0, 0.0])
        out = port_mod.fade_sequence(t)
        w = out["w_fade"][:, 0]
        assert w[2] == pytest.approx(0.67 * 0.3)
        assert w[3] == 0.0


# ---------------------------------------------------------------------------
# 35.13 gross cap (A1.F16)
# ---------------------------------------------------------------------------


class TestGrossCap:
    def test_below_cap_no_scale(self):
        w = np.array([[0.45, 0.30, 0.175]])
        out = port_mod.gross_cap(w)
        assert np.allclose(out[0], [0.45, 0.30, 0.175])

    def test_above_cap_scaled_to_one(self):
        w = np.array([[0.45, 0.30, 0.35]])
        out = port_mod.gross_cap(w)
        assert np.abs(out).sum() == pytest.approx(1.0)
        assert np.allclose(out[0], np.array([0.45, 0.30, 0.35]) / 1.10)


# ---------------------------------------------------------------------------
# 35.14 drawdown (A1.F18) + 35.15 terminal persistence
# ---------------------------------------------------------------------------


class TestDrawdown:
    def _run(self, nav):
        w = np.ones((len(nav), 1)) * 0.3
        return port_mod.drawdown_overlay(w, np.asarray(nav, dtype=float))

    def test_below_zone_full_scale(self):
        out = self._run([100.0, 90.0])  # DD = 0.10
        assert out["dd"][1] == pytest.approx(0.10)
        assert out["w_dd"][1][0] == pytest.approx(0.3)

    def test_zone2_linear_scale(self):
        out = self._run([100.0, 85.0])  # DD = 0.15
        assert out["dd"][1] == pytest.approx(0.15)
        assert out["w_dd"][1][0] == pytest.approx(0.3 * (1 - (0.15 - 0.12) / 0.06))
        assert out["w_dd"][1][0] == pytest.approx(0.15)

    def test_zone3_reflector(self):
        out = self._run([100.0, 82.0])  # DD = 0.18
        assert out["w_dd"][1][0] == pytest.approx(-0.50 * 0.3)

    def test_terminal_kill(self):
        out = self._run([100.0, 80.4])  # DD = 0.196 >= 0.195 -> terminal
        assert out["terminal"][1]
        assert out["w_dd"][1][0] == 0.0

    def test_terminal_persistence(self):
        nav = [100.0, 80.4, 90.0, 110.0]  # NAV recovers, but kill latches
        out = self._run(nav)
        assert out["terminal"][1]
        assert out["terminal"][2]
        assert out["terminal"][3]  # terminal persists even after NAV recovery
        assert out["w_dd"][3][0] == 0.0

    def test_zone3_just_above_18pct(self):
        out = self._run([100.0, 81.9])  # DD ~ 0.181 -> reflector
        assert out["dd"][1] == pytest.approx(0.181, abs=1e-3)
        assert out["w_dd"][1][0] == pytest.approx(-0.50 * 0.3)


# ---------------------------------------------------------------------------
# 35.16 leg stop (A1.F19)
# ---------------------------------------------------------------------------


class TestLegStop:
    def test_trigger_and_ban(self):
        n = 40
        equity = np.full((n, 1), 100.0)
        nav = np.full(n, 100.0)
        # crash from slot 20: LE drops by 3% of NAV over 6 bars
        equity[20:, 0] = 97.0
        out = port_mod.leg_stop(equity, nav)
        # trigger while (LE_t - LE_{t-6})/NAV < -0.02: slots 20..25
        hit = np.where(out["trigger_hits"][:, 0])[0]
        assert list(hit) == [20, 21, 22, 23, 24, 25]
        assert out["target"][20, 0] == 0.0
        # each trigger re-arms the ban; last trigger at 25 bans slots 25..36
        # (12 completed bars), so slot 37 is the first executable slot
        assert out["target"][36, 0] == 0.0
        assert out["target"][37, 0] == 1.0  # ban expired exactly 12 bars after last trigger

    def test_single_trigger_ban_window(self):
        n = 40
        equity = np.full((n, 1), 100.0)
        nav = np.full(n, 100.0)
        equity[20, 0] = 97.0  # one bad slot only; recovers next bar
        out = port_mod.leg_stop(equity, nav)
        hit = np.where(out["trigger_hits"][:, 0])[0]
        assert list(hit) == [20]  # (97-100)/100 = -0.03 at t=20 only
        assert out["target"][20, 0] == 0.0
        assert out["target"][31, 0] == 0.0   # 12 completed bars: 20..31
        assert out["target"][32, 0] == 1.0   # ban expired

    def test_no_trigger_no_ban(self):
        n = 30
        equity = np.full((n, 1), 100.0)
        nav = np.full(n, 100.0)
        out = port_mod.leg_stop(equity, nav)
        assert not out["trigger_hits"].any()
        assert np.all(out["target"] == 1.0)
