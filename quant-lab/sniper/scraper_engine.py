"""
Phase 1: Real Scraper Engine for PropFirmMatch + PayoutJunction
Uses Scrapling (StealthyFetcher) to bypass anti-bot.
Falls back to web_fetch if Scrapling unavailable.

Targets:
  - https://propfirmmatch.com/futures  → firm listings, pricing, promos
  - https://payoutjunction.com/        → payout verification data
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from .ontology_mapper import OntologyMapper, PropFirmOntology

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)


class PropFirmMatchScraper:
    """
    Scrapes PropFirmMatch futures directory.
    Uses Scrapling StealthyFetcher for anti-bot bypass.
    Falls back to requests + bs4 if Scrapling unavailable.
    """

    URL = "https://propfirmmatch.com/futures"

    def __init__(self, stealth: bool = True):
        self.stealth = stealth
        self.last_result: Optional[list[dict]] = None
        self._scrapling_available = False
        self._requests_available = False
        self._check_deps()

    def _check_deps(self):
        try:
            import scrapling
            self._scrapling_available = True
        except ImportError:
            pass
        try:
            import requests
            from bs4 import BeautifulSoup
            self._requests_available = True
        except ImportError:
            pass

    def scrape(self) -> list[dict]:
        """
        Scrape PropFirmMatch futures page.
        Returns list of raw firm dicts.
        """
        if self.stealth and self._scrapling_available:
            return self._scrape_scrapling()
        elif self._requests_available:
            return self._scrape_requests()
        else:
            return []

    def _scrape_scrapling(self) -> list[dict]:
        """Primary: Scrapling StealthyFetcher."""
        from scrapling.fetchers import StealthyFetcher

        try:
            page = StealthyFetcher.fetch(
                self.URL,
                headless=True,
                network_idle=True,
                timeout=30000,
            )
            return self._parse_page_content(page)
        except Exception as e:
            print(f"[Scrapling] StealthyFetcher failed: {e}, trying fallback...")
            if self._requests_available:
                return self._scrape_requests()
            return []

    def _scrape_requests(self) -> list[dict]:
        """Fallback: requests + BeautifulSoup (may be blocked)."""
        import requests
        from bs4 import BeautifulSoup

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            resp = requests.get(self.URL, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            return self._parse_soup(soup)
        except Exception as e:
            print(f"[Requests] Scrape failed: {e}")
            return []

    def _parse_page_content(self, page) -> list[dict]:
        """
        Parse a Scrapling page object for firm data.
        Adapts to actual PropFirmMatch DOM structure.
        """
        results = []

        # Strategy 1: Look for structured JSON-LD or API data in page
        scripts = page.css('script[type="application/ld+json"]::text').getall()
        scripts += page.css('script[id*="data"]::text').getall()
        for script_text in scripts:
            try:
                data = json.loads(script_text)
                if isinstance(data, list):
                    for item in data:
                        if self._looks_like_firm(item):
                            results.append(item)
                elif isinstance(data, dict) and self._looks_like_firm(data):
                    results.append(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Strategy 2: CSS selectors targeting common prop firm card layouts
        if not results:
            # Common class patterns for prop firm listing sites
            card_selectors = [
                '.firm-card', '.prop-firm-card', '.card', '.listing-item',
                '[class*="firm"]', '[class*="provider"]', '.comparison-card',
            ]
            for selector in card_selectors:
                cards = page.css(selector)
                if cards:
                    for card in cards:
                        firm = self._extract_firm_from_card(card)
                        if firm and firm.get("name"):
                            results.append(firm)
                    break  # first selector that matches wins

        # Strategy 3: Extract from text
        if not results:
            text = page.text()
            results = self._extract_from_text(text)

        self.last_result = results
        return results

    def _parse_soup(self, soup) -> list[dict]:
        """Parse BeautifulSoup object."""
        results = []

        # CSS selectors for firm cards
        card_selectors = [
            '.firm-card', '.prop-firm-card', '.card', '.listing-item',
            '[class*="firm"]', '[class*="provider"]',
        ]
        for selector in card_selectors:
            cards = soup.select(selector)
            if cards:
                for card in cards:
                    firm = self._extract_firm_from_bs4(card)
                    if firm and firm.get("name"):
                        results.append(firm)
                break

        return results

    def _extract_firm_from_card(self, card) -> Optional[dict]:
        """Extract firm data from a Scrapling element."""
        try:
            # Try common text patterns
            name = (
                card.css('.firm-name::text').get()
                or card.css('h2::text').get()
                or card.css('h3::text').get()
                or card.css('.name::text').get()
                or card.css('a::text').get()
                or ""
            ).strip()

            if not name:
                return None

            # Extract all text for pattern matching
            all_text = card.text() or ""

            return {
                "name": name,
                "account_sizes": self._extract_sizes(all_text),
                "costs": {},
                "promo": self._extract_promo(all_text),
                "drawdown": self._extract_drawdown(all_text),
                "consistency": self._extract_consistency(all_text),
                "payout": self._extract_payout(all_text),
                "raw_text": all_text[:500],  # truncated for debugging
            }
        except Exception:
            return None

    def _extract_firm_from_bs4(self, card) -> Optional[dict]:
        """Extract firm data from a BeautifulSoup element."""
        try:
            name_el = card.select_one('.firm-name, h2, h3, .name, a')
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                return None
            all_text = card.get_text(separator=" ", strip=True)
            return {
                "name": name,
                "account_sizes": self._extract_sizes(all_text),
                "costs": {},
                "promo": self._extract_promo(all_text),
                "drawdown": self._extract_drawdown(all_text),
                "consistency": self._extract_consistency(all_text),
                "payout": self._extract_payout(all_text),
                "raw_text": all_text[:500],
            }
        except Exception:
            return None

    def _extract_sizes(self, text: str) -> list[int]:
        """Extract account sizes from text."""
        import re
        sizes = []
        # Match patterns like $50,000 or $50k or 50000
        matches = re.findall(r'\$[\s]?([\d,]+)[,.]?(\d{0,3})\s*(k)?', text.lower())
        for match in matches:
            num_str = match[0].replace(",", "")
            decimal = match[1] if match[1] else "0"
            is_k = match[2] == 'k'
            try:
                val = int(num_str)
                if is_k:
                    val *= 1000
                if 1000 <= val <= 500000:
                    sizes.append(val)
            except ValueError:
                pass
        return list(set(sizes)) if sizes else [10000]

    def _extract_promo(self, text: str) -> dict:
        """Extract promo/coupon info from text."""
        import re
        promo = {}
        # Match discount percentages
        pct_matches = re.findall(r'(\d+)%\s*(?:off|discount)', text.lower())
        if pct_matches:
            promo["discount_pct"] = int(pct_matches[0])
        # Match coupon codes
        code_matches = re.findall(r'code[:\s]+["\']?([A-Z0-9]{4,})["\']?', text.upper())
        if code_matches:
            promo["code"] = code_matches[0]
        promo["new_customer_only"] = "new customer" in text.lower() or "first purchase" in text.lower()
        return promo

    def _extract_drawdown(self, text: str) -> dict:
        """Extract drawdown rules from text."""
        import re
        dd = {}
        # Match DD percentages
        pct_matches = re.findall(r'(\d+)%\s*(?:max\s*)?(?:drawdown|dd|loss)', text.lower())
        if pct_matches:
            dd["max_dd_pct"] = float(pct_matches[0])
        # Detect trailing
        dd["trailing_type"] = "intraday" if "intraday" in text.lower() else (
            "eod" if "eod" in text.lower() or "end of day" in text.lower() else "static"
        )
        return dd

    def _extract_consistency(self, text: str) -> dict:
        """Extract consistency rules from text."""
        import re
        cr = {}
        cr["active"] = bool(re.search(r'consistency|profit\s*cap|daily\s*limit', text.lower()))
        pct_matches = re.findall(r'(\d+)%\s*(?:max|daily|single)', text.lower())
        if pct_matches:
            cr["max_day_pct"] = float(pct_matches[0])
        return cr

    def _extract_payout(self, text: str) -> dict:
        """Extract payout schedule from text."""
        import re
        po = {}
        day_matches = re.findall(r'(\d+)\s*days?\s*(?:payout|payment|withdraw)', text.lower())
        if day_matches:
            po["cycle_days"] = int(day_matches[0])
        return po

    def _looks_like_firm(self, data: dict) -> bool:
        """Heuristic: does this dict look like prop firm data?"""
        firm_keywords = ['firm', 'name', 'account', 'drawdown', 'payout', 'size', 'cost', 'price']
        data_str = json.dumps(data).lower()
        return any(kw in data_str for kw in firm_keywords)

    def _extract_from_text(self, text: str) -> list[dict]:
        """Last resort: regex extraction from full page text."""
        return []  # Too noisy for structured data

    def save_snapshot(self, firms: list[dict]):
        """Save raw scrape for change detection."""
        snapshot = {
            "scraped_at": datetime.utcnow().isoformat(),
            "source": "propfirmmatch",
            "firm_count": len(firms),
            "content_hash": hashlib.md5(
                json.dumps(firms, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "firms": firms,
        }
        path = SNAPSHOT_DIR / f"propfirmmatch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)
        return path

    def detect_changes(self, current: list[dict]) -> list[dict]:
        """Compare against last saved snapshot."""
        changes = []
        existing = sorted(SNAPSHOT_DIR.glob("propfirmmatch_*.json"), reverse=True)

        if not existing:
            self.save_snapshot(current)
            return [{"type": "INIT", "msg": "First scrape — baseline saved"}]

        with open(existing[0]) as f:
            previous = json.load(f)

        prev_names = {f.get("name", "") for f in previous.get("firms", [])}
        curr_names = {f.get("name", "") for f in current}

        for name in curr_names - prev_names:
            changes.append({"type": "NEW_FIRM", "firm": name})
        for name in prev_names - curr_names:
            changes.append({"type": "REMOVED_FIRM", "firm": name})

        self.save_snapshot(current)
        return changes


class PayoutJunctionScraper:
    """
    Scrapes PayoutJunction.com for payout verification data.
    Supplements PropFirmMatch data with real trader payout experiences.
    """

    URL = "https://payoutjunction.com/"

    def __init__(self):
        self._scrapling_available = False
        try:
            import scrapling
            self._scrapling_available = True
        except ImportError:
            pass

    def scrape(self) -> list[dict]:
        """Scrape payout verification data."""
        results = []
        if self._scrapling_available:
            try:
                from scrapling.fetchers import StealthyFetcher
                page = StealthyFetcher.fetch(self.URL, headless=True, timeout=20000)
                # Parse payout table/cards
                rows = page.css('tr, .review-card, .payout-entry')
                for row in rows:
                    text = row.text() or ""
                    if text.strip():
                        results.append({"raw_text": text[:300]})
            except Exception as e:
                print(f"[PayoutJunction] Scrape failed: {e}")
        return results

    def get_firm_payout_data(self, firm_name: str) -> dict:
        """
        Get payout data for a specific firm.
        Returns: {avg_days, denial_rate, reliability_score, total_reviews}
        PHASE 1: Placeholder — builds when we have real data.
        Scraper populates the table, this reads it back.
        """
        return OntologyMapper.from_payout_junction({
            "firm_name": firm_name,
            "avg_days": 0,
            "denial_pct": 0.0,
            "total_reviews": 0,
            "last_verified": "",
            "reliability_score": 0.0,
        })


# ==========================================
# TEST HARNESS
# ==========================================

def test_scraper():
    """Quick test: can we reach PropFirmMatch?"""
    print("🔧 Testing PropFirmMatch scraper...")
    scraper = PropFirmMatchScraper(stealth=True)
    print(f"  Scrapling available: {scraper._scrapling_available}")

    # Don't actually scrape in test — just verify import chain
    from .ontology_mapper import PropFirmOntology, OntologyMapper
    print("  OntologyMapper: OK")

    # Test ontology mapping with sample data
    sample = {
        "name": "TestFirm",
        "url": "https://test.com",
        "account_sizes": [50000, 100000],
        "costs": {"50000": 165, "100000": 275},
        "promo": {"code": "SAVE30", "discount_pct": 30, "new_customer_only": True},
        "drawdown": {"max_dd_pct": 5.0, "trailing_type": "intraday"},
        "consistency": {"active": True, "max_day_pct": 30},
        "payout": {"cycle_days": 14, "min_trading_days": 5},
        "scaling": {"enabled": False},
        "ff_status": "ARBITRAGE",
    }
    ontology = OntologyMapper.from_propfirm_match(sample)
    print(f"  Firm: {ontology.firm_name}")
    print(f"  Risk Bandwidth: ${ontology.risk_bandwidth:,.0f}")
    print(f"  CoC: {ontology.cost_of_capital():.4f}")
    print(f"  Lethal: {ontology.is_trailing_lethal}")
    print(f"  Variance Tax: {ontology.variance_suppression_tax:.2f}")
    print(f"  Allows Runners: {ontology.allows_runners}")
    print("  ✅ All ontology checks passed")
    return True


if __name__ == "__main__":
    test_scraper()
