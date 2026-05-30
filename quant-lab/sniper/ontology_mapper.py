"""
Phase 1: Ontology Translation Layer (A-1)
Maps PropFirmMatch raw marketing data → Quant Lab constraint vocabulary.

Marketing Term → Ontology Term → Mathematical Impact:
  Account Size         → Illusionary Notional        → Irrelevant (CEREBUS sizes by risk %)
  Max Drawdown (Static)→ Hard Floor Bandwidth         → Absolute loss tolerance limit
  Trailing Drawdown    → Intraday Peak Tether         → LETHAL: forces aggressive scale-out
  Consistency Rule     → Variance Suppression Tax     → Caps single-day yield
  Payout Frequency     → Capital Lockup Latency (T_lock) → Time-decay cost of synthetic leverage
  Promo / Discount     → Bandwidth Subsidy            → Lowers CoC, increases PES
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TrailingType(Enum):
    """Drawdown tether types ranked by lethality."""
    STATIC = "static"           # Safe: fixed from initial balance
    EOD = "eod"                 # Moderate: tether moves on EOD balance
    INTRADAY = "intraday"       # LETHAL: tether moves with unrealized profits
    UNKNOWN = "unknown"


class DDType(Enum):
    """Drawdown calculation basis."""
    BALANCE = "balance"         # Based on closed balance only
    EQUITY = "equity"           # Based on equity (includes unrealized)
    UNKNOWN = "unknown"


@dataclass
class PropFirmOntology:
    """
    The normalized mathematical reality of a prop firm offer.
    All marketing fluff stripped. Only constraint math remains.
    """
    # Identity
    firm_name: str
    source_url: str = ""
    scraped_from: str = ""       # "propfirmmatch", "payoutjunction", "official"

    # Cost Structure
    account_size: int = 0
    eval_fee: float = 0.0
    promo_discount_pct: float = 0.0       # 0.0 to 1.0
    promo_code: Optional[str] = None
    promo_new_customer_only: bool = False
    net_fee: float = 0.0                   # eval_fee * (1 - promo_discount)

    # Drawdown Constraints (the "bandwidth")
    max_dd_pct: float = 0.05               # e.g. 0.05 = 5%
    max_dd_amount: float = 0.0             # account_size * max_dd_pct
    is_trailing: bool = False
    trailing_type: TrailingType = TrailingType.STATIC
    dd_basis: DDType = DDType.BALANCE

    # Risk Bandwidth (THE key number)
    risk_bandwidth: float = 0.0            # $ amount of usable risk

    # Consistency Rules (Variance Suppression Tax)
    has_consistency_rule: bool = False
    max_single_day_profit_pct: float = 0.0  # e.g. 0.30 = max 30% of total profit from one day
    variance_suppression_tax: float = 1.0   # 1.0 = no tax, >1.0 = drag

    # Capital Velocity (Latency)
    payout_cycle_days: int = 14
    min_trading_days: int = 5
    capital_lockup_latency: float = 0.0     # T_lock in years

    # Scaling
    scale_enabled: bool = False
    scale_min_profit_pct: float = 0.0
    scale_delay_days: int = 0

    # F&F (Friends & Family)
    ff_access: bool = False
    max_accounts_per_identity: int = 1
    ff_discount_pct: float = 0.0

    # Taxonomy flags
    is_trailing_lethal: bool = False        # True if trailing_type == INTRADAY
    allows_runners: bool = True             # False if lethal tether forces atomic scalps
    allowed_instruments: list = field(default_factory=list)
    news_trading_restricted: bool = False

    # Raw pricing (for fragmentation cost estimation)
    raw_cost_per_size: dict = field(default_factory=dict)   # {size: cost}
    raw_account_sizes: list = field(default_factory=list)

    # Health
    is_active: bool = True
    notes: list = field(default_factory=list)

    def __post_init__(self):
        """Calculate derived fields from raw inputs."""
        self._calc_bandwidth()
        self._calc_net_fee()
        self._calc_variance_tax()
        self._calc_lethality()
        self._calc_latency()

    def _calc_bandwidth(self):
        self.max_dd_amount = self.account_size * self.max_dd_pct
        self.risk_bandwidth = self.max_dd_amount

    def _calc_net_fee(self):
        self.net_fee = self.eval_fee * (1.0 - self.promo_discount_pct)

    def _calc_variance_tax(self):
        if not self.has_consistency_rule:
            self.variance_suppression_tax = 1.0
        else:
            # If max day = 30% of total, tax = 1/0.30 = 3.33x penalty on velocity
            self.variance_suppression_tax = 1.0 / max(self.max_single_day_profit_pct, 0.01)

    def _calc_lethality(self):
        self.is_trailing_lethal = self.trailing_type == TrailingType.INTRADAY
        self.allows_runners = (
            self.trailing_type in (TrailingType.STATIC, TrailingType.EOD)
            and self.dd_basis == DDType.BALANCE
        )

    def _calc_latency(self):
        self.capital_lockup_latency = self.payout_cycle_days / 365.0

    def cost_of_capital(self, consistency_penalty: float = 1.0) -> float:
        """
        CoC = Net Fee / Risk Bandwidth
        Enhanced: CoC × latency_decay × consistency_penalty
        """
        if self.risk_bandwidth <= 0:
            return 999.9
        base_coc = self.net_fee / self.risk_bandwidth
        latency_decay = 1.0 + (self.payout_cycle_days / 14.0) * 0.005
        return base_coc * latency_decay * consistency_penalty

    def to_dict(self) -> dict:
        """Serialize to dict for JSON output."""
        return {
            "firm_name": self.firm_name,
            "source_url": self.source_url,
            "scraped_from": self.scraped_from,
            "account_size": self.account_size,
            "eval_fee": self.eval_fee,
            "net_fee": self.net_fee,
            "promo_code": self.promo_code,
            "promo_discount_pct": self.promo_discount_pct,
            "risk_bandwidth": self.risk_bandwidth,
            "max_dd_pct": self.max_dd_pct,
            "max_dd_amount": self.max_dd_amount,
            "is_trailing": self.is_trailing,
            "trailing_type": self.trailing_type.value,
            "is_trailing_lethal": self.is_trailing_lethal,
            "allows_runners": self.allows_runners,
            "has_consistency_rule": self.has_consistency_rule,
            "variance_suppression_tax": self.variance_suppression_tax,
            "payout_cycle_days": self.payout_cycle_days,
            "cost_of_capital": self.cost_of_capital(),
            "ff_access": self.ff_access,
            "is_active": self.is_active,
            "allowed_instruments": self.allowed_instruments,
        }


class OntologyMapper:
    """
    Translates PropFirmMatch / PayoutJunction raw data into PropFirmOntology.
    Single source of truth for all constraint math.
    """

    @staticmethod
    def map_trailing_type(raw_text: str) -> TrailingType:
        t = raw_text.lower().strip()
        if "intraday" in t or "equity" in t or "eod" in t and "intraday" in t:
            return TrailingType.INTRADAY
        if "eod" in t or "end of day" in t or "end-of-day" in t:
            return TrailingType.EOD
        if "static" in t or "fixed" in t or "balance only" in t:
            return TrailingType.STATIC
        return TrailingType.UNKNOWN

    @staticmethod
    def map_dd_basis(trailing_type: TrailingType) -> DDType:
        if trailing_type == TrailingType.INTRADAY:
            return DDType.EQUITY
        return DDType.BALANCE

    @staticmethod
    def from_propfirm_match(raw: dict) -> PropFirmOntology:
        """
        Map PropFirmMatch scrape dict to ontology.

        Expected raw keys (from PropFirmMatch DOM scrape):
          name, url, account_sizes[], costs{}, promo{}, drawdown{},
          consistency{}, payout{}, scaling{}, instruments[], news, ff_status

        If scraping doesn't provide all fields, defaults are safe (worst-case).
        """
        # Parse drawdown block
        dd = raw.get("drawdown", {}) or {}
        dd_pct_raw = dd.get("max_dd_pct", raw.get("max_dd_pct", 5.0))
        dd_pct = dd_pct_raw / 100.0 if dd_pct_raw > 1.0 else dd_pct_raw  # normalize

        trailing_text = dd.get("trailing_type", raw.get("trailing_type", "static"))
        trailing_type = OntologyMapper.map_trailing_type(trailing_text)
        dd_basis = OntologyMapper.map_dd_basis(trailing_type)

        # Parse account size and cost
        sizes = raw.get("account_sizes", [raw.get("account_size", 10000)])
        costs = raw.get("costs", {}) or {}
        primary_size = sizes[0] if sizes else 10000
        primary_cost = costs.get(str(primary_size), costs.get(primary_size, raw.get("cost", 0)))

        # Parse promo
        promo = raw.get("promo", {}) or {}
        promo_discount = promo.get("discount_pct", 0.0)
        if promo_discount > 1.0:
            promo_discount /= 100.0
        promo_nco = promo.get("new_customer_only", True)

        # Parse consistency rule
        cr = raw.get("consistency", {}) or {}
        has_cr = cr.get("active", raw.get("consistency_active", False))
        cr_max_day = cr.get("max_day_pct", raw.get("max_day_pct", 0.30))
        if cr_max_day > 1.0:
            cr_max_day /= 100.0

        # Parse payout
        po = raw.get("payout", {}) or {}
        payout_days = po.get("cycle_days", raw.get("payout_cycle_days", 14))
        min_days = po.get("min_trading_days", raw.get("min_trading_days", 5))

        # Parse scaling
        sc = raw.get("scaling", {}) or {}

        # Parse FF
        ff = raw.get("ff_status", "UNTESTED").upper() == "ARBITRAGE"

        return PropFirmOntology(
            firm_name=raw.get("name", "Unknown"),
            source_url=raw.get("url", ""),
            scraped_from="propfirmmatch",
            account_size=primary_size,
            eval_fee=primary_cost,
            promo_discount_pct=promo_discount,
            promo_code=promo.get("code"),
            promo_new_customer_only=promo_nco,
            max_dd_pct=dd_pct,
            is_trailing=trailing_type != TrailingType.STATIC,
            trailing_type=trailing_type,
            dd_basis=dd_basis,
            has_consistency_rule=has_cr,
            max_single_day_profit_pct=cr_max_day,
            payout_cycle_days=payout_days,
            min_trading_days=min_days,
            ff_access=ff,
            raw_cost_per_size={int(k) if isinstance(k, str) and k.isdigit() else k: float(v) for k, v in costs.items()} if isinstance(costs, dict) and costs else {primary_size: primary_cost},
            raw_account_sizes=sizes if isinstance(sizes, list) else [primary_size],
            allowed_instruments=raw.get("instruments", []),
            news_trading_restricted=raw.get("news_restricted", False),
            scale_enabled=sc.get("enabled", False),
            scale_min_profit_pct=sc.get("min_profit_pct", 0.0),
            scale_delay_days=sc.get("delay_days", 30),
        )

    @staticmethod
    def from_payout_junction(raw: dict) -> dict:
        """
        Map PayoutJunction payout verification data.
        This doesn't create a full ontology — it supplements one with real payout data.

        Returns dict: {firm_name, avg_payout_days, denial_rate, last_verified}
        """
        return {
            "firm_name": raw.get("firm_name", ""),
            "avg_payout_days": raw.get("avg_days", 0),
            "denial_rate": raw.get("denial_pct", 0.0),
            "total_reviews": raw.get("total_reviews", 0),
            "last_verified": raw.get("last_verified", ""),
            "payout_reliability_score": raw.get("reliability_score", 0.0),
        }


# ==========================================
# DEPRECATED: Old classes from v1.0
# Kept for backward compat. Remove in Phase 2.
# ==========================================

def normalize_raw_scrape(raw_data: dict) -> dict:
    """
    Legacy adapter: PropFirmMatch raw → normalized flat dict.
    Maintains backward compat with Phase 1 skeleton code.
    """
    ontology = OntologyMapper.from_propfirm_match(raw_data)
    return ontology.to_dict()
