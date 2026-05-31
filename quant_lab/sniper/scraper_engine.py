"""
Phase 1: Real Scraper Engine for PropFirmMatch + PayoutJunction
Calibrated against live DOM (2026-05-30 browser scrape).

DOM Structure (PropFirmMatch):
  - TWO TABS: Forex (CFD-like: indices, metals, energy, stocks, crypto) | Futures
  - Comparison table: <TABLE> with columns FIRM | RANK/REVIEWS | COUNTRY | YEARS | ASSETS | PLATFORMS | MAX ALLOCATIONS | PROMO | ACTIONS
  - Nav: Forex | Futures | Crypto buttons (top nav bar, NOT tabs within page)
  - Forex tab URL: loads table under same page (nav button click, no URL change)
  - Futures tab URL: https://propfirmmatch.com/futures
  - Firm detail pages: /{category}/prop-firms/{slug}
  - Promo data in table: e.g. "50%OFF\nMATCH" (discount % + code)
  - Individual firm page tabs: Overview | Challenges (N) | Reviews (N) | Offers (N) | Announcements | Payouts
  - Assets column (Forex): comma-separated list like "Crypto,Energy,FX,Indices,Metals"
  - Assets column (Futures): typically empty or shows platform codes

Anti-bot: Cloudflare Turnstile — requires Scrapling StealthyFetcher or CloakBrowser.

Targets:
  - https://propfirmmatch.com/futures  → futures firm listings, pricing, promos
  - https://propfirmmatch.com          → forex/CFD firm listings (after clicking Forex nav button)
  - https://propfirmmatch.com/futures/prop-firms/{slug}  → futures firm detail pages
  - https://payoutjunction.com/        → payout verification data
"""

import json
import time
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .ontology_mapper import OntologyMapper, PropFirmOntology

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)


class PropFirmMatchScraper:
    """
    Scrapes PropFirmMatch futures directory.

    TWO-PASS APPROACH:
      Pass 1: Scrape /futures comparison table → firm names, ratings, promos, max allocations
      Pass 2: Visit each firm's detail page → drawdown rules, consistency, payout, instruments
    """

    FUTURES_URL = "https://propfirmmatch.com/futures"
    FOREX_URL = "https://propfirmmatch.com"  # Forex tab loads on main page
    FIRM_URL_TEMPLATE = "https://propfirmmatch.com/futures/prop-firms/{slug}"
    FOREX_FIRM_URL_TEMPLATE = "https://propfirmmatch.com/prop-firms/{slug}"

    # Tab categories
    CATEGORY_FOREX = "forex"
    CATEGORY_FUTURES = "futures"

    # Known firm name → slug mapping (from live DOM data)
    KNOWN_FIRM_SLUGS = {
        # Futures
        "my funded futures": "my-funded-futures",
        "topstep": "topstep",
        "apex trader funding": "apex-trader-funding",
        "take profit trader": "take-profit-trader",
        "fundednext futures": "fundednext-futures",
        "lucid trading": "lucid-trading",
        "alpha futures": "alpha-futures",
        "tradeify": "tradeify",
        "top one futures": "top-one-futures",
        "funded futures family": "funded-futures-family",
        "e8 futures": "e8-futures",
        "goat funded futures": "goat-funded-futures",
        "traders launch": "traders-launch",
        "tradeday": "tradeday",
        "futureselite": "futureselite",
        # Forex/CFD
        "fundingpips": "fundingpips",
        "the5ers": "the-5-ers",
        "goat funded trader": "goat-funded-trader",
        "brightfunded": "brightfunded",
        "e8 markets": "e8-markets",
        "alpha capital": "alpha-capital-group",
        "crypto fund trader": "crypto-fund-trader",
        "blue guardian": "blue-guardian",
        "blueberry funded": "blueberry-funded",
        "maven": "maven",
        "besquared trading": "besquared-trading",
        "trade the pool": "trade-the-pool",
        "for traders": "for-traders",
    }

    def __init__(self, stealth: bool = True):
        self.stealth = stealth
        self.last_result: Optional[list[dict]] = None
        self._scrapling_available = False
        self._check_deps()

    def _check_deps(self):
        try:
            import scrapling
            self._scrapling_available = True
        except ImportError:
            pass

    def scrape(self) -> list[dict]:
        """Full two-pass scrape: summary table + individual firm pages."""
        if self._scrapling_available:
            return self._scrape_with_scrapling()
        return []

    def scrape_table_only(self) -> list[dict]:
        """Pass 1 only: scrape the comparison table for firm names, promos, allocations."""
        if self._scrapling_available:
            return self._scrape_table_scrapling()
        return []

    # ── SCRAPLING PATH ──────────────────────────────────────

    def _scrape_with_scrapling(self) -> list[dict]:
        """Full two-pass scrape using Scrapling StealthyFetcher."""
        from scrapling.fetchers import StealthyFetcher

        # Pass 1: Comparison table
        try:
            page = StealthyFetcher.fetch(
                self.BASE_URL, headless=True, network_idle=True, timeout=30000,
            )
            basic_firms = _parse_table_from_page(page)
        except Exception as e:
            print(f"[Scrapling] Table fetch failed: {e}")
            return []

        # Pass 2: Detail pages (limit to avoid hammering)
        detailed = []
        for firm in basic_firms[:8]:  # top 8 firms for now
            slug = firm.get("_slug") or self._slugify(firm["name"])
            detail_url = self.FIRM_URL_TEMPLATE.format(slug=slug)
            try:
                time.sleep(1.5)  # polite delay
                detail_page = StealthyFetcher.fetch(
                    detail_url, headless=True, network_idle=True, timeout=25000,
                )
                details = _parse_firm_detail_from_page(detail_page)
                firm.update(details)
                detailed.append(firm)
            except Exception as e:
                print(f"[Scrapling] Detail fetch failed for {firm['name']}: {e}")
                detailed.append(firm)  # keep basic data at least

        self.last_result = detailed
        return detailed

    def _scrape_table_scrapling(self) -> list[dict]:
        """Scrape only the comparison table."""
        from scrapling.fetchers import StealthyFetcher
        try:
            page = StealthyFetcher.fetch(
                self.BASE_URL, headless=True, network_idle=True, timeout=30000,
            )
            firms = _parse_table_from_page(page)
            self.last_result = firms
            return firms
        except Exception as e:
            print(f"[Scrapling] Table only fetch failed: {e}")
            return []

    # ── FIRM SLUG RESOLUTION ────────────────────────────────

    def _slugify(self, name: str) -> str:
        """Convert firm name to URL slug."""
        clean = name.lower().strip()
        # Remove rank prefix like "4\n\n" or "NEW\n\n"
        clean = re.sub(r'^(new\s+|\d+\s+)', '', clean)
        # Check known slugs first
        if clean in self.KNOWN_FIRM_SLUGS:
            return self.KNOWN_FIRM_SLUGS[clean]
        # Generic: lowercase, replace spaces with hyphens, remove special chars
        slug = re.sub(r'[^a-z0-9\s-]', '', clean)
        slug = re.sub(r'\s+', '-', slug.strip())
        return slug

    # ── DUAL-TAB SCRAPING (FUTURES + FOREX/CFD) ──────────────

    def scrape_both_tabs(self) -> dict:
        """
        Scrape both Futures and Forex tabs.
        Returns {"futures": [...], "forex": [...], "combined": [...]}.
        """
        return {
            "futures": self.scrape(category="futures"),
            "forex": self.scrape(category="forex"),
            "combined": self.scrape(category="futures") + self.scrape(category="forex"),
        }

    def scrape(self, category: str = "futures") -> list[dict]:
        """
        Scrape a specific category tab.
        category: "futures" | "forex"
        """
        if category == "forex":
            url = self.FOREX_URL
        else:
            url = self.FUTURES_URL

        if self._scrapling_available:
            return self._scrape_table_scrapling_url(url, category)
        return []

    def _scrape_table_scrapling_url(self, url: str, category: str) -> list[dict]:
        """Scrape comparison table from a specific URL with category tagging."""
        from scrapling import StealthyFetcher
        try:
            page = StealthyFetcher.get(url, stealthy=True)
            firms = _parse_table_from_page(page)
            for f in firms:
                f["_category"] = category
                f["_scraped_at"] = datetime.utcnow().isoformat()
            return firms
        except Exception as e:
            print(f"[Scrapling] {category} table fetch failed: {e}")
            return []

    def _scrape_with_scrapling(self) -> list[dict]:
        """Legacy: scrape only futures (default behavior)."""
        from scrapling import StealthyFetcher
        try:
            page = StealthyFetcher.get(self.FUTURES_URL, stealthy=True)
            basic_firms = _parse_table_from_page(page)
        except Exception as e:
            print(f"[Scrapling] Table fetch failed: {e}")
            return []
        detailed = []
        for firm in basic_firms[:8]:
            slug = self.KNOWN_FIRM_SLUGS.get(firm["name"].lower(), self._slugify(firm["name"]))
            detail_url = self.FIRM_URL_TEMPLATE.format(slug=slug)
            try:
                time.sleep(1.5)
                detail_page = StealthyFetcher.get(detail_url, stealthy=True)
                details = _parse_firm_detail_from_page(detail_page)
                firm.update(details)
                detailed.append(firm)
            except Exception as e:
                print(f"[Scrapling] Detail fetch failed for {firm['name']}: {e}")
                detailed.append(firm)
        self.last_result = detailed
        return detailed

    def _scrape_table_scrapling(self) -> list[dict]:
        """Legacy: scrape only futures table."""
        return self._scrape_table_scrapling_url(self.FUTURES_URL, "futures")

    # ── SNAPSHOTS & CHANGE DETECTION ────────────────────────

    def save_snapshot(self, firms: list[dict]) -> Path:
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
        # Promo changes
        prev_promos = {(f.get("name") or ""): (f.get("promo") or {}) for f in previous.get("firms", [])}
        for f in curr_names & prev_names:
            cp = next((x for x in current if x.get("name") == f), {}).get("promo", {})
            pp = prev_promos.get(f, {})
            if cp != pp:
                changes.append({"type": "PROMO_CHANGE", "firm": f, "old": pp, "new": cp})
        self.save_snapshot(current)
        return changes


# ── PARSERS (DOM-specific, calibrated 2026-05-30) ─────────────────

def _parse_table_from_page(page) -> list[dict]:
    """
    Parse PropFirmMatch /futures comparison table.
    Calibrated: table has <tbody> with <td> cells per row.
    Columns: FIRM | RANK/REVIEWS | COUNTRY | YEARS | ASSETS | PLATFORMS | MAX_ALLOC | PROMO | ACTIONS
    """
    firms = []
    rows = page.css('table tbody tr')

    for row in rows:
        cells = row.css('td')
        if len(cells) < 7:
            continue

        # Cell 0: Firm name (may include NEW badge + rank number)
        firm_text = cells[0].text() or ""
        firm_name = _clean_firm_name(firm_text)
        if not firm_name:
            continue

        # Cell 1: Rank + Reviews → e.g. "4.6\n\n53\n\nreviews"
        rank_text = cells[1].text() or ""
        rating, review_count = _parse_rank_reviews(rank_text)

        # Cell 2: Country
        country = (cells[2].text() or "").strip()

        # Cell 3: Years in operation
        years_text = (cells[3].text() or "").strip()
        years = _parse_years(years_text)

        # Cell 5: Platforms → e.g. "Tr\nMo\n+ 7" (abbreviated platform names)
        platforms_text = (cells[5].text() or "").strip()
        platforms = _parse_platforms(platforms_text)

        # Cell 6: Max Allocations → e.g. "$450K" or "$3.2M"
        max_alloc_text = (cells[6].text() or "").strip()
        max_alloc = _parse_max_allocation(max_alloc_text)

        # Cell 7: Promo → e.g. "50%OFF\n\nMATCH" or empty
        promo_text = (cells[7].text() or "").strip() if len(cells) > 7 else ""
        promo = _parse_promo(promo_text)

        firms.append({
            "name": firm_name,
            "rating": rating,
            "review_count": review_count,
            "country": country,
            "years": years,
            "platforms": platforms,
            "max_allocation": max_alloc,
            "promo": promo,
            "drawdown": {},      # filled in Pass 2
            "consistency": {},   # filled in Pass 2
            "payout": {},        # filled in Pass 2
            "scaling": {},
            "instruments": [],
            "_slug": "",
            "_raw_rank_text": rank_text[:100],
        })

    return firms


def _parse_firm_detail_from_page(page) -> dict:
    """
    Parse individual firm detail page.
    Calibrated: has tabbed sections — Overview, Consistency Rules, Firm Rules, Challenges, Payout Policy.
    """
    details = {
        "drawdown": {},
        "consistency": {},
        "payout": {},
        "instruments": [],
        "firm_rules": [],
    }

    # Get full page text for regex extraction
    full_text = page.text() or ""

    # ── CONSISTENCY RULES ──
    # Pattern: "profit on any single day cannot exceed XX% of the total profit"
    cons_match = re.search(
        r'profit on any single day cannot exceed (\d+)%', full_text, re.IGNORECASE
    )
    if cons_match:
        details["consistency"]["active"] = True
        details["consistency"]["max_day_pct"] = float(cons_match.group(1))
    else:
        details["consistency"]["active"] = False

    # ── DRAWDOWN ──
    # Pattern: "Max Loss" or "Max Drawdown" or trailing DD mentions
    dd_match = re.search(r'max\s*(?:loss|drawdown)[:\s]+\$?([\d,]+)', full_text, re.IGNORECASE)
    if dd_match:
        dd_val = float(dd_match.group(1).replace(",", ""))
        details["drawdown"]["max_dd_amount"] = dd_val

    # Trailing DD detection
    if re.search(r'trailing\s*(?:drawdown|loss|dd)', full_text, re.IGNORECASE):
        details["drawdown"]["trailing_type"] = "eod"
    elif re.search(r'intraday\s*(?:drawdown|loss|dd)', full_text, re.IGNORECASE):
        details["drawdown"]["trailing_type"] = "intraday"
    else:
        details["drawdown"]["trailing_type"] = "static"

    # ── PAYOUT ──
    payout_match = re.search(r'payout[:\s]+(\d+)\s*days?', full_text, re.IGNORECASE)
    if payout_match:
        details["payout"]["cycle_days"] = int(payout_match.group(1))

    # ── INSTRUMENTS ──
    known_instruments = ["ES", "NQ", "CL", "GC", "YM", "RTY", "SI", "HG", "NG", "ZB", "ZN", "ZW", "ZC"]
    found_instruments = []
    for inst in known_instruments:
        if re.search(rf'\b{inst}\b', full_text):
            found_instruments.append(inst)
    details["instruments"] = found_instruments

    # ── NEWS TRADING ──
    details["news_restricted"] = bool(re.search(r'news\s*(?:restrict|prohibit|ban)', full_text, re.IGNORECASE))

    # ── OVERNIGHT HOLDING ──
    details["overnight_allowed"] = not bool(re.search(r'overnight\s*(?:not\s*allowed|prohibit|close)', full_text, re.IGNORECASE))

    return details


# ── TEXT CLEANUP HELPERS ─────────────────────────────────────

def _clean_firm_name(text: str) -> str:
    """Extract clean firm name from table cell text.
    Input: '4\n\nMy Funded Futures\n\n50992' or 'NEW\n\nLucid Trading\n\n12603'
    Output: 'My Funded Futures'
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # Filter out: rank numbers, NEW badge, numeric IDs
    name_lines = []
    for line in lines:
        if line.upper() == 'NEW':
            continue
        if re.match(r'^\d+$', line):  # pure number = rank or ID
            continue
        if re.match(r'^\d+\.\d+$', line):  # rating like 4.5
            continue
        name_lines.append(line)
    return ' '.join(name_lines) if name_lines else ""


def _parse_rank_reviews(text: str) -> tuple:
    """Parse '4.6\n\n53\n\nreviews' → (4.6, 53)"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    rating = 0.0
    reviews = 0
    for line in lines:
        if re.match(r'^\d+\.\d+$', line):
            rating = float(line)
        elif re.match(r'^\d+$', line):
            reviews = int(line)
    return rating, reviews


def _parse_years(text: str) -> int:
    """Parse '10+' → 10, '2' → 2"""
    m = re.search(r'(\d+)', text)
    return int(m.group(1)) if m else 0


def _parse_platforms(text: str) -> list:
    """Parse 'Tr\nMo\n+ 7' → ['Tradovate', 'Mo'] (abbreviated platform names)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    # Remove the "+ N" count line
    return [l for l in lines if not re.match(r'^\+\s*\d+$', l)]


def _parse_max_allocation(text: str) -> int:
    """Parse '$450K' → 450000, '$3.2M' → 3200000"""
    text = text.strip().replace('$', '').replace(',', '')
    m = re.match(r'([\d.]+)\s*(K|M|B)?', text, re.IGNORECASE)
    if not m:
        return 0
    val = float(m.group(1))
    suffix = (m.group(2) or '').upper()
    if suffix == 'K':
        val *= 1000
    elif suffix == 'M':
        val *= 1_000_000
    elif suffix == 'B':
        val *= 1_000_000_000
    return int(val)


def _parse_promo(text: str) -> dict:
    """Parse '50%OFF\n\nMATCH' → {discount_pct: 50, code: 'MATCH'}"""
    result = {}
    if not text:
        return result
    # Discount percentage
    pct = re.search(r'(\d+)%\s*(?:OFF|DISCOUNT)', text, re.IGNORECASE)
    if pct:
        result["discount_pct"] = int(pct.group(1))
    # Promo code (uppercase word after discount, typically 4-10 chars)
    code = re.search(r'\n([A-Z]{4,12})\s*$', text)
    if code:
        result["code"] = code.group(1)
    else:
        # Try inline: "MATCH" on its own line
        for line in text.split('\n'):
            line = line.strip()
            if line and re.match(r'^[A-Z]{4,12}$', line):
                result["code"] = line
                break
    result["new_customer_only"] = True  # PropFirmMatch promos are typically new-customer
    return result


# ── PAYOUT JUNCTION SCRAPER ─────────────────────────────────

class PayoutJunctionScraper:
    """
    Scrapes PayoutJunction.com for payout verification data.
    JS-rendered SPA — requires Scrapling/CloakBrowser.
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
        if not self._scrapling_available:
            return []
        try:
            from scrapling.fetchers import StealthyFetcher
            page = StealthyFetcher.fetch(self.URL, headless=True, network_idle=True, timeout=25000)
            # PayoutJunction is a JS SPA — data loads after network idle
            text = page.text() or ""
            return self._parse_payout_data(text)
        except Exception as e:
            print(f"[PayoutJunction] Scrape failed: {e}")
            return []

    def _parse_payout_data(self, text: str) -> list[dict]:
        """Parse payout data from page text."""
        results = []
        # Pattern: firm name + payout days + denial info
        # Calibrated: TBD after first successful scrape
        return results

    def get_firm_payout_data(self, firm_name: str) -> dict:
        """Get payout data for a specific firm. Placeholder until live data."""
        return OntologyMapper.from_payout_junction({
            "firm_name": firm_name,
            "avg_days": 0,
            "denial_pct": 0.0,
            "total_reviews": 0,
            "last_verified": "",
            "reliability_score": 0.0,
        })


# ── TEST HARNESS ─────────────────────────────────────────────

def test_scraper():
    """Verify import chain and ontology mapping."""
    from .ontology_mapper import PropFirmOntology, OntologyMapper
    print("[OK] Imports OK")

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
    ont = OntologyMapper.from_propfirm_match(sample)
    print(f"  Firm: {ont.firm_name}, BW=${ont.risk_bandwidth:,.0f}, CoC={ont.cost_of_capital():.4f}")

    # Test text parsers
    assert _clean_firm_name("4\n\nMy Funded Futures\n\n50992") == "My Funded Futures"
    assert _clean_firm_name("NEW\n\nLucid Trading\n\n12603") == "Lucid Trading"
    assert _parse_max_allocation("$450K") == 450000
    assert _parse_max_allocation("$3.2M") == 3200000
    assert _parse_promo("50%OFF\n\nMATCH") == {"discount_pct": 50, "code": "MATCH", "new_customer_only": True}
    assert _parse_rank_reviews("4.6\n\n53\n\nreviews") == (4.6, 53)
    print("[OK] All parser tests passed")
    return True


if __name__ == "__main__":
    test_scraper()
