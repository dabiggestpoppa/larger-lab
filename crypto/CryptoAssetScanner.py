"""
CryptoAssetScanner - Crypto Asset Discovery and Filtering Module
================================================================

Discovers crypto assets via CoinGecko (market-cap-ranked) and DexScreener
(dex-level liquidity) free public APIs, then runs every candidate through a
**Structural Validity Firewall** before the feed reaches the Symmetry Trap
Engine (quant-lab/engines/symmetry_trap.py).

Firewall criteria mirror the Symmetry Trap session / AU mechanics:
  - Minimum market cap and daily volume   -> ensures institutional-grade depth
  - Minimum age                           -> avoids death-spiral / rug-pull tokens
  - Volume stability (7d vs 30d avg)      -> mirrors Symmetry Trap volume-stability
    regime filter - unstable volume = unreliable impulse detection
  - Decay detection (liquidity drop)      -> analogous to the 80% Kill-Switch rule;
    assets that bleed >50% liquidity are flagged before they corrupt signal.

All endpoints are free/public - no API keys required.
Results are persisted to valid_crypto_assets.json (sibling of this file)
and a baseline is maintained for longitudinal decay tracking.

Author:  OWL - Crypto Feeder Pipeline (MAD Directive 2026-05-31)
Usage:
  python CryptoAssetScanner.py
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

COINGECKO_MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=250&page=1"
    "&sparkline=true&price_change_percentage=7d,30d"
)
DEXSCREENER_LATEST_URL = (
    "https://api.dexscreener.com/latest/dex/tokens/"
)

OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "valid_crypto_assets.json"
BASELINE_FILE = OUTPUT_DIR / "baseline_crypto_assets.json"

REQUEST_TIMEOUT: int = 15
MAX_RETRIES: int = 3
RETRY_BACKOFF_FACTOR: float = 1.5
RETRY_STATUS_FORCELIST: Tuple[int, ...] = (429, 500, 502, 503, 504)

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("CryptoAssetScanner")

# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------


@dataclass
class FilterConfig:
    """Adjustable thresholds - mirrors AU / tier-config pattern in Symmetry Trap."""

    min_market_cap: float = 50_000_000
    min_volume_24h: float = 1_000_000
    min_age_days: int = 30
    volume_stability_pct: float = 0.20
    decay_threshold_pct: float = 0.50


@dataclass
class AssetRecord:
    """A single asset after passing through the Structured Validity Firewall."""

    symbol: str
    name: str
    source: str  # "coingecko" | "dexscreener" | "merged"
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    volume_7d_avg: Optional[float] = None
    volume_30d_avg: Optional[float] = None
    price_usd: Optional[float] = None
    price_change_7d_pct: Optional[float] = None
    age_days: Optional[int] = None
    passed_firewall: bool = False
    decay_flag: bool = False
    decay_pct: Optional[float] = None
    scanned_at: str = ""
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.scanned_at:
            self.scanned_at = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# HTTP SESSION FACTORY
# ---------------------------------------------------------------------------


def _build_session(max_retries: int = MAX_RETRIES) -> requests.Session:
    """Return a requests.Session with retry/backoff baked in."""
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=list(RETRY_STATUS_FORCELIST),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------


class CryptoAssetScanner:
    """
    Discovery -> Firewall -> Persist pipeline for crypto asset candidates.

    Designed to feed the Symmetry Trap Engine (and downstream CEREBUS FX
    pipeline) with a curated, structurally-valid universe of crypto assets.

    Usage::

        config = FilterConfig(min_market_cap=100_000_000)
        scanner = CryptoAssetScanner(config)
        raw       = scanner.scan_assets()
        filtered  = scanner.filter_assets(raw)
        scanner.save_results(filtered)
        decayed   = scanner.check_decay(filtered)
    """

    def __init__(self, config: Optional[FilterConfig] = None) -> None:
        self.config = config or FilterConfig()
        self.session: requests.Session = _build_session()
        self._scan_timestamp: str = datetime.now(timezone.utc).isoformat()
        logger.info(
            "CryptoAssetScanner initialised - thresholds: min_mcap=%s, "
            "min_vol24h=%s, min_age=%dd, stability=%.0f%%",
            self._fmt(self.config.min_market_cap),
            self._fmt(self.config.min_volume_24h),
            self.config.min_age_days,
            self.config.volume_stability_pct * 100,
        )

    # -- Helpers ---------------------------------------------------------

    @staticmethod
    def _fmt(n: Optional[float]) -> str:
        """Human-friendly number for log lines."""
        if n is None:
            return "n/a"
        if n >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"${n / 1_000_000:.1f}M"
        return f"${n:,.0f}"

    def _get(self, url: str, label: str) -> Optional[Any]:
        """GET with manual retry layer on top of Session retries."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as exc:
                status = (
                    exc.response.status_code if exc.response is not None else "?"
                )
                if status in RETRY_STATUS_FORCELIST and attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_FACTOR**attempt
                    logger.warning(
                        "%s HTTP %s - retry %.1fs (%d/%d)",
                        label,
                        status,
                        wait,
                        attempt,
                        MAX_RETRIES,
                    )
                    time.sleep(wait)
                    continue
                logger.error("%s HTTP %s - giving up: %s", label, status, exc)
            except requests.exceptions.ConnectionError as exc:
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_FACTOR**attempt
                    logger.warning(
                        "%s connection error - retry %.1fs: %s", label, wait, exc
                    )
                    time.sleep(wait)
                    continue
                logger.error("%s connection error - giving up: %s", label, exc)
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_FACTOR**attempt
                    logger.warning("%s timeout - retry %.1fs", label, wait)
                    time.sleep(wait)
                    continue
                logger.error(
                    "%s timeout - giving up after %d attempts", label, MAX_RETRIES
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("%s unexpected error: %s", label, exc)
                return None
        return None

    # -- 1. scan_assets() ------------------------------------------------

    def scan_assets(self) -> List[AssetRecord]:
        """
        Pull asset lists from CoinGecko and DexScreener, then merge/dedupe
        on CoinGecko id (or symbol for DexScreener-only tokens).

        Returns a combined list of AssetRecord objects.
        """
        logger.info("--- Starting asset scan [%s] ---", self._scan_timestamp)

        # -- CoinGecko ---------------------------------------------------
        cg_data = self._get(COINGECKO_MARKETS_URL, "CoinGecko/markets")
        cg_records: List[AssetRecord] = []
        if cg_data and isinstance(cg_data, list):
            cg_records = self._parse_coingecko(cg_data)
            logger.info("CoinGecko returned %d assets", len(cg_records))
        else:
            logger.warning(
                "CoinGecko returned no data - proceeding with DexScreener only"
            )

        # -- DexScreener -------------------------------------------------
        dx_data = self._get(DEXSCREENER_LATEST_URL, "DexScreener/latest")
        dx_records: List[AssetRecord] = []
        if dx_data:
            dx_records = self._parse_dexscreener(dx_data)
            logger.info("DexScreener returned %d assets", len(dx_records))
        else:
            logger.warning(
                "DexScreener returned no data - proceeding with CoinGecko only"
            )

        # -- Merge / dedupe (symbol-upper key) ---------------------------
        merged = self._merge_records(cg_records, dx_records)
        logger.info("Merged asset universe: %d unique candidates", len(merged))
        return merged

    # -- 2. filter_assets() -----------------------------------------------

    def filter_assets(self, assets: List[AssetRecord]) -> List[AssetRecord]:
        """
        Run every candidate through the **Structural Validity Firewall**.

        Gate 1 - Market cap > config.min_market_cap
        Gate 2 - 24h volume > config.min_volume_24h
        Gate 3 - Age > config.min_age_days
        Gate 4 - Volume stability: 7d avg within +/-20% of 30d avg

        Assets passing all four gates get passed_firewall=True.
        Every accept/reject decision is logged individually.
        """
        logger.info(
            "--- Running Structural Validity Firewall on %d assets ---",
            len(assets),
        )
        passed: List[AssetRecord] = []
        rejected_count = 0

        for asset in assets:
            reasons: List[str] = []
            ok = True

            # Gate 1 - Market Cap
            if (
                asset.market_cap is not None
                and asset.market_cap < self.config.min_market_cap
            ):
                reasons.append(
                    f"market_cap {self._fmt(asset.market_cap)} "
                    f"< {self._fmt(self.config.min_market_cap)}"
                )
                ok = False

            # Gate 2 - 24h Volume
            if (
                asset.volume_24h is not None
                and asset.volume_24h < self.config.min_volume_24h
            ):
                reasons.append(
                    f"vol24h {self._fmt(asset.volume_24h)} "
                    f"< {self._fmt(self.config.min_volume_24h)}"
                )
                ok = False

            # Gate 3 - Age
            if (
                asset.age_days is not None
                and asset.age_days < self.config.min_age_days
            ):
                reasons.append(f"age {asset.age_days}d < {self.config.min_age_days}d")
                ok = False

            # Gate 4 - Volume Stability (7d avg vs 30d avg)
            if (
                asset.volume_7d_avg is not None
                and asset.volume_30d_avg is not None
                and asset.volume_30d_avg > 0
            ):
                ratio = abs(asset.volume_7d_avg - asset.volume_30d_avg) / asset.volume_30d_avg
                if ratio > self.config.volume_stability_pct:
                    reasons.append(
                        f"volume instability {ratio:.1%} "
                        f"> {self.config.volume_stability_pct:.0%} "
                        f"(7d avg={self._fmt(asset.volume_7d_avg)}, "
                        f"30d avg={self._fmt(asset.volume_30d_avg)})"
                    )
                    ok = False

            if ok:
                asset.passed_firewall = True
                asset.notes.append("FIREWALL PASS")
                passed.append(asset)
                logger.info(
                    "ACCEPT  %-10s | mcap=%s  vol24h=%s  age=%s days",
                    asset.symbol.upper(),
                    self._fmt(asset.market_cap),
                    self._fmt(asset.volume_24h),
                    asset.age_days or "n/a",
                )
            else:
                rejected_count += 1
                asset.notes.extend(reasons)
                logger.info(
                    "REJECT  %-10s | %s",
                    asset.symbol.upper(),
                    "; ".join(reasons),
                )

        logger.info(
            "Firewall result: %d PASSED / %d REJECTED out of %d total",
            len(passed),
            rejected_count,
            len(assets),
        )
        return passed

    # -- 3. check_decay() ------------------------------------------------

    def check_decay(self, current_assets: List[AssetRecord]) -> List[AssetRecord]:
        """
        Compare current assets against the persisted baseline.

        Any asset whose current 24h volume is < config.decay_threshold_pct
        (default 50%) of its baseline volume is marked decay_flag=True.

        Returns a list of assets that triggered the decay flag.
        """
        baseline = self.load_baseline()
        if not baseline:
            logger.info(
                "No baseline found - skipping decay check "
                "(run save_results first)"
            )
            return []

        baseline_map: Dict[str, Dict[str, Any]] = {}
        for entry in baseline:
            key = entry.get("symbol", "").upper()
            if key:
                baseline_map[key] = entry

        decayed: List[AssetRecord] = []
        threshold = self.config.decay_threshold_pct

        for asset in current_assets:
            key = asset.symbol.upper()
            if key not in baseline_map:
                continue
            base_entry = baseline_map[key]
            base_vol = base_entry.get("volume_24h")

            if base_vol and asset.volume_24h is not None and base_vol > 0:
                ratio = asset.volume_24h / base_vol
                if ratio < threshold:
                    asset.decay_flag = True
                    asset.decay_pct = 1.0 - ratio
                    asset.notes.append(
                        f"DECAY flag: vol24h dropped "
                        f"{1.0 - ratio:.1%} from baseline "
                        f"({self._fmt(base_vol)} -> "
                        f"{self._fmt(asset.volume_24h)})"
                    )
                    decayed.append(asset)
                    logger.warning(
                        "DECAY  %-10s | vol24h %.1f%% of baseline",
                        asset.symbol.upper(),
                        ratio * 100,
                    )

        logger.info("Decay check complete: %d assets flagged", len(decayed))
        return decayed

    # -- 4. save_results() -----------------------------------------------

    def save_results(self, assets: List[AssetRecord]) -> Path:
        """
        Write validated assets to valid_crypto_assets.json and also update
        baseline_crypto_assets.json for future decay comparison.

        Returns the path written.
        """
        payload = {
            "scan_timestamp": self._scan_timestamp,
            "count": len(assets),
            "thresholds": {
                "min_market_cap": self.config.min_market_cap,
                "min_volume_24h": self.config.min_volume_24h,
                "min_age_days": self.config.min_age_days,
                "volume_stability_pct": self.config.volume_stability_pct,
                "decay_threshold_pct": self.config.decay_threshold_pct,
            },
            "assets": [asdict(a) for a in assets],
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        logger.info("Saved %d assets -> %s", len(assets), OUTPUT_FILE)

        with open(BASELINE_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        logger.info("Baseline updated -> %s", BASELINE_FILE)

        return OUTPUT_FILE

    # -- 5. load_baseline() -----------------------------------------------

    def load_baseline(self) -> List[Dict[str, Any]]:
        """
        Load the previous scan baseline for decay comparison.

        Returns a list of asset dicts, or an empty list if no baseline exists.
        """
        if not BASELINE_FILE.exists():
            logger.info("Baseline file not found: %s", BASELINE_FILE)
            return []
        try:
            with open(BASELINE_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            assets = data.get("assets", [])
            logger.info(
                "Loaded baseline: %d assets from %s", len(assets), BASELINE_FILE
            )
            return assets
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load baseline: %s", exc)
            return []

    # -- Internal parsers ------------------------------------------------

    @staticmethod
    def _parse_coingecko(data: list) -> List[AssetRecord]:
        """Convert raw CoinGecko /coins/markets response to AssetRecord list."""
        records: List[AssetRecord] = []
        for item in data:
            sparkline = item.get("sparkline_in_7d") or {}
            prices_7d: List[float] = sparkline.get("price", []) or []

            vol_24h: Optional[float] = item.get("total_volume")
            vol_7d_avg: Optional[float] = None
            vol_30d_avg: Optional[float] = None

            if vol_24h and len(prices_7d) >= 2:
                p_first = prices_7d[0] or 1.0
                p_last = prices_7d[-1] or 1.0
                ratio_7d = p_last / p_first if p_first else 1.0
                vol_7d_avg = vol_24h * ratio_7d
                pct_30d = (
                    item.get("price_change_percentage_30d_in_currency") or 0.0
                )
                vol_30d_avg = vol_24h * (1.0 + pct_30d / 100.0)

            age_days: Optional[int] = None
            genesis = item.get("genesis_date")
            if genesis:
                try:
                    genesis_dt = datetime.fromisoformat(
                        genesis.replace("Z", "+00:00")
                    )
                    age_days = (datetime.now(timezone.utc) - genesis_dt).days
                except ValueError:
                    age_days = None

            record = AssetRecord(
                symbol=item.get("symbol", ""),
                name=item.get("name", ""),
                source="coingecko",
                market_cap=item.get("market_cap"),
                volume_24h=vol_24h,
                volume_7d_avg=vol_7d_avg,
                volume_30d_avg=vol_30d_avg,
                price_usd=item.get("current_price"),
                price_change_7d_pct=item.get(
                    "price_change_percentage_7d_in_currency"
                ),
                age_days=age_days,
            )
            records.append(record)
        return records

    @staticmethod
    def _parse_dexscreener(data: Dict[str, Any]) -> List[AssetRecord]:
        """Convert raw DexScreener /latest/dex/tokens/ response to AssetRecord list."""
        records: List[AssetRecord] = []
        pairs = data.get("pairs") or []
        seen_symbols: set = set()

        for pair in pairs:
            base = pair.get("baseToken") or {}
            symbol = (base.get("symbol") or "").lower()
            name = base.get("name") or symbol

            if not symbol or symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)

            fdv = pair.get("fdv") or pair.get("marketCap")
            vol = pair.get("volume") or {}
            vol_24h = vol.get("h24")

            price = pair.get("priceUsd")
            try:
                price_usd = float(price) if price is not None else None
            except (ValueError, TypeError):
                price_usd = None

            created_at_ms = pair.get("pairCreatedAt")
            age_days: Optional[int] = None
            if created_at_ms:
                age_days = int(
                    (time.time() * 1000 - created_at_ms) / (1000 * 86400)
                )

            record = AssetRecord(
                symbol=symbol,
                name=name,
                source="dexscreener",
                market_cap=fdv,
                volume_24h=vol_24h,
                price_usd=price_usd,
                age_days=age_days,
            )
            records.append(record)

        records.sort(key=lambda r: r.volume_24h or 0, reverse=True)
        return records[:100]

    @staticmethod
    def _merge_records(
        cg_records: List[AssetRecord],
        dx_records: List[AssetRecord],
    ) -> List[AssetRecord]:
        """
        Merge CoinGecko + DexScreener assets into a single deduplicated list.
        CoinGecko data takes precedence; DexScreener-only tokens are appended.
        """
        merged_map: Dict[str, AssetRecord] = {}

        for rec in cg_records:
            key = rec.symbol.upper()
            merged_map[key] = rec

        for rec in dx_records:
            key = rec.symbol.upper()
            if key in merged_map:
                existing = merged_map[key]
                if existing.volume_24h is None and rec.volume_24h:
                    existing.volume_24h = rec.volume_24h
                if existing.price_usd is None and rec.price_usd:
                    existing.price_usd = rec.price_usd
                existing.source = "merged"
            else:
                merged_map[key] = rec

        return list(merged_map.values())


# ---------------------------------------------------------------------------
# STANDALONE ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("=" * 62)
    logger.info("  CryptoAssetScanner - Standalone Run")
    logger.info("=" * 62)

    config = FilterConfig(
        min_market_cap=50_000_000,
        min_volume_24h=1_000_000,
        min_age_days=30,
        volume_stability_pct=0.20,
        decay_threshold_pct=0.50,
    )

    scanner = CryptoAssetScanner(config)

    # Step 1 - Scan
    raw_assets = scanner.scan_assets()
    logger.info("Step 1 complete: %d raw assets discovered", len(raw_assets))

    # Step 2 - Firewall
    filtered = scanner.filter_assets(raw_assets)
    logger.info("Step 2 complete: %d assets passed firewall", len(filtered))

    # Step 3 - Save
    output_path = scanner.save_results(filtered)
    logger.info("Step 3 complete: results saved to %s", output_path)

    # Step 4 - Decay check (against previous baseline, if any)
    decayed = scanner.check_decay(filtered)
    if decayed:
        logger.warning("Step 4: %d assets flagged for decay", len(decayed))
    else:
        logger.info("Step 4: no decay detected (or no baseline yet)")

    # Summary
    logger.info("=" * 62)
    logger.info("SCAN COMPLETE")
    logger.info("  Raw discovered : %d", len(raw_assets))
    logger.info("  Firewall passed : %d", len(filtered))
    logger.info("  Decay flagged   : %d", len(decayed))
    logger.info("  Output file     : %s", output_path)
    logger.info("=" * 62)
