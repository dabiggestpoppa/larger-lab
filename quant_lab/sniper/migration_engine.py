"""
Fertile Soil Migration Engine - Phase 3
Monitors prop firm degradation and detects when to migrate capital to live accounts.

Migration triggers:
  1. Crossover: prop firm PES drops below live capital PES
  2. Toxic well: firm degradation signals (promo expired, rule changes, payout delays, patches)
  3. PES collapse: >30% PES drop in 30 days
  4. Monte Carlo: AUM growth trajectory crosses viability threshold

Migration is a ONE-WAY GATE: once capital moves to live, we do not go back.
The engine's job is to detect when staying in props costs more than leaving.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date, timedelta

from quant_lab.sniper.pes_calculator import PESCalculator, FirmProfile, EngineEdge, PESResult
from quant_lab.sniper.database import (
    get_connection,
    list_deployments,
    get_latest_snapshots,
    list_firms,
)


# ===========================================================
# 1. CROSSOVER DETECTOR
# ===========================================================

def crossover_detector(
    current_pes: float,
    live_pes: float,
    total_aum: float,
) -> dict:
    """
    Detects when prop firm PES drops below live capital PES.

    The crossover point formula:
        When (edge_prop × leverage_prop) < (edge_live × leverage_live)

    Calibrated range: ~$8K-$12K for CEREBUS edge (WR 85.7%, Sharpe 8.5).
    Higher WR -> props stay optimal longer.
    Degrading edge -> crossover comes sooner.

    Args:
        current_pes: Current PES score of the active prop deployment.
        live_pes: Equivalent PES of live capital at same risk level.
        total_aum: Total AUM currently deployed across prop firms.

    Returns:
        {
            status: "OPTIMAL" | "DEGRADED" | "CROSSOVER",
            crossover_aum: float,       # AUM threshold where live > prop
            recommendation: str
        }
    """
    # Base crossover range for reference edge (85.7% WR, Sharpe 8.5)
    base_crossover_low = 8000.0
    base_crossover_high = 12000.0

    # Derive edge quality from the PES ratio degradation
    # If current_pes is much lower than what our edge should produce,
    # the effective edge has degraded -> crossover comes sooner
    edge_ratio = current_pes / max(live_pes, 0.001)

    if edge_ratio >= 0.85:
        status = "OPTIMAL"
        # Within optimal band - props are still better
        crossover_aum = int(base_crossover_high * (1.0 + (edge_ratio - 0.85) * 2))
        recommendation = (
            f"Prop deployment optimal. Crossover at ${crossover_aum:,}. "
            f"Current AUM ${total_aum:,.0f} - {'within' if total_aum < crossover_aum else 'approaching'} safe zone."
        )
    elif edge_ratio >= 0.50:
        status = "DEGRADED"
        # Edge degrading - crossover is sooner
        degradation_factor = 1.0 - edge_ratio
        crossover_aum = int(base_crossover_low * (1.0 - degradation_factor))
        recommendation = (
            f"Prop edge degraded ({edge_ratio:.0%} of live PES). "
            f"Crossover threshold lowered to ${crossover_aum:,}. "
            f"{'Total AUM already past crossover - begin live migration.' if total_aum > crossover_aum else 'Monitor closely.'}"
        )
    else:
        status = "CROSSOVER"
        crossover_aum = int(base_crossover_low * 0.5)
        recommendation = (
            f"CROSSOVER TRIGGERED. Prop PES ({current_pes:.4f}) is "
            f"{edge_ratio:.0%} of live PES ({live_pes:.4f}). "
            f"Migrate capital to live accounts immediately. "
            f"Estimated drag of staying: ${(total_aum * 0.02):,.0f}/month."
        )

    return {
        "status": status,
        "crossover_aum": crossover_aum,
        "pes_ratio": round(edge_ratio, 4),
        "recommendation": recommendation,
    }


# ===========================================================
# 2. TOXIC WELL SCANNER
# ===========================================================

def toxic_well_scanner(active_deployments: list) -> list:
    """
    Scans active deployments for degradation signals.

    Toxicity signal weights (total = 100):
        patch_signal:      40  - firm patched/exploited the strategy
        promo_loss:        20  - promo expired or revoked
        rule_change:       20  - tighter trailing DD, stricter consistency, news restrictions
        pes_drop:          15  - PES dropped >20% from initial
        payout_delay:       5  - payout from PayoutJunction showing delays

    Action thresholds (toxicity_score):
        0-25:   MONITOR
        26-50:  SCALE_DOWN
        51-100: EXIT

    Args:
        active_deployments: list of dicts with keys:
            firm_name (str)
            pes_initial (float)
            pes_current (float)
            status (str) - "ACTIVE" | "PAUSED" | etc.
            Optional: promo_active (bool), rule_changed (bool),
                      patch_signal (bool), payout_delayed (bool)

    Returns:
        list of {firm_name, toxicity_score, signals, action}
    """
    PATCH_WEIGHT = 40
    PROMO_WEIGHT = 20
    RULE_WEIGHT = 20
    PES_WEIGHT = 15
    PAYOUT_WEIGHT = 5

    results = []

    for deployment in active_deployments:
        firm_name = deployment.get("firm_name", "Unknown")
        signals = []
        score = 0

        pes_initial = deployment.get("pes_initial", 0.0)
        pes_current = deployment.get("pes_current", 0.0)

        # ── Patch signal (weight: 40) ──
        if deployment.get("patch_signal", False):
            score += PATCH_WEIGHT
            signals.append("PATCH_SIGNAL: Strategy likely patched by firm")

        # ── Promo loss (weight: 20) ──
        promo_active = deployment.get("promo_active", None)
        if promo_active is False:
            score += PROMO_WEIGHT
            signals.append("PROMO_LOST: Active promo expired or revoked")
        elif promo_active is True and deployment.get("promo_expiring_soon", False):
            score += PROMO_WEIGHT // 2
            signals.append("PROMO_EXPIRING: Promo expires within 14 days")

        # ── Rule change (weight: 20) ──
        if deployment.get("rule_changed", False):
            score += RULE_WEIGHT
            rule_details = deployment.get("rule_change_details", "Unknown rule change")
            signals.append(f"RULE_CHANGE: {rule_details}")

        # ── PES drop (weight: 15) ──
        if pes_initial > 0:
            pes_drop_pct = (pes_initial - pes_current) / pes_initial
            if pes_drop_pct > 0.20:
                score += PES_WEIGHT
                signals.append(
                    f"PES_DROP: Score fell {pes_drop_pct:.0%} "
                    f"({pes_initial:.4f} -> {pes_current:.4f})"
                )
            elif pes_drop_pct > 0.10:
                score += PES_WEIGHT // 2
                signals.append(
                    f"PES_DECLINING: Score fell {pes_drop_pct:.0%} "
                    f"({pes_initial:.4f} -> {pes_current:.4f})"
                )

        # ── Payout delay (weight: 5) ──
        if deployment.get("payout_delayed", False):
            score += PAYOUT_WEIGHT
            delay_days = deployment.get("avg_payout_days", 0)
            signals.append(f"PAYOUT_DELAY: Avg payout taking {delay_days} days")

        # ── Determine action ──
        if score > 50:
            action = "EXIT"
        elif score > 25:
            action = "SCALE_DOWN"
        else:
            action = "MONITOR"

        results.append({
            "firm_name": firm_name,
            "toxicity_score": min(score, 100),
            "signals": signals,
            "action": action,
        })

    # Sort by toxicity descending - worst first
    results.sort(key=lambda r: r["toxicity_score"], reverse=True)
    return results


# ===========================================================
# 3. MONTE CARLO AUM PATH SIMULATOR
# ===========================================================

def monte_carlo_aum_path(
    initial_aum: float,
    wr: float = 0.857,
    edge_monthly_r: float = 15.0,
    months: int = 12,
    simulations: int = 1000,
) -> dict:
    """
    Monte Carlo simulation of AUM growth under prop firm constraints.

    Models:
        - Payout cycles (biweekly extraction, 14-day + 3-day buffer)
        - Consistency drag (max day caps reduce compounding)
        - Promo availability (refresh rate, F&F network depth)
        - Patch probability (increases over time - firms learn)

    Args:
        initial_aum: Starting AUM in USD.
        wr: Win rate (default 0.857 for CEREBUS Symmetry Trap).
        edge_monthly_r: Expected monthly R-multiple return.
        months: Simulation horizon.
        simulations: Number of Monte Carlo paths.

    Returns:
        {
            median_curve: list[float],   # median AUM at each month
            p10_curve: list[float],      # 10th percentile (bad case)
            p90_curve: list[float],      # 90th percentile (good case)
            ruin_probability: float,     # probability of drawdown > max allowed
            crossover_month: int | None  # month where live becomes better
        }
    """
    rng = np.random.default_rng(seed=42)

    # Model parameters
    payout_cycle_months = 14.0 / 30.0  # ~0.467 months per payout
    consistency_drag = 0.22  # 22% compounding reduction from consistency rules
    monthly_vol = edge_monthly_r * 0.35  # volatility of monthly returns
    patch_probability_annual = 0.15  # 15% chance per year a given prop firm patches
    patch_probability_monthly = 1.0 - (1.0 - patch_probability_annual) ** (1.0 / 12.0)

    # Crossover: live becomes better (calibrated ~$10K for ref edge)
    crossover_aum = 10000.0 * (wr / 0.857)

    # Pre-allocate: shape (simulations, months+1)
    paths = np.full((simulations, months + 1), initial_aum, dtype=np.float64)
    ruined = np.zeros(simulations, dtype=bool)
    crossover_month = np.full(simulations, -1, dtype=np.int32)

    for sim in range(simulations):
        aum = initial_aum
        is_patched = False

        for month in range(1, months + 1):
            if ruined[sim]:
                paths[sim, month] = paths[sim, month - 1]
                continue

            # Monthly return: edge × consistency_drag × noise
            monthly_return = (
                edge_monthly_r
                * wr
                * (1.0 - consistency_drag)
                * (1.0 + rng.normal(0, monthly_vol / max(edge_monthly_r, 1)))
            )

            # Payout extraction: extract every payout cycle
            if month % max(1, int(payout_cycle_months * 2)) == 0:
                # Payouts extracted - AUM stays flat, capital moves to treasury
                pass
            else:
                aum += monthly_return

            # Patch check
            if not is_patched and rng.random() < patch_probability_monthly:
                is_patched = True
                aum *= 0.7  # 30% loss on patch (wipeout risk)
                if aum < initial_aum * 0.5:
                    ruined[sim] = True

            # Crossover check
            if crossover_month[sim] == -1 and aum > crossover_aum:
                crossover_month[sim] = month

            paths[sim, month] = max(aum, 0.0)

    # Percentile curves
    median_curve = np.median(paths, axis=0).tolist()
    p10_curve = np.percentile(paths, 10, axis=0).tolist()
    p90_curve = np.percentile(paths, 90, axis=0).tolist()

    ruin_probability = float(np.mean(ruined))

    # Crossover month: median across simulations that crossed
    crossed = crossover_month[crossover_month > 0]
    median_crossover = int(np.median(crossed)) if len(crossed) > 0 else None

    return {
        "median_curve": [round(v, 2) for v in median_curve],
        "p10_curve": [round(v, 2) for v in p10_curve],
        "p90_curve": [round(v, 2) for v in p90_curve],
        "ruin_probability": round(ruin_probability, 4),
        "crossover_month": median_crossover,
        "initial_aum": initial_aum,
        "simulations": simulations,
        "months": months,
    }


# ===========================================================
# 4. MIGRATION ALERT (MASTER FUNCTION)
# ===========================================================

def migration_alert(current_state: dict) -> dict:
    """
    Master function: combines crossover + toxic_well + MC simulation.

    Migration triggers (any one triggers alert):
        1. PES_prop < PES_live AND crossover_aum < current_AUM
        2. toxicity_score > 50
        3. PES dropped >30% in 30 days

    Args:
        current_state: dict with keys:
            current_pes (float)
            live_pes (float)
            total_aum (float)
            active_deployments (list) - for toxic_well_scanner
            pes_30_days_ago (float) - PES 30 days prior
            Optional: wr (float), edge_monthly_r (float)

    Returns:
        {
            alert: bool,
            urgency: "NONE" | "WATCH" | "ACT_NOW",
            actions: list[str],
            estimated_impact: float  # $/month impact if not migrated
        }
    """
    actions = []
    urgency = "NONE"
    estimated_impact = 0.0

    current_pes = current_state.get("current_pes", 0.0)
    live_pes = current_state.get("live_pes", 0.0)
    total_aum = current_state.get("total_aum", 0.0)
    active_deployments = current_state.get("active_deployments", [])
    pes_30_days_ago = current_state.get("pes_30_days_ago", current_pes)
    wr = current_state.get("wr", 0.857)
    edge_monthly_r = current_state.get("edge_monthly_r", 15.0)

    # ── Check 1: Crossover ──
    crossover = crossover_detector(current_pes, live_pes, total_aum)
    if crossover["status"] == "CROSSOVER":
        urgency = "ACT_NOW"
        actions.append(f"CROSSOVER: {crossover['recommendation']}")
    elif crossover["status"] == "DEGRADED":
        if urgency != "ACT_NOW":
            urgency = "WATCH"
        actions.append(f"DEGRADED: {crossover['recommendation']}")

    # ── Check 2: Toxic well scan ──
    if active_deployments:
        toxic_results = toxic_well_scanner(active_deployments)
        for result in toxic_results:
            if result["toxicity_score"] > 50:
                urgency = "ACT_NOW"
                actions.append(
                    f"EXIT {result['firm_name']}: toxicity={result['toxicity_score']}/100. "
                    f"Signals: {'; '.join(result['signals'])}"
                )
            elif result["toxicity_score"] > 25:
                if urgency != "ACT_NOW":
                    urgency = "WATCH"
                actions.append(
                    f"SCALE_DOWN {result['firm_name']}: toxicity={result['toxicity_score']}/100. "
                    f"Signals: {'; '.join(result['signals'])}"
                )

    # ── Check 3: PES crash in 30 days ──
    if pes_30_days_ago > 0:
        pes_change_pct = (pes_30_days_ago - current_pes) / pes_30_days_ago
        if pes_change_pct > 0.30:
            urgency = "ACT_NOW"
            actions.append(
                f"PES_CRASH: PES dropped {pes_change_pct:.0%} in 30 days "
                f"({pes_30_days_ago:.4f} -> {current_pes:.4f}). Immediate review required."
            )

    # ── Estimate impact ──
    if urgency != "NONE":
        # Drag = AUM × PES ratio degradation × monthly edge
        pes_ratio = current_pes / max(live_pes, 0.001)
        drag_factor = max(0.0, 1.0 - pes_ratio)
        estimated_impact = total_aum * drag_factor * (edge_monthly_r / 100.0) * wr

    # ── If no triggers but MC shows future crossover ──
    if urgency == "NONE" and total_aum > 0:
        try:
            mc = monte_carlo_aum_path(
                initial_aum=total_aum,
                wr=wr,
                edge_monthly_r=edge_monthly_r,
                months=6,
                simulations=500,
            )
            if mc["crossover_month"] is not None and mc["crossover_month"] <= 3:
                urgency = "WATCH"
                actions.append(
                    f"MC_FORECAST: Crossover projected in {mc['crossover_month']} months. "
                    f"Prepare live account setup."
                )
        except Exception:
            pass  # MC failure should not block the main alert

    alert = urgency != "NONE"

    return {
        "alert": alert,
        "urgency": urgency,
        "actions": actions,
        "estimated_impact": round(estimated_impact, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ===========================================================
# 5. WEEKLY REBALANCE CHECK
# ===========================================================

def weekly_rebalance_check() -> dict:
    """
    Weekly cron-triggered check.
    Re-runs PES for all active firms, compares against crossover threshold.

    Reads from the database (SQLite via database.py).
    Returns rebalancing recommendations.

    Returns:
        {
            check_date: str,
            firms_evaluated: int,
            recommendations: list[dict],
            summary: str
        }
    """
    today = date.today().isoformat()
    recommendations = []

    calculator = PESCalculator()
    deployments = list_deployments(status="ACTIVE")
    snapshots = get_latest_snapshots()

    # Build lookup from snapshots
    snapshot_lookup = {}
    for snap in snapshots:
        key = (snap.get("firm_name", ""), snap.get("account_size", 0))
        snapshot_lookup[key] = snap

    for deployment in deployments:
        firm_name = deployment.get("firm_name", "Unknown")
        account_size = deployment.get("account_size", 0)
        pes_score = deployment.get("pes_score", 0.0)
        crossover_threshold = deployment.get("crossover_threshold", 10000)
        total_cost = deployment.get("total_cost", 0)
        quantity = deployment.get("quantity", 1)

        total_deployed = account_size * quantity

        # Current PES approximation (from stored deployment data)
        current_pes = pes_score

        # Live PES at equivalent leverage
        live_leverage = 100.0  # reference
        edge = EngineEdge(
            win_rate=0.857,
            max_drawdown_pct=0.05,
            avg_trades_per_day=2.0,
            sharpe_ratio=8.5,
            profit_factor=8.0,
            instrument="ES",
        )
        firm = FirmProfile(
            name=firm_name,
            account_size=account_size,
            cost=total_cost / max(quantity, 1),
            max_daily_loss_pct=0.05,
            max_trailing_dd_pct=0.06,
            consistency_rule_max_day_pct=0.30,
            min_trading_days=5,
            payout_cycle_days=14,
            payout_buffer_days=3,
            scale_delay_days=30,
            scale_min_profit_pct=0.08,
            leverage_multiplier=live_leverage,
        )
        live_pes_result = calculator.full_pes(firm, edge)
        live_pes = live_pes_result.pes_score

        # Run crossover check
        cross = crossover_detector(current_pes, live_pes, total_deployed)

        if cross["status"] != "OPTIMAL":
            rec = {
                "firm_name": firm_name,
                "account_size": account_size,
                "quantity": quantity,
                "current_pes": round(current_pes, 4),
                "live_pes": round(live_pes, 4),
                "total_deployed": total_deployed,
                "crossover_aum": cross["crossover_aum"],
                "status": cross["status"],
                "recommendation": cross["recommendation"],
            }
            recommendations.append(rec)

    # Sort by severity (DEGRADED first, then status alphabetical)
    recommendations.sort(key=lambda r: (0 if r["status"] == "CROSSOVER" else 1))

    firms_evaluated = len(deployments)
    degraded_count = sum(1 for r in recommendations if r["status"] == "DEGRADED")
    crossover_count = sum(1 for r in recommendations if r["status"] == "CROSSOVER")

    if crossover_count > 0:
        summary = (
            f"ALERT: {crossover_count}/{firms_evaluated} firms past crossover threshold. "
            f"Recommend immediate capital migration."
        )
    elif degraded_count > 0:
        summary = (
            f"WARNING: {degraded_count}/{firms_evaluated} firms showing PES degradation. "
            f"Scale down positions and prepare live accounts."
        )
    else:
        summary = (
            f"ALL CLEAR: {firms_evaluated} firms evaluated. "
            f"All prop deployments remain optimal."
        )

    return {
        "check_date": today,
        "firms_evaluated": firms_evaluated,
        "degraded_count": degraded_count,
        "crossover_count": crossover_count,
        "recommendations": recommendations,
        "summary": summary,
    }
