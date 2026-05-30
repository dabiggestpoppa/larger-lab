"""
Phase 1+2: F&F (Friends & Family) Scaling Matrix + Capital Deployment Router

THE SHALLOW WELL ARBITRAGE:
  Prop firms price risk assuming 1:1 identity-to-account.
  We break that assumption. By fragmenting capital across N identities (F&F network),
  we access "new customer" promos repeatedly AND bypass consistency rules because
  no single account hits the daily profit cap.

  10x $1k accounts: a $200 daily profit is only 20% of each account.
  1x $10k account:  a $200 daily profit is 2% — but the consistency rule
                   measures against TOTAL profit, so Monolith days get capped.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .ontology_mapper import PropFirmOntology


@dataclass
class FFFragmentationResult:
    """Result of F&F fragmentation analysis for a single firm."""
    firm_name: str
    strategy: str                       # "SHALLOW_WELL" or "DEEP_WELL"
    account_size: int
    quantity: int
    total_cost: float
    total_bandwidth: float
    fleet_coc: float                    # fleet Cost of Capital
    deep_well_coc: float                # single large account CoC
    coc_reduction_pct: float            # how much CoC improved
    consistency_bypass: bool            # does fragmentation bypass the rule?
    bypass_factor: float                # 1.0 = no bypass, >1 = effective multiplier
    monthly_yield_estimate: float       # expected $/month from CEREBUS edge
    max_single_day_pct_of_account: float  # daily profit as % of single account
    notes: List[str] = field(default_factory=list)


class FFScalingMatrix:
    """
    Calculates the exponential decay of CoC when deploying multiple
    accounts via Friends & Family silos.
    """

    @staticmethod
    def calculate_fleet_pes(
        base_ontology: PropFirmOntology,
        num_accounts: int,
        promo_repeatable: bool = True,
    ) -> dict:
        """
        Calculate fleet metrics for N accounts under F&F.

        promo_repeatable: True if F&F lets us use the promo on each identity.
        """
        if promo_repeatable:
            unit_fee = base_ontology.net_fee
        else:
            unit_fee = base_ontology.eval_fee

        fleet_bandwidth = base_ontology.risk_bandwidth * num_accounts
        fleet_fee = unit_fee * num_accounts

        fleet_coc = fleet_fee / fleet_bandwidth if fleet_bandwidth > 0 else 999.9
        single_coc = base_ontology.cost_of_capital()

        coc_reduction = (1.0 - (fleet_coc / single_coc)) * 100.0 if single_coc > 0 else 0.0

        return {
            "fleet_size": num_accounts,
            "total_bandwidth": fleet_bandwidth,
            "fleet_coc": fleet_coc,
            "single_coc": single_coc,
            "coc_reduction_pct": coc_reduction,
            "bandwidth_multiplier": num_accounts,
            "total_upfront_cost": fleet_fee,
        }

    def find_optimal_fragmentation(
        self,
        ontology: PropFirmOntology,
        target_aum: int,
        max_identities: int = 10,
    ) -> FFFragmentationResult:
        """
        Find the optimal account size × quantity to minimize CoC
        while hitting the target AUM.
        """
        best_score = -999.0
        best_config = None

        # Possible fragmentation levels: divide target AUM into accounts
        fragmentations = self._generate_fragmentations(target_aum)

        for acc_size, qty in fragmentations:
            cost_per = self._estimate_cost(ontology, acc_size)
            promo_repeatable = ontology.ff_access
            unit_fee = ontology.net_fee if promo_repeatable else ontology.eval_fee

            # Scale fee by account size relative to primary
            scaled_fee = cost_per * (acc_size / max(ontology.account_size, 1))
            if promo_repeatable and ontology.promo_code:
                scaled_fee *= (1.0 - ontology.promo_discount_pct)

            total_cost = scaled_fee * qty
            total_bandwidth = ontology.max_dd_amount * qty

            fleet_coc = total_cost / total_bandwidth if total_bandwidth > 0 else 999.9
            single_coc = ontology.cost_of_capital()

            # Consistency bypass: does this fragmentation help?
            bypass = False
            bypass_factor = 1.0
            typical_daily_pnl_pct = 0.02  # ~2% of account per good day
            daily_pct_per_account = typical_daily_pnl_pct
            daily_pct_per_account_adjusted = typical_daily_pnl_pct / qty
            if ontology.has_consistency_rule and ontology.max_single_day_profit_pct > 0:
                # More accounts = each account's share of total profit is smaller
                if daily_pct_per_account_adjusted < ontology.max_single_day_profit_pct:
                    bypass = True
                    bypass_factor = 1.0 + (1.0 / qty)

            # Geometric yield: bandwidth × bypass_factor / total_cost
            monthly_yield = (total_bandwidth * 0.05) * bypass_factor  # rough 5% monthly on risk capital
            score = monthly_yield / max(total_cost, 0.01)

            if score > best_score:
                best_score = score
                best_config = FFFragmentationResult(
                    firm_name=ontology.firm_name,
                    strategy="SHALLOW_WELL" if bypass else ("F&F" if ontology.ff_access else "STANDARD"),
                    account_size=acc_size,
                    quantity=qty,
                    total_cost=total_cost,
                    total_bandwidth=total_bandwidth,
                    fleet_coc=fleet_coc,
                    deep_well_coc=single_coc,
                    coc_reduction_pct=((1.0 - fleet_coc / max(single_coc, 0.001)) * 100.0),
                    consistency_bypass=bypass,
                    bypass_factor=bypass_factor,
                    monthly_yield_estimate=monthly_yield,
                    max_single_day_pct_of_account=daily_pct_per_account_adjusted * 100.0 if bypass else daily_pct_per_account * 100.0,
                    notes=[],
                )

        if best_config:
            if bypass:
                best_config.notes.append(
                    f"Consistency rule bypassed: profit split across {best_config.quantity} accounts"
                )
            if ontology.ff_access and ontology.promo_code:
                best_config.notes.append(
                    f"F&F promo repeat: '{ontology.promo_code}' × {best_config.quantity}"
                )

        return best_config

    def _generate_fragmentations(self, target_aum: int) -> list:
        """Generate (account_size, quantity) pairs that sum to target_aum."""
        common_sizes = [1000, 2500, 5000, 10000, 15000, 25000, 50000, 100000, 150000]
        results = []
        for size in common_sizes:
            if target_aum % size == 0:
                qty = target_aum // size
                if 1 <= qty <= 100:
                    results.append((size, qty))
        if not results:
            # Default: closest round number
            size = 5000
            qty = max(1, target_aum // size)
            results.append((size, qty))
        return results

    def _estimate_cost(self, ontology: PropFirmOntology, account_size: int) -> float:
        """Estimate eval fee for a given account size."""
        if not ontology.raw_cost_per_size:
            ratio = account_size / max(ontology.account_size, 1)
            return ontology.eval_fee * ratio
        # Try int key first, then string key
        cost = ontology.raw_cost_per_size.get(account_size)
        if cost is None:
            cost = ontology.raw_cost_per_size.get(str(account_size))
        if cost is not None:
            return cost
        # Linear interpolation from nearest
        int_keys = []
        for k in ontology.raw_cost_per_size:
            try:
                int_keys.append((int(k), ontology.raw_cost_per_size[k]))
            except (ValueError, TypeError):
                pass
        if int_keys:
            nearest = min(int_keys, key=lambda x: abs(x[0] - account_size))
            ratio = account_size / max(nearest[0], 1)
            return nearest[1] * ratio
        ratio = account_size / max(ontology.account_size, 1)
        return ontology.eval_fee * ratio


@dataclass
class DeploymentDirective:
    """The final output of Phase 1: where to deploy, how much, and why."""
    firm_name: str
    strategy: str                       # SHALLOW_WELL, DEEP_WELL, or SKIP
    account_size: int
    quantity: int
    total_cost: float
    total_bandwidth: float
    pes_score: float
    coc: float
    crossover_threshold: int
    consistency_bypass: bool
    allowed_engines: list               # which CEREBUS engines work here
    lethal_constraints: list             # warnings
    monthly_yield_estimate: float
    notes: List[str]


class CapitalDeploymentRouter:
    """
    Master router. Takes firm ontologies + CEREBUS edge → ranked deployment directives.
    This is the Phase 1 output machine.
    """

    # CEREBUS composite edge (from backtest reports)
    DEFAULT_EDGE = {
        "win_rate": 0.857,           # Symmetry Trap 4Y
        "max_dd_pct": 0.05,
        "avg_trades_per_day": 2.0,
        "sharpe_ratio": 8.5,
        "profit_factor": 8.0,
        "monthly_r_multiple": 15.0,   # expected R per month
    }

    def __init__(self, edge: Optional[dict] = None):
        self.edge = edge or self.DEFAULT_EDGE
        self.ff_matrix = FFScalingMatrix()

    def generate_deployment_matrix(
        self,
        ontologies: List[PropFirmOntology],
        target_bandwidth: float = 50000.0,
    ) -> List[DeploymentDirective]:
        """
        Rank all prop firms and output optimal deployment directives.
        """
        directives = []

        for ont in ontologies:
            directive = self._evaluate_firm(ont, target_bandwidth)
            if directive:
                directives.append(directive)

        # Sort by PES descending
        directives.sort(key=lambda d: d.pes_score, reverse=True)
        return directives

    def _evaluate_firm(
        self,
        ont: PropFirmOntology,
        target_bandwidth: float,
    ) -> Optional[DeploymentDirective]:
        """Evaluate a single firm and produce a deployment directive."""

        if not ont.is_active:
            return None

        notes = []
        lethal_constraints = []
        allowed_engines = ["P90_CASCADE", "SYMMETRY_TRAP"]

        # === Constraint Analysis ===

        # Trailing DD lethality check
        if ont.is_trailing_lethal:
            lethal_constraints.append("INTRADAY_TETHER: Forces atomic scalps, no runners")
            allowed_engines = ["P90_CASCADE"]  # ST needs runners
            notes.append("Lethal trailing DD — scale out at 0.5 AU")

        # Consistency rule check
        bypass = False
        if ont.has_consistency_rule:
            if ont.max_single_day_profit_pct <= 0.30:
                bypass = True  # F&F can bypass
                notes.append("Consistency bypass available via F&F fragmentation")
            else:
                notes.append(f"Consistency cap: {ont.max_single_day_profit_pct:.0%} of total profit")

        # === F&F Fragmentation ===
        target_aum = int(target_bandwidth / max(ont.max_dd_pct, 0.01))
        ff_result = self.ff_matrix.find_optimal_fragmentation(
            ont,
            target_aum=min(target_aum, 100000),  # cap search space
            max_identities=10 if ont.ff_access else 1,
        )

        if ff_result is None:
            return None

        strategy = ff_result.strategy
        account_size = ff_result.account_size
        quantity = ff_result.quantity
        total_cost = ff_result.total_cost
        total_bandwidth = ff_result.total_bandwidth
        coc = ff_result.fleet_coc

        # === PES Calculation (simplified for Phase 1) ===
        wr = self.edge["win_rate"]
        monthly_r = self.edge["monthly_r_multiple"]
        velocity = 30.0 / max(ont.payout_cycle_days, 1)
        effective_leverage = account_size / max(ont.max_dd_amount, 1)

        numerator = effective_leverage * wr * velocity
        denominator = coc + (ont.variance_suppression_tax - 1.0) + (ont.capital_lockup_latency * 0.5)
        pes = numerator / max(denominator, 0.001)

        # === Crossover ===
        crossover = int(total_bandwidth * 2.5)  # rough: props optimal up to 2.5x bandwidth

        # === Monthly Yield Estimate ===
        monthly_yield = total_bandwidth * monthly_r * wr * 0.01  # scaled

        # === Skip logic ===
        if coc > 0.50:
            strategy = "SKIP"
            notes.append(f"CoC too high ({coc:.1%}) — not viable")

        if ff_result.coc_reduction_pct > 0:
            notes.append(f"F&F CoC reduction: {ff_result.coc_reduction_pct:.1f}%")

        return DeploymentDirective(
            firm_name=ont.firm_name,
            strategy=strategy,
            account_size=account_size,
            quantity=quantity,
            total_cost=total_cost,
            total_bandwidth=total_bandwidth,
            pes_score=round(pes, 4),
            coc=round(coc, 6),
            crossover_threshold=crossover,
            consistency_bypass=bypass,
            allowed_engines=allowed_engines,
            lethal_constraints=lethal_constraints,
            monthly_yield_estimate=round(monthly_yield, 2),
            notes=notes,
        )

    def to_json(self, directives: List[DeploymentDirective]) -> dict:
        """Serialize deployment matrix to JSON for output."""
        return {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
            "target_bandwidth": directives[0].total_bandwidth if directives else 0,
            "edge_metrics": self.edge,
            "directive_count": len(directives),
            "directives": [
                {
                    "rank": i + 1,
                    "firm": d.firm_name,
                    "strategy": d.strategy,
                    "account_size": d.account_size,
                    "quantity": d.quantity,
                    "total_cost": d.total_cost,
                    "total_bandwidth": d.total_bandwidth,
                    "pes_score": d.pes_score,
                    "coc": d.coc,
                    "crossover_threshold": d.crossover_threshold,
                    "consistency_bypass": d.consistency_bypass,
                    "allowed_engines": d.allowed_engines,
                    "lethal_constraints": d.lethal_constraints,
                    "monthly_yield_estimate": d.monthly_yield_estimate,
                    "notes": d.notes,
                }
                for i, d in enumerate(directives)
            ],
        }
