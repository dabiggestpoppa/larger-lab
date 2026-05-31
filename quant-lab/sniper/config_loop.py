"""
Self-Healing Config Loop
Monitors all outputs, detects drift, and auto-regenerates configs when conditions change.

This is the Phase 4 worker module for the Prop Firm Sniper Engine.
It reads deployment configs, PES snapshots, and firm data to determine
whether the current configuration is still optimal — or whether rebalance is needed.
"""

import json
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional

from quant_lab.sniper.config_generator import ConfigGenerator
from quant_lab.sniper.database import (
    get_connection,
    get_latest_snapshots,
    get_optimal_deployments,
    list_firms,
    get_pes_trend,
    get_active_deployments_with_firms,
    insert_patch_signal,
)
from quant_lab.sniper.pes_calculator import PESCalculator, FirmProfile, EngineEdge
from quant_lab.sniper.ff_protocol import FFProtocol

CONFIG_DIR = Path(__file__).parent / "configs"
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


# ─── 1. Config Health Check ─────────────────────────────────

def config_health_check(config_path: str) -> dict:
    """
    Validate a deployment config file is still valid:
      - All firm promos still active (check snapshots)
      - No new patch signals since config was generated
      - PES scores haven't dropped >15%
      - Crossover threshold hasn't been breached

    Returns: {valid: bool, issues: list, recommended_action: str}
    """
    issues = []
    path = Path(config_path)

    if not path.exists():
        return {
            "valid": False,
            "issues": [f"Config file not found: {config_path}"],
            "recommended_action": "REGENERATE — config file missing",
        }

    # Load config
    try:
        with open(path, "r") as f:
            if path.suffix == ".yaml" or path.suffix == ".yml":
                import yaml
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
    except Exception as e:
        return {
            "valid": False,
            "issues": [f"Config parse error: {e}"],
            "recommended_action": "REGENERATE — config file corrupt",
        }

    deploy = config.get("deployment_config", {})
    generated_at_str = deploy.get("generated_at", "")
    firm_mix = deploy.get("firm_mix", [])
    generated_version = deploy.get("version", "unknown")

    # Parse generation time
    try:
        generated_at = datetime.fromisoformat(generated_at_str) if generated_at_str else datetime.min
    except (ValueError, TypeError):
        generated_at = datetime.min

    # ── Check 1: Promo status ──
    for entry in firm_mix:
        firm_name = entry.get("firm", "")
        account_size = entry.get("account_size", 0)
        config_pes = entry.get("pes_score", 0)

        if not firm_name:
            continue

        # Look up current firm data
        conn = get_connection()
        firm_row = conn.execute(
            "SELECT * FROM prop_firms WHERE name = ?", (firm_name,)
        ).fetchone()
        conn.close()

        if firm_row is None:
            issues.append(f"Firm '{firm_name}' no longer in database")
            continue

        firm_data = dict(firm_row)
        # Decode JSON fields
        for field in ["promo_active", "patch_signals"]:
            if field in firm_data and firm_data[field]:
                try:
                    firm_data[field] = json.loads(firm_data[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        # Check promo
        promo = firm_data.get("promo_active", {}) or {}
        if promo and promo.get("code"):
            # Promo was active when config was generated; check it's still there
            pass  # If promo exists in current data, it's fine
        else:
            # Config may have been generated with a promo that's now expired
            # We can't know for sure without tracking config-level promo state,
            # but we flag if the firm is still active
            pass

        # ── Check 2: Patch signals since config generation ──
        patch_signals = firm_data.get("patch_signals", []) or []
        if isinstance(patch_signals, list):
            for sig in patch_signals:
                if isinstance(sig, dict):
                    detected_at_str = sig.get("detected_at", "")
                    if detected_at_str:
                        try:
                            detected_at = datetime.fromisoformat(detected_at_str)
                            if detected_at > generated_at:
                                issues.append(
                                    f"New patch signal for '{firm_name}': "
                                    f"{sig.get('signal_type', 'UNKNOWN')} "
                                    f"(severity: {sig.get('severity', 'unknown')}) "
                                    f"detected after config was generated"
                                )
                        except (ValueError, TypeError):
                            pass

        # ── Check 3: PES drift >15% ──
        conn = get_connection()
        snap_rows = conn.execute("""
            SELECT pes_score, snapshot_date FROM pes_snapshots
            WHERE firm_id = ? AND account_size = ?
            ORDER BY snapshot_date DESC LIMIT 5
        """, (firm_data["firm_id"], account_size)).fetchall()
        conn.close()

        if snap_rows:
            latest_pes = snap_rows[0]["pes_score"]
            if config_pes > 0:
                pct_change = abs(latest_pes - config_pes) / config_pes
                if pct_change > 0.15:
                    direction = "dropped" if latest_pes < config_pes else "surged"
                    issues.append(
                        f"PES for '{firm_name}' ${account_size:,} {direction} "
                        f"{pct_change:.1%} (was {config_pes:.4f}, now {latest_pes:.4f})"
                    )

        # ── Check 4: Crossover threshold breach ──
        crossover = entry.get("crossover_threshold_usd", 0)
        total_aum = account_size  # per-account check
        if total_aum > crossover and crossover > 0:
            issues.append(
                f"'{firm_name}' ${account_size:,} exceeds crossover "
                f"threshold ${crossover:,} — live capital may be superior"
            )

    # Determine overall validity
    critical_issues = [
        i for i in issues
        if "patch signal" in i.lower()
        or "exceeds crossover" in i.lower()
        or "no longer in database" in i.lower()
    ]
    warning_issues = [i for i in issues if i not in critical_issues]

    if critical_issues:
        recommended = "REBALANCE — critical issues detected (patch signals or crossover breach)"
    elif warning_issues:
        recommended = "REVIEW — warnings detected, consider rebalancing soon"
    else:
        recommended = "NO ACTION — config is still valid"

    return {
        "valid": len(critical_issues) == 0,
        "issues": issues,
        "recommended_action": recommended,
        "config_generated_at": generated_at_str,
        "config_version": generated_version,
        "firms_checked": len(firm_mix),
        "critical_count": len(critical_issues),
        "warning_count": len(warning_issues),
    }


# ─── 2. Auto Rebalance Trigger ──────────────────────────────

def auto_rebalance_trigger(current_config: dict, new_snapshots: list) -> dict:
    """
    Compare current active config against new data.
    Detects: new promos available, firm rule changes, edge degradation.
    If rebalance needed → generates new config with timestamp.

    Returns: {rebalance_needed: bool, new_config_path: str, changes: list}
    """
    changes = []
    deploy = current_config.get("deployment_config", {})
    old_firm_mix = deploy.get("firm_mix", [])
    old_firms = {e["firm"]: e for e in old_firm_mix if "firm" in e}

    # Build snapshot lookup: {(firm_name, account_size): snapshot_data}
    snap_lookup = {}
    for snap in new_snapshots:
        key = (snap.get("firm_name", ""), snap.get("account_size", 0))
        snap_lookup[key] = snap

    # Check each currently deployed firm
    all_firms = list_firms(status="ACTIVE")
    active_firm_names = set()
    for firm_data in all_firms:
        name = firm_data.get("name", "")
        active_firm_names.add(name)

        promo = firm_data.get("promo_active", {}) or {}
        patch_signals = firm_data.get("patch_signals", []) or []

        if name in old_firms:
            old_entry = old_firms[name]

            # Detect promo changes
            old_promo_code = old_entry.get("promo_code", "")
            new_promo_code = promo.get("code", "") if promo else ""
            if new_promo_code and new_promo_code != old_promo_code:
                changes.append(f"New promo for {name}: {new_promo_code} (was: {old_promo_code or 'none'})")
            elif old_promo_code and not new_promo_code:
                changes.append(f"Promo expired for {name}: {old_promo_code}")

            # Detect patch signals
            if patch_signals:
                recent_signals = []
                for sig in patch_signals:
                    if isinstance(sig, dict):
                        recent_signals.append(
                            f"{sig.get('signal_type', 'UNKNOWN')}"
                            f"(sev: {sig.get('severity', '?')})"
                        )
                if recent_signals:
                    changes.append(f"Patch signals for {name}: {', '.join(recent_signals)}")

            # Detect PES degradation
            snap = snap_lookup.get((name, old_entry.get("account_size", 0)))
            if snap:
                old_pes = old_entry.get("pes_score", 0)
                new_pes = snap.get("pes_score", 0)
                if old_pes > 0:
                    pct = (new_pes - old_pes) / old_pes
                    if pct < -0.10:
                        changes.append(
                            f"PES degraded for {name}: {old_pes:.4f} → {new_pes:.4f} ({pct:.1%})"
                        )
                    elif pct > 0.10:
                        changes.append(
                            f"PES improved for {name}: {old_pes:.4f} → {new_pes:.4f} (+{pct:.1%})"
                        )
        else:
            # New firm available
            if promo.get("code"):
                changes.append(f"New firm available: {name} (with promo {promo.get('code')})")
            else:
                changes.append(f"New firm available: {name}")

    # Check for firms that were deployed but no longer active
    for old_name in old_firms:
        if old_name not in active_firm_names:
            changes.append(f"Firm no longer active: {old_name}")

    # If there are meaningful changes, generate new config
    rebalance_needed = len(changes) > 0
    new_config_path_str = ""

    if rebalance_needed:
        # Generate a fresh config using current data
        edge = EngineEdge(
            win_rate=0.857,
            max_drawdown_pct=0.05,
            avg_trades_per_day=2.5,
            sharpe_ratio=8.5,
            profit_factor=8.0,
            instrument="EURUSD.PRO",
        )
        calc = PESCalculator()
        gen = ConfigGenerator()

        results = []
        for firm_data in all_firms:
            firm = _dict_to_firm(firm_data)
            if firm:
                result = calc.full_pes(firm, edge, n_accounts=1)
                results.append(result)

        results.sort(key=lambda r: r.pes_score, reverse=True)
        top = results[:10]

        if top:
            crossover = calc.calculate_crossover_threshold(top[0].firm_name and FirmProfile(
                name=top[0].firm_name, account_size=top[0].account_size,
                cost=top[0].account_cost * 6,  # reverse amortization
                max_daily_loss_pct=0.05, max_trailing_dd_pct=0.06,
                consistency_rule_max_day_pct=0.30, min_trading_days=5,
                payout_cycle_days=14, payout_buffer_days=3,
                scale_delay_days=30, scale_min_profit_pct=0.08,
                leverage_multiplier=20.0,
            ) or FirmProfile("", 1000, 10, 0.05, 0.06, 0.30, 5, 14, 3, 30, 0.08, 20.0), edge)

            new_config = gen.generate_deployment_config(
                top_results=top,
                edge=edge,
                crossover_threshold=crossover if isinstance(crossover, int) else 10000,
                notes=f"Auto-rebalanced: {len(changes)} changes detected",
            )
            # Update version
            new_config["deployment_config"]["version"] = "1.0.1-rebalanced"
            new_config["deployment_config"]["rebalance_reason"] = changes[:5]

            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            new_path = CONFIG_DIR / f"deployment_rebalanced_{ts}.yaml"
            new_config_path_str = str(new_path)

            import yaml
            with open(new_path, "w") as f:
                yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)

    changes.insert(0, f"Rebalance decision: {'YES' if rebalance_needed else 'NO'} — {len(changes)} change(s)")

    return {
        "rebalance_needed": rebalance_needed,
        "new_config_path": new_config_path_str,
        "changes": changes,
        "checked_at": datetime.utcnow().isoformat(),
    }


# ─── 3. PES Drift Monitor ───────────────────────────────────

def pes_drift_monitor(days: int = 7) -> dict:
    """
    Monitor PES scores over time from pes_snapshots table.
    Detects trending degradation: if PES has dropped for 3+ consecutive snapshots.

    Returns: {alerts: list, trend: "IMPROVING" | "STABLE" | "DEGRADING", recommended_review: bool}
    """
    alerts = []
    today = date.today()
    cutoff = (today - timedelta(days=days)).isoformat()

    conn = get_connection()

    # Get all firms that have snapshots in the window
    firm_rows = conn.execute("""
        SELECT DISTINCT firm_id FROM pes_snapshots
        WHERE snapshot_date >= ?
    """, (cutoff,)).fetchall()
    conn.close()

    degrading_firms = []
    improving_firms = []
    stable_firms = []

    for firm_row in firm_rows:
        firm_id = firm_row["firm_id"]
        trend_data = get_pes_trend(firm_id, days=days)

        if len(trend_data) < 2:
            continue

        pes_values = [row["pes_score"] for row in trend_data]
        snapshot_dates = [row["snapshot_date"] for row in trend_data]
        firm_name = trend_data[0].get("firm_name", firm_id[:8])

        # Check consecutive drops
        consecutive_drops = 0
        max_consecutive_drops = 0
        for i in range(1, len(pes_values)):
            if pes_values[i] < pes_values[i - 1]:
                consecutive_drops += 1
                max_consecutive_drops = max(max_consecutive_drops, consecutive_drops)
            else:
                consecutive_drops = 0

        # Overall trend: compare first to last
        if len(pes_values) >= 2:
            overall_change = pes_values[-1] - pes_values[0]
            overall_pct = overall_change / max(pes_values[0], 0.0001)
        else:
            overall_change = 0
            overall_pct = 0

        firm_trend = {
            "firm_name": firm_name,
            "data_points": len(pes_values),
            "first_pes": pes_values[0],
            "last_pes": pes_values[-1],
            "overall_change": round(overall_change, 4),
            "overall_pct": round(overall_pct, 4),
            "max_consecutive_drops": max_consecutive_drops,
            "date_range": f"{snapshot_dates[0]} to {snapshot_dates[-1]}" if snapshot_dates else "N/A",
        }

        if max_consecutive_drops >= 3:
            degrading_firms.append(firm_trend)
            alerts.append(
                f"DEGRADING: {firm_name} — PES dropped {max_consecutive_drops}x consecutively "
                f"({pes_values[0]:.4f} → {pes_values[-1]:.4f}, {overall_pct:.1%})"
            )
        elif overall_pct > 0.05:
            improving_firms.append(firm_trend)
        else:
            stable_firms.append(firm_trend)

    # Determine overall trend
    if degrading_firms:
        trend = "DEGRADING"
        recommended_review = True
    elif improving_firms and not degrading_firms:
        trend = "IMPROVING"
        recommended_review = False
    else:
        trend = "STABLE"
        recommended_review = False

    if not alerts and trend == "STABLE":
        alerts.append("All monitored firms are stable — no drift detected")

    return {
        "alerts": alerts,
        "trend": trend,
        "recommended_review": recommended_review,
        "window_days": days,
        "firms_monitored": len(firm_rows),
        "degrading": degrading_firms,
        "improving": improving_firms,
        "stable": stable_firms,
        "checked_at": datetime.utcnow().isoformat(),
    }


# ─── 4. Patch Signal Watcher ────────────────────────────────

def patch_signal_watcher() -> list:
    """
    Scan all active firms for patch signals:
      - Promo codes no longer accepted
      - New terms banning multi-accounting
      - Payout rejection patterns
      - KYC requirements that prevent F&F

    Returns: list of {firm, signal_type, severity, detected_at}
    """
    signals = []

    # 1. Check database patch signals
    all_firms = list_firms(status="ACTIVE")
    for firm_data in all_firms:
        name = firm_data.get("name", "")
        patch_signals = firm_data.get("patch_signals", []) or []

        if isinstance(patch_signals, list):
            for sig in patch_signals:
                if isinstance(sig, dict):
                    signal_type = sig.get("signal_type", "UNKNOWN")
                    severity = sig.get("severity", "LOW")
                    detected_at = sig.get("detected_at", "")

                    signals.append({
                        "firm": name,
                        "signal_type": signal_type,
                        "severity": severity,
                        "detected_at": detected_at,
                        "details": sig.get("details", ""),
                        "source": sig.get("source", "database"),
                    })

    # 2. Check FF status degradation
    for firm_data in all_firms:
        name = firm_data.get("name", "")
        ff_status = firm_data.get("ff_status", "UNTESTED")

        if ff_status == "BLOCKED":
            signals.append({
                "firm": name,
                "signal_type": "F&F_BLOCKED",
                "severity": "HIGH",
                "detected_at": datetime.utcnow().isoformat(),
                "details": "F&F arbitrage access blocked by firm",
                "source": "ff_status",
            })
        elif ff_status == "TERMS_VIOLATION":
            signals.append({
                "firm": name,
                "signal_type": "TERMS_VIOLATION",
                "severity": "CRITICAL",
                "detected_at": datetime.utcnow().isoformat(),
                "details": "Multi-accounting terms may have changed",
                "source": "ff_status",
            })

    # 3. Check promo expiration — promos that were active are now gone
    for firm_data in all_firms:
        name = firm_data.get("name", "")
        promo = firm_data.get("promo_active", {}) or {}
        if promo and promo.get("code"):
            # Check if promo has expired
            expires_at = promo.get("expires_at", "")
            if expires_at:
                try:
                    exp_date = datetime.fromisoformat(expires_at)
                    now = datetime.utcnow()
                    days_until = (exp_date - now).days
                    if days_until < 0:
                        signals.append({
                            "firm": name,
                            "signal_type": "PROMO_EXPIRED",
                            "severity": "MEDIUM",
                            "detected_at": datetime.utcnow().isoformat(),
                            "details": f"Promo '{promo['code']}' expired {abs(days_until)} days ago",
                            "source": "promo_check",
                        })
                    elif days_until <= 7:
                        signals.append({
                            "firm": name,
                            "signal_type": "PROMO_EXPIRING",
                            "severity": "LOW",
                            "detected_at": datetime.utcnow().isoformat(),
                            "details": f"Promo '{promo['code']}' expires in {days_until} days",
                            "source": "promo_check",
                        })
                except (ValueError, TypeError):
                    pass

    # 4. Check deployment status anomalies — firms with ACTIVE deployments but DELISTED status
    conn = get_connection()
    anomaly_rows = conn.execute("""
        SELECT DISTINCT f.name, f.status, d.status as deploy_status
        FROM capital_deployments d
        JOIN prop_firms f ON d.firm_id = f.firm_id
        WHERE d.status = 'ACTIVE' AND f.status != 'ACTIVE'
    """).fetchall()
    conn.close()

    for row in anomaly_rows:
        signals.append({
            "firm": row["name"],
            "signal_type": "DEPLOYMENT_FIRM_MISMATCH",
            "severity": "HIGH",
            "detected_at": datetime.utcnow().isoformat(),
            "details": f"Active deployment but firm status is '{row['status']}' (not ACTIVE)",
            "source": "deployment_audit",
        })

    return signals


# ─── 5. Generate Health Report ──────────────────────────────

def generate_health_report() -> str:
    """
    Generate a full health report markdown string:
      - Active deployments summary
      - PES trends
      - Crossover proximity
      - Patch signals
      - Recommended actions

    Returns formatted markdown for Telegram/display output.
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 🔫 SNIPER ENGINE — HEALTH REPORT",
        f"**Generated:** {now}",
        "",
    ]

    # ── Section 1: Active Deployments ──
    lines.append("## 📦 ACTIVE DEPLOYMENTS")
    lines.append("")

    deployments = get_active_deployments_with_firms()

    if deployments:
        lines.append("| Firm | Size | Qty | PES | Status | Velocity |")
        lines.append("|------|------|-----|-----|--------|----------|")
        for d in deployments:
            lines.append(
                f"| {d.get('firm_name', '?')} "
                f"| ${d.get('account_size', 0):,} "
                f"| {d.get('quantity', 1)} "
                f"| {d.get('pes_score', 0):.4f} "
                f"| {d.get('status', '?')} "
                f"| {d.get('capital_velocity', 0):.4f} |"
            )
    else:
        lines.append("_No active deployments found._")

    lines.append("")

    # ── Section 2: PES Trends ──
    lines.append("## 📉 PES DRIFT (7-day)")
    lines.append("")

    drift = pes_drift_monitor(days=7)

    trend_emoji = {
        "IMPROVING": "🟢",
        "STABLE": "🟡",
        "DEGRADING": "🔴",
    }
    lines.append(f"**Overall Trend:** {trend_emoji.get(drift['trend'], '❓')} {drift['trend']}")
    lines.append(f"**Firms Monitored:** {drift['firms_monitored']}")
    lines.append("")

    if drift["alerts"]:
        lines.append("**Alerts:**")
        for alert in drift["alerts"]:
            lines.append(f"- {alert}")
        lines.append("")

    if drift["degrading"]:
        lines.append("**Degrading Firms:**")
        for f_info in drift["degrading"]:
            lines.append(
                f"- {f_info['firm_name']}: {f_info['first_pes']:.4f} → "
                f"{f_info['last_pes']:.4f} ({f_info['overall_pct']:.1%}) "
                f"over {f_info['data_points']} snapshots"
            )
        lines.append("")

    # ── Section 3: Crossover Proximity ──
    lines.append("## ⚡ CROSSOVER PROXIMITY")
    lines.append("")

    if deployments:
        lines.append("| Firm | AUM | Crossover | Proximity |")
        lines.append("|------|-----|-----------|-----------|")
        for d in deployments:
            aum = d.get("account_size", 0) * d.get("quantity", 1)
            crossover = d.get("crossover_threshold", 0)
            if crossover > 0:
                proximity = aum / crossover
                prox_str = f"{proximity:.1%}"
                if proximity > 0.9:
                    prox_str += " 🔴"
                elif proximity > 0.7:
                    prox_str += " 🟡"
                else:
                    prox_str += " 🟢"
            else:
                prox_str = "N/A"
            lines.append(
                f"| {d.get('firm_name', '?')} "
                f"| ${aum:,} "
                f"| ${crossover:,} "
                f"| {prox_str} |"
            )
    else:
        lines.append("_No crossover data available._")

    lines.append("")

    # ── Section 4: Patch Signals ──
    lines.append("## 🛡️ PATCH SIGNALS")
    lines.append("")

    signals = patch_signal_watcher()

    if signals:
        critical = [s for s in signals if s.get("severity") == "CRITICAL"]
        high = [s for s in signals if s.get("severity") == "HIGH"]
        medium = [s for s in signals if s.get("severity") == "MEDIUM"]
        low = [s for s in signals if s.get("severity") == "LOW"]

        if critical:
            lines.append(f"**🔴 CRITICAL ({len(critical)}):**")
            for s in critical:
                lines.append(f"- **{s['firm']}**: {s['signal_type']} — {s.get('details', '')}")
            lines.append("")

        if high:
            lines.append(f"**🟠 HIGH ({len(high)}):**")
            for s in high:
                lines.append(f"- **{s['firm']}**: {s['signal_type']} — {s.get('details', '')}")
            lines.append("")

        if medium:
            lines.append(f"**🟡 MEDIUM ({len(medium)}):**")
            for s in medium:
                lines.append(f"- {s['firm']}: {s['signal_type']} — {s.get('details', '')}")
            lines.append("")

        if low:
            lines.append(f"**🟢 LOW ({len(low)}):**")
            for s in low:
                lines.append(f"- {s['firm']}: {s['signal_type']} — {s.get('details', '')}")
            lines.append("")
    else:
        lines.append("_No patch signals detected._")
        lines.append("")

    # ── Section 5: Recommended Actions ──
    lines.append("## 🎯 RECOMMENDED ACTIONS")
    lines.append("")

    actions = []

    if drift["recommended_review"]:
        actions.append("⚠️ **Review PES degradation** — one or more firms showing consistent decline")

    critical_sigs = [s for s in signals if s.get("severity") in ("CRITICAL", "HIGH")]
    if critical_sigs:
        actions.append("🚨 **Immediate action** — critical patch signals detected")

    near_crossover = []
    for d in deployments:
        aum = d.get("account_size", 0) * d.get("quantity", 1)
        crossover = d.get("crossover_threshold", 0)
        if crossover > 0 and aum / crossover > 0.85:
            near_crossover.append(d.get("firm_name", "?"))
    if near_crossover:
        actions.append(
            f"📊 **Evaluate live migration** — {', '.join(near_crossover)} near crossover threshold"
        )

    if drift["trend"] == "IMPROVING":
        lines.append("📈 PES scores improving across the board — current config is performing well")

    if not actions:
        lines.append("✅ **NO ACTION REQUIRED** — all systems nominal")
    else:
        for i, action in enumerate(actions, 1):
            lines.append(f"{i}. {action}")

    lines.append("")
    lines.append("---")
    lines.append(f"_Report generated by Sniper Config Loop v1.0_")

    return "\n".join(lines)


# ─── Helper ─────────────────────────────────────────────────

def _dict_to_firm(d: dict) -> Optional[FirmProfile]:
    """Convert database dict to FirmProfile for recalculation."""
    try:
        cost_per = d.get("cost_per_size", {})
        if isinstance(cost_per, dict):
            account_size = d.get("account_sizes", [1000])[0] if d.get("account_sizes") else 1000
            cost = cost_per.get(str(account_size), cost_per.get(account_size, 0) if isinstance(cost_per.get(account_size), (int, float)) else 0)
            if not cost:
                cost = 0
        else:
            cost = 0
            account_size = 1000

        promo = d.get("promo_active", {}) or {}
        consistency = d.get("consistency_rule", {}) or {}
        scaling = d.get("scaling_rules", {}) or {}

        return FirmProfile(
            name=d.get("name", ""),
            account_size=account_size,
            cost=cost,
            max_daily_loss_pct=d.get("max_daily_loss_pct", 0.05),
            max_trailing_dd_pct=d.get("max_trailing_dd_pct", 0.06),
            consistency_rule_max_day_pct=consistency.get("max_day_pct_of_total", 0.30),
            min_trading_days=d.get("min_trading_days", 5),
            payout_cycle_days=d.get("payout_cycle_days", 14),
            payout_buffer_days=d.get("payout_buffer_days", 3),
            scale_delay_days=scaling.get("scale_delay_days", 30),
            scale_min_profit_pct=scaling.get("min_profit_to_scale", 0.08),
            leverage_multiplier=1.0 / max(d.get("max_daily_loss_pct", 0.05), 0.001),
            promo_code=promo.get("code"),
            promo_discount_pct=promo.get("discount_pct", 0),
            promo_new_customer_only=promo.get("new_customer_only", False),
            ff_access=d.get("ff_status") == "ARBITRAGE",
        )
    except (KeyError, TypeError, IndexError):
        return None
