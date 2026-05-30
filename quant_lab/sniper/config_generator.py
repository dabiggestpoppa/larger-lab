"""
Deployment Config Generator
Outputs YAML/JSON config that the execution engine reads.
Separates OC2 intelligence from trading logic — the engine lives above the house.
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

from .pes_calculator import PESResult, EngineEdge


CONFIG_DIR = Path(__file__).parent / "configs"
CONFIG_DIR.mkdir(exist_ok=True)


class ConfigGenerator:
    """
    Generates deployment configs from PES analysis.
    Output is read by the execution engine — OC2 never touches trading logic.
    """

    def generate_deployment_config(
        self,
        top_results: list[PESResult],
        edge,
        crossover_threshold: int = 10000,
        notes: str = "",
    ) -> dict:
        """Generate full deployment config from ranked PES results."""
        now = datetime.utcnow().isoformat()

        firm_mix = []
        for r in top_results:
            firm_mix.append({
                "firm": r.firm_name,
                "account_size": r.account_size,
                "pes_score": r.pes_score,
                "effective_leverage": r.effective_leverage,
                "capital_velocity": r.capital_velocity,
                "omega": r.omega,
                "alpha": r.alpha,
                "survival_probability": r.survival_probability,
                "crossover_threshold_usd": r.crossover_threshold,
                "notes": r.notes,
            })

        config = {
            "deployment_config": {
                "generated_at": now,
                "version": "1.0.0",
                "crossover_threshold_usd": crossover_threshold,
                "edge_metrics": {
                    "win_rate": edge.win_rate,
                    "max_drawdown_pct": edge.max_drawdown_pct,
                    "avg_trades_per_day": edge.avg_trades_per_day,
                    "sharpe_ratio": edge.sharpe_ratio,
                    "profit_factor": edge.profit_factor,
                    "instrument": edge.instrument,
                },
                "firm_mix": firm_mix,
                "risk_parameters": self._derive_risk_parameters(top_results, edge),
                "metadata": {
                    "generated_by": "oc2-scope",
                    "notes": notes,
                },
            }
        }
        return config

    def _derive_risk_parameters(self, results, edge) -> dict:
        """Derive execution engine risk parameters from PES analysis."""
        if not results:
            return {}

        best = results[0]

        # Risk per trade scales with effective exposure
        risk_per_trade = round(1.0 / best.effective_leverage, 4)

        # Consistency buffer from drag
        consistency_buffer = round(1.0 - best.consistency_drag, 4)

        # Max correlated exposure from survival analysis
        max_correlated = max(1, int(best.survival_probability * 5))

        # Diversification: more firms = less correlation risk
        firm_diversification_min = min(len(results), 3)

        # Diminishing return threshold
        diminishing_return = best.crossover_threshold

        return {
            "risk_per_trade": risk_per_trade,
            "consistency_buffer": consistency_buffer,
            "max_correlated_exposure": max_correlated,
            "firm_diversification_min": firm_diversification_min,
            "diminishing_return_threshold": diminishing_return,
            "max_drawdown_pct": edge.max_drawdown_pct,
            "instrument": edge.instrument,
        }

    def save_yaml(self, config: dict, label: str = "deployment") -> Path:
        """Save config as YAML."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = CONFIG_DIR / f"{label}_{ts}.yaml"
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        return path

    def save_json(self, config: dict, label: str = "deployment") -> Path:
        """Save config as JSON."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = CONFIG_DIR / f"{label}_{ts}.json"
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        return path

    def format_scope_output(
        self,
        top_results: list[PESResult],
        ff_status: str = "STANDARD",
    ) -> str:
        """Format the oc2 scope output for display."""
        if not top_results:
            return "⚠️ No viable prop firm deployments found with current edge metrics."

        best = top_results[0]
        total_risk = best.effective_exposure * best.effective_leverage
        lines = [
            f"🎯 BEST EXPLOIT: {best.firm_name} ${best.account_size:,}",
            f"   PES: {best.pes_score:.4f} | "
            f"Ω: {best.omega:.4f} | "
            f"α: {best.alpha:.4f}",
            f"   Effective Lev: {best.effective_leverage:.1f}:1 | "
            f"Velocity: {best.capital_velocity:.4f}",
            f"   Total Risk Capital: ${total_risk:,.0f} | "
            f"Cost/acct: ${best.account_cost:.2f}",
            f"   Survival (n accounts): {best.survival_probability:.1%}",
            f"   Crossover Threshold: ${best.crossover_threshold:,} "
            f"(beyond this → go live)",
            f"   F&F Status: {ff_status}",
            f"   Consistency Drag: {best.consistency_drag:.1%} | "
            f"Scaling Friction: {best.scaling_friction:.4f}",
        ]

        if best.notes:
            lines.append(f"   Notes: {'; '.join(best.notes)}")

        if len(top_results) > 1:
            lines.append("")
            lines.append("📊 FULL RANKING:")
            for i, r in enumerate(top_results, 1):
                total_aum = r.account_size
                over_crossover = "⚠️ OVER CROSSOVER" if total_aum > r.crossover_threshold else ""
                lines.append(
                    f"   {i}. {r.firm_name} ${r.account_size:,} — "
                    f"PES: {r.pes_score:.4f} | "
                    f"EL: {r.effective_leverage:.1f}:1 | "
                    f"Crossover: ${r.crossover_threshold:,} "
                    f"{over_crossover}"
                )

        return "\n".join(lines)
