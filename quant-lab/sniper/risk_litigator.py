"""
Risk Litigator — Dynamic Risk Gatekeeper
=========================================
Enforces account-specific risk profiles before every order submission.

Two modes:
  PROP_TRAILING — Prop firm survival guards (daily loss cap, streak reduction, DD buffer)
  KELLY_MAX    — Maximum velocity (no daily cap, no streak reduction, full pyramid)

This is the "Shield" layer from the lab expansion plan.
Runs as a pre-trade gate — blocks orders that violate the active risk profile.

Usage:
    from .risk_litigator import RiskLitigator, RiskProfile, AccountState

    litigator = RiskLitigator(profile=RiskProfile.PROP_TRAILING)
    result = litigator.check_order(entry_price, sl_price, contracts, account_state)
    # result = {"allowed": True/False, "reason": "...", "adjusted_size": ...}
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ─── ENUMS ───────────────────────────────────────────────────────────────────

class RiskProfile(Enum):
    PROP_TRAILING = "PROP_TRAILING"
    KELLY_MAX = "KELLY_MAX"


class BlockReason(Enum):
    DAILY_LOSS_CAP = "Daily Loss Cap Proximity"
    TRAILING_DD_BREACH = "Trailing Drawdown Breach Risk"
    SIZE_EXCEEDS_MAX = "Position Size Exceeds Prop Max"
    CORRELATION_CAP = "Correlation Cap Breached"
    STREAK_REDUCTION = "Consecutive Loss Reduction Active"
    STREAK_HALT = "Session Halt — 6+ Consecutive Losses"
    DD_DERISK = "DD Derisk Active — Reduced Size"
    TIME_GATE = "Outside Trading Window"


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────────

@dataclass
class AccountState:
    """Current account state for risk evaluation."""
    balance: float
    equity: float
    daily_pnl: float = 0.0
    intraday_peak_equity: float = 0.0
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    total_trades_today: int = 0
    open_positions: list = field(default_factory=list)
    correlated_exposure: dict = field(default_factory=dict)  # e.g. {"EU": 1, "CHF": 0}


@dataclass
class OrderRequest:
    """Order request to be evaluated by the risk gate."""
    asset_name: str
    entry_price: float
    sl_price: float
    tp_price: float
    contracts: int
    tick_size: float = 1.0
    tick_value: float = 1.0
    direction: str = "long"  # "long" | "short"


@dataclass
class RiskResult:
    """Result of risk gate evaluation."""
    allowed: bool
    reason: str
    adjusted_contracts: Optional[int] = None
    block_reason: Optional[BlockReason] = None


# ─── RISK LITIGATOR ──────────────────────────────────────────────────────────

class RiskLitigator:
    """
    Dynamic risk gatekeeper. Enforces account-specific risk profiles.

    PROP_TRAILING mode:
        - 0.40% daily loss cap
        - 6% trailing DD with derisk at 8%
        - 5 consecutive losses → reduce to 0.50%
        - 6+ consecutive losses → session halt
        - Correlation caps (EU+CHF ≤ 1 position)
        - Phase 1: 0.75% risk until 4% buffer built
        - Phase 2: 1.0% risk after buffer confirmed

    KELLY_MAX mode:
        - No daily loss cap
        - No streak reduction
        - Full Kelly sizing (up to 5%)
        - No correlation caps
    """

    # ── PROP FIRM CONSTANTS ──────────────────────────────────────────────────
    DAILY_LOSS_CAP_PCT = 0.004        # 0.40% daily loss hard limit
    DAILY_LOSS_WARNING_PCT = 0.0035   # 0.35% — start blocking new entries
    TRAILING_DD_LIMIT = 0.06          # 6% trailing DD
    TRAILING_DD_DERISK = 0.08         # 8% — derisk to 0.50%
    PHASE1_RISK_PCT = 0.0075          # 0.75% per trade (Phase 1)
    PHASE2_RISK_PCT = 0.01            # 1.0% per trade (Phase 2)
    BUFFER_PROMOTION_PCT = 0.04       # 4% buffer to promote to Phase 2
    STREAK_REDUCTION_THRESHOLD = 5    # 5 losses → reduce size
    STREAK_HALT_THRESHOLD = 6         # 6 losses → session halt
    DERISK_RECOVERY_WINS = 2          # 2 consecutive wins to resume
    CORRELATION_CAP_EU_CHF = 1        # EU + CHF combined ≤ 1 full position
    CORRELATION_CAP_GBP_CROSSES = 1   # GBP crosses combined ≤ 1
    CORRELATION_CAP_XAU_XAG = 1       # XAU + XAG combined ≤ 1

    def __init__(
        self,
        profile: RiskProfile = RiskProfile.PROP_TRAILING,
        account_type: str = "trailing",  # "trailing" | "static"
        static_dd_limit: float = 0.10,   # 10% for static accounts
    ):
        self.profile = profile
        self.account_type = account_type
        self.static_dd_limit = static_dd_limit
        self.is_phase2 = False          # Auto-promoted when buffer confirmed
        self.is_derisked = False        # True when DD derisk active
        self.session_halted = False     # True when 6+ consecutive losses

    def check_order(
        self,
        order: OrderRequest,
        account: AccountState,
    ) -> RiskResult:
        """
        Evaluate an order against the active risk profile.

        Returns:
            RiskResult with allowed=True/False, reason, and adjusted size if needed.
        """
        # ── KELLY MAX MODE — Minimal gates ──────────────────────────────────
        if self.profile == RiskProfile.KELLY_MAX:
            return self._kelly_check(order, account)

        # ── PROP TRAILING MODE — Full risk gates ────────────────────────────
        return self._prop_check(order, account)

    def _kelly_check(self, order: OrderRequest, account: AccountState) -> RiskResult:
        """Kelly Max mode — only basic sanity checks."""
        # Even Kelly has a max risk per trade
        risk_per_trade = abs(order.entry_price - order.sl_price) * order.contracts * order.tick_value
        max_risk = account.balance * 0.05  # 5% max Kelly

        if risk_per_trade > max_risk:
            adjusted = int(max_risk / (abs(order.entry_price - order.sl_price) * order.tick_value))
            return RiskResult(
                allowed=True,
                reason=f"Kelly size adjusted from {order.contracts} to {adjusted} (5% max)",
                adjusted_contracts=max(adjusted, 1),
            )

        return RiskResult(allowed=True, reason="Kelly Max — order approved")

    def _prop_check(self, order: OrderRequest, account: AccountState) -> RiskResult:
        """Prop Trailing mode — full risk gate protocol."""

        # ── GATE 1: Session Halt ───────────────────────────────────────────
        if self.session_halted:
            return RiskResult(
                allowed=False,
                reason=f"BLOCKED: {BlockReason.STREAK_HALT.value}",
                block_reason=BlockReason.STREAK_HALT,
            )

        # ── GATE 2: Daily Loss Cap ─────────────────────────────────────────
        daily_loss_pct = abs(account.daily_pnl) / account.balance if account.balance > 0 else 0

        if daily_loss_pct >= self.DAILY_LOSS_WARNING_PCT:
            if daily_loss_pct >= self.DAILY_LOSS_CAP_PCT:
                return RiskResult(
                    allowed=False,
                    reason=f"BLOCKED: {BlockReason.DAILY_LOSS_CAP.value} "
                           f"({daily_loss_pct:.3f}% >= {self.DAILY_LOSS_CAP_PCT:.3f}%)",
                    block_reason=BlockReason.DAILY_LOSS_CAP,
                )
            # Warning zone — allow but log
            logger.warning(
                f"[{order.asset_name}] Daily loss warning: {daily_loss_pct:.3f}% "
                f"(cap: {self.DAILY_LOSS_CAP_PCT:.3f}%)"
            )

        # ── GATE 3: Trailing Drawdown ──────────────────────────────────────
        if account.intraday_peak_equity > 0:
            current_dd = (account.intraday_peak_equity - account.equity) / account.intraday_peak_equity

            if current_dd >= self.TRAILING_DD_LIMIT:
                return RiskResult(
                    allowed=False,
                    reason=f"BLOCKED: {BlockReason.TRAILING_DD_BREACH.value} "
                           f"({current_dd:.2%} >= {self.TRAILING_DD_LIMIT:.2%})",
                    block_reason=BlockReason.TRAILING_DD_BREACH,
                )

            if current_dd >= (self.TRAILING_DD_LIMIT - 0.015):
                # Within 1.5% of DD limit — derisk
                self.is_derisked = True
                logger.warning(
                    f"[{order.asset_name}] DD derisk active: {current_dd:.2%} "
                    f"(limit: {self.TRAILING_DD_LIMIT:.2%})"
                )

        # ── GATE 4: Position Size ──────────────────────────────────────────
        risk_per_trade = abs(order.entry_price - order.sl_price) * order.contracts * order.tick_value

        # Determine max risk based on phase and derisk state
        if self.is_derisked:
            max_risk_pct = self.PHASE1_RISK_PCT * 0.5  # Half of Phase 1
        elif self.is_phase2:
            max_risk_pct = self.PHASE2_RISK_PCT
        else:
            max_risk_pct = self.PHASE1_RISK_PCT

        max_risk = account.balance * max_risk_pct

        if risk_per_trade > max_risk:
            adjusted = int(max_risk / (abs(order.entry_price - order.sl_price) * order.tick_value))
            if adjusted < 1:
                return RiskResult(
                    allowed=False,
                    reason=f"BLOCKED: {BlockReason.SIZE_EXCEEDS_MAX.value} "
                           f"(risk ${risk_per_trade:.0f} > max ${max_risk:.0f})",
                    block_reason=BlockReason.SIZE_EXCEEDS_MAX,
                )
            return RiskResult(
                allowed=True,
                reason=f"Size adjusted from {order.contracts} to {adjusted} "
                       f"(max risk: {max_risk_pct:.2%})",
                adjusted_contracts=adjusted,
            )

        # ── GATE 5: Streak Reduction ───────────────────────────────────────
        if account.consecutive_losses >= self.STREAK_HALT_THRESHOLD:
            self.session_halted = True
            return RiskResult(
                allowed=False,
                reason=f"BLOCKED: {BlockReason.STREAK_HALT.value} "
                       f"({account.consecutive_losses} consecutive losses)",
                block_reason=BlockReason.STREAK_HALT,
            )

        if account.consecutive_losses >= self.STREAK_REDUCTION_THRESHOLD:
            # Reduce size by 50%
            adjusted = max(order.contracts // 2, 1)
            return RiskResult(
                allowed=True,
                reason=f"Streak reduction active ({account.consecutive_losses} losses). "
                       f"Size reduced from {order.contracts} to {adjusted}",
                adjusted_contracts=adjusted,
            )

        # ── GATE 6: Correlation Cap ────────────────────────────────────────
        asset = order.asset_name.upper()
        current_exposure = account.correlated_exposure.copy()

        # Check EU+CHF correlation
        if any(x in asset for x in ["EUR", "EU"]):
            chf_exposure = current_exposure.get("CHF", 0) + current_exposure.get("USDCHF", 0)
            if chf_exposure >= self.CORRELATION_CAP_EU_CHF:
                return RiskResult(
                    allowed=False,
                    reason=f"BLOCKED: {BlockReason.CORRELATION_CAP.value} "
                           f"(EU+CHF exposure = {chf_exposure})",
                    block_reason=BlockReason.CORRELATION_CAP,
                )

        if any(x in asset for x in ["CHF", "USDCHF"]):
            eu_exposure = current_exposure.get("EU", 0) + current_exposure.get("EURUSD", 0)
            if eu_exposure >= self.CORRELATION_CAP_EU_CHF:
                return RiskResult(
                    allowed=False,
                    reason=f"BLOCKED: {BlockReason.CORRELATION_CAP.value} "
                           f"(EU+CHF exposure = {eu_exposure})",
                    block_reason=BlockReason.CORRELATION_CAP,
                )

        # ── GATE 7: Time Gate ──────────────────────────────────────────────
        current_hour = datetime.now(timezone.utc).hour
        # EST trading window: 3AM-12PM EST = 8AM-5PM UTC (approx, adjust for DST)
        if current_hour < 7 or current_hour >= 17:
            return RiskResult(
                allowed=False,
                reason=f"BLOCKED: {BlockReason.TIME_GATE.value} "
                       f"(current UTC hour: {current_hour})",
                block_reason=BlockReason.TIME_GATE,
            )

        # ── ALL GATES PASSED ───────────────────────────────────────────────
        return RiskResult(allowed=True, reason="All risk gates passed — order approved")

    def check_buffer_promotion(self, account: AccountState) -> bool:
        """
        Check if account has built enough buffer to promote from Phase 1 to Phase 2.
        Phase 1: 0.75% risk until 4% buffer built
        Phase 2: 1.0% risk after buffer confirmed
        """
        if self.is_phase2:
            return True

        # Calculate buffer from initial balance
        # This is simplified — in production you'd track initial balance separately
        buffer = account.equity - account.balance
        buffer_pct = buffer / account.balance if account.balance > 0 else 0

        if buffer_pct >= self.BUFFER_PROMOTION_PCT:
            self.is_phase2 = True
            logger.info(f"Phase 2 promoted! Buffer: {buffer_pct:.2%}")
            return True

        return False

    def check_derisk_recovery(self, account: AccountState) -> bool:
        """
        Check if derisk condition can be lifted.
        Requires 2 consecutive wins after derisk.
        """
        if not self.is_derisked:
            return True

        if account.consecutive_wins >= self.DERISK_RECOVERY_WINS:
            self.is_derisked = False
            logger.info("Derisk lifted — 2 consecutive wins achieved")
            return True

        return False

    def reset_session(self):
        """Reset session-level state (call at session start)."""
        self.session_halted = False
        # Note: is_derisked and is_phase2 persist across sessions

    def get_status(self) -> dict:
        """Get current risk litigator status for dashboard."""
        return {
            "profile": self.profile.value,
            "phase": "Phase 2" if self.is_phase2 else "Phase 1",
            "risk_pct": self.PHASE2_RISK_PCT if self.is_phase2 else self.PHASE1_RISK_PCT,
            "derisk_active": self.is_derisked,
            "session_halted": self.session_halted,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
