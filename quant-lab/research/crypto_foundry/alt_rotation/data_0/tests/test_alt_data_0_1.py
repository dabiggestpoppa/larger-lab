"""ALT-DATA-0.1 truth-repair test suite.

Asserts the specific repair guarantees required by the human review:
1. rank-band coverage counts UNIQUE PIT assets per date (denominators
   10/15/25/50/100/100/200, band sums == 500 per date)
2. perp eligibility prototype is non-empty with the canonical schema and
   no (date, cmc_id, venue, instrument) duplicates
3. FULLY_ELIGIBLE can never be true when liquidity status != VERIFIED
4. the internal CMC web endpoint is not labeled as an official documented API
5. earliest_verified rank date is empirically tested (probe file exists)
6. ticker-reuse classifications are explicit (collision audit classes)
7. coverage CSV declares asset_count_method = UNIQUE_PIT_ASSET
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

DATA0 = Path(__file__).resolve().parent.parent
DATA0_1 = DATA0.parent / "data_0_1"
RAW = DATA0 / "probes" / "raw"
DATES = ["2024-06-01", "2025-01-01", "2025-06-01", "2026-01-01", "2026-08-20"]
BAND_SIZES = {"1-10": 10, "11-25": 15, "26-50": 25, "51-100": 50,
              "101-200": 100, "201-300": 100, "301-500": 200}
MIN_MATURITY = 30


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ----------------------------------------------------------------------
# Repair 1 — rank-band coverage: UNIQUE PIT assets per date
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def coverage() -> list[dict]:
    return load_csv(DATA0 / "ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv")


@pytest.fixture(scope="module")
def elig() -> list[dict]:
    return load_csv(DATA0 / "ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv")


@pytest.fixture(scope="module")
def pit() -> list[dict]:
    return load_csv(DATA0 / "ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv")


@pytest.fixture(scope="module")
def collisions() -> list[dict]:
    return load_csv(DATA0_1 / "ALT_DATA_0_1_IDENTITY_COLLISION_AUDIT.csv")


def band_of(rank: str) -> str:
    r = int(rank)
    for band, size in BAND_SIZES.items():
        lo, hi = (int(band.split("-")[0]), int(band.split("-")[1]))
        if lo <= r <= hi:
            return band
    raise AssertionError(f"rank {rank} outside 1-500")


def test_band_unique_counts_per_date_sum_to_500(pit):
    """Unique PIT assets per (date, band) from the rank prototype."""
    per_date_band = {}
    for row in pit:
        key = (row["historical_date"], band_of(row["cmc_rank"]))
        per_date_band[key] = per_date_band.get(key, 0) + 1
    for date in DATES:
        total = sum(per_date_band.get((date, b), 0) for b in BAND_SIZES)
        assert total == 500, f"{date}: unique assets sum {total} != 500"


def test_band_denominators_exact(pit):
    """Each band holds exactly its true size per date (no venue inflation)."""
    per_date_band = {}
    for row in pit:
        key = (row["historical_date"], band_of(row["cmc_rank"]))
        per_date_band[key] = per_date_band.get(key, 0) + 1
    for date in DATES:
        for band, size in BAND_SIZES.items():
            assert per_date_band.get((date, band), 0) == size, \
                f"{date} band {band}: expected {size}, got " \
                f"{per_date_band.get((date, band), 0)}"


def test_band_sum_denominators_2500(pit):
    """5 dates x 500 unique = 2500 total unique asset-date rows."""
    assert len(pit) == 2500, f"PIT prototype rows {len(pit)} != 2500"


def test_coverage_csv_declares_unique_method(coverage):
    headers = coverage[0]
    assert headers.get("asset_count_method") == "UNIQUE_PIT_ASSET", headers
    # every band must sum to its aggregate denominator across the 5 dates
    # (skip the ALL_DATES aggregate rows; they duplicate the per-date sum)
    agg = {}
    for row in coverage:
        if row["historical_date"] == "ALL_DATES":
            continue
        band = row["band"]
        agg[band] = agg.get(band, 0) + int(row["n_unique_assets"])
    for band, size in BAND_SIZES.items():
        assert agg[band] == size * len(DATES), \
            f"band {band}: aggregate unique {agg[band]} != {size * len(DATES)}"


# ----------------------------------------------------------------------
# Repair 3 — perp eligibility prototype non-empty + canonical schema
# ----------------------------------------------------------------------
def test_eligibility_prototype_non_empty(elig):
    assert len(elig) > 0, "ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv is empty"
    # canonical schema
    for col in ["historical_date", "cmc_id", "symbol", "historical_rank",
                "venue", "venue_instrument_id", "listing_timestamp",
                "listing_timestamp_authority", "delisting_timestamp",
                "delisting_timestamp_authority", "contract_age_days_at_t",
                "tradable_at_t", "mature_30d_at_t",
                "historical_price_data_available",
                "historical_funding_data_available",
                "historical_volume_data_available",
                "liquidity_evidence_status", "contract_existence_eligible",
                "contract_maturity_eligible", "historical_data_eligible",
                "historical_liquidity_verified", "eligibility_status",
                "exclusion_reason"]:
        assert col in elig[0], f"missing canonical column {col}"


def test_eligibility_no_duplicate_rows(elig):
    seen = set()
    for row in elig:
        key = (row["historical_date"], row["cmc_id"], row["venue"],
               row["venue_instrument_id"])
        assert key not in seen, f"duplicate row {key}"
        seen.add(key)


def test_eligibility_covers_all_pit_dates(elig):
    dates = {r["historical_date"] for r in elig}
    assert dates == set(DATES), dates


# ----------------------------------------------------------------------
# Repair 4 — liquidity truth: FULLY_ELIGIBLE requires VERIFIED liquidity
# ----------------------------------------------------------------------
def test_fully_eligible_requires_verified_liquidity(elig):
    for row in elig:
        if row["eligibility_status"] == "FULLY_ELIGIBLE":
            assert row["historical_liquidity_verified"] == "TRUE", row


def test_no_fully_eligible_used(elig):
    """DATA-0/0.1 never verified historical liquidity -> no FULLY_ELIGIBLE."""
    statuses = {r["eligibility_status"] for r in elig}
    assert "FULLY_ELIGIBLE" not in statuses, statuses
    assert "ELIGIBLE_EX_LIQUIDITY" in statuses or \
        "CONTRACT_MATURITY_ELIGIBLE" in statuses


def test_eligible_ex_liquidity_never_liquidity_verified(elig):
    for row in elig:
        if row["eligibility_status"] == "ELIGIBLE_EX_LIQUIDITY":
            assert row["historical_liquidity_verified"] == "FALSE", row


# ----------------------------------------------------------------------
# Repair 6 — CMC authority: internal endpoint is not an official API
# ----------------------------------------------------------------------
def test_cmc_not_labeled_official_documented_api():
    registry = load_csv(DATA0 / "ALT_DATA_0_SOURCE_AUTHORITY_REGISTRY.csv")
    cmc_rows = [r for r in registry if r["provider"].startswith("CoinMarketCap")]
    assert cmc_rows
    # the PIT snapshot rows must carry the empirical web-endpoint label
    # with the honesty fields; other CMC rows (tags/sector, paid API) use
    # their own classes and are not part of this assertion.
    web_rows = [r for r in cmc_rows
                if "EMPIRICALLY_VERIFIED_WEB_ENDPOINT" in r["class"]]
    assert web_rows, "no CMC row carries the empirical web-endpoint label"
    for r in web_rows:
        assert r["official_documentation"] in (
            "NO", "UNVERIFIED", "NO_UNVERIFIED"), r
        assert r["api_key_required"] == "NO", r
        assert "INTERNAL_ENDPOINT" in r["stability_risk"], r
        assert r["tos_review_required"] in (
            "YES", "YES_FOR_LONG_TERM_OPERATION"), r
    # no CMC row may be labeled as an officially documented public API
    # (only the internal web endpoint carries the empirical label)
    for r in cmc_rows:
        assert "PRIMARY_VERIFIED" not in r["class"] or \
            "WEB_ENDPOINT" in r["class"], r


def test_consensus_matrix_cmc_label():
    consensus = load_csv(DATA0 / "ALT_DATA_0_SOURCE_CONSENSUS_MATRIX.csv")
    cmc_col = [h for h in consensus[0] if h.startswith("CoinMarketCap")]
    assert cmc_col
    joined = "\n".join(r.get(cmc_col[0], "") for r in consensus)
    assert "EMPIRICALLY_VERIFIED_WEB_ENDPOINT" in joined or \
        "internal web" in joined.lower()


# ----------------------------------------------------------------------
# Repair 7 — earliest verified rank date must be empirically tested
# ----------------------------------------------------------------------
@pytest.mark.parametrize("date", ["2022-06-01", "2021-06-01", "2020-06-01"])
def test_earliest_history_dates_empirically_probed(date):
    key = date.replace("-", "")
    probe = RAW / f"cmc_snapshot_{key}_top500.json"
    assert probe.is_file(), f"{probe.name} missing (earliest-history claim)"
    data = json.loads(probe.read_text(encoding="utf-8"))
    rows = data["data"]
    assert len(rows) == 500, f"{date}: {len(rows)} rows != 500"


def test_earliest_verified_claim_matches_probe():
    decision = json.loads(
        (DATA0 / "ALT_DATA_0_DECISION.json").read_text(encoding="utf-8"))
    assert "2020-06-01" in decision["earliest_verified_rank_history"]
    assert "UNVERIFIED" in decision["earliest_history_claim_note"]
    assert "any date supported" not in \
        decision["earliest_verified_rank_history"].lower()


# ----------------------------------------------------------------------
# Repair 8 — identity collision audit: explicit classes
# ----------------------------------------------------------------------
def test_collision_classes_explicit(collisions):
    classes = {r["collision_class"] for r in collisions}
    assert "TRUE_TICKER_REUSE" in classes
    assert "PROVIDER_SYMBOL_COLLISION" in classes
    assert "UNKNOWN_COLLISION" in classes
    for r in collisions:
        assert r["classification_note"], f"missing note for {r}"
        assert r["collision_class"] in (
            "TRUE_TICKER_REUSE", "PROVIDER_SYMBOL_COLLISION",
            "UNKNOWN_COLLISION", "NO_COLLISION",
            "MULTIPLIER_ALIAS", "VENUE_ALIAS"), r["collision_class"]


def test_true_ticker_reuse_is_small_subset(collisions):
    """608 was conflated; true reuse must be materially smaller than the
    provider-collision count."""
    from collections import Counter
    counts = Counter(r["collision_class"] for r in collisions)
    assert counts["TRUE_TICKER_REUSE"] <= counts["PROVIDER_SYMBOL_COLLISION"]
    assert counts["TRUE_TICKER_REUSE"] < 50


# ----------------------------------------------------------------------
# Repair 9 — decision artifact consistency
# ----------------------------------------------------------------------
def test_decision_says_repaired_and_criteria_met():
    d0 = json.loads(
        (DATA0 / "ALT_DATA_0_DECISION.json").read_text(encoding="utf-8"))
    assert d0["repaired_by"] == "CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR"
    for k, v in d0["pass_criteria"].items():
        assert v is True, f"pass criterion {k} not satisfied"
    # FULLY_ELIGIBLE must be documented as removed, never an active status;
    # the prototype-level guarantee is enforced by
    # test_no_fully_eligible_used.
    assert "ELIGIBLE_EX_LIQUIDITY" in d0["liquidity_taxonomy"]
    assert "FULLY_ELIGIBLE removed" in d0["liquidity_taxonomy"]


def test_data0_1_decision_exists_and_consistent():
    d1 = json.loads(
        (DATA0_1 / "ALT_DATA_0_1_DECISION.json").read_text(encoding="utf-8"))
    assert d1["checkpoint"] == "CRYPTO-ALT-DATA-0.1-FOUNDATION-TRUTH-REPAIR"
    assert d1["decision"] in (
        "PASS_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION",
        "PARTIAL_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION",
        "FAIL_ALT_POINT_IN_TIME_UNIVERSE_FOUNDATION")
    assert d1["earliest_verified_rank_history"] == "2020-06-01"
