"""
OC2 Scope - Main Workflow Orchestrator
`oc2 scope the prop space out` - SCAN -> VERIFY -> CALCULATE -> RANK -> OUTPUT

This is the top-level entry point. It ties together:
  database.py        - firm data
  pes_calculator.py  - math engine
  ff_protocol.py     - F&F arbitrage
  config_generator.py - YAML output
"""

import sys
from typing import Optional

from pes_calculator import PESCalculator, FirmProfile, EngineEdge
from database import (
    init_database, list_firms, upsert_firm, get_firm_by_name,
    insert_pes_snapshot, get_latest_snapshots, get_optimal_deployments,
)
from ff_protocol import FFProtocol, FFStatus, PromoDetails
from config_generator import ConfigGenerator


class OC2Scope:
    """
    Main orchestrator for `oc2 scope the prop space out`.
    """

    def __init__(self, edge: Optional[EngineEdge] = None):
        """
        Initialize with CEREBUS edge metrics.
        If None, uses default CEREBUS v4.0 edge.
        """
        self.edge = edge or EngineEdge(
            win_rate=0.857,
            max_drawdown_pct=0.05,
            avg_trades_per_day=2.5,
            sharpe_ratio=8.5,
            profit_factor=8.0,
            instrument="EURUSD.PRO",
        )
        self.calculator = PESCalculator()
        self.ff_protocol = FFProtocol(ff_network_size=5)
        self.config_gen = ConfigGenerator()
        init_database()

    def scope(
        self,
        min_pes: float = 0.0,
        max_results: int = 10,
        generate_config: bool = True,
        label: str = "deployment",
    ) -> str:
        """
        Full `oc2 scope` workflow.
        Returns formatted output string.
        """
        # STEP 1: SCAN - get all active firms from database
        firms = list_firms()
        if not firms:
            return "WARNING: No firms in database. Run `oc2 scope --seed` to add sample firms."

        # STEP 2: VERIFY - check promos, apply F&F
        # STEP 3: CALCULATE - PES for each firm
        all_results = []
        ff_overall_status = FFStatus.STANDARD

        for firm_data in firms:
            firm = self._dict_to_firm_profile(firm_data)

            # Verify promo if active
            ff_status = FFStatus(firm_data.get("ff_status", "UNTESTED"))
            promo_active = firm_data.get("promo_active", {})
            if promo_active and isinstance(promo_active, dict) and promo_active.get("code"):
                promo = PromoDetails(
                    code=promo_active.get("code", ""),
                    discount_pct=promo_active.get("discount_pct", 0),
                    new_customer_only=promo_active.get("new_customer_only", False),
                    verified_on_official=promo_active.get("verified", False),
                    expires_at=promo_active.get("expires_at"),
                    source_url=firm_data.get("website", ""),
                )
                verification = self.ff_protocol.verify_promo(
                    promo, ff_access=(ff_status == FFStatus.ARBITRAGE)
                )
                if not verification["promo_valid"]:
                    firm.promo_code = None
                    firm.promo_discount_pct = 0.0

            # Full PES calculation
            result = self.calculator.full_pes(firm, self.edge, n_accounts=1)
            result.notes.append(f"FF: {ff_status.value}")

            # Check crossover
            total_aum = firm.account_size
            if total_aum > result.crossover_threshold:
                result.notes.append("OVER crossover threshold")
                result.is_optimal = False

            all_results.append(result)

            if ff_status == FFStatus.ARBITRAGE:
                ff_overall_status = FFStatus.ARBITRAGE

        # STEP 4: RANK - sort by PES descending
        all_results.sort(key=lambda r: r.pes_score, reverse=True)

        # Filter by minimum PES
        viable = [r for r in all_results if r.pes_score >= min_pes][:max_results]

        # STEP 5: COMPUTE crossover
        crossover_firm = self._dict_to_firm_profile(firms[0]) if firms else FirmProfile(
            name="", account_size=1000, cost=10, max_daily_loss_pct=0.05,
            max_trailing_dd_pct=0.06, consistency_rule_max_day_pct=0.30,
            min_trading_days=5, payout_cycle_days=14, payout_buffer_days=3,
            scale_delay_days=30, scale_min_profit_pct=0.08, leverage_multiplier=20.0,
        )
        crossover = self.calculator.calculate_crossover_threshold(crossover_firm, self.edge)

        # STEP 6: OUTPUT
        output = self.config_gen.format_scope_output(viable, ff_status=ff_overall_status.value)

        # STEP 7: Generate config
        if generate_config and viable:
            config = self.config_gen.generate_deployment_config(
                top_results=viable,
                edge=self.edge,
                crossover_threshold=crossover,
            )
            yaml_path = self.config_gen.save_yaml(config, label)
            json_path = self.config_gen.save_json(config, label)
            output += f"\n\nConfig saved:\n   YAML: {yaml_path}\n   JSON: {json_path}"

        return output

    def seed_sample_firms(self) -> str:
        """Seed the database with sample futures prop firms for testing."""
        sample_firms = [
            {
                "name": "Topstep",
                "website": "https://www.topstep.com",
                "account_sizes": [50000, 100000, 150000],
                "cost_per_size": {"50000": 165, "100000": 275, "150000": 395},
                "promo_active": {"code": "SUMMER20", "discount_pct": 0.20, "new_customer_only": True, "verified": True},
                "max_daily_loss_pct": 0.033,
                "max_trailing_dd_pct": 0.05,
                "consistency_rule": {"max_day_pct_of_total": 0.50},
                "min_trading_days": 5,
                "payout_cycle_days": 10,
                "payout_buffer_days": 2,
                "payout_method": "Wire/Crypto",
                "scaling_rules": {"min_profit_to_scale": 0.05, "scale_delay_days": 30},
                "allowed_instruments": ["ES", "NQ", "CL", "GC"],
                "news_restrictions": True,
                "ff_status": "UNTESTED",
                "status": "ACTIVE",
            },
            {
                "name": "Apex Trader Funding",
                "website": "https://www.atf.com",
                "account_sizes": [25000, 50000, 100000, 200000],
                "cost_per_size": {"25000": 147, "50000": 217, "100000": 347, "200000": 547},
                "promo_active": {"code": "APEX30", "discount_pct": 0.30, "new_customer_only": True, "verified": True},
                "max_daily_loss_pct": 0.05,
                "max_trailing_dd_pct": 0.10,
                "consistency_rule": {"max_day_pct_of_total": 0.30},
                "min_trading_days": 1,
                "payout_cycle_days": 14,
                "payout_buffer_days": 3,
                "payout_method": "Crypto",
                "scaling_rules": {"min_profit_to_scale": 0.08, "scale_delay_days": 30},
                "allowed_instruments": ["ES", "NQ", "CL", "GC", "YM", "RTY"],
                "news_restrictions": False,
                "ff_status": "UNTESTED",
                "status": "ACTIVE",
            },
            {
                "name": "My Funded Futures",
                "website": "https://www.myfundedfutures.com",
                "account_sizes": [50000, 100000, 150000],
                "cost_per_size": {"50000": 150, "100000": 225, "150000": 300},
                "promo_active": {},
                "max_daily_loss_pct": 0.033,
                "max_trailing_dd_pct": 0.05,
                "consistency_rule": {"max_day_pct_of_total": 0.50},
                "min_trading_days": 5,
                "payout_cycle_days": 7,
                "payout_buffer_days": 2,
                "payout_method": "Crypto",
                "scaling_rules": {"min_profit_to_scale": 0.10, "scale_delay_days": 15},
                "allowed_instruments": ["ES", "NQ", "CL"],
                "news_restrictions": True,
                "ff_status": "UNTESTED",
                "status": "ACTIVE",
            },
            {
                "name": "TickFundedTrader",
                "website": "https://www.tickfundedtrader.com",
                "account_sizes": [25000, 50000, 100000],
                "cost_per_size": {"25000": 99, "50000": 189, "100000": 349},
                "promo_active": {"code": "TICK25", "discount_pct": 0.25, "new_customer_only": True, "verified": True},
                "max_daily_loss_pct": 0.05,
                "max_trailing_dd_pct": 0.10,
                "consistency_rule": {"max_day_pct_of_total": 0.30},
                "min_trading_days": 1,
                "payout_cycle_days": 14,
                "payout_buffer_days": 3,
                "payout_method": "Crypto/Wise",
                "scaling_rules": {"min_profit_to_scale": 0.08, "scale_delay_days": 30},
                "allowed_instruments": ["ES", "NQ", "CL", "GC"],
                "news_restrictions": False,
                "ff_status": "ARBITRAGE",
                "status": "ACTIVE",
            },
            {
                "name": "The Trading Pit",
                "website": "https://www.thetradingpit.com",
                "account_sizes": [50000, 100000],
                "cost_per_size": {"50000": 5000, "100000": 10000},
                "promo_active": {},
                "max_daily_loss_pct": 0.06,
                "max_trailing_dd_pct": 0.12,
                "consistency_rule": {"max_day_pct_of_total": 0.30},
                "min_trading_days": 10,
                "payout_cycle_days": 14,
                "payout_buffer_days": 5,
                "payout_method": "Wire",
                "scaling_rules": {"min_profit_to_scale": 0.10, "scale_delay_days": 30},
                "allowed_instruments": ["ES", "NQ"],
                "news_restrictions": True,
                "ff_status": "STANDARD",
                "status": "ACTIVE",
            },
        ]

        added = []
        for f in sample_firms:
            fid = upsert_firm(f)
            added.append(f"{f['name']} ({fid[:8]}...)")

        return f"Seeded {len(added)} firms:\n" + "\n".join(f"  - {a}" for a in added)

    def _dict_to_firm_profile(self, d: dict) -> FirmProfile:
        """Convert database dict to FirmProfile."""
        cost_per = d.get("cost_per_size", {})
        if isinstance(cost_per, dict):
            account_size = d.get("account_sizes", [1000])[0] if d.get("account_sizes") else 1000
            cost = cost_per.get(str(account_size), 0)
            if not cost:
                # Try int keys
                cost = cost_per.get(account_size, 0)
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


def main():
    """CLI entry: python scope.py [command]"""
    init_database()

    if len(sys.argv) < 2 or sys.argv[1] == "scope":
        scope = OC2Scope()
        min_pes = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        result = scope.scope(min_pes=min_pes)
        print(result)

    elif sys.argv[1] == "seed":
        scope = OC2Scope()
        print(scope.seed_sample_firms())

    elif sys.argv[1] == "firms":
        firms = list_firms()
        if not firms:
            print("No firms in database. Run 'seed' first.")
        for f in firms:
            print(f"  - {f['name']} | {f.get('status','?')} | FF: {f.get('ff_status','?')} | Sizes: {f.get('account_sizes',[])}")

    elif sys.argv[1] == "deployments":
        deps = get_optimal_deployments()
        if not deps:
            print("No active deployments.")
        for d in deps:
            print(f"  - {d['firm_name']} ${d['account_size']:,} x {d.get('quantity',1)} | PES: {d.get('pes_score','0'):.4f} | {d.get('status','?')}")

    elif sys.argv[1] == "snapshots":
        snaps = get_latest_snapshots()
        if not snaps:
            print("No PES snapshots yet.")
        for s in snaps:
            optimal = " [OPTIMAL]" if s.get("is_optimal") else ""
            print(f"  - {s['firm_name']} ${s['account_size']:,} | PES: {s['pes_score']:.4f} | {s['snapshot_date']}{optimal}")

    else:
        print("Usage: python scope.py [seed|scope|firms|deployments|snapshots]")


if __name__ == "__main__":
    main()
