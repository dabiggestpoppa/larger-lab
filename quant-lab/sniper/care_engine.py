"""
CARE Engine — Capital Allocation & Resource Engine
Phase 2: Deployment Config Generator + Live Monitor

Functions:
  promo_verify        — verify promo codes against PropFirmMatch snapshots
  live_firm_monitor   — monitor firm state, detect changes, alert levels
  generate_deployment_config — full deployment config from ranked firms + edge
  run_scope           — SCAN → VERIFY → CALCULATE → RANK → CONFIG → OUTPUT

All outputs are YAML/JSON configs. This module does NOT trade.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .pes_calculator import PESCalculator, FirmProfile, EngineEdge
from .config_generator import ConfigGenerator
from .ff_protocol import FFProtocol, FFStatus, PromoDetails
from .database import get_firm_by_name, list_firms

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

# ─── DATA STRUCTURES ──────────────────────────────────────────

@dataclass
class PromoResult:
    """Result of promo verification."""
    valid: bool
    discount_pct: float
    new_customer_only: bool
    ff_eligible: bool
    expiry: Optional[str]
    reason: str = ""


@dataclass
class FirmAlert:
    """Live monitoring status for a single firm."""
    firm_name: str
    status: str            # ACTIVE / SUSPENDED / UNKNOWN
    active_promo: Optional[dict]
    rule_changes: list[str]
    alert_level: str       # OK / WATCH / PATCHED / SUSPENDED
    last_snapshot: Optional[str]
    prev_snapshot: Optional[str]
    details: dict = field(default_factory=dict)


# ─── KNOWN PATCH SIGNALS (promo codes known to be dead) ───────

KNOWN_INVALID_PROMOS = {
    # code_lower: reason
    "SUMMER20": "Expired seasonal promo — no longer valid",
    "WELCOME50": "Deprecated — replaced by current offer",
    "APEX30": "Requires new KYC via affiliate link; direct use fails",
}

# ─── MODULE 1: PROMO VERIFICATION ────────────────────────────

def promo_verify(promo_code: str, firm_name: str) -> PromoResult:
    """
    Verify a promo code against known active promos from PropFirmMatch snapshots.

    Strategy:
      1. Check KNOWN_INVALID_PROMOS (fast fail)
      2. Scan SNAPSHOT_DIR for propfirmmatch_*.json snapshots
      3. Look for promo code in the firm's promo data
      4. If found in latest snapshot → VALID with discounts from snapshot
      5. If not found in any snapshot → INVALID

    Returns PromoResult with full verification details.
    """
    if not promo_code:
        return PromoResult(
            valid=False,
            discount_pct=0.0,
            new_customer_only=False,
            ff_eligible=False,
            expiry=None,
            reason="Empty promo code",
        )

    code_upper = promo_code.strip().upper()

    # Step 1: Check known-invalid list
    if code_upper in KNOWN_INVALID_PROMOS:
        return PromoResult(
            valid=False,
            discount_pct=0.0,
            new_customer_only=False,
            ff_eligible=False,
            expiry=None,
            reason=KNOWN_INVALID_PROMOS[code_upper],
        )

    # Step 2: Scan snapshots
    if not SNAPSHOT_DIR.exists():
        return PromoResult(
            valid=False,
            discount_pct=0.0,
            new_customer_only=False,
            ff_eligible=False,
            expiry=None,
            reason=f"No snapshots directory found ({SNAPSHOT_DIR})",
        )

    snapshot_files = sorted(SNAPSHOT_DIR.glob("propfirmmatch_*.json"), reverse=True)
    if not snapshot_files:
        return PromoResult(
            valid=False,
            discount_pct=0.0,
            new_customer_only=False,
            ff_eligible=False,
            expiry=None,
            reason="No snapshot files available — run scraper first",
        )

    # Step 3: Search latest snapshots for the firm + promo
    firm_name_lower = firm_name.strip().lower()
    latest_match = None
    latest_time = None

    for snap_path in snapshot_files[:5]:  # search last 5 snapshots
        try:
            with open(snap_path) as f:
                snap = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        scraped_at = snap.get("scraped_at", "")
        firms = snap.get("firms", [])

        for f in firms:
            f_name = (f.get("name") or "").strip().lower()
            if f_name != firm_name_lower and firm_name_lower not in f_name:
                continue

            promo_data = f.get("promo") or {}
            snap_code = (promo_data.get("code") or "").strip().upper()
            if snap_code == code_upper:
                if latest_time is None or scraped_at > latest_time:
                    latest_time = scraped_at
                    latest_match = promo_data

    if latest_match:
        discount = latest_match.get("discount_pct", 0.0)
        # Normalize: if > 1, it's a percentage (50), not decimal (0.5)
        if discount > 1.0:
            discount = discount / 100.0
        return PromoResult(
            valid=True,
            discount_pct=discount,
            new_customer_only=latest_match.get("new_customer_only", True),
            ff_eligible=True,
            expiry=None,
            reason=f"Verified in snapshot from {latest_time}",
        )

    # Step 4: Check database for known promos (seeded firms)
    firm_db = get_firm_by_name(firm_name)
    if firm_db:
        promo_active = firm_db.get("promo_active") or {}
        if isinstance(promo_active, str):
            try:
                promo_active = json.loads(promo_active)
            except json.JSONDecodeError:
                promo_active = {}
        db_code = (promo_active.get("code") or "").strip().upper()
        if db_code == code_upper:
            discount = promo_active.get("discount_pct", 0.0)
            if discount > 1.0:
                discount = discount / 100.0
            return PromoResult(
                valid=True,
                discount_pct=discount,
                new_customer_only=promo_active.get("new_customer_only", True),
                ff_eligible=True,
                expiry=promo_active.get("expires_at"),
                reason=f"Verified in database (seeded data)",
            )

    return PromoResult(
        valid=False,
        discount_pct=0.0,
        new_customer_only=False,
        ff_eligible=False,
        expiry=None,
        reason=f"Code '{code_upper}' not found in any snapshot or database for firm '{firm_name}'",
    )


# ─── MODULE 2: LIVE FIRM MONITOR ─────────────────────────────

def live_firm_monitor(firm_name: str) -> dict:
    """
    Monitor current state of a prop firm: active promos, rule changes, alerts.

    Compares latest vs previous snapshot to detect changes.

    Alert levels:
      OK        — no changes detected
      WATCH     — minor changes (pricing, metadata)
      PATCHED   — critical changes (rules, backdoor closed)
      SUSPENDED — firm status is not ACTIVE

    Returns FirmAlert dict with full state.
    """
    if not SNAPSHOT_DIR.exists():
        return {
            "firm_name": firm_name,
            "status": "UNKNOWN",
            "active_promo": None,
            "rule_changes": [],
            "alert_level": "OK",
            "last_snapshot": None,
            "prev_snapshot": None,
            "details": {"reason": "No snapshots directory found"},
        }

    snapshot_files = sorted(SNAPSHOT_DIR.glob("propfirmmatch_*.json"), reverse=True)
    firm_name_lower = firm_name.strip().lower()

    latest_firm_data = None
    prev_firm_data = None
    latest_snap_time = None
    prev_snap_time = None

    for snap_path in snapshot_files:
        try:
            with open(snap_path) as f:
                snap = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        scraped_at = snap.get("scraped_at", "")
        for f in snap.get("firms", []):
            f_name = (f.get("name") or "").strip().lower()
            if f_name == firm_name_lower or firm_name_lower in f_name:
                if latest_firm_data is None:
                    latest_firm_data = f
                    latest_snap_time = scraped_at
                elif prev_firm_data is None:
                    prev_firm_data = f
                    prev_snap_time = scraped_at
                    break  # found both

    # Also check database for baseline
    firm_db = get_firm_by_name(firm_name)

    if latest_firm_data is None and firm_db:
        # Use database as fallback baseline
        promo_active = firm_db.get("promo_active") or {}
        if isinstance(promo_active, str):
            try:
                promo_active = json.loads(promo_active)
            except json.JSONDecodeError:
                promo_active = {}

        alert_level = "OK"
        rule_changes = []
        status = firm_db.get("status", "ACTIVE")
        if status != "ACTIVE":
            alert_level = "SUSPENDED"

        return {
            "firm_name": firm_name,
            "status": status,
            "active_promo": promo_active if promo_active.get("code") else None,
            "rule_changes": rule_changes,
            "alert_level": alert_level,
            "last_snapshot": None,
            "prev_snapshot": None,
            "details": {
                "source": "database",
                "ff_status": firm_db.get("ff_status", "UNTESTED"),
                "account_sizes": firm_db.get("account_sizes", []),
                "payout_cycle_days": firm_db.get("payout_cycle_days", 14),
                "max_daily_loss_pct": firm_db.get("max_daily_loss_pct", 0.05),
            },
        }

    if latest_firm_data is None:
        return {
            "firm_name": firm_name,
            "status": "UNKNOWN",
            "active_promo": None,
            "rule_changes": [],
            "alert_level": "OK",
            "last_snapshot": None,
            "prev_snapshot": None,
            "details": {"reason": f"No data found for '{firm_name}' in any snapshot or database"},
        }

    # Compare snapshots for changes
    rule_changes = []
    alert_level = "OK"

    if prev_firm_data and latest_firm_data:
        # Promo changes
        lp = latest_firm_data.get("promo") or {}
        pp = prev_firm_data.get("promo") or {}
        if lp != pp:
            old_code = pp.get("code", "none")
            new_code = lp.get("code", "none")
            old_pct = pp.get("discount_pct", 0)
            new_pct = lp.get("discount_pct", 0)
            rule_changes.append(f"Promo changed: {old_code} (-{old_pct}%) → {new_code} (-{new_pct}%)")
            alert_level = "WATCH"

        # Drawdown changes
        ldd = latest_firm_data.get("drawdown") or {}
        pdd = prev_firm_data.get("drawdown") or {}
        if ldd != pdd:
            rule_changes.append(f"Drawdown rules changed: {pdd} → {ldd}")
            alert_level = "PATCHED"  # DD changes are critical

        # Consistency rule changes
        lc = latest_firm_data.get("consistency") or {}
        pc = prev_firm_data.get("consistency") or {}
        if lc != pc:
            rule_changes.append(f"Consistency rules changed: {pc} → {lc}")
            alert_level = "WATCH"

        # Payout changes
        lpo = latest_firm_data.get("payout") or {}
        ppo = prev_firm_data.get("payout") or {}
        if lpo != ppo:
            rule_changes.append(f"Payout terms changed: {ppo} → {lpo}")
            alert_level = "WATCH"

    # Determine status
    status = "ACTIVE"
    ff_status = latest_firm_data.get("ff_status", "UNTESTED")
    if ff_status == "PATCHED":
        alert_level = "PATCHED"
        rule_changes.append("F&F backdoor marked as PATCHED")

    result = {
        "firm_name": firm_name,
        "status": status,
        "active_promo": latest_firm_data.get("promo") or None,
        "rule_changes": rule_changes,
        "alert_level": alert_level,
        "last_snapshot": latest_snap_time,
        "prev_snapshot": prev_snap_time,
        "details": {
            "rating": latest_firm_data.get("rating"),
            "max_allocation": latest_firm_data.get("max_allocation"),
            "platforms": latest_firm_data.get("platforms", []),
            "instruments": latest_firm_data.get("instruments", []),
            "ff_status": ff_status,
            "drawdown": latest_firm_data.get("drawdown", {}),
            "consistency": latest_firm_data.get("consistency", {}),
            "payout": latest_firm_data.get("payout", {}),
        },
    }

    return result


# ─── MODULE 3: DEPLOYMENT CONFIG GENERATOR ───────────────────

def generate_deployment_config(firm_results: list, edge: dict) -> dict:
    """
    Takes ranked firm results + CEREBUS edge metrics.
    Returns full deployment config dict.

    Parameters:
      firm_results: list of dicts, each with keys:
        firm_name, alert_level, promo_code, promo_discount, ff_eligible,
        account_size, payout_cycle_days, etc.
        (from live_firm_monitor output or direct firm data)
      edge: dict with CEREBUS edge keys:
        win_rate, sharpe_ratio, avg_trades_per_day, etc.

    Returns full deployment_config dict ready for YAML/JSON serialization.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Determine crossover threshold from edge
    crossover_base = 10000
    wr = edge.get("win_rate", 0.857)
    edge_factor = wr / 0.857
    crossover_threshold = int(crossover_base * edge_factor)

    # Build firm mix
    firm_mix = []
    risk_per_trade = 0.01  # default 1% risk per trade
    max_correlated_exposure = 0
    notes = []

    for i, fr in enumerate(firm_results):
        if not isinstance(fr, dict):
            continue

        firm_name = fr.get("firm_name", f"unknown_{i}")
        alert_level = fr.get("alert_level", "OK")

        # Skip if suspended or patched (unless CARE_OPTIMAL override)
        if alert_level == "SUSPENDED":
            notes.append(f"SKIPPED {firm_name}: suspended")
            continue

        # Determine strategy
        ff_eligible = fr.get("ff_eligible", False)
        promo_code = fr.get("promo_code")
        alert = fr.get("alert_level", "OK")

        if alert == "PATCHED":
            strategy = "STANDARD"
            notes.append(f"{firm_name}: F&F backdoor patched — falling back to STANDARD")
        elif ff_eligible and promo_code:
            strategy = "CARE_OPTIMAL"
        elif ff_eligible:
            strategy = "F&F"
        elif promo_code:
            strategy = "STANDARD"
        else:
            strategy = "SHALLOW_WELL" if i < 3 else "STANDARD"

        # Account sizing
        if isinstance(fr.get("account_size"), list):
            account_size = fr["account_size"][0] if fr["account_size"] else 50000
        else:
            account_size = fr.get("account_size", 50000)

        # Quantity: based on position in ranking (top firm gets more)
        quantity = max(1, 4 - i)  # 4, 3, 2, 1, 1...

        # Pricing
        promo_discount = fr.get("promo_discount", 0.0)
        if promo_discount > 1.0:
            promo_discount /= 100.0
        base_cost = fr.get("cost", account_size * 0.003)  # rough estimate
        true_cost = base_cost * (1.0 - promo_discount) * quantity

        firm_mix.append({
            "firm": firm_name,
            "accounts": quantity,
            "size": account_size,
            "promo_applied": promo_code or "NONE",
            "true_cost": round(true_cost, 2),
            "ff_eligible": ff_eligible,
            "strategy": strategy,
            "alert_level": alert_level,
        })

        max_correlated_exposure += account_size * quantity * 0.05  # 5% risk per account

    # Consistency buffer: conservative estimate based on edge
    sharpe = edge.get("sharpe_ratio", 8.5)
    consistency_buffer = round(1.0 / sharpe * 100, 3) if sharpe > 0 else 0.1

    config = {
        "deployment_config": {
            "generated_at": now,
            "crossover_threshold_usd": crossover_threshold,
            "edge_metrics": {
                "win_rate": wr,
                "sharpe_ratio": sharpe,
                "avg_trades_per_day": edge.get("avg_trades_per_day", 2.0),
            },
            "firm_mix": firm_mix,
            "risk_parameters": {
                "risk_per_trade": risk_per_trade,
                "max_correlated_exposure": int(max_correlated_exposure),
                "consistency_buffer": consistency_buffer,
            },
            "notes": notes,
        }
    }

    return config


# ─── MODULE 4: FULL SCOPE WORKFLOW ────────────────────────────

def run_scope(full: bool = False) -> dict:
    """
    Full CARE scope workflow: SCAN → VERIFY → CALCULATE → RANK → CONFIG → OUTPUT

    Steps:
      1. SCAN: List all firms from database + check snapshots
      2. VERIFY: Run promo_verify on each firm's promo
      3. CALCULATE: PES for each firm using CEREBUS edge
      4. RANK: Sort by PES descending
      5. CONFIG: Generate deployment config
      6. OUTPUT: Return full dict (can be saved as YAML/JSON)

    If full=True, also runs live_firm_monitor for rule change detection.

    Returns full deployment config dict.
    """
    edge = EngineEdge(
        win_rate=0.857,
        max_drawdown_pct=0.05,
        avg_trades_per_day=2.0,
        sharpe_ratio=8.5,
        profit_factor=8.0,
        instrument="EURUSD.PRO",
    )
    calculator = PESCalculator()
    ff_protocol = FFProtocol(ff_network_size=5)
    config_gen = ConfigGenerator()

    # STEP 1: SCAN — get firms from DB
    firms = list_firms()
    if not firms:
        return {
            "error": "No firms in database. Run seed first.",
            "deployment_config": None,
        }

    # STEP 2: VERIFY promos + STEP 3: CALCULATE PES
    ranked_results = []
    monitor_data = {}

    for firm_data in firms:
        firm_name = firm_data.get("name", "Unknown")

        # Build FirmProfile from DB data
        cost_per = firm_data.get("cost_per_size", {})
        if isinstance(cost_per, dict):
            sizes = firm_data.get("account_sizes", [50000])
            if isinstance(sizes, str):
                try:
                    sizes = json.loads(sizes)
                except json.JSONDecodeError:
                    sizes = [50000]
            account_size = sizes[0] if sizes else 50000
            cost = cost_per.get(str(account_size), 0) or cost_per.get(account_size, 0)
        else:
            account_size = 50000
            cost = 0

        promo_active = firm_data.get("promo_active", {}) or {}
        if isinstance(promo_active, str):
            try:
                promo_active = json.loads(promo_active)
            except json.JSONDecodeError:
                promo_active = {}

        consistency = firm_data.get("consistency_rule", {}) or {}
        if isinstance(consistency, str):
            try:
                consistency = json.loads(consistency)
            except json.JSONDecodeError:
                consistency = {}

        scaling = firm_data.get("scaling_rules", {}) or {}
        if isinstance(scaling, str):
            try:
                scaling = json.loads(scaling)
            except json.JSONDecodeError:
                scaling = {}

        promo_code = promo_active.get("code")
        promo_discount = promo_active.get("discount_pct", 0.0)
        promo_nco = promo_active.get("new_customer_only", True)

        # Verify promo
        promo_result = None
        if promo_code:
            promo_result = promo_verify(promo_code, firm_name)

        # F&F verify
        ff_status_str = firm_data.get("ff_status", "UNTESTED")
        ff_access = ff_status_str == "ARBITRAGE"

        if promo_code:
            promo_details = PromoDetails(
                code=promo_code,
                discount_pct=promo_discount / 100.0 if promo_discount > 1.0 else promo_discount,
                new_customer_only=promo_nco,
                verified_on_official=promo_result.valid if promo_result else False,
                expires_at=promo_active.get("expires_at"),
                source_url=firm_data.get("source_url", ""),
            )
            ff_verify = ff_protocol.verify_promo(promo_details, ff_access=ff_access)
        else:
            ff_verify = {"promo_valid": False, "checks": {}, "action": "SKIP", "reason": "No promo"}

        max_daily = firm_data.get("max_daily_loss_pct", 0.05)
        leverage = 1.0 / max(max_daily, 0.001)

        firm_profile = FirmProfile(
            name=firm_name,
            account_size=account_size,
            cost=cost,
            max_daily_loss_pct=max_daily,
            max_trailing_dd_pct=firm_data.get("max_trailing_dd_pct", 0.06),
            consistency_rule_max_day_pct=consistency.get("max_day_pct_of_total", 0.30),
            min_trading_days=firm_data.get("min_trading_days", 5),
            payout_cycle_days=firm_data.get("payout_cycle_days", 14),
            payout_buffer_days=firm_data.get("payout_buffer_days", 3),
            scale_delay_days=scaling.get("scale_delay_days", 30),
            scale_min_profit_pct=scaling.get("min_profit_to_scale", 0.08),
            leverage_multiplier=leverage,
            promo_code=promo_code if ff_verify.get("promo_valid") else None,
            promo_discount_pct=promo_discount / 100.0 if promo_discount > 1.0 and ff_verify.get("promo_valid") else 0.0,
            promo_new_customer_only=promo_nco,
            ff_access=ff_access,
        )

        # CALCULATE PES
        pes_result = calculator.full_pes(firm_profile, edge, n_accounts=1)

        ranked_results.append({
            "firm_name": firm_name,
            "pes_score": pes_result.pes_score,
            "crossover_threshold": pes_result.crossover_threshold,
            "effective_leverage": pes_result.effective_leverage,
            "capital_velocity": pes_result.capital_velocity,
            "omega": pes_result.omega,
            "alpha": pes_result.alpha,
            "survival_probability": pes_result.survival_probability,
            "account_size": account_size,
            "promo_code": firm_profile.promo_code,
            "promo_discount": firm_profile.promo_discount_pct,
            "ff_eligible": ff_access,
            "ff_status": ff_status_str,
            "payout_cycle_days": firm_data.get("payout_cycle_days", 14),
            "cost": cost,
            "alert_level": "OK",
            "pes_notes": pes_result.notes,
            "promo_valid": promo_result.valid if promo_result else False,
        })

    # STEP 2b: If full mode, run live monitor for rule changes
    if full:
        for r in r in ranked_results:
            monitor = live_firm_monitor(r["firm_name"])
            monitor_data[r["firm_name"]] = monitor
            r["alert_level"] = monitor.get("alert_level", "OK")
            r["rule_changes"] = monitor.get("rule_changes", [])

    # STEP 4: RANK — sort by PES descending
    ranked_results.sort(key=lambda x: x["pes_score"], reverse=True)

    # STEP 5: CONFIG — generate deployment config
    edge_dict = {
        "win_rate": edge.win_rate,
        "sharpe_ratio": edge.sharpe_ratio,
        "avg_trades_per_day": edge.avg_trades_per_day,
    }
    deployment_config = generate_deployment_config(ranked_results, edge_dict)

    # STEP 6: OUTPUT
    deployment_config["deployment_config"]["firm_rankings"] = [
        {
            "rank": i + 1,
            "firm": r["firm_name"],
            "pes_score": r["pes_score"],
            "alpha": r["alpha"],
            "omega": r["omega"],
            "survival": r["survival_probability"],
            "crossover": r["crossover_threshold"],
            "alert_level": r["alert_level"],
            "promo_valid": r["promo_valid"],
        }
        for i, r in enumerate(ranked_results)
    ]

    if full:
        deployment_config["deployment_config"]["monitor_data"] = monitor_data

    return deployment_config


# ─── CLI HELPER ──────────────────────────────────────────────

def format_care_output(result: dict) -> str:
    """Format run_scope output for human-readable display."""
    if "error" in result:
        return f"⚠️ CARE Error: {result['error']}"

    dc = result.get("deployment_config", {})
    lines = [
        f"═══ CARE ENGINE OUTPUT — {dc.get('generated_at', '?')} ═══",
        f"Crossover threshold: ${dc.get('crossover_threshold_usd', 0):,}",
        "",
        "── FIRM MIX ──",
    ]

    for fm in dc.get("firm_mix", []):
        promo_str = f" | Promo: {fm['promo_applied']}" if fm['promo_applied'] != "NONE" else ""
        ff_str = " [FF]" if fm['ff_eligible'] else ""
        alert_str = f" ⚠️ {fm['alert_level']}" if fm['alert_level'] != "OK" else ""
        lines.append(
            f"  • {fm['firm']}{ff_str}: {fm['accounts']}x ${fm['size']:,}{promo_str} "
            f"| Cost: ${fm['true_cost']:,.2f} | {fm['strategy']}{alert_str}"
        )

    lines.append("")
    lines.append("── RANKINGS ──")
    for r in dc.get("firm_rankings", []):
        promo_check = "✅" if r.get("promo_valid") else "❌"
        alert = f" [{r['alert_level']}]" if r['alert_level'] != "OK" else ""
        lines.append(
            f"  #{r['rank']} {r['firm']}: PES={r['pes_score']:.4f} | α={r['alpha']:.4f} | "
            f"Ω={r['omega']:.4f} | S={r['survival']:.2%} | {promo_check}{alert}"
        )

    rp = dc.get("risk_parameters", {})
    lines.extend([
        "",
        "── RISK ──",
        f"  Risk/trade: {rp.get('risk_per_trade', 0):.1%}",
        f"  Max correlated exposure: ${rp.get('max_correlated_exposure', 0):,}",
        f"  Consistency buffer: {rp.get('consistency_buffer', 0):.4f}",
    ])

    if dc.get("notes"):
        lines.extend(["", "── NOTES ──"])
        for n in dc["notes"]:
            lines.append(f"  • {n}")

    return "\n".join(lines)
