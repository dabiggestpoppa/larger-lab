"""
F&F (Friends & Family) Acquisition Protocol
Structural arbitrage engine — exploits gap between firm assumptions and operational reality.

The backdoor is open until proven closed.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class PatchSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FFStatus(Enum):
    ARBITRAGE = "ARBITRAGE"    # F&F backdoor confirmed open
    PATCHED = "PATCHED"        # Backdoor closed, use standard pricing
    STANDARD = "STANDARD"      # No F&F access
    UNTESTED = "UNTESTED"      # Not yet evaluated


@dataclass
class PromoDetails:
    code: str
    discount_pct: float
    new_customer_only: bool
    verified_on_official: bool
    expires_at: Optional[str]
    source_url: str  # where it was found (PropFirmMatch or official)


@dataclass
class PatchSignal:
    signal_type: str
    severity: PatchSeverity
    detected_at: str
    details: str
    action_required: str


class FFProtocol:
    """
    F&F Arbitrage Engine.
    Manages multi-account acquisition, promo verification, and patch detection.
    """

    # ─── Operational Security Rules ──────────────────────────

    OS_RULES = [
        "NEVER use the same payout wallet/crypto address across F&F accounts",
        "NEVER execute from the same IP/device simultaneously without VPS isolation",
        "NEVER use identical KYC metadata patterns where avoidable",
    ]

    def __init__(self, ff_network_size: int = 5):
        self.ff_network_size = ff_network_size  # number of F&F identities available
        self.patch_log: list[PatchSignal] = []

    def calculate_true_cost_basis(
        self,
        standard_cost: float,
        promo_discount_pct: float,
        promo_new_customer_only: bool,
        n_accounts: int,
        ff_access: bool = True,
    ) -> dict:
        """
        Calculate true cost per account with F&F arbitrage applied.

        Standard user: pays full price for accounts 2, 3, 4...
        F&F protocol: applies "New Customer" promo to ALL accounts via distinct identities.
        Cost basis stays flat at the discounted floor.
        """
        if promo_new_customer_only and not ff_access:
            # No F&F access → only first account gets promo
            total = standard_cost * (1 - promo_discount_pct) + standard_cost * (n_accounts - 1)
            per_account = total / n_accounts

            return {
                "total_cost": round(total, 2),
                "per_account": round(per_account, 2),
                "promo_applied_count": 1,
                "ff_active": False,
                "savings_vs_standard": round(standard_cost * n_accounts * promo_discount_pct, 2),
            }

        # F&F access or promo is not NCO → all accounts get promo rate
        discounted = standard_cost * (1 - promo_discount_pct)
        total = discounted * n_accounts
        per_account = discounted

        return {
            "total_cost": round(total, 2),
            "per_account": round(per_account, 2),
            "promo_applied_count": n_accounts,
            "ff_active": ff_access and promo_new_customer_only,
            "savings_vs_standard": round(standard_cost * n_accounts * promo_discount_pct, 2),
        }

    def verify_promo(
        self,
        promo: PromoDetails,
        ff_access: bool = True,
    ) -> dict:
        """
        Boolean gate: is this promo valid for our acquisition method?
        Must pass ALL conditions to be valid.
        """
        checks = {
            "code_exists": bool(promo.code),
            "verified_official": promo.verified_on_official,
            "not_expired": True,
            "accessible": True,
        }

        # Check expiration
        if promo.expires_at:
            try:
                exp = datetime.fromisoformat(promo.expires_at)
                if exp < datetime.utcnow():
                    checks["not_expired"] = False
            except ValueError:
                checks["not_expired"] = False

        # Check new customer only
        if promo.new_customer_only and not ff_access:
            checks["accessible"] = False

        all_pass = all(checks.values())

        return {
            "promo_valid": all_pass,
            "checks": checks,
            "action": "APPLY" if all_pass else "SKIP",
            "reason": "" if all_pass else self._reason_failed(checks),
        }

    def _reason_failed(self, checks: dict) -> str:
        failed = [k for k, v in checks.items() if not v]
        return f"Failed checks: {', '.join(failed)}"

    def assess_patch_risk(self, firm_name: str, signals: list[dict]) -> FFStatus:
        """
        Determine if the F&F backdoor is still open based on patch signals.
        """
        if not signals:
            return FFStatus.ARBITRAGE

        severities = [s.get("severity", "LOW") for s in signals]
        now = datetime.utcnow().isoformat()

        # Critical = immediate closure
        if PatchSeverity.CRITICAL.value in severities:
            signal = PatchSignal(
                signal_type="BACKDOOR_CLOSED",
                severity=PatchSeverity.CRITICAL,
                detected_at=now,
                details=f"{firm_name}: Critical patch signal — immediate cessation required",
                action_required="STOP all F&F scaling. Mark PATCHED.",
            )
            self.patch_log.append(signal)
            return FFStatus.PATCHED

        # High severity = strong signal
        if severities.count(PatchSeverity.HIGH.value) >= 2:
            signal = PatchSignal(
                signal_type="MULTI_HIGH_PATCH",
                severity=PatchSeverity.HIGH,
                detected_at=now,
                details=f"{firm_name}: Multiple high-severity patch signals detected",
                action_required="Verify manually. Consider marking PATCHED.",
            )
            self.patch_log.append(signal)
            return FFStatus.PATCHED

        # Medium = caution
        if PatchSeverity.MEDIUM.value in severities:
            signal = PatchSignal(
                signal_type="DEVICE_FINGERPRINT",
                severity=PatchSeverity.MEDIUM,
                detected_at=now,
                details=f"{firm_name}: Device fingerprinting or similar warning detected",
                action_required="Use fresh VPS/browser profile. Proceed with caution.",
            )
            self.patch_log.append(signal)
            return FFStatus.ARBITRAGE  # still usable but flagged

        return FFStatus.ARBITRAGE

    def generate_acquisition_plan(
        self,
        firm_name: str,
        account_size: int,
        standard_cost: float,
        promo: Optional[PromoDetails],
        n_accounts: int,
        ff_status: FFStatus,
    ) -> dict:
        """Generate full acquisition plan with OS rules + cost breakdown."""
        ff_access = ff_status == FFStatus.ARBITRAGE

        if promo:
            cost_info = self.calculate_true_cost_basis(
                standard_cost=standard_cost,
                promo_discount_pct=promo.discount_pct,
                promo_new_customer_only=promo.new_customer_only,
                n_accounts=n_accounts,
                ff_access=ff_access,
            )
        else:
            cost_info = {
                "total_cost": standard_cost * n_accounts,
                "per_account": standard_cost,
                "promo_applied_count": 0,
                "ff_active": False,
                "savings_vs_standard": 0,
            }

        return {
            "firm": firm_name,
            "account_size": account_size,
            "n_accounts": n_accounts,
            "ff_status": ff_status.value,
            "cost_breakdown": cost_info,
            "os_rules": self.OS_RULES,
            "max_recommended": min(n_accounts, self.ff_network_size),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_patch_summary(self) -> list[dict]:
        """Return all patch signals as dicts."""
        return [
            {
                "type": s.signal_type,
                "severity": s.severity.value,
                "detected": s.detected_at,
                "details": s.details,
                "action": s.action_required,
            }
            for s in self.patch_log
        ]
