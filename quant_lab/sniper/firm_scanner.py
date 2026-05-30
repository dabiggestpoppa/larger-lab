"""
Prop Firm Scanner
Scrapes PropFirmMatch.com/futures and cross-references official sites.
Identifies active promos, verifies terms, flags changes.
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

# Optional: use requests/bs4 if available, otherwise fallback to web_fetch
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)


@dataclass
class ScannedFirm:
    name: str
    source_url: str
    account_sizes: list[int]
    costs: dict  # {size: cost}
    promo_code: Optional[str]
    promo_discount_pct: float
    promo_new_customer_only: bool
    promo_expires: Optional[str]
    max_daily_loss_pct: float
    max_trailing_dd_pct: float
    consistency_rule: dict
    payout_cycle_days: int
    payout_method: str
    scaling_rules: dict
    scraped_at: str
    content_hash: str  # for change detection


from dataclasses import dataclass


class FirmScanner:
    """
    Scans prop firm listings and cross-references with official sites.
    Uses web_fetch (lightweight) or requests+bs4 (full scrape) depending on availability.
    """

    PROPFIRM_MATCH_URL = "https://propfirmmatch.com/futures-prop-firms"
    KNOWN_FIRMS = [
        {"name": "Topstep", "url": "https://www.topstep.com"},
        {"name": "Apex Trader Funding", "url": "https://www.atf.com"},
        {"name": "My Funded Futures", "url": "https://www.myfundedfutures.com"},
        {"name": "TickFundedTrader", "url": "https://www.tickfundedtrader.com"},
        {"name": "The Trading Pit", "url": "https://www.thetradingpit.com"},
        {"name": "Funded Trading Plus", "url": "https://www.fundedtradingplus.com"},
        {"name": "BluFunded", "url": "https://www.blufunded.com"},
        {"name": "MyForexFunds", "url": "https://www.myforexfunds.com"},
    ]

    def __init__(self, use_web_fetch: bool = True):
        self.use_web_fetch = use_web_fetch or not HAS_REQUESTS
        self.last_scan: Optional[list[ScannedFirm]] = None

    def scan_all(self) -> list[ScannedFirm]:
        """
        Full scan: PropFirmMatch + individual firm sites.
        Returns list of ScannedFirm objects.
        """
        results = []

        # Step 1: Scan PropFirmMatch directory
        pfm_data = self._scan_propfirm_match()
        results.extend(pfm_data)

        # Step 2: Cross-reference known firms
        for firm_info in self.KNOWN_FIRMS:
            firm_data = self._scan_official_site(firm_info["name"], firm_info["url"])
            if firm_data:
                results.append(firm_data)

        # Step 3: Deduplicate by name (official site takes priority)
        seen = {}
        for r in results:
            seen[r.name] = r  # last one wins (official > directory)

        self.last_scan = list(seen.values())
        return self.last_scan

    def _scan_propfirm_match(self) -> list[ScannedFirm]:
        """Scrape PropFirmMatch futures directory."""
        results = []

        if self.use_web_fetch:
            # Use web_fetch via exec (lightweight)
            # This is a placeholder — actual scrape would parse the markdown
            return results

        if HAS_REQUESTS:
            try:
                resp = requests.get(self.PROPFIRM_MATCH_URL, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                # Parse firm cards — structure depends on site layout
                # This is a template; actual selectors need to be calibrated
                results = self._parse_pfm_html(soup)
            except Exception as e:
                print(f"⚠️ PropFirmMatch scrape failed: {e}")

        return results

    def _parse_pfm_html(self, soup) -> list[ScannedFirm]:
        """Parse PropFirmMatch HTML — template for when BS4 is available."""
        results = []
        # Placeholder: actual CSS selectors needed
        # firm_cards = soup.select(".firm-card")
        # for card in firm_cards:
        #     name = card.select_one(".firm-name").text.strip()
        #     ...
        return results

    def _scan_official_site(self, name: str, url: str) -> Optional[ScannedFirm]:
        """Scan individual firm's official site for current pricing/promos."""
        if not HAS_REQUESTS:
            return None

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            content = resp.text
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # Basic parsing — would need site-specific selectors
            # This is a template structure
            return ScannedFirm(
                name=name,
                source_url=url,
                account_sizes=[],
                costs={},
                promo_code=None,
                promo_discount_pct=0.0,
                promo_new_customer_only=False,
                promo_expires=None,
                max_daily_loss_pct=0.05,
                max_trailing_dd_pct=0.10,
                consistency_rule={},
                payout_cycle_days=14,
                payout_method="Crypto",
                scaling_rules={},
                scraped_at=datetime.utcnow().isoformat(),
                content_hash=content_hash,
            )
        except Exception:
            return None

    def detect_changes(self, current: list[ScannedFirm]) -> list[dict]:
        """
        Compare current scan against last saved snapshot.
        Returns list of changes detected.
        """
        changes = []
        snapshot_file = SNAPSHOT_DIR / "last_scan.json"

        if not snapshot_file.exists():
            self._save_snapshot(current)
            return [{"type": "INIT", "msg": "First scan — baseline saved"}]

        with open(snapshot_file) as f:
            previous = json.load(f)

        prev_by_name = {f["name"]: f for f in previous.get("firms", [])}

        for firm in current:
            prev = prev_by_name.get(firm.name)
            if not prev:
                changes.append({
                    "type": "NEW_FIRM",
                    "firm": firm.name,
                    "msg": f"New firm detected: {firm.name}",
                })
                continue

            # Check content hash for any changes
            if firm.content_hash != prev.get("content_hash", ""):
                changes.append({
                    "type": "CONTENT_CHANGE",
                    "firm": firm.name,
                    "msg": f"Content changed on {firm.name} — review for promo/term updates",
                })

            # Check promo changes
            if firm.promo_code != prev.get("promo_code"):
                changes.append({
                    "type": "PROMO_CHANGE",
                    "firm": firm.name,
                    "old": prev.get("promo_code"),
                    "new": firm.promo_code,
                    "msg": f"Promo changed: {prev.get('promo_code')} → {firm.promo_code}",
                })

        self._save_snapshot(current)
        return changes

    def _save_snapshot(self, firms: list[ScannedFirm]):
        """Save scan snapshot for change detection."""
        snapshot = {
            "scraped_at": datetime.utcnow().isoformat(),
            "firms": [
                {
                    "name": f.name,
                    "source_url": f.source_url,
                    "account_sizes": f.account_sizes,
                    "costs": f.costs,
                    "promo_code": f.promo_code,
                    "promo_discount_pct": f.promo_discount_pct,
                    "content_hash": f.content_hash,
                }
                for f in firms
            ],
        }
        with open(SNAPSHOT_DIR / "last_scan.json", "w") as f:
            json.dump(snapshot, f, indent=2)

    def format_scan_results(self, firms: list[ScannedFirm]) -> str:
        """Format scan results for display."""
        if not firms:
            return "⚠️ No firms scanned. Check connectivity or enable requests+bs4."

        lines = [f"📡 SCAN RESULTS — {len(firms)} firms | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"]
        lines.append("")

        for f in firms:
            promo_str = ""
            if f.promo_code:
                nco = " [NCO]" if f.promo_new_customer_only else ""
                promo_str = f" | Promo: {f.promo_code} (-{f.promo_discount_pct*100:.0f}%{nco})"

            sizes = f.account_sizes or ["—"]
            lines.append(
                f"  • {f.name}{promo_str}\n"
                f"    Sizes: {sizes} | Payout: {f.payout_cycle_days}d | "
                f"DD: {f.max_daily_loss_pct:.1%}/{f.max_trailing_dd_pct:.1%}"
            )

        return "\n".join(lines)
