"""
Prop Exploit Score (PES) Calculator
Core math engine for capital allocation optimization.

Meta equation:     Ω = (E × L × V) / (C × T × R)
PES formula:       PES = (EL × WRE × PFF) ÷ (AC + CD + SF + OC)
Capital velocity:  Vc = P / Δt
Alpha (deepest):   α = Extractable Capital Flow / Constraint Surface
Effective exposure: X = D × λ
Survival:           S = 1 - (1-p)^n
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class FirmProfile:
    """Complete prop firm profile for PES calculation."""
    name: str
    account_size: int
    cost: float
    max_daily_loss_pct: float
    max_trailing_dd_pct: float
    consistency_rule_max_day_pct: float  # e.g. 0.30 means max day < 30% of total
    min_trading_days: int
    payout_cycle_days: int
    payout_buffer_days: int
    scale_delay_days: int
    scale_min_profit_pct: float
    leverage_multiplier: float  # effective λ
    promo_code: Optional[str] = None
    promo_discount_pct: float = 0.0
    promo_new_customer_only: bool = False
    ff_access: bool = False


@dataclass
class EngineEdge:
    """CEREBUS engine edge metrics → Sniper inputs."""
    win_rate: float  # e.g. 0.857 for 85.7%
    max_drawdown_pct: float
    avg_trades_per_day: float
    sharpe_ratio: float
    profit_factor: float
    instrument: str  # "EURUSD.PRO", "USDCHF.PRO", etc.


@dataclass
class PESResult:
    """Full PES calculation result."""
    firm_name: str
    account_size: int
    effective_leverage: float
    win_rate_edge: float
    payout_frequency_factor: float
    account_cost: float
    consistency_drag: float
    scaling_friction: float
    opportunity_cost_live: float
    effective_exposure: float  # D × λ
    capital_velocity: float  # Vc = P / Ωt
    omega: float  # Ω meta score
    alpha: float  # extractable alpha score
    survival_probability: float  # S = 1-(1-p)^n
    pes_score: float  # final PES
    crossover_threshold: int  # AUM in USD where props < live
    is_optimal: bool
    notes: list[str]


class PESCalculator:
    """
    Calculates Prop Exploit Score and related metrics.
    All math derived from the ontology — no black boxes.
    """

    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate  # annual risk-free for opportunity cost

    def calculate_effective_leverage(self, firm: FirmProfile) -> float:
        """
        Notional exposure per $1 risk AFTER max daily loss + trailing DD + consistency caps.
        EL = account_size / (account_size × max_daily_loss_pct) adjusted for trailing DD
        """
        # Base effective leverage from daily loss limit
        base_el = 1.0 / firm.max_daily_loss_pct  # e.g. 1/0.05 = 20x

        # Trailing DD compression: trailing DD is tighter than static DD
        # If trailing DD < max allowed DD by X%, effective leverage is reduced
        trailing_dd_ratio = firm.max_trailing_dd_pct / (firm.max_daily_loss_pct * 2)  # rough estimate
        if trailing_dd_ratio < 1.0:
            base_el *= trailing_dd_ratio

        # Consistency cap reduces effective position sizing
        consistency_factor = 1.0 - (firm.consistency_rule_max_day_pct * 0.3)  # ~30% drag at 30% max day
        base_el *= max(consistency_factor, 0.3)  # floor at 30%

        return round(base_el, 2)

    def calculate_win_rate_edge(self, edge: EngineEdge, firm: FirmProfile) -> float:
        """
        Expected WR adjusted for firm-specific rule constraints.
        Some rules degrade edge more than others.
        """
        base_wr = edge.win_rate

        # Consistency rule degrades effective WR (harder to maintain streak)
        consistency_penalty = firm.consistency_rule_max_day_pct * 0.05  # ~1.5% at 30%
        adjusted_wr = base_wr - consistency_penalty

        # Trading frequency: if min_trading_days is high and your engine is selective
        frequency_factor = min(1.0, edge.avg_trades_per_day * firm.min_trading_days / 10)
        adjusted_wr *= frequency_factor

        return round(max(adjusted_wr, 0.1), 4)  # floor at 10%

    def calculate_payout_frequency_factor(self, firm: FirmProfile) -> float:
        """
        PFF = 1 / (payout_cycle_days + payout_buffer_days)
        Biweekly (14d) + 3d buffer = 1/17 = 0.059
        Monthly (30d) + 3d buffer = 1/33 = 0.030
        """
        total_days = firm.payout_cycle_days + firm.payout_buffer_days
        return round(1.0 / total_days, 4)

    def calculate_account_cost(self, firm: FirmProfile, expected_payouts_to_breakeven: int = 6) -> float:
        """
        Upfront fee amortized over expected payout cycles to breakeven.
        If promo applies, use discounted cost.
        Effective cost accounts for F&F access.
        """
        cost = firm.cost
        if firm.promo_code and (not firm.promo_new_customer_only or firm.ff_access):
            cost = cost * (1.0 - firm.promo_discount_pct)

        # Amortized cost per payout cycle
        return round(cost / expected_payouts_to_breakeven, 2)

    def calculate_consistency_drag(self, firm: FirmProfile) -> float:
        """
        Mathematical penalty from consistency rules.
        If max day must be <30% of total profit, caps optimal position sizing.
        Reduces geometric compounding rate by ~22% at 30% consistency rule.
        """
        # Linear approximation: drag = max_day_pct × 0.73 (calibrated from 30% → ~22% drag)
        drag = firm.consistency_rule_max_day_pct * 0.73
        return round(drag, 4)

    def calculate_scaling_friction(self, firm: FirmProfile) -> float:
        """
        Time delay + additional cost to scale up.
        Modeled as lost compounding periods.
        """
        if firm.scale_delay_days == 0:
            return 0.0

        # Friction = delay_days / 365 × required_profit_pct
        # If you need 8% profit to scale and wait 30 days:
        # Friction = 30/365 × 0.08 = 0.0066 per scaling event
        annual_friction = (firm.scale_delay_days / 365.0) * firm.scale_min_profit_pct
        return round(annual_friction, 4)

    def calculate_opportunity_cost(self, firm: FirmProfile, edge: EngineEdge) -> float:
        """
        What $X in a live account at equivalent leverage would generate
        in the same timeframe with no payout latency or consistency drag.

        OC = effective_risk_capital × risk_free_rate × (payout_latency / 365)
        This is the capital you're NOT deploying elsewhere.
        """
        effective_risk = firm.account_size * firm.max_daily_loss_pct
        live_leverage_return = effective_risk * self.risk_free_rate * (
            (firm.payout_cycle_days + firm.payout_buffer_days) / 365.0
        )
        return round(live_leverage_return, 2)

    def calculate_effective_exposure(self, firm: FirmProfile) -> float:
        """
        X = D × λ
        D = allowed drawdown (REAL capital)
        λ = leverage multiplier
        A $100K prop @ 5% DD = $5K effective risk bandwidth
        """
        dd = firm.account_size * firm.max_daily_loss_pct
        return round(dd * firm.leverage_multiplier, 2)

    def calculate_capital_velocity(self, firm: FirmProfile, edge: EngineEdge) -> float:
        """
        Vc = Extractable Payout / Payout Cycle Time
        Extractable payout = effective_risk × WR_edge × trades_per_cycle
        """
        effective_risk = firm.account_size * firm.max_daily_loss_pct
        trades_per_cycle = edge.avg_trades_per_day * firm.payout_cycle_days
        extractable_payout = effective_risk * edge.win_rate * trades_per_cycle * 0.01  # scaled
        total_time = firm.payout_cycle_days + firm.payout_buffer_days
        return round(extractable_payout / max(total_time, 1), 4)

    def calculate_alpha(self, firm: FirmProfile, edge: EngineEdge, pes_score: float) -> float:
        """
        Deepest layer: α = Extractable Capital Flow / Constraint Surface
        Constraint surface = sum of all friction terms
        Higher PES → higher alpha per unit constraint
        """
        dividend = self.calculate_capital_velocity(firm, edge) * edge.win_rate
        divisor = (
            self.calculate_account_cost(firm)
            + self.calculate_consistency_drag(firm)
            + self.calculate_scaling_friction(firm)
        )
        return round(dividend / max(divisor, 0.001), 4)

    def calculate_survival_probability(self, edge: EngineEdge, n_accounts: int = 1) -> float:
        """
        S = 1 - (1-p)^n
        p = success probability per account (mapped from WR)
        n = number of accounts
        More accounts = exponentially higher extraction survivability
        """
        # Map WR to success probability (conservative: WR × 0.85)
        p = edge.win_rate * 0.85
        s = 1.0 - math.pow(1.0 - p, n_accounts)
        return round(s, 4)

    def calculate_crossover_threshold(
        self, firm: FirmProfile, edge: EngineEdge, live_leverage: float = 100.0
    ) -> int:
        """
        At what total prop AUM does live capital become superior per unit risk?

        Solve: PES(prop_N_accounts) = PES(live_at_equivalent_risk)

        Calibrated baseline: ~$8K-$12K for typical CEREBUS edge (85% WR, 5% DD accounts)
        Scales dynamically with edge quality.
        """
        # Base crossover for reference edge (85% WR, $1K accounts, biweekly payout)
        base_crossover = 10000.0

        # Edge quality factor: higher WR → props stay optimal longer
        edge_factor = edge.win_rate / 0.85  # normalized to reference

        # Drawdown factor: tighter DD → accounts become expensive faster
        dd_factor = 0.05 / firm.max_daily_loss_pct  # normalized to reference

        # Live leverage comparison
        live_factor = firm.leverage_multiplier / live_leverage

        crossover = base_crossover * edge_factor * dd_factor * live_factor
        return int(max(crossover, 1000))  # floor at $1K

    def full_pes(
        self, firm: FirmProfile, edge: EngineEdge, n_accounts: int = 1
    ) -> PESResult:
        """
        Calculate complete PES for a (firm, account_size) combination.
        Returns PESResult with all intermediate values for transparency.
        """
        notes = []

        # Core components
        el = self.calculate_effective_leverage(firm)
        wre = self.calculate_win_rate_edge(edge, firm)
        pff = self.calculate_payout_frequency_factor(firm)
        ac = self.calculate_account_cost(firm)
        cd = self.calculate_consistency_drag(firm)
        sf = self.calculate_scaling_friction(firm)
        oc = self.calculate_opportunity_cost(firm, edge)

        # PES formula
        numerator = el * wre * pff
        denominator = ac + cd + sf + oc
        pes = round(numerator / max(denominator, 0.001), 4)

        # Derived metrics
        ee = self.calculate_effective_exposure(firm)
        vc = self.calculate_capital_velocity(firm, edge)

        # Meta equation: Ω = (E × L × V) / (C × T × R)
        numerator_meta = ee * el * vc
        denominator_meta = (firm.cost * (firm.payout_cycle_days + firm.payout_buffer_days) *
                          (cd + sf + 0.01))
        omega = round(numerator_meta / max(denominator_meta, 0.001), 4)

        # Alpha
        alpha = self.calculate_alpha(firm, edge, pes)

        # Survival
        survival = self.calculate_survival_probability(edge, n_accounts)

        # Crossover
        crossover = self.calculate_crossover_threshold(firm, edge)

        # Build notes
        if firm.promo_code and (not firm.promo_new_customer_only or firm.ff_access):
            notes.append(f"Promo '{firm.promo_code}' applied (-{firm.promo_discount_pct*100}%)")
        if firm.promo_new_customer_only and not firm.ff_access:
            notes.append(f"Promo NCO only — F&F access not confirmed")
        if cd > 0.15:
            notes.append(f"High consistency drag ({cd:.1%}) — caps compounding")
        if sf > 0.005:
            notes.append(f"Scaling friction elevated ({sf:.4f})")

        is_optimal = pes > 0.5  # configurable threshold

        return PESResult(
            firm_name=firm.name,
            account_size=firm.account_size,
            effective_leverage=el,
            win_rate_edge=wre,
            payout_frequency_factor=pff,
            account_cost=ac,
            consistency_drag=cd,
            scaling_friction=sf,
            opportunity_cost_live=oc,
            effective_exposure=ee,
            capital_velocity=vc,
            omega=omega,
            alpha=alpha,
            survival_probability=survival,
            pes_score=pes,
            crossover_threshold=crossover,
            is_optimal=is_optimal,
            notes=notes,
        )

    def multi_account_pes(
        self, firm: FirmProfile, edge: EngineEdge, quantities: list[int]
    ) -> dict[int, PESResult]:
        """
        Calculate PES for multiple account quantities.
        Used to find optimal quantity within crossover threshold.
        Returns {quantity: PESResult}
        """
        results = {}
        for qty in quantities:
            results[qty] = self.full_pes(firm, edge, n_accounts=qty)
        return results

    def find_optimal_quantity(
        self, firm: FirmProfile, edge: EngineEdge, max_accounts: int = 20
    ) -> tuple[int, PESResult]:
        """
        Find the optimal number of accounts for a given firm.
        Balances PES vs crossover threshold.
        Returns (optimal_qty, PESResult)
        """
        best_qty = 1
        best_pes = self.full_pes(firm, edge, 1)

        for qty in range(2, max_accounts + 1):
            total_aum = firm.account_size * qty
            result = self.full_pes(firm, edge, qty)

            # If beyond crossover, stop — live capital is better
            if total_aum > result.crossover_threshold:
                break

            if result.pes_score > best_pes.pes_score:
                best_qty = qty
                best_pes = result

        return best_qty, best_pes
