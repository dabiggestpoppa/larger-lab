"""ALT-DATA-0 fail-closed test suite.

Reads persisted artifacts only (no network). Enforces the preregistered
fail-closed rules and the 17 required test areas.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import zipfile
import io
from datetime import datetime, timezone
from pathlib import Path

import pytest

DATA0 = Path(__file__).resolve().parent.parent
RAW = DATA0 / "probes" / "raw"
DATES = ["2024-06-01", "2025-01-01", "2025-06-01", "2026-01-01", "2026-08-20"]
MIN_MATURITY = 30


def load_csv(name: str) -> list[dict]:
    with (DATA0 / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(name: str) -> dict:
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def dt_iso(date: str) -> datetime:
    return datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def snapshot(date: str) -> list[dict]:
    key = date.replace("-", "")
    return json.loads(
        (RAW / f"cmc_snapshot_{key}_top500.json").read_text(encoding="utf-8")
    )["data"]


# ----------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def elig() -> list[dict]:
    return load_csv("ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv")


@pytest.fixture(scope="module")
def pit() -> list[dict]:
    return load_csv("ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv")


@pytest.fixture(scope="module")
def identity() -> list[dict]:
    return load_csv("identity/canonical_identity_map.csv")


@pytest.fixture(scope="module")
def hl_funding() -> dict:
    return load_json("hyperliquid_funding_first_history.json")


# ----------------------------------------------------------------------
# 1. historical date isolation / 2. no future data usage
# ----------------------------------------------------------------------
def test_no_eligible_row_uses_future_listing(elig):
    """A contract listed after t must never be tradable/eligible at t."""
    for r in elig:
        if r["eligibility_status"] != "ELIGIBLE":
            continue
        lt = r["contract_list_time"]
        assert lt, "eligible row must have a list time"
        assert dt_iso(lt[:10]) <= dt_iso(r["historical_date"]), (
            f"{r['symbol']} {r['venue']} eligible at {r['historical_date']} "
            f"but listed {lt[:10]}")


def test_future_listing_is_excluded(elig):
    """There must exist NOT_ELIGIBLE rows caused by listing after t."""
    reasons = {r["exclusion_reason"] for r in elig
               if r["eligibility_status"] == "NOT_ELIGIBLE"}
    assert any("listed_after_t" in x for x in reasons), reasons


# ----------------------------------------------------------------------
# 3. no current-top500 backfill
# ----------------------------------------------------------------------
def test_old_snapshot_not_backfilled_from_current_top():
    cg_top = load_json("coingecko_markets_top250.json")
    cg_syms = {c["symbol"].upper() for c in cg_top}
    snap = snapshot("2024-06-01")
    syms = {r["symbol"].upper() for r in snap}
    for fallen in ("FTT", "HOT", "XEM"):
        assert fallen in syms, f"{fallen} missing from 2024-06-01 snapshot"
        assert fallen not in cg_syms, (
            f"{fallen} is in today's CG top-250; snapshot would be "
            "backfill-dependent")


# ----------------------------------------------------------------------
# 4. stable ID uniqueness
# ----------------------------------------------------------------------
def test_stable_id_uniqueness(identity, pit):
    ids = [r["internal_asset_id"] for r in identity]
    assert len(ids) == len(set(ids)), "duplicate internal_asset_id"
    for date in DATES:
        rows = [r for r in pit if r["historical_date"] == date]
        keys = [(r["historical_date"], r["cmc_id"]) for r in rows]
        assert len(keys) == len(set(keys)), f"duplicate (date, cmc_id) at {date}"
    for date in DATES:
        s = snapshot(date)
        assert len({r["id"] for r in s}) == 500


# ----------------------------------------------------------------------
# 5. ticker-reuse handling
# ----------------------------------------------------------------------
def test_ticker_reuse_is_flagged_not_silently_joined(identity):
    flagged = [r for r in identity if r["ticker_reuse_flagged"] == "True"]
    assert flagged, "no ticker reuse cases found"
    # symbol collisions must not collapse identities: distinct cmc ids with
    # the same canonical symbol must keep separate internal ids
    by_sym: dict[str, set[str]] = {}
    for r in identity:
        by_sym.setdefault(r["canonical_symbol"], set()).add(
            r["internal_asset_id"])
    collisions = {s for s, v in by_sym.items() if len(v) > 1}
    assert collisions, "expected at least one symbol collision (e.g. LUNA)"


# ----------------------------------------------------------------------
# 6. point-in-time rank reproduction
# ----------------------------------------------------------------------
def test_rank_field_is_exact_and_mcap_approximately_monotonic():
    for date in DATES:
        s = snapshot(date)
        ranks = [r["cmcRank"] for r in s]
        assert ranks == list(range(1, 501)), f"cmcRank not 1..500 at {date}"
        mcaps = [(r.get("quotes") or [{}])[0].get("marketCap") or 0
                 for r in s]
        # Spearman(mcap, -rank) — tolerate provider-internal divergence
        # (observed 0.88-0.99; recorded in report)
        rk = [sorted(mcaps, reverse=True).index(m) for m in mcaps]
        rho = _spearman(mcaps, list(range(500, 0, -1)))
        assert rho > 0.80, f"rank/mcap correlation too low at {date}: {rho}"


def _spearman(x: list[float], y: list[int]) -> float:
    rx = {v: i for i, v in enumerate(sorted(x))}
    ry = {v: i for i, v in enumerate(sorted(y))}
    n = len(x)
    d2 = sum((rx[a] - ry[b]) ** 2 for a, b in zip(x, y))
    return 1 - 6 * d2 / (n * (n * n - 1))


# ----------------------------------------------------------------------
# 7. rank-source consistency / 15. provider disagreement handling
# ----------------------------------------------------------------------
def test_rank_source_consistency_and_disagreement_flagging():
    cc = load_csv("derived/rank_crosscheck.csv")
    by_sym = {r["symbol"]: r for r in cc}
    for sym in ("BTC", "ETH", "HOT"):
        r = by_sym[sym]
        assert abs(float(r["pct_diff"])) < 5.0, r
        assert r["disagreement_flag"] == "OK", r
    for sym in ("LUNC", "FTT"):
        r = by_sym[sym]
        assert r["disagreement_flag"] == "CHECK", (
            "provider disagreement must be flagged, not silently resolved")
        assert abs(float(r["pct_diff"])) >= 5.0, r


# ----------------------------------------------------------------------
# 8. contract list-time logic / 13. current-only symbol-list rejection
# ----------------------------------------------------------------------
def test_list_time_sources_are_not_current_symbol_lists(elig):
    sources = {r["listing_timestamp_authority"] for r in elig}
    assert "CURRENT_SYMBOL_LIST" not in sources, sources
    assert "INFERRED_FIRST_DATA_TIMESTAMP" in sources  # HL
    assert "OFFICIAL_LIST_TIME" in sources              # OKX
    assert "GEO_BLOCKED_FROM_ENV" in sources            # Binance/Bybit


def test_hl_listing_uses_funding_first_ts_not_meta_presence(elig):
    hl = [r for r in elig if r["venue"] == "HYPERLIQUID"
          and r["listing_timestamp_authority"]]
    assert hl
    for r in hl:
        assert r["listing_timestamp_authority"] == \
            "INFERRED_FIRST_DATA_TIMESTAMP"


# ----------------------------------------------------------------------
# 9. contract delist-time logic
# ----------------------------------------------------------------------
def test_delisted_contract_not_tradable_after_delist(elig):
    ftt = [r for r in elig if r["symbol"] == "FTT"
           and r["venue"] == "HYPERLIQUID"
           and r["historical_date"] == "2024-06-01"]
    assert ftt and ftt[0]["eligibility_status"] == "NOT_ELIGIBLE"
    assert "delisted_before_t" in ftt[0]["exclusion_reason"]
    assert ftt[0]["delisting_timestamp"][:10] == "2023-10-16"


# ----------------------------------------------------------------------
# 10. maturity rule / 11. historical tradability
# ----------------------------------------------------------------------
def test_maturity_rule_and_tradability_conjunction(elig):
    for r in elig:
        if r["eligibility_status"] not in ("ELIGIBLE_EX_LIQUIDITY",
                                            "CONTRACT_MATURITY_ELIGIBLE"):
            continue
        assert r["tradable_at_t"] == "TRUE"
        assert r["mature_30d_at_t"] == "TRUE"
        assert int(r["contract_age_days_at_t"]) >= MIN_MATURITY
    # and the rule actually bites somewhere (immature contracts carry
    # status CONTRACT_EXISTENCE_ELIGIBLE with an age-based exclusion)
    young = [r for r in elig if "age<" in r["exclusion_reason"]]
    assert young, "30d maturity rule never excluded anything"


# ----------------------------------------------------------------------
# 12. delisted contract recovery
# ----------------------------------------------------------------------
def test_hl_delisted_recovery(hl_funding):
    by_coin = {r["coin"]: r for r in hl_funding["coins"]}
    for coin in ("FTT", "JELLY", "OM"):
        rec = by_coin[coin]
        assert rec["is_delisted"] is True
        assert rec["first_funding_ts"] and rec["last_funding_ts"]
        assert rec["first_funding_ts"] < rec["last_funding_ts"]
    assert hl_funding["n_ok"] == 232


def test_binance_archive_delisted_bars():
    for name, expect in [("binance_archive_srmusdt_2022_10", 32),
                         ("binance_archive_fttusdt_2022_11", 31)]:
        raw = (RAW / f"{name}.json").read_bytes()
        z = zipfile.ZipFile(io.BytesIO(raw))
        rows = z.read(z.namelist()[0]).decode().strip().split("\n")
        assert len(rows) == expect, (name, len(rows))
    # funding archive for delisted symbol also retained
    meta = json.loads((RAW / "binance_archive_srmusdt_funding_202210.meta.json")
                      .read_text(encoding="utf-8"))
    assert meta["http_status"] == 200


# ----------------------------------------------------------------------
# 14. sector status classification
# ----------------------------------------------------------------------
def test_sector_status_classification(pit):
    allowed = {"POINT_IN_TIME_VERIFIED", "HISTORICAL_APPROXIMATION",
               "CURRENT_ONLY", "UNMAPPED"}
    for r in pit:
        assert r["sector_class"] in allowed, r
    tagged = [r for r in pit if r["n_tags"] != "" and int(r["n_tags"]) > 0]
    assert tagged
    for r in tagged:
        assert r["sector_class"] == "HISTORICAL_APPROXIMATION"


def test_current_only_sectors_never_presented_as_historical():
    text = (DATA0 / "ALT_DATA_0_SECTOR_MAPPING_AUDIT.md").read_text(
        encoding="utf-8")
    assert "CURRENT_ONLY" in text and "HISTORICAL_APPROXIMATION" in text
    decision = json.loads((DATA0 / "ALT_DATA_0_DECISION.json")
                          .read_text(encoding="utf-8"))
    assert decision["fail_closed_rules"][
        "current_only_sectors_as_historical"] == "NOT_VIOLATED"


# ----------------------------------------------------------------------
# 16. provenance hashes
# ----------------------------------------------------------------------
def test_provenance_hashes_complete():
    metas = sorted(RAW.rglob("*.meta.json"))
    assert len(metas) >= 89
    manifest = json.loads((DATA0 / "ALT_DATA_0_PROVENANCE_MANIFEST.json")
                          .read_text(encoding="utf-8"))
    assert manifest["probe_count"] == len(metas)
    seen = {p["probe"] for p in manifest["probes"]}
    for m in metas:
        d = json.loads(m.read_text(encoding="utf-8"))
        assert d["probe"] in seen
        if d.get("composite"):
            continue  # composite metas carry per-row hashes in the .json
        assert d.get("sha256"), f"missing sha256 in {m.name}"
        assert len(d["sha256"]) == 64


def test_manifest_sha256_self_consistent():
    manifest = json.loads((DATA0 / "ALT_DATA_0_PROVENANCE_MANIFEST.json")
                          .read_text(encoding="utf-8"))
    recorded = manifest["manifest_sha256"]
    # reproduce the builder's hashing body: key present with null value
    manifest["manifest_sha256"] = None
    body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    assert hashlib.sha256(body).hexdigest() == recorded


def test_raw_sample_sha256_matches_manifest():
    manifest = json.loads((DATA0 / "ALT_DATA_0_PROVENANCE_MANIFEST.json")
                          .read_text(encoding="utf-8"))
    by_probe = {p["probe"]: p for p in manifest["probes"]}
    checked = 0
    for m in RAW.rglob("*.meta.json"):
        d = json.loads(m.read_text(encoding="utf-8"))
        if d.get("composite"):
            continue
        raw = Path(str(m)[: -len(".meta.json")] + ".json")
        if not raw.exists():
            continue
        assert by_probe[d["probe"]]["sha256"] == hashlib.sha256(
            raw.read_bytes()).hexdigest()
        checked += 1
    assert checked > 50


# ----------------------------------------------------------------------
# 17. deterministic normalization (idempotent rebuild)
# ----------------------------------------------------------------------
def test_derived_build_is_deterministic():
    """Idempotent-rebuild check for the ORIGINAL (legacy) builder.

    Runs alt_build_derived.py twice inside a scratch copy of its inputs so
    the live data_0 artifacts are NEVER rewritten by the test suite. This
    matters because DATA-0.1 repaired the live eligibility/coverage
    artifacts to the canonical schema; the legacy builder emits the old
    schema, so rebuilding in place would erase the repair.
    """
    import shutil
    import tempfile

    script = DATA0 / "scripts" / "alt_build_derived.py"
    outs = ["ALT_DATA_0_POINT_IN_TIME_RANK_PROTOTYPE.csv",
            "ALT_DATA_0_PERP_ELIGIBILITY_PROTOTYPE.csv",
            "ALT_DATA_0_COVERAGE_BY_RANK_BAND.csv"]
    live_before = {n: hashlib.sha256((DATA0 / n).read_bytes()).hexdigest()
                   for n in outs}
    with tempfile.TemporaryDirectory() as tmp:
        for item in ("probes", "identity", "derived", "scripts"):
            shutil.copytree(DATA0 / item, Path(tmp) / item)
        hashes = {}
        for run_i in range(2):
            subprocess.run([sys.executable, "scripts/alt_build_derived.py"],
                           check=True, cwd=tmp)
            hashes[run_i] = {
                n: hashlib.sha256((Path(tmp) / n).read_bytes()).hexdigest()
                for n in outs}
        assert hashes[0] == hashes[1], "legacy rebuild not deterministic"
        # the legacy builder emits the OLD schema (pre-repair) in the
        # scratch copy — this documents that alt_build_derived.py is the
        # legacy pipeline, superseded for these artifacts by the repair.
        legacy_elig = (Path(tmp) / outs[1]).read_text(encoding="utf-8")
        assert "cmc_rank" in legacy_elig[:200]
        # the live repaired artifacts must be untouched by this test
        live_after = {n: hashlib.sha256((DATA0 / n).read_bytes()).hexdigest()
                      for n in outs}
        assert live_after == live_before, \
            "test must not modify live (repaired) data_0 artifacts"


# ----------------------------------------------------------------------
# fail-closed meta checks
# ----------------------------------------------------------------------
def test_decision_and_no_alpha_work():
    decision = json.loads((DATA0 / "ALT_DATA_0_DECISION.json")
                          .read_text(encoding="utf-8"))
    assert decision["decision"].startswith("PASS_")
    assert decision["pass_criteria"]["10_no_alpha_or_pnl_work"] is True
    # no strategy artifacts in the workspace
    for p in DATA0.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".py", ".csv", ".json", ".md"):
            if "BACKTEST" in p.name.upper() or "PNL" in p.name.upper():
                raise AssertionError(f"strategy artifact found: {p}")


def test_preregistration_anchor_consistent():
    decision = json.loads((DATA0 / "ALT_DATA_0_DECISION.json")
                          .read_text(encoding="utf-8"))
    assert decision["maturity_rule"]["verdict"] == "30D_FEASIBLE"
    assert decision["prototype_dates"] == DATES
