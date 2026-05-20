"""
CEREBUS Stat Tracker Tool
=========================
Replicates MAD's stat tracking methodology from the CEREBUS Excel file.

Usage:
    from cerebus_stat_tracker import CerebusStatTracker
    
    tracker = CerebusStatTracker()
    tracker.load_trades(trades_list)
    report = tracker.generate_full_report()
    print(report)

Methods:
    hit_rate()              — Overall and per-pattern hit rates
    fib_level_analysis()    — Fibonacci level hit rates (-25%, -50%, -100%, -132%, -168%)
    session_analysis()      — Session-based metrics (Asian, London, NY)
    rekey_probability()     — Rekey trigger probability analysis
    temporal_patterns()     — Day-of-week and time-based patterns
    cross_market_comparison() — Cross-pair/instrument comparison
    confidence_interval()   — Wilson score confidence intervals
    generate_full_report()  — Complete formatted report
"""

import math
from collections import defaultdict
from typing import List, Dict, Any, Optional


class CerebusStatTracker:
    """
    Replicates MAD's CEREBUS Excel stat tracking methodology.
    
    MAD tracks:
    - Hit rates with Wilson score confidence intervals
    - Fibonacci extension targets: -25%, -50%, -100%, -132%, -168%
    - Session definitions: Asian (00:00-08:00), London (08:00-16:00), NY (13:00-21:00)
    - Rekey probability: consecutive lower-timeframe patterns triggering higher-timeframe rekey
    - Pattern sequences: AB(72%) -> BC(-25%) -> CD(61.8%)
    - ILM zone interactions: Daily ILM, IELM, WILM hit rates
    - Tolerance bands: ±0.15, ±0.25, ±0.50
    - Day-of-week delivery profiles
    - Quarter level interactions
    """
    
    # MAD's Fibonacci levels (from hit_rate_summary sheet)
    FIB_LEVELS = ["-25%", "-50%", "-100%", "-132%", "-168%"]
    
    # MAD's session definitions (UTC)
    SESSIONS = {
        "Asian":  {"start": 0,  "end": 8,  "label": "Tokyo+Sydney"},
        "London": {"start": 8,  "end": 16, "label": "London"},
        "NY":     {"start": 13, "end": 21, "label": "New York"},
    }
    
    # MAD's ILM types (from ILM Zone Behaviors sheet)
    ILM_TYPES = ["Daily_ILM", "IELM", "WILM"]
    
    # MAD's tolerance bands
    TOLERANCE_BANDS = [0.15, 0.25, 0.50]
    
    # MAD's day-of-week mapping
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    def __init__(self):
        self.trades: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []
        self.fib_data: Dict[str, list] = defaultdict(list)
        self.session_data: Dict[str, list] = defaultdict(list)
        self.ilm_data: Dict[str, list] = defaultdict(list)
    
    # ─── Data Loading ──────────────────────────────────────────────
    
    def load_trades(self, trades: List[Dict[str, Any]]):
        """
        Load trade results.
        
        Each trade dict should have:
            - result: "win" or "loss"
            - pnl: float (pips or price)
            - session: str ("Asian", "London", "NY", "Overlap")
            - day_of_week: str
            - fib_level: str (e.g., "-25%", "-50%")
            - pattern_type: str (optional)
            - ilm_type: str (optional)
            - tolerance: float (optional)
            - rekey: bool (optional)
            - timestamp: str (optional)
        """
        self.trades = trades
    
    def load_patterns(self, patterns: List[Dict[str, Any]]):
        """Load pattern formation data."""
        self.patterns = patterns
    
    def add_fib_result(self, level: str, hit: bool, session: str = "", day: str = ""):
        """Add a single Fibonacci level result."""
        self.fib_data[level].append({
            "hit": hit,
            "session": session,
            "day": day,
        })
    
    def add_session_result(self, session: str, result: str, pnl: float = 0):
        """Add a session-based result."""
        self.session_data[session].append({
            "result": result,
            "pnl": pnl,
        })
    
    def add_ilm_result(self, ilm_type: str, hit: bool, continuation: bool):
        """Add an ILM zone interaction result."""
        self.ilm_data[ilm_type].append({
            "hit": hit,
            "continuation": continuation,
        })
    
    # ─── Core Metrics ──────────────────────────────────────────────
    
    def hit_rate(self, data: Optional[List] = None) -> Dict[str, Any]:
        """
        Calculate hit rate with Wilson score confidence interval.
        
        MAD's methodology: simple hit rate + Wilson score CI at 95%.
        Formula: hits / total, with CI = p ± z * sqrt(p*(1-p)/n)
        """
        if data is None:
            data = self.trades
        
        total = len(data)
        if total == 0:
            return {"hit_rate": 0, "hits": 0, "total": 0, "ci_low": 0, "ci_high": 0}
        
        hits = sum(1 for t in data if t.get("result") == "win")
        p = hits / total
        
        # Wilson score 95% CI
        z = 1.96
        ci_low = max(0, p - z * math.sqrt(p * (1 - p) / total))
        ci_high = min(1, p + z * math.sqrt(p * (1 - p) / total))
        
        return {
            "hit_rate": round(p * 100, 2),
            "hits": hits,
            "misses": total - hits,
            "total": total,
            "ci_low": round(ci_low * 100, 2),
            "ci_high": round(ci_high * 100, 2),
        }
    
    def fib_level_analysis(self) -> Dict[str, Dict]:
        """
        Analyze hit rates per Fibonacci level.
        
        MAD tracks these specific levels (from hit_rate_summary):
        - -25%:  98.22% hit rate (276/281 weeks)
        - -50%:  96.44% hit rate (271/281 weeks)  
        - -100%: 92.17% hit rate (259/281 weeks)
        - -132%: 87.19% hit rate (245/281 weeks)  [violation level]
        - -168%: 71.53% hit rate (201/281 weeks)
        
        Also computes per-session and per-day breakdowns.
        """
        results = {}
        
        for level in self.FIB_LEVELS:
            level_data = self.fib_data.get(level, [])
            if not level_data:
                results[level] = {"hit_rate": 0, "total": 0, "note": "No data loaded"}
                continue
            
            hits = sum(1 for d in level_data if d["hit"])
            total = len(level_data)
            p = hits / total if total > 0 else 0
            
            # Per-session breakdown
            session_breakdown = {}
            for session_name in self.SESSIONS:
                session_hits = sum(1 for d in level_data if d.get("session") == session_name and d["hit"])
                session_total = sum(1 for d in level_data if d.get("session") == session_name)
                if session_total > 0:
                    session_breakdown[session_name] = {
                        "hit_rate": round(session_hits / session_total * 100, 2),
                        "total": session_total,
                    }
            
            # Per-day breakdown
            day_breakdown = {}
            for day in self.DAYS:
                day_hits = sum(1 for d in level_data if d.get("day") == day and d["hit"])
                day_total = sum(1 for d in level_data if d.get("day") == day)
                if day_total > 0:
                    day_breakdown[day] = {
                        "hit_rate": round(day_hits / day_total * 100, 2),
                        "total": day_total,
                    }
            
            results[level] = {
                "hit_rate": round(p * 100, 2),
                "hits": hits,
                "total": total,
                "session_breakdown": session_breakdown,
                "day_breakdown": day_breakdown,
            }
        
        return results
    
    def session_analysis(self) -> Dict[str, Dict]:
        """
        Session-based performance metrics.
        
        MAD's session definitions (from Session & Timing Metrics):
        - Asian:  00:00-08:00 UTC (Tokyo + Sydney)
        - London: 08:00-16:00 UTC
        - NY:     13:00-21:00 UTC
        - Overlap: 13:00-16:00 UTC (London-NY)
        
        Key findings from Excel:
        - London-NY overlap has strongest continuation (83.5% for 72% retracement)
        - Asian session establishes baseline for London/NY targets
        - Best session for DMR: 7-11 UTC. Worst: 2-4 UTC (Asian)
        """
        results = {}
        
        for session_name in list(self.SESSIONS.keys()) + ["Overlap"]:
            session_trades = [t for t in self.trades if t.get("session") == session_name]
            hr = self.hit_rate(session_trades)
            
            pnls = [t.get("pnl", 0) for t in session_trades]
            total_pnl = sum(pnls)
            avg_pnl = total_pnl / len(pnls) if pnls else 0
            
            results[session_name] = {
                "hit_rate": hr,
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "trade_count": len(session_trades),
            }
        
        return results
    
    def rekey_probability(self) -> Dict[str, Any]:
        """
        Rekey probability analysis.
        
        MAD's rekey methodology (from REKEY HYPOTHESIS TEST RESULTS):
        - Rekey trigger: consecutive 15M 61.8-88% under WILM → 4H rekey
        - Highest probability rekey condition: 94.3% (218 occurrences)
        - Rekey is confirmed when price returns to the ILM zone and continues
        
        Pattern sequence (from Pattern Formations):
        - AB(72%) → BC(-25%) → CD(61.8%): 81.2% success (487 patterns)
        """
        rekey_trades = [t for t in self.trades if t.get("rekey", False)]
        non_rekey = [t for t in self.trades if not t.get("rekey", False)]
        
        return {
            "rekey_hit_rate": self.hit_rate(rekey_trades),
            "non_rekey_hit_rate": self.hit_rate(non_rekey),
            "rekey_count": len(rekey_trades),
            "rekey_percentage": round(len(rekey_trades) / max(len(self.trades), 1) * 100, 2),
            "methodology": {
                "trigger": "Consecutive 15M 61.8-88% under WILM → 4H rekey",
                "confirmation": "Price returns to ILM zone and continues",
                "best_condition": "94.3% probability (218 occurrences)",
            }
        }
    
    def temporal_patterns(self) -> Dict[str, Any]:
        """
        Day-of-week and time-based pattern analysis.
        
        MAD's methodology (from session_data_full_week, quarterly_analysis):
        - Tracks delivery by day of week
        - Monday Fibonacci: calculate from Monday London open/close range
        - Thursday range targets: specific to Thursday's behavior
        - Quarterly analysis: groups data into quarters for trend detection
        """
        results = {}
        
        # Day-of-week analysis
        for day in self.DAYS:
            day_trades = [t for t in self.trades if t.get("day_of_week") == day]
            if day_trades:
                hr = self.hit_rate(day_trades)
                pnls = [t.get("pnl", 0) for t in day_trades]
                results[day] = {
                    "hit_rate": hr,
                    "total_pnl": round(sum(pnls), 2),
                    "trade_count": len(day_trades),
                }
        
        # Monday Fibonacci specific (from monday_fibonacci_calculations)
        monday_trades = [t for t in self.trades if t.get("day_of_week") == "Monday"]
        results["monday_fibonacci"] = {
            "hit_rate": self.hit_rate(monday_trades),
            "methodology": "Calculate Fib from Monday London session range, use as weekly targets",
            "trade_count": len(monday_trades),
        }
        
        # Thursday range (from thursday_range_targets)
        thursday_trades = [t for t in self.trades if t.get("day_of_week") == "Thursday"]
        results["thursday_range"] = {
            "hit_rate": self.hit_rate(thursday_trades),
            "methodology": "Thursday range expansion targets",
            "trade_count": len(thursday_trades),
        }
        
        return results
    
    def cross_market_comparison(self) -> Dict[str, Dict]:
        """
        Cross-market/pair comparison methodology.
        
        MAD tracks the same patterns across:
        - Forex: EUR/USD, USD/CHF, GBP/USD, USD/JPY, USD/CAD, AUD/USD, NZD/USD, CHF/JPY
        - Indices: DE30, FR40, US500, USTEC100
        - Commodities: OIL/USD
        
        Methodology: same Fibonacci levels and session analysis applied uniformly.
        """
        markets = defaultdict(list)
        for t in self.trades:
            market = t.get("market", "Unknown")
            markets[market].append(t)
        
        results = {}
        for market, mkt_trades in markets.items():
            hr = self.hit_rate(mkt_trades)
            pnls = [t.get("pnl", 0) for t in mkt_trades]
            results[market] = {
                "hit_rate": hr,
                "total_pnl": round(sum(pnls), 2),
                "trade_count": len(mkt_trades),
            }
        
        return results
    
    def confidence_interval(self, hits: int, total: int, confidence: float = 0.95) -> tuple:
        """
        Wilson score confidence interval.
        
        MAD uses this to validate that hit rates are statistically significant.
        """
        if total == 0:
            return (0, 0)
        
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        p = hits / total
        
        denominator = 1 + z*z / total
        center = (p + z*z / (2*total)) / denominator
        spread = z * math.sqrt((p*(1-p) + z*z/(4*total)) / total) / denominator
        
        return (round(max(0, center - spread) * 100, 2), 
                round(min(1, center + spread) * 100, 2))
    
    def ilm_analysis(self) -> Dict[str, Dict]:
        """
        ILM (Institutional Liquidity Matrix) zone analysis.
        
        MAD's ILM types (from ILM Zone Behaviors):
        - Daily ILM: 69% hit rate
        - IELM (Intraday Extreme Liquidity Model): 48.3% hit rate  
        - WILM (Weekly ILM): 34.2% hit rate
        
        Continuation vs Reversal: 65% continuation vs 35% reversal (1,567 setups)
        """
        results = {}
        
        for ilm_type in self.ILM_TYPES:
            type_data = self.ilm_data.get(ilm_type, [])
            if not type_data:
                results[ilm_type] = {"note": "No data loaded"}
                continue
            
            hits = sum(1 for d in type_data if d["hit"])
            total = len(type_data)
            continuations = sum(1 for d in type_data if d.get("continuation"))
            
            results[ilm_type] = {
                "hit_rate": round(hits / max(total, 1) * 100, 2),
                "total": total,
                "continuation_rate": round(continuations / max(total, 1) * 100, 2),
                "reversal_rate": round((total - continuations) / max(total, 1) * 100, 2),
            }
        
        return results
    
    def tolerance_analysis(self) -> Dict[float, Dict]:
        """
        Tolerance band analysis.
        
        MAD tests three tolerance levels (from TOLERANCE_COMPARISON):
        - ±0.15: Tightest, fewer entries, higher quality
        - ±0.25: Medium balance
        - ±0.50: Widest, more entries, lower quality
        
        Applied to Fibonacci level entries to filter noise.
        """
        results = {}
        
        for tol in self.TOLERANCE_BANDS:
            tol_trades = [t for t in self.trades if t.get("tolerance") == tol]
            if tol_trades:
                hr = self.hit_rate(tol_trades)
                results[tol] = {
                    "hit_rate": hr,
                    "trade_count": len(tol_trades),
                }
            else:
                results[tol] = {"note": "No data loaded"}
        
        return results
    
    # ─── Report Generation ─────────────────────────────────────────
    
    def generate_full_report(self) -> str:
        """Generate a complete formatted report matching MAD's Excel format."""
        lines = []
        lines.append("=" * 70)
        lines.append("CEREBUS STAT TRACKING REPORT")
        lines.append("=" * 70)
        
        # Overall hit rate
        hr = self.hit_rate()
        lines.append(f"\n📊 OVERALL HIT RATE")
        lines.append(f"   Rate: {hr['hit_rate']}% ({hr['hits']}/{hr['total']})")
        lines.append(f"   95% CI: [{hr['ci_low']}%, {hr['ci_high']}%]")
        
        # Fibonacci levels
        lines.append(f"\n📐 FIBONACCI LEVEL ANALYSIS")
        fib = self.fib_level_analysis()
        for level, data in fib.items():
            if "hit_rate" in data:
                lines.append(f"   {level}: {data['hit_rate']}% ({data.get('total', 0)} samples)")
            else:
                lines.append(f"   {level}: {data.get('note', 'N/A')}")
        
        # Session analysis
        lines.append(f"\n🕐 SESSION ANALYSIS")
        sessions = self.session_analysis()
        for sname, sdata in sessions.items():
            hr = sdata["hit_rate"]
            lines.append(f"   {sname}: {hr['hit_rate']}% WR, {sdata['trade_count']} trades, "
                        f"PnL: {sdata['total_pnl']}")
        
        # Rekey analysis
        lines.append(f"\n🔄 REKEY PROBABILITY")
        rekey = self.rekey_probability()
        lines.append(f"   Rekey trades: {rekey['rekey_count']} ({rekey['rekey_percentage']}%)")
        lines.append(f"   Rekey WR: {rekey['rekey_hit_rate']['hit_rate']}%")
        lines.append(f"   Non-rekey WR: {rekey['non_rekey_hit_rate']['hit_rate']}%")
        
        # Temporal patterns
        lines.append(f"\n📅 TEMPORAL PATTERNS")
        temporal = self.temporal_patterns()
        for day, data in temporal.items():
            if isinstance(data, dict) and "hit_rate" in data:
                lines.append(f"   {day}: {data['hit_rate']['hit_rate']}% WR, "
                            f"{data.get('trade_count', 0)} trades")
        
        # ILM analysis
        lines.append(f"\n🏛️ ILM ZONE ANALYSIS")
        ilm = self.ilm_analysis()
        for ilm_type, data in ilm.items():
            if "hit_rate" in data:
                lines.append(f"   {ilm_type}: {data['hit_rate']}% hit rate, "
                            f"{data['continuation_rate']}% continuation")
            else:
                lines.append(f"   {ilm_type}: {data.get('note', 'N/A')}")
        
        # Cross-market
        lines.append(f"\n🌍 CROSS-MARKET COMPARISON")
        cross = self.cross_market_comparison()
        for market, data in cross.items():
            lines.append(f"   {market}: {data['hit_rate']['hit_rate']}% WR, "
                        f"{data['trade_count']} trades, PnL: {data['total_pnl']}")
        
        lines.append(f"\n{'=' * 70}")
        lines.append("END OF REPORT")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ─── Standalone test ──────────────────────────────────────────────

if __name__ == "__main__":
    # Demo with sample data matching MAD's known results
    tracker = CerebusStatTracker()
    
    # Simulate MAD's hit_rate_summary data (281 weeks)
    sample_trades = []
    # -25%: 98.22% = 276/281
    for i in range(276):
        sample_trades.append({"result": "win", "pnl": 1, "fib_level": "-25%", "session": "London", "day_of_week": "Monday"})
    for i in range(5):
        sample_trades.append({"result": "loss", "pnl": -1, "fib_level": "-25%", "session": "Asian", "day_of_week": "Monday"})
    
    # -50%: 96.44% = 271/281
    for i in range(271):
        sample_trades.append({"result": "win", "pnl": 2, "fib_level": "-50%", "session": "London", "day_of_week": "Tuesday"})
    for i in range(10):
        sample_trades.append({"result": "loss", "pnl": -1, "fib_level": "-50%", "session": "NY", "day_of_week": "Tuesday"})
    
    tracker.load_trades(sample_trades)
    
    # Add Fib data
    for level, hits, total in [("-25%", 276, 281), ("-50%", 271, 281), ("-100%", 259, 281), ("-132%", 245, 281), ("-168%", 201, 281)]:
        for _ in range(hits):
            tracker.add_fib_result(level, True, "London", "Monday")
        for _ in range(total - hits):
            tracker.add_fib_result(level, False, "Asian", "Monday")
    
    # Add ILM data
    for ilm_type, hits, total in [("Daily_ILM", 1473, 2134), ("IELM", 1031, 2134), ("WILM", 730, 2134)]:
        for _ in range(hits):
            tracker.add_ilm_result(ilm_type, True, True)
        for _ in range(total - hits):
            tracker.add_ilm_result(ilm_type, False, False)
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(tracker.generate_full_report())
