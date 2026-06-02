"""
Phase 5: Grafana Dashboard Configuration
==========================================
Generates Grafana dashboard JSON for CEREBUS ML monitoring.
Panels: regime distribution, WR by regime, P&L curve, kill switch events, system health.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def generate_dashboard(output_path: str | Path = None) -> dict:
    """
    Generate a complete Grafana dashboard JSON for CEREBUS ML monitoring.
    """
    dashboard = {
        "dashboard": {
            "id": None,
            "uid": "cerebus-ml",
            "title": "CEREBUS ML — Regime-Adaptive Engine",
            "tags": ["cerebus", "ml", "trading"],
            "timezone": "America/New_York",
            "refresh": "30s",
            "time": {"from": "now-24h", "to": "now"},
            "panels": [
                # ── Panel 1: Regime Distribution (Pie Chart) ──
                {
                    "id": 1,
                    "title": "Regime Distribution (Today)",
                    "type": "piechart",
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": "cerebus_regime_total",
                            "legendFormat": "{{regime}}",
                        }
                    ],
                    "options": {
                        "pieType": "donut",
                        "legend": {"displayMode": "table", "placement": "right"},
                    },
                },
                # ── Panel 2: Win Rate by Regime (Bar Chart) ──
                {
                    "id": 2,
                    "title": "Win Rate by Regime",
                    "type": "barchart",
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                    "targets": [
                        {
                            "expr": "cerebus_win_rate_by_regime",
                            "legendFormat": "{{regime}}",
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 70},
                                    {"color": "green", "value": 85},
                                ]
                            },
                            "max": 100,
                            "min": 0,
                            "unit": "percent",
                        }
                    },
                },
                # ── Panel 3: P&L Curve (Time Series) ──
                {
                    "id": 3,
                    "title": "Cumulative P&L (R-Multiples)",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "expr": "cerebus_cumulative_pnl_r",
                            "legendFormat": "P&L (R)",
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "custom": {"drawStyle": "line", "fillOpacity": 10},
                        }
                    },
                },
                # ── Panel 4: Kill Switch Events (Stat) ──
                {
                    "id": 4,
                    "title": "Kill Switch Events (24h)",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 4, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "increase(cerebus_kill_switch_total[24h])",
                            "legendFormat": "Events",
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 0},
                                    {"color": "yellow", "value": 2},
                                    {"color": "red", "value": 5},
                                ]
                            }
                        }
                    },
                },
                # ── Panel 5: Guardrail Rejections (Stat) ──
                {
                    "id": 5,
                    "title": "Guardrail Rejections (24h)",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 4, "x": 4, "y": 8},
                    "targets": [
                        {
                            "expr": "increase(cerebus_guardrail_rejection_total[24h])",
                            "legendFormat": "Rejections",
                        }
                    ],
                },
                # ── Panel 6: PSI Drift Score (Gauge) ──
                {
                    "id": 6,
                    "title": "PSI Drift Score",
                    "type": "gauge",
                    "gridPos": {"h": 4, "w": 4, "x": 8, "y": 8},
                    "targets": [
                        {
                            "expr": "cerebus_psi_drift_score",
                            "legendFormat": "PSI",
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": 0},
                                    {"color": "yellow", "value": 0.1},
                                    {"color": "red", "value": 0.2},
                                ]
                            },
                            "max": 0.5,
                            "min": 0,
                        }
                    },
                },
                # ── Panel 7: Rolling Win Rate (Time Series) ──
                {
                    "id": 7,
                    "title": "Rolling Win Rate (50 trades)",
                    "type": "timeseries",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "cerebus_rolling_win_rate_50",
                            "legendFormat": "WR%",
                        },
                        {
                            "expr": "cerebus_backtest_win_rate",
                            "legendFormat": "Backtest WR%",
                        },
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "max": 100,
                            "min": 0,
                            "unit": "percent",
                        }
                    },
                },
                # ── Panel 8: System Health (Table) ──
                {
                    "id": 8,
                    "title": "System Health",
                    "type": "table",
                    "gridPos": {"h": 6, "w": 24, "x": 0, "y": 16},
                    "targets": [
                        {
                            "expr": "cerebus_component_health",
                            "legendFormat": "{{component}}",
                        }
                    ],
                },
                # ── Panel 9: Feature Importance (Bar Chart) ──
                {
                    "id": 9,
                    "title": "SHAP Feature Importance",
                    "type": "barchart",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 22},
                    "targets": [
                        {
                            "expr": "cerebus_shap_importance",
                            "legendFormat": "{{feature}}",
                        }
                    ],
                },
                # ── Panel 10: Entry Quality Distribution (Histogram) ──
                {
                    "id": 10,
                    "title": "Entry Quality Score Distribution",
                    "type": "histogram",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 22},
                    "targets": [
                        {
                            "expr": "cerebus_entry_quality_score",
                            "legendFormat": "Quality",
                        }
                    ],
                },
            ],
        },
        "overwrite": True,
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(dashboard, f, indent=2)
        print(f"✅ Grafana dashboard saved: {output_path}")

    return dashboard


def generate_prometheus_rules(output_path: str | Path = None) -> dict:
    """Generate Prometheus alerting rules for CEREBUS ML."""
    rules = {
        "groups": [
            {
                "name": "cerebus_ml_alerts",
                "rules": [
                    {
                        "alert": "CerebusHighDrift",
                        "expr": "cerebus_psi_drift_score > 0.20",
                        "for": "1h",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "Feature drift detected — retrain XGBoost",
                            "description": "PSI={{ $value }} exceeds 0.20 threshold",
                        },
                    },
                    {
                        "alert": "CerebusWinRateDrop",
                        "expr": "cerebus_rolling_win_rate_50 < cerebus_backtest_win_rate * 0.90",
                        "for": "2h",
                        "labels": {"severity": "warning"},
                        "annotations": {
                            "summary": "Rolling WR dropped >10% below backtest",
                        },
                    },
                    {
                        "alert": "CerebusGuardrailRejection",
                        "expr": "increase(cerebus_guardrail_rejection_total[1h]) > 0",
                        "labels": {"severity": "info"},
                        "annotations": {
                            "summary": "Guardrail intercepted an anomalous order",
                        },
                    },
                    {
                        "alert": "CerebusKillSwitch",
                        "expr": "increase(cerebus_kill_switch_total[1h]) > 0",
                        "labels": {"severity": "critical"},
                        "annotations": {
                            "summary": "Kill switch triggered",
                        },
                    },
                ],
            }
        ]
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(rules, f, indent=2)
        print(f"✅ Prometheus rules saved: {output_path}")

    return rules


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent / "monitoring" / "grafana"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_dashboard(out_dir / "cerebus_ml_dashboard.json")
    generate_prometheus_rules(out_dir / "cerebus_ml_alerts.json")
