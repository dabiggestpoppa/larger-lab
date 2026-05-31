"""
Sniper Dashboard API — Standalone FastAPI server
Port 8090 (avoids conflict with OCE backend on 8000)
Reads from: quant-lab/sniper/sniper.db
"""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')

import json
from pathlib import Path
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Database functions from sniper module
from quant_lab.sniper.database import (
    get_connection,
    list_firms,
    get_firm_by_name,
    list_deployments,
    get_latest_snapshots,
    get_active_deployments_with_firms,
    get_optimal_deployments,
    get_pes_trend,
    init_database,
)
from quant_lab.sniper.pes_calculator import PESCalculator, PESResult
from quant_lab.sniper.ff_matrix import CapitalDeploymentRouter, FFScalingMatrix
from quant_lab.sniper.ontology_mapper import OntologyMapper

# ─── Config ────────────────────────────────────────────────
SNIPER_DB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\sniper\sniper.db")

# ─── Ensure DB exists ──────────────────────────────────────
if SNIPER_DB.exists():
    init_database()

app = FastAPI(
    title="Prop Firm Sniper API",
    version="1.0",
    description="Dashboard data layer for Prop Firm Sniper Engine",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8090"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ─── Health ────────────────────────────────────────────────

@app.get("/api/health")
def health():
    db_exists = SNIPER_DB.exists()
    firm_count = 0
    deployment_count = 0
    if db_exists:
        try:
            conn = get_connection()
            firm_count = conn.execute("SELECT COUNT(*) FROM prop_firms").fetchone()[0]
            deployment_count = conn.execute("SELECT COUNT(*) FROM capital_deployments").fetchone()[0]
            conn.close()
        except Exception:
            pass
    return {
        "status": "ok" if db_exists else "degraded",
        "db_connected": db_exists,
        "firms": firm_count,
        "deployments": deployment_count,
        "timestamp": datetime.utcnow().isoformat(),
    }

# ─── Firms ─────────────────────────────────────────────────

def _enrich_firm_with_true_costs(firm: dict) -> dict:
    """Parse and inject true cost fields from DB JSON columns."""
    import json as _json
    for col in ("true_cost_per_size", "activation_fees", "billing_types"):
        val = firm.get(col)
        if isinstance(val, str):
            try:
                firm[col] = _json.loads(val)
            except Exception:
                firm[col] = {}
    # Also parse cost_per_size if still string
    cps = firm.get("cost_per_size")
    if isinstance(cps, str):
        try:
            firm["cost_per_size"] = _json.loads(cps)
        except Exception:
            firm["cost_per_size"] = {}
    return firm

@app.get("/api/firms")
def get_firms(status: Optional[str] = Query(None, description="ACTIVE, PATCHED, SUSPENDED")):
    """List all tracked prop firms with true cost data."""
    firms = list_firms(status=status)
    firms = [_enrich_firm_with_true_costs(f) for f in firms]
    return {"firms": firms, "count": len(firms)}

@app.get("/api/firms/{firm_name}")
def get_firm_detail(firm_name: str):
    """Get a single firm's full data."""
    firm = get_firm_by_name(firm_name)
    if not firm:
        raise HTTPException(404, f"Firm '{firm_name}' not found")
    return firm

# ─── PES Scores ───────────────────────────────────────────

@app.get("/api/pes/latest")
def get_latest_pes():
    """Get latest PES snapshots for all firms, ranked by score."""
    snapshots = get_latest_snapshots()
    return {"snapshots": snapshots, "count": len(snapshots)}

@app.get("/api/pes/trend/{firm_name}")
def get_pes_trend(firm_name: str, days: int = Query(30, ge=1, le=365)):
    """Get PES score history for a firm (for charting)."""
    firm = get_firm_by_name(firm_name)
    if not firm:
        raise HTTPException(404, f"Firm '{firm_name}' not found")
    trend = get_pes_trend(firm["firm_id"], days=days)
    return {"firm": firm_name, "trend": trend, "days": days}

# ─── Deployments ──────────────────────────────────────────

@app.get("/api/deployments")
def get_deployments(status: str = Query("ACTIVE")):
    """List capital deployments."""
    deployments = list_deployments(status=status)
    return {"deployments": deployments, "count": len(deployments)}

@app.get("/api/deployments/active-full")
def get_active_deployments_full():
    """Get active deployments with full firm data (joined)."""
    data = get_active_deployments_with_firms()
    return {"deployments": data, "count": len(data)}

# ─── Deployment Matrix ────────────────────────────────────

@app.get("/api/matrix")
def get_deployment_matrix():
    """Full deployment matrix — firm mix + PES scores for dashboard firm table."""
    firms = list_firms(status="ACTIVE")
    deployments = list_deployments(status="ACTIVE")
    snapshots = get_latest_snapshots()

    # Build firm_mix
    firm_mix = []
    for firm in firms:
        firm = _enrich_firm_with_true_costs(firm)
        firm_snapshots = [s for s in snapshots if s.get("firm_name") == firm["name"]]
        pes = firm_snapshots[0]["pes_score"] if firm_snapshots else 0.0

        # Get deployments for this firm
        firm_deps = [d for d in deployments if d.get("firm_name") == firm["name"]]
        total_accounts = sum(d.get("quantity", 1) for d in firm_deps)

        true_cost = _calc_true_cost(firm)
        # primary_size for display
        sizes = firm.get("account_sizes", [])
        primary_size = sizes[0] if sizes else 0

        firm_mix.append({
            "firm": firm["name"],
            "accounts": total_accounts,
            "size": primary_size,
            "promo_applied": firm.get("promo_active", {}).get("code", "") if isinstance(firm.get("promo_active"), dict) else "",
            "true_cost": true_cost,
            "activation_fee": true_cost.get("activation", 0) if isinstance(true_cost, dict) else 0,
            "challenge_fee": true_cost.get("challenge_fee", 0) if isinstance(true_cost, dict) else 0,
            "billing_type": true_cost.get("billing", "unknown") if isinstance(true_cost, dict) else "unknown",
            "cost_source": true_cost.get("note", "") if isinstance(true_cost, dict) else "",
            "ff_eligible": firm.get("ff_status") == "ARBITRAGE",
            "strategy": _classify_strategy(firm),
            "alert_level": firm.get("status", "OK"),
            "pes_score": round(pes, 2),
        })

    # Sort by PES desc
    firm_mix.sort(key=lambda x: x["pes_score"], reverse=True)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "crossover_threshold_usd": 12000,
        "firm_mix": firm_mix,
        "risk_parameters": {
            "risk_per_trade": 0.01,
            "max_correlated_exposure": 3,
            "consistency_buffer": 0.15,
        },
        "notes": [],
    }

def _calc_true_cost(firm: dict) -> dict:
    """Return true cost breakdown using DB true_cost_per_size (activation + challenge fee)."""
    true_costs = firm.get("true_cost_per_size", {})
    act_fees = firm.get("activation_fees", {})
    bill_types = firm.get("billing_types", {})
    
    # Fallback to cost_per_size if no true cost data yet
    if not true_costs:
        costs = firm.get("cost_per_size", {})
        if costs:
            vals = [float(v) for v in costs.values() if isinstance(v, (int, float, str))]
            promo = firm.get("promo_active", {}) or {}
            discount = promo.get("discount_pct", 0) / 100 if isinstance(promo, dict) else 0
            cheapest = min(vals) * (1 - discount) if vals else 0
            return {"total": round(cheapest, 2), "activation": 0, "challenge_fee": round(cheapest, 2), "billing": "unknown", "note": "PROMO_PRICE_NOT_TRUE_COST"}
        return {"total": 0, "activation": 0, "challenge_fee": 0, "billing": "unknown", "note": "NO_DATA"}
    
    # Use true cost data
    all_sizes = sorted([int(k) for k in true_costs.keys()])
    if not all_sizes:
        return {"total": 0, "activation": 0, "challenge_fee": 0, "billing": "unknown"}
    
    # Return the 50K or closest size
    target = 50 if 50 in all_sizes else all_sizes[len(all_sizes)//2]
    total = float(true_costs.get(str(target), 0))
    act = float(act_fees.get(str(target), 0))
    fee = total - act
    billing = bill_types.get(str(target), "unknown")
    
    return {
        "total": round(total, 2),
        "activation": round(act, 2),
        "challenge_fee": round(fee, 2),
        "billing": billing,
        "size_k": target,
        "note": "TRUE_COST_VERIFIED"
    }

def _classify_strategy(firm: dict) -> str:
    ff = firm.get("ff_status", "UNTESTED")
    if ff == "ARBITRAGE":
        return "F&F"
    if firm.get("scaling_rules") and firm["scaling_rules"] != "{}":
        return "SHALLOW_WELL"
    return "STANDARD"

# ─── True Cost Comparison ────────────────────────────────

@app.get("/api/true-costs")
def get_true_costs(size_k: int = Query(50, description="Account size in K (25, 50, 100, etc.)")):
    """Ranked true cost comparison for all firms at a given account size.
    Uses activation + challenge fee from DB, NOT promo prices."""
    firms = list_firms(status="ACTIVE")
    results = []

    for firm in firms:
        firm = _enrich_firm_with_true_costs(firm)
        true_costs = firm.get("true_cost_per_size", {})
        acts = firm.get("activation_fees", {})
        bills = firm.get("billing_types", {})

        # Match exact size or nearest
        sizes_avail = sorted([int(k) for k in true_costs.keys()])
        if not sizes_avail:
            continue
        matched = size_k if str(size_k) in true_costs else None
        if not matched:
            # Find nearest
            nearest = min(sizes_avail, key=lambda x: abs(x - size_k))
            if abs(nearest - size_k) <= 25:
                matched = nearest
        if not matched:
            continue

        sk = str(matched)
        total = float(true_costs.get(sk, 0))
        act = float(acts.get(sk, 0))
        fee = total - act
        billing = bills.get(sk, "unknown")

        results.append({
            "firm": firm["name"],
            "size_k": matched,
            "activation": act,
            "challenge_fee": round(fee, 2),
            "total": total,
            "billing": billing,
            "cost_per_1k": round(total / matched, 2),
        })

    results.sort(key=lambda x: x["total"])
    return {
        "size_k": size_k,
        "firms": results,
        "count": len(results),
        "generated_at": datetime.utcnow().isoformat(),
        "note": "TRUE_COST = activation + challenge fee (NOT promo price)",
    }

# ─── Overview Dashboard ───────────────────────────────────

@app.get("/api/overview")
def get_overview():
    """Top-level dashboard overview: summary numbers + alerts."""
    firms = list_firms(status="ACTIVE")
    deployments = list_deployments(status="ACTIVE")
    snapshots = get_latest_snapshots()

    # Calculate totals
    total_capital = sum(d.get("total_cost", 0) for d in deployments)
    total_deployed = sum(d.get("quantity", 1) for d in deployments)
    avg_pes = sum(s.get("pes_score", 0) for s in snapshots) / max(len(snapshots), 1)

    # Alerts
    alerts = []
    for firm in firms:
        if firm.get("status") == "PATCHED":
            alerts.append({"level": "warning", "message": f'{firm["name"]} is PATCHED'})
        if firm.get("status") == "SUSPENDED":
            alerts.append({"level": "danger", "message": f'{firm["name"]} is SUSPENDED'})

    # Crossover proximity
    crossover_threshold = 12000
    crossover_pct = min(round((total_capital / crossover_threshold) * 100), 100) if crossover_threshold > 0 else 0

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_firms_tracked": len(firms),
            "active_deployments": total_deployed,
            "total_capital_deployed": round(total_capital, 2),
            "avg_pes_score": round(avg_pes, 2),
            "crossover_proximity_pct": crossover_pct,
        },
        "alerts": alerts,
        "alerts_count": len(alerts),
        "top_firm": snapshots[0]["firm_name"] if snapshots else None,
        "top_pes": snapshots[0]["pes_score"] if snapshots else 0,
    }

# ─── Snapshots History ────────────────────────────────────

@app.get("/api/snapshots/summary")
def get_snapshots_summary():
    """PES summary for charting."""
    snapshots = get_latest_snapshots()
    return {
        "date": date.today().isoformat(),
        "scores": [
            {
                "firm": s.get("firm_name", "Unknown"),
                "pes": s.get("pes_score", 0),
                "account_size": s.get("account_size", 0),
                "is_optimal": bool(s.get("is_optimal", 0)),
            }
            for s in sorted(snapshots, key=lambda x: x.get("pes_score", 0), reverse=True)
        ],
    }

# ─── Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("🚀 Sniper Dashboard API starting on http://localhost:8090")
    print(f"📊 Database: {SNIPER_DB}")
    print(f"   Firms: {len(list_firms())}")
    print(f"   Deployments: {len(list_deployments())}")
    print(f"   Snapshots: {len(get_latest_snapshots())}")
    uvicorn.run(app, host="0.0.0.0", port=8090, log_level="info")
