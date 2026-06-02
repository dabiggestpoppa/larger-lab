"""
Phase 3: Optuna Bayesian Parameter Optimizer (Layer 3)
========================================================
Multi-objective optimization of CEREBUS parameters per asset per regime.
Objectives: maximize WR, maximize PF, minimize max DD.
"""
from __future__ import annotations

import json
from pathlib import Path

import optuna
import numpy as np
import pandas as pd
from optuna.samplers import NSGAIISampler
import joblib

# Search space defaults
DEFAULT_SEARCH_SPACE = {
    "au_multiplier": (0.35, 0.65),
    "trigger_multiplier": (1.0, 1.5),
    "dz_lower_pct": (0.25, 0.40),
    "dz_upper_pct": (0.45, 0.60),
    "buffer_pips": (3.0, 20.0),
    "min_pullback_pct": (0.25, 0.40),
    "max_pullback_pct": (0.50, 0.65),
}


class CerebusBayesianOptimizer:
    """
    Bayesian optimization of CEREBUS parameters per asset per regime.
    Uses Optuna with NSGA-II sampler for multi-objective optimization.
    """

    def __init__(
        self,
        asset_name: str,
        regime: str,
        search_space: dict = None,
        n_trials: int = 200,
        seed: int = 42,
    ):
        self.asset_name = asset_name
        self.regime = regime
        self.search_space = search_space or DEFAULT_SEARCH_SPACE
        self.n_trials = n_trials
        self.seed = seed
        self.study = None

    def _suggest_params(self, trial: optuna.Trial) -> dict:
        """Suggest parameters from search space."""
        params = {}
        for name, bounds in self.search_space.items():
            if isinstance(bounds[0], int):
                params[name] = trial.suggest_int(name, bounds[0], bounds[1])
            else:
                params[name] = trial.suggest_float(name, bounds[0], bounds[1])
        return params

    def optimize(self, backtest_fn, directions: list[str] = None) -> dict:
        """
        Run multi-objective optimization.

        Parameters
        ----------
        backtest_fn : callable
            Function(params) -> dict with keys: sharpe_ratio, win_rate, profit_factor, max_drawdown_pct
        directions : list of str
            ["maximize", "maximize", "minimize"] for [sharpe*wr, pf, -dd]

        Returns
        -------
        dict with best params and Pareto front
        """
        if directions is None:
            directions = ["maximize", "maximize", "minimize"]

        self.study = optuna.create_study(
            directions=directions,
            sampler=NSGAIISampler(seed=self.seed),
            study_name=f"{self.asset_name}_{self.regime}",
        )

        def objective(trial):
            params = self._suggest_params(trial)
            results = backtest_fn(params)

            sharpe = results.get("sharpe_ratio", 0)
            wr = results.get("win_rate", 0)
            pf = results.get("profit_factor", 1)
            max_dd = results.get("max_drawdown_pct", 100)

            # Composite: Sharpe*WR, PF, -DD
            return sharpe * wr, pf, -max_dd

        self.study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        # Extract Pareto front
        pareto_trials = self.study.best_trials
        best_params = []
        for t in pareto_trials[:5]:  # Top 5 non-dominated solutions
            best_params.append({
                "params": t.params,
                "values": t.values,
            })

        print(f"\n=== OPTIMAL PARAMS FOR {self.asset_name} ({self.regime}) ===")
        print(f"Pareto front: {len(pareto_trials)} solutions")
        for i, bp in enumerate(best_params[:3]):
            print(f"  Solution {i+1}: {bp['params']}")
            print(f"    Sharpe*WR={bp['values'][0]:.4f}, PF={bp['values'][1]:.2f}, -DD={bp['values'][2]:.2f}")

        result = {
            "asset": self.asset_name,
            "regime": self.regime,
            "pareto_front": best_params,
            "n_trials": self.n_trials,
            "study": self.study,
        }
        if best_params:
            result["best_params"] = best_params[0]["params"]
        return result

    def save_study(self, path: str | Path):
        """Save Optuna study."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.study, path / f"{self.asset_name}_{self.regime}_study.pkl")

    @staticmethod
    def optimize_all_assets(
        assets: list[str],
        regimes: list[str],
        backtest_fn,
        n_trials: int = 200,
        output_dir: str | Path = None,
    ) -> dict:
        """Run optimization for all asset × regime combinations."""
        results = {}
        for asset in assets:
            for regime in regimes:
                try:
                    optimizer = CerebusBayesianOptimizer(asset, regime, n_trials=n_trials)
                    result = optimizer.optimize(backtest_fn)
                    results[f"{asset}_{regime}"] = result
                    if output_dir:
                        optimizer.save_study(output_dir)
                except Exception as e:
                    print(f"  ❌ {asset}/{regime}: {e}")
                    results[f"{asset}_{regime}"] = {"error": str(e)}
        return results
