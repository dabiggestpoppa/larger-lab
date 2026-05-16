#!/usr/bin/env python3
"""
MAD Content Farm — Analytics & ROI Prediction Engine

Takes performance data from content_tracker.py, runs Oransim predictions
on which content types perform best, and generates daily reports with
actionable recommendations.

Usage:
    # Generate today's report
    python analytics.py report

    # Run Oransim predictions for a specific niche
    python analytics.py predict --niche fitness --platform douyin

    # Compare niches
    python analytics.py compare --niches fitness cooking tech

    # Full pipeline: update snapshots → predict → report
    python analytics.py run-all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parent.parent.parent
CONTENT_FARM = WORKSPACE / "content-farm"
ORANSIM_BACKEND = WORKSPACE / "oransim" / "backend"
DATA_DIR = CONTENT_FARM / "data"
REPORTS_DIR = CONTENT_FARM / "output" / "reports"
WEEKLY_DIR = REPORTS_DIR / "weekly"

# Add oransim backend to path so we can import the engine
sys.path.insert(0, str(ORANSIM_BACKEND))


# ── Config Loading ─────────────────────────────────────────────────

def load_config() -> dict:
    """Load analytics.yaml config."""
    import yaml  # type: ignore
    config_path = CONTENT_FARM / "config" / "analytics.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Oransim Integration ────────────────────────────────────────────

class OransimPredictor:
    """Wrapper around Oransim's prediction API for content farm analytics."""

    def __init__(self, config: dict):
        self.config = config
        self.oransim_cfg = config.get("oransim", {})
        self.mode = self.oransim_cfg.get("mode", "mock")
        self._api_state = None
        self._wm = None
        self._ag = None

    def _ensure_bootstrapped(self):
        """Bootstrap the Oransim runtime (loads world model, agent population, etc.)."""
        if self._api_state is not None:
            return
        try:
            from oransim import api_state as state
            state.bootstrap()
            self._api_state = state
            self._wm = state.WM
            self._ag = state.AG
        except Exception as e:
            print(f"⚠️  Oransim bootstrap failed: {e}")
            print("   Falling back to heuristic predictions.")
            self._api_state = None

    def predict_niche(
        self,
        niche: str,
        platform: str = "douyin",
        caption: str = "",
        budget: float | None = None,
    ) -> dict:
        """Run an Oransim prediction for a given niche + platform.

        Returns a dict with predicted KPIs.
        """
        self._ensure_bootstrapped()
        defaults = self.oransim_cfg.get("defaults", {})

        if not caption:
            caption = f"Best performing {niche} content"

        if budget is None:
            budget = defaults.get("total_budget", 50000)

        platform_alloc = defaults.get("platform_alloc", {"douyin": 0.6, "xhs": 0.4})
        if platform not in platform_alloc:
            platform_alloc = {platform: 1.0}

        if self._api_state is None:
            return self._heuristic_predict(niche, platform, budget)

        try:
            return self._oransim_predict(niche, platform, caption, budget, platform_alloc)
        except Exception as e:
            print(f"⚠️  Oransim prediction failed: {e}")
            return self._heuristic_predict(niche, platform, budget)

    def _oransim_predict(
        self,
        niche: str,
        platform: str,
        caption: str,
        budget: float,
        platform_alloc: dict,
    ) -> dict:
        """Call the actual Oransim engine."""
        from oransim.api_schemas import PredictRequest, CreativeInput
        from oransim.api_helpers import build_scenario
        from oransim import api_state

        req = PredictRequest(
            creative=CreativeInput(
                caption=caption[:200],
                duration_sec=15.0,
                visual_style="bright",
                music_mood="upbeat",
            ),
            total_budget=budget,
            platform_alloc=platform_alloc,
            kol_niche=niche,
            use_llm=self.mode == "api",
            n_souls=self.oransim_cfg.get("defaults", {}).get("n_souls", 100),
            lifecycle_days=self.oransim_cfg.get("defaults", {}).get("lifecycle_days", 14),
        )

        scenario, macro_summary = build_scenario(req)

        # Run world model impression simulation
        imp = api_state.WM.simulate_impression(
            scenario.creative,
            platform,
            budget * platform_alloc.get(platform, 1.0),
            audience_filter=None,
            kol=scenario.kol_per_platform.get(platform),
            rng_seed=42,
        )

        oc = api_state.AG.simulate(
            imp,
            scenario.creative,
            kol=scenario.kol_per_platform.get(platform),
            rng_seed=42,
        )

        # Extract KPIs from outcome
        total_clicks = int(oc.click.sum()) if hasattr(oc.click, 'sum') else int(oc.click)
        total_conversions = int(oc.convert.sum()) if hasattr(oc.convert, 'sum') else int(oc.convert)
        total_impressions = int(imp.total_impressions) if hasattr(imp, 'total_impressions') else 0

        ctr = total_clicks / max(total_impressions, 1)
        cvr = total_conversions / max(total_clicks, 1)
        cpm = budget / max(total_impressions, 1) * 1000
        cpc = budget / max(total_clicks, 1)
        roas = (total_conversions * 50) / max(budget, 1)  # Assume ¥50 avg order

        return {
            "source": "oransim",
            "niche": niche,
            "platform": platform,
            "budget": budget,
            "predicted_impressions": total_impressions,
            "predicted_clicks": total_clicks,
            "predicted_conversions": total_conversions,
            "predicted_ctr": round(ctr, 4),
            "predicted_cvr": round(cvr, 4),
            "predicted_cpm": round(cpm, 2),
            "predicted_cpc": round(cpc, 2),
            "predicted_roas": round(roas, 2),
            "macro_context": macro_summary,
        }

    def _heuristic_predict(self, niche: str, platform: str, budget: float) -> dict:
        """Fallback heuristic prediction when Oransim engine isn't available.

        Uses industry benchmark data calibrated to niche/platform.
        """
        # Benchmark CTR/CVR by niche (from industry reports)
        niche_benchmarks = {
            "fitness":    {"ctr": 0.045, "cvr": 0.025, "cpm": 25},
            "cooking":    {"ctr": 0.038, "cvr": 0.020, "cpm": 22},
            "tech":       {"ctr": 0.030, "cvr": 0.015, "cpm": 30},
            "lifestyle":  {"ctr": 0.035, "cvr": 0.018, "cpm": 20},
            "finance":    {"ctr": 0.025, "cvr": 0.012, "cpm": 35},
        }
        # Platform multipliers
        platform_mult = {
            "douyin":      {"reach": 1.2, "engagement": 1.0},
            "xhs":         {"reach": 0.8, "engagement": 1.3},
            "xiaohongshu": {"reach": 0.8, "engagement": 1.3},
            "tiktok":      {"reach": 1.0, "engagement": 0.9},
            "kuaishou":    {"reach": 0.9, "engagement": 0.8},
        }

        bench = niche_benchmarks.get(niche, {"ctr": 0.035, "cvr": 0.018, "cpm": 25})
        pm = platform_mult.get(platform, {"reach": 1.0, "engagement": 1.0})

        cpm = bench["cpm"] / pm["reach"]
        impressions = int(budget / cpm * 1000)
        clicks = int(impressions * bench["ctr"] * pm["engagement"])
        conversions = int(clicks * bench["cvr"] * pm["engagement"])
        cpc = budget / max(clicks, 1)
        roas = (conversions * 50) / max(budget, 1)

        return {
            "source": "heuristic",
            "niche": niche,
            "platform": platform,
            "budget": budget,
            "predicted_impressions": impressions,
            "predicted_clicks": clicks,
            "predicted_conversions": conversions,
            "predicted_ctr": round(bench["ctr"] * pm["engagement"], 4),
            "predicted_cvr": round(bench["cvr"] * pm["engagement"], 4),
            "predicted_cpm": round(cpm, 2),
            "predicted_cpc": round(cpc, 2),
            "predicted_roas": round(roas, 2),
        }

    def predict_all_niches(self, niches: list[str] | None = None) -> list[dict]:
        """Run predictions for all configured niches."""
        if niches is None:
            niches = self.oransim_cfg.get("niches", ["fitness", "cooking", "tech", "lifestyle", "finance"])
        results = []
        for niche in niches:
            for platform in ["douyin", "xhs"]:
                pred = self.predict_niche(niche, platform)
                results.append(pred)
        return results


# ── Report Generation ──────────────────────────────────────────────

class ReportGenerator:
    """Generates daily and weekly analytics reports."""

    def __init__(self, config: dict, db_path: Path):
        self.config = config
        self.db_path = db_path
        self.classification = config.get("classification", {})
        self.benchmarks = config.get("benchmarks", {})

    def _get_engagement_benchmark(self, niche: str) -> dict:
        """Get engagement rate benchmark for a niche."""
        return self.benchmarks.get(niche, self.benchmarks.get("default", {
            "good_engagement_rate": 0.04,
            "viral_threshold": 0.12,
        }))

    def _classify_content(self, engagement_rate: float, niche: str) -> str:
        """Classify content as 'scale', 'keep', or 'kill'."""
        bench = self._get_engagement_benchmark(niche)
        good = bench.get("good_engagement_rate", 0.04)
        scale_thresh = self.classification.get("scale_threshold", 1.5)
        keep_thresh = self.classification.get("keep_threshold", 0.8)
        kill_thresh = self.classification.get("kill_threshold", 0.5)

        ratio = engagement_rate / max(good, 0.001)
        if ratio >= scale_thresh:
            return "scale"
        elif ratio <= kill_thresh:
            return "kill"
        else:
            return "keep"

    def generate_daily_report(
        self,
        predictions: list[dict],
        summary: dict,
        niche_perf: list[dict],
        top_posts: list[dict],
        bottom_posts: list[dict],
    ) -> str:
        """Generate a daily markdown report."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        lines: list[str] = []

        # Header
        lines.extend([
            f"# 📊 MAD Content Farm — Daily Report",
            f"",
            f"**Date:** {date_str}  ",
            f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Period:** Last 24 hours",
            f"",
            f"---",
            f"",
        ])

        # Summary
        lines.extend([
            f"## 📈 Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Posts | {summary.get('total_posts', 0)} |",
            f"| Total Views | {summary.get('total_views', 0):,} |",
            f"| Total Likes | {summary.get('total_likes', 0):,} |",
            f"| Total Comments | {summary.get('total_comments', 0):,} |",
            f"| Total Shares | {summary.get('total_shares', 0):,} |",
            f"| New Followers | {summary.get('total_followers', 0):,} |",
            f"| Avg Engagement Rate | {summary.get('engagement_rate', 0):.2%} |",
            f"",
        ])

        # Niche Performance
        lines.extend([
            f"## 🏷️ Niche Performance",
            f"",
            f"| Niche | Posts | Views | Engagement |",
            f"|-------|-------|-------|------------|",
        ])
        for n in niche_perf:
            lines.append(
                f"| {n['niche']:12s} | {n['post_count']:>5} | "
                f"{n['total_views']:>10,} | {n['engagement_rate']:>8.2%} |"
            )
        lines.append("")

        # Top Performers
        lines.extend([
            f"## 🚀 Top Performers",
            f"",
        ])
        if top_posts:
            lines.extend([
                f"| Platform | Niche | Views | Likes | Eng. Rate |",
                f"|----------|-------|-------|-------|-----------|",
            ])
            for p in top_posts[:10]:
                views = p.get("views", 0) or 0
                likes = p.get("likes", 0) or 0
                comments = p.get("comments", 0) or 0
                shares = p.get("shares", 0) or 0
                eng = (likes + comments + shares) / max(views, 1)
                lines.append(
                    f"| {p['platform']:8s} | {p['niche']:10s} | "
                    f"{views:>8,} | {likes:>6,} | {eng:>7.2%} |"
                )
        else:
            lines.append("_No posts in this period._")
        lines.append("")

        # Bottom Performers
        lines.extend([
            f"## ⚠️ Underperformers",
            f"",
        ])
        if bottom_posts:
            lines.extend([
                f"| Platform | Niche | Views | Likes | Eng. Rate |",
                f"|----------|-------|-------|-------|-----------|",
            ])
            for p in bottom_posts[:10]:
                views = p.get("views", 0) or 0
                likes = p.get("likes", 0) or 0
                comments = p.get("comments", 0) or 0
                shares = p.get("shares", 0) or 0
                eng = (likes + comments + shares) / max(views, 1)
                lines.append(
                    f"| {p['platform']:8s} | {p['niche']:10s} | "
                    f"{views:>8,} | {likes:>6,} | {eng:>7.2%} |"
                )
        else:
            lines.append("_No posts in this period._")
        lines.append("")

        # Oransim Predictions
        lines.extend([
            f"## 🔮 Oransim Predictions",
            f"",
            f"Predicted ROI by niche (¥50K budget, 14-day lifecycle):",
            f"",
            f"| Niche | Platform | Clicks | Conv. | CTR | CVR | ROAS |",
            f"|-------|----------|--------|-------|-----|-----|------|",
        ])
        for pred in sorted(predictions, key=lambda x: x.get("predicted_roas", 0), reverse=True):
            lines.append(
                f"| {pred['niche']:10s} | {pred['platform']:8s} | "
                f"{pred['predicted_clicks']:>7,} | {pred['predicted_conversions']:>5,} | "
                f"{pred['predicted_ctr']:>5.2%} | {pred['predicted_cvr']:>5.2%} | "
                f"{pred['predicted_roas']:>4.1f}x |"
            )
        lines.append("")

        # Recommendations
        lines.extend(self._generate_recommendations(niche_perf, predictions))
        lines.append("")

        # Footer
        lines.extend([
            f"---",
            f"",
            f"*Generated by MAD Content Farm Analytics Engine 🦉*",
            f"*Next report: {(now + timedelta(days=1)).strftime('%Y-%m-%d')} 06:00 UTC*",
        ])

        return "\n".join(lines)

    def _generate_recommendations(
        self,
        niche_perf: list[dict],
        predictions: list[dict],
    ) -> list[str]:
        """Generate actionable recommendations based on data + predictions."""
        lines = [
            f"## 💡 Recommendations",
            f"",
        ]

        if not niche_perf:
            lines.append("_Not enough data for recommendations. Need at least 5 posts per niche._")
            return lines

        # Sort niches by engagement rate
        sorted_niches = sorted(niche_perf, key=lambda x: x.get("engagement_rate", 0), reverse=True)

        # Scale recommendations
        scale_niches = []
        kill_niches = []
        keep_niches = []

        for n in sorted_niches:
            niche = n["niche"]
            eng = n.get("engagement_rate", 0)
            classification = self._classify_content(eng, niche)
            if classification == "scale":
                scale_niches.append(n)
            elif classification == "kill":
                kill_niches.append(n)
            else:
                keep_niches.append(n)

        if scale_niches:
            lines.append("### ✅ Scale These")
            for n in scale_niches:
                lines.append(
                    f"- **{n['niche']}** — Engagement: {n['engagement_rate']:.2%} | "
                    f"Posts: {n['post_count']} | "
                    f"→ Double down. Increase posting frequency by 50%."
                )
            lines.append("")

        if keep_niches:
            lines.append("### 🔄 Keep & Optimize")
            for n in keep_niches:
                lines.append(
                    f"- **{n['niche']}** — Engagement: {n['engagement_rate']:.2%} | "
                    f"Posts: {n['post_count']} | "
                    f"→ Test different hooks, thumbnails, and posting times."
                )
            lines.append("")

        if kill_niches:
            lines.append("### 🛑 Kill or Pivot")
            for n in kill_niches:
                lines.append(
                    f"- **{n['niche']}** — Engagement: {n['engagement_rate']:.2%} | "
                    f"Posts: {n['post_count']} | "
                    f"→ Pause this niche. Reallocate budget to top performers."
                )
            lines.append("")

        # Oransim-based recommendations
        if predictions:
            best_pred = max(predictions, key=lambda x: x.get("predicted_roas", 0))
            worst_pred = min(predictions, key=lambda x: x.get("predicted_roas", 0))
            lines.append("### 🔮 Oransim Insights")
            lines.append(
                f"- Highest predicted ROAS: **{best_pred['niche']}** on "
                f"**{best_pred['platform']}** ({best_pred['predicted_roas']}x)"
            )
            lines.append(
                f"- Lowest predicted ROAS: **{worst_pred['niche']}** on "
                f"**{worst_pred['platform']}** ({worst_pred['predicted_roas']}x)"
            )
            lines.append("")

        return lines


# ── Main Pipeline ──────────────────────────────────────────────────

def run_report(config: dict, db_path: Path) -> Path:
    """Run the full daily report pipeline."""
    import content_tracker as ct

    conn = ct.get_connection(db_path)

    # Gather data
    summary = ct.get_summary(conn, days=1)
    niche_perf = ct.get_niche_performance(conn, days=7)
    all_posts = ct.list_posts(conn, limit=100, days=7)

    # Sort for top/bottom
    scored_posts = []
    for p in all_posts:
        views = p.get("views", 0) or 0
        eng = (p.get("likes", 0) or 0) + (p.get("comments", 0) or 0) + (p.get("shares", 0) or 0)
        p["_eng_rate"] = eng / max(views, 1)
        scored_posts.append(p)

    scored_posts.sort(key=lambda x: x["_eng_rate"], reverse=True)
    top_posts = scored_posts[:10]
    bottom_posts = scored_posts[-10:] if len(scored_posts) > 10 else []

    # Run Oransim predictions
    predictor = OransimPredictor(config)
    predictions = predictor.predict_all_niches()

    # Generate report
    reporter = ReportGenerator(config, db_path)
    report_md = reporter.generate_daily_report(
        predictions=predictions,
        summary=summary,
        niche_perf=niche_perf,
        top_posts=top_posts,
        bottom_posts=bottom_posts,
    )

    # Write report
    now = datetime.now(timezone.utc)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{now.strftime('%Y-%m-%d')}.md"
    report_path.write_text(report_md, encoding="utf-8")

    conn.close()
    return report_path


# ── CLI Interface ──────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MAD Content Farm — Analytics & ROI Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # report
    sub.add_parser("report", help="Generate daily report")

    # predict
    pred_p = sub.add_parser("predict", help="Run Oransim prediction")
    pred_p.add_argument("--niche", default="fitness")
    pred_p.add_argument("--platform", default="douyin")
    pred_p.add_argument("--budget", type=float, default=None)
    pred_p.add_argument("--caption", default="")

    # compare
    cmp_p = sub.add_parser("compare", help="Compare niches")
    cmp_p.add_argument("--niches", nargs="+", default=["fitness", "cooking", "tech", "lifestyle", "finance"])

    # run-all
    sub.add_parser("run-all", help="Full pipeline: predict → report")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    config = load_config()
    db_path = WORKSPACE / config.get("database", {}).get("path", "content-farm/data/performance.db")

    if args.command == "report":
        path = run_report(config, db_path)
        print(f"✅ Report generated: {path}")

    elif args.command == "predict":
        predictor = OransimPredictor(config)
        result = predictor.predict_niche(
            niche=args.niche,
            platform=args.platform,
            caption=args.caption,
            budget=args.budget,
        )
        print(f"\n🔮 Oransim Prediction: {args.niche} on {args.platform}")
        print(f"   Source:     {result['source']}")
        print(f"   Budget:     ¥{result['budget']:,.0f}")
        print(f"   Impressions:{result['predicted_impressions']:,}")
        print(f"   Clicks:     {result['predicted_clicks']:,}")
        print(f"   Conversions:{result['predicted_conversions']:,}")
        print(f"   CTR:        {result['predicted_ctr']:.2%}")
        print(f"   CVR:        {result['predicted_cvr']:.2%}")
        print(f"   CPM:        ¥{result['predicted_cpm']:.2f}")
        print(f"   CPC:        ¥{result['predicted_cpc']:.2f}")
        print(f"   ROAS:       {result['predicted_roas']}x")

    elif args.command == "compare":
        predictor = OransimPredictor(config)
        print(f"\n📊 Niche Comparison (Oransim Predictions)")
        print(f"{'Niche':<12} {'Platform':<8} {'Clicks':>8} {'Conv':>6} {'CTR':>7} {'CVR':>7} {'ROAS':>6}")
        print("-" * 60)
        for niche in args.niches:
            for platform in ["douyin", "xhs"]:
                r = predictor.predict_niche(niche, platform)
                print(
                    f"{r['niche']:<12} {r['platform']:<8} "
                    f"{r['predicted_clicks']:>8,} {r['predicted_conversions']:>6,} "
                    f"{r['predicted_ctr']:>6.2%} {r['predicted_cvr']:>6.2%} "
                    f"{r['predicted_roas']:>5.1f}x"
                )

    elif args.command == "run-all":
        print("🔄 Running full analytics pipeline...")
        path = run_report(config, db_path)
        print(f"✅ Report generated: {path}")
        print(f"\n📋 Report preview:")
        content = path.read_text(encoding="utf-8")
        # Show first 40 lines
        for line in content.split("\n")[:40]:
            print(f"  {line}")
        if len(content.split("\n")) > 40:
            print(f"  ... ({len(content.split(chr(10)))} lines total)")


if __name__ == "__main__":
    main()
