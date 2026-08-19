"""QL-EXEC-R5.1 — TradeLocker DEMO read-only integration offline tests.

Proves the four order-prevention barriers and the full read-only audit
pipeline against FakeTradeLocker (zero network). The SAME audit code path runs
against the real demo via ``runtime/tradelocker_demo_readonly.py``.

Covers R5.1 test matrix items 1-32 (offline halves; the live halves are gated
on demo credentials and recorded as WAITING_TRADELOCKER_DEMO_ACCESS).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tokenize
from pathlib import Path

_QL = Path(__file__).resolve().parents[2]  # quant-lab/
if str(_QL) not in sys.path:
    sys.path.insert(0, str(_QL))

import pytest  # noqa: E402

from execution_runtime.tradelocker import (  # noqa: E402
    DemoEnvironmentError,
    DemoReadOnlyAudit,
    FakeTradeLocker,
    ReadOnlyProviderWriteForbiddenError,
    ReadOnlyTradeLockerBrokerSession,
    ReadOnlyTransport,
    TradeLockerAuthProvider,
    TradeLockerBrokerSession,
    TradeLockerClient,
    render_artifacts,
)
from execution_runtime.types import OrderIntent  # noqa: E402

R5_DECISION = (
    Path(__file__).resolve().parents[2]
    / ".."
    / "research"
    / "execution_runtime_foundation"
    / "r5_tradelocker"
    / "QL_EXEC_R5_DECISION.json"
)

BASE_URL = "https://demo.tradelocker.com/backend-api"
FAKE_CREDS = {"EMAIL": "u@e.com", "PASS": "p"}
FAKE_SERVER = "demo-server"


def _seeded_fake() -> FakeTradeLocker:
    fake = FakeTradeLocker()
    fake.set_credentials("u@e.com", "p", FAKE_SERVER)
    fake.add_instrument(101, name="EURUSD", symbol_id=1001)
    fake.add_instrument(101, name="GBPUSD", symbol_id=1002)
    fake.add_instrument(101, name="USDJPY", symbol_id=1003)
    # TB canonical basket trio (availability audit only — no TB strategy math)
    fake.add_instrument(101, name="GBPAUD", symbol_id=1004)
    fake.add_instrument(101, name="GBPNZD", symbol_id=1005)
    fake.add_instrument(101, name="AUDNZD", symbol_id=1006)
    fake.add_instrument(102, name="GBPUSD", symbol_id=2001)
    # pre-existing provider truth: one pending order + one filled execution
    # with DISTINCT orderId / positionId (orderId != positionId semantic).
    fake._orders[101][9001] = {
        "id": 9001,
        "tradableInstrumentId": fake.instrument_ids(101)["GBPUSD"],
        "side": "buy",
        "qty": 0.1,
        "type": "limit",
        "validity": "GTC",
        "status": "Pending",
        "positionId": 0,
        "price": 1.25000,
        "stopPrice": 0.0,
        "strategyId": "R5_1_FIXTURE",
        "serverTime": fake._now_ms(),
    }
    fake._executions[101].append({
        "id": 7001,
        "orderId": 9002,
        "tradableInstrumentId": fake.instrument_ids(101)["EURUSD"],
        "side": "sell",
        "qty": 0.05,
        "price": 1.10000,
        "strategyId": "R5_1_FIXTURE",
        "positionId": 9003,
        "serverTime": fake._now_ms(),
    })
    fake.seed_foreign_position(101, symbol="GBPUSD", qty=2.0, strategy_id="FOREIGN")
    return fake


def _audit(fake: FakeTradeLocker) -> DemoReadOnlyAudit:
    return DemoReadOnlyAudit(
        transport=fake,
        base_url=BASE_URL,
        secret_provider=lambda n: FAKE_CREDS.get(n, ""),
        email_ref="EMAIL",
        password_ref="PASS",
        server=FAKE_SERVER,
    )


def _tl_session(fake: FakeTradeLocker) -> TradeLockerBrokerSession:
    auth = TradeLockerAuthProvider(
        base_url=BASE_URL,
        transport=fake,
        secret_provider=lambda n: FAKE_CREDS.get(n, ""),
        email_ref="EMAIL",
        password_ref="PASS",
        server=FAKE_SERVER,
    )
    client = TradeLockerClient(auth=auth, transport=fake, acc_num=1000001)
    session = TradeLockerBrokerSession(
        client=client, account_id=101, acc_num=1000001, server=FAKE_SERVER
    )
    assert session.connect()
    return session


# ── 1-2. frozen authority ────────────────────────────────────────────────


def test_r5_1_r5_decision_pass():
    d = json.loads(R5_DECISION.read_text(encoding="utf-8"))
    assert d["checkpoint"] == "QL-EXEC-R5-TRADELOCKER-PROVIDER-FOUNDATION-AND-DUAL-PROVIDER-CONFORMANCE"
    assert d["status"] == "PASS"
    assert d["mt5_regression_pass"] is True
    assert d["r4_2_unmodified"] is True


def test_r5_1_base_sha_is_hex40():
    d = json.loads(R5_DECISION.read_text(encoding="utf-8"))
    sha = d["base_commit"]
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)


# ── 3. regression ────────────────────────────────────────────────────────
# Full-suite pass is asserted at the checkpoint level (459 + this file); the
# suite run is recorded in the test audit artifact.

# ── 4-5. environment gate ────────────────────────────────────────────────


def test_r5_1_demo_environment_gate_accepts_demo():
    fake = _seeded_fake()
    audit = _audit(fake)
    assert audit.run()["demo_environment_verified"] is True


@pytest.mark.parametrize(
    "url",
    [
        "https://tradelocker.com/backend-api",
        "https://live.tradelocker.com/backend-api",
        "https://demo.tradelocker.com.evil.example/backend-api",
    ],
)
def test_r5_1_demo_environment_gate_refuses_non_demo(url):
    fake = _seeded_fake()
    with pytest.raises(DemoEnvironmentError):
        DemoReadOnlyAudit(
            transport=fake,
            base_url=url,
            secret_provider=lambda n: FAKE_CREDS.get(n, ""),
            email_ref="EMAIL",
            password_ref="PASS",
            server=FAKE_SERVER,
        )


def test_r5_1_live_environment_never_used():
    audit = _audit(_seeded_fake()).run()
    assert audit["live_environment_used"] is False


# ── 6-11. auth / accounts / config / instruments ─────────────────────────


def test_r5_1_auth_succeeds():
    audit = _audit(_seeded_fake()).run()
    assert audit["auth_count"] == 1
    assert audit["access_token_expiry_seconds"] is not None
    assert audit["access_token_expiry_seconds"] > 0


def test_r5_1_account_enumeration():
    audit = _audit(_seeded_fake()).run()
    assert audit["account_count"] == 2


def test_r5_1_account_id_and_acc_num_retained_separately():
    audit = _audit(_seeded_fake()).run()
    accounts = {a["account_id"]: a["acc_num"] for a in audit["accounts"]}
    assert accounts == {101: 1000001, 102: 1000002}


def test_r5_1_config_fetched_and_hashed():
    audit = _audit(_seeded_fake()).run()
    h = audit["account_101"]["config_hash"]
    assert h.startswith("cfg_") and len(h) == 20
    # deterministic: same payload → same hash
    from execution_runtime.tradelocker.config import TradeLockerConfigParser

    parser = TradeLockerConfigParser()
    import copy

    from execution_runtime.tradelocker.fake_server import CONFIG_D

    assert parser.parse(copy.deepcopy(CONFIG_D)).version_hash == parser.parse(
        copy.deepcopy(CONFIG_D)
    ).version_hash


def test_r5_1_instrument_discovery_with_routes():
    audit = _audit(_seeded_fake()).run()
    catalog = audit["account_101"]["instrument_catalog"]
    assert "EURUSD" in catalog and "GBPUSD" in catalog
    eurusd = catalog["EURUSD"]
    assert eurusd["info_route_id"] == "a"
    assert eurusd["trade_route_id"] == "b"
    assert eurusd["tradable_instrument_id"] is not None


# ── 15-16. market data ───────────────────────────────────────────────────


def test_r5_1_quote_read_with_provider_timestamp():
    audit = _audit(_seeded_fake()).run()
    md = {m["symbol"]: m for m in audit["account_101"]["market_data"]}
    assert "EURUSD" in md
    assert md["EURUSD"]["bid"] > 0.0
    assert md["EURUSD"]["ask"] >= md["EURUSD"]["bid"]
    assert md["EURUSD"]["server_time_ms"] > 0
    assert md["EURUSD"]["source_timestamp_preserved"] is True


# ── 18. TB symbol availability ───────────────────────────────────────────


def test_r5_1_tb_symbol_availability_all_three():
    audit = _audit(_seeded_fake()).run()
    tba = audit["tb_symbol_availability"]
    assert tba["verdict"] == "ALL_3_AVAILABLE"
    for s in ("GBPAUD", "GBPNZD", "AUDNZD"):
        assert tba["symbols"][s]["available"] is True
        assert tba["symbols"][s]["info_route_id"]
        assert tba["symbols"][s]["trade_route_id"]


# ── 17, 19-20. positions / orders / history ──────────────────────────────


def test_r5_1_positions_orders_history_read():
    audit = _audit(_seeded_fake()).run()
    acc = audit["account_101"]
    assert acc["positions_count"] == 1  # seeded foreign position
    assert acc["positions"][0]["symbol"] == "GBPUSD"
    assert acc["positions"][0]["ownership_tag"] == "FOREIGN"
    assert acc["orders_count"] == 1
    assert acc["orders"][0]["order_id"] == "9001"
    assert acc["history_count"] == 1
    assert acc["fill_count"] == 1


def test_r5_1_order_id_not_position_id_preserved():
    audit = _audit(_seeded_fake()).run()
    fills = audit["account_101"]["fills"]
    assert len(fills) == 1
    f = fills[0]
    assert f["order_id"] == "9002"
    assert f["position_id"] == "9003"
    assert f["order_id"] != f["position_id"]


def test_r5_1_foreign_position_normalized_not_owned():
    audit = _audit(_seeded_fake()).run()
    pos = audit["account_101"]["positions"][0]
    assert pos["ownership_tag"] == "FOREIGN"  # never claimed by runtime


# ── 21. multi-account isolation ──────────────────────────────────────────


def test_r5_1_multi_account_isolation():
    audit = _audit(_seeded_fake()).run()
    ma = audit["multi_account"]
    assert ma["accounts_audited"] == [101, 102]
    assert ma["isolation_proven"] is True
    # instruments never leak across accounts
    cat101 = set(audit["account_101"]["instrument_catalog"].keys())
    cat102 = set(audit["account_102"]["instrument_catalog"].keys())
    assert "EURUSD" in cat101 and "EURUSD" not in cat102
    assert cat102 == {"GBPUSD"}


# ── 22-27. write barriers ────────────────────────────────────────────────


def test_r5_1_transport_denies_order_post():
    fake = _seeded_fake()
    guard = ReadOnlyTransport(fake)
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        guard.request(
            _req("POST", f"{BASE_URL}/trade/accounts/101/orders", {"qty": "1"})
        )
    assert guard.mutation_calls() == 1


def test_r5_1_transport_denies_order_delete():
    fake = _seeded_fake()
    guard = ReadOnlyTransport(fake)
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        guard.request(_req("DELETE", f"{BASE_URL}/trade/accounts/101/orders/9001"))
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        guard.request(_req("DELETE", f"{BASE_URL}/trade/accounts/101/orders"))
    assert guard.mutation_calls() == 2


def test_r5_1_transport_denies_position_close():
    fake = _seeded_fake()
    guard = ReadOnlyTransport(fake)
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        guard.request(_req("DELETE", f"{BASE_URL}/trade/positions/7001", {"qty": "0"}))
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        guard.request(_req("DELETE", f"{BASE_URL}/trade/accounts/101/positions"))
    assert guard.mutation_calls() == 2


def test_r5_1_transport_allows_auth_and_reads():
    fake = _seeded_fake()
    guard = ReadOnlyTransport(fake)
    # auth POSTs permitted through the barrier (provider rejects wrong creds)
    resp = guard.request(_req("POST", f"{BASE_URL}/auth/jwt/token", {"email": "x"}))
    assert resp.status == 401  # reached the provider — barrier did not block
    # reads permitted; provider requires auth, so expect its 401, not a barrier
    # denial — proves the GET traversed the barrier
    resp = guard.request(_req("GET", f"{BASE_URL}/trade/config"))
    assert resp.status == 401
    assert guard.mutation_calls() == 0


def test_r5_1_session_write_methods_blocked():
    fake = _seeded_fake()
    ro = ReadOnlyTradeLockerBrokerSession(_tl_session(fake))
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        ro.submit_order(_intent())
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        ro.close_position("7001")
    with pytest.raises(ReadOnlyProviderWriteForbiddenError):
        ro.cancel_order("9001")
    w = ro.write_attempts()
    assert w == {
        "can_submit_new_risk": False,
        "submit_attempts": 1,
        "close_attempts": 1,
        "cancel_attempts": 1,
        "total": 3,
    }


def test_r5_1_session_read_methods_delegate():
    fake = _seeded_fake()
    ro = ReadOnlyTradeLockerBrokerSession(_tl_session(fake))
    assert ro.identity().broker_company == "TradeLocker"
    assert len(ro.positions()) == 1
    assert len(ro.orders()) == 1
    assert ro.health()["connected"] is True
    assert ro.can_submit_new_risk is False


def test_r5_1_audit_write_counters_zero():
    audit = _audit(_seeded_fake()).run()
    assert audit["broker_write_calls"] == 0
    assert audit["submit_calls"] == 0
    assert audit["close_calls"] == 0
    assert audit["cancel_calls"] == 0
    assert audit["transport_write_attempts"] == 0
    assert audit["can_submit_new_risk"] is False


# ── health / artifacts ───────────────────────────────────────────────────


def test_r5_1_health_healthy_read_only():
    audit = _audit(_seeded_fake()).run()
    h = audit["health"]
    assert h["overall"] == "HEALTHY_READ_ONLY"
    assert h["AUTH_OK"] and h["ACCOUNT_BOUND"] and h["READ_ONLY_ENFORCED"]


def test_r5_1_render_artifacts(tmp_path):
    audit = _audit(_seeded_fake()).run()
    rendered = render_artifacts(audit, tmp_path)
    expected = [
        "QL_EXEC_R5_1_ACCOUNT_DISCOVERY.json",
        "QL_EXEC_R5_1_AUTH_AUDIT.json",
        "QL_EXEC_R5_1_MULTI_ACCOUNT_AUDIT.json",
        "QL_EXEC_R5_1_CONFIG_SNAPSHOT.json",
        "QL_EXEC_R5_1_INSTRUMENT_CATALOG.csv",
        "QL_EXEC_R5_1_TB_SYMBOL_AVAILABILITY.json",
        "QL_EXEC_R5_1_MARKET_DATA_AUDIT.csv",
        "QL_EXEC_R5_1_POSITIONS_SNAPSHOT.json",
        "QL_EXEC_R5_1_ORDERS_SNAPSHOT.json",
        "QL_EXEC_R5_1_HISTORY_NORMALIZATION.csv",
        "QL_EXEC_R5_1_RATE_LIMIT_AUDIT.json",
        "QL_EXEC_R5_1_CLOCK_AUDIT.json",
        "QL_EXEC_R5_1_REAL_BROKERSESSION_CONFORMANCE.csv",
        "QL_EXEC_R5_1_READ_ONLY_BARRIER_AUDIT.json",
    ]
    for name in expected:
        assert name in rendered, name
    barrier = json.loads(
        (tmp_path / "QL_EXEC_R5_1_READ_ONLY_BARRIER_AUDIT.json").read_text(encoding="utf-8")
    )
    assert barrier["all_barriers_hold"] is True
    assert barrier["runtime_authority_gate"]["can_submit_new_risk"] is False


# ── 28-29. secrets hygiene (source-level audits) ─────────────────────────


def _string_literals(path: Path) -> list:
    out = []
    with tokenize.open(str(path)) as f:
        for tok in tokenize.generate_tokens(f.readline):
            if tok.type == tokenize.STRING:
                try:
                    out.append(eval(tok.string))
                except Exception:
                    pass
    return out


def test_r5_1_no_credentials_in_source():
    root = Path(__file__).resolve().parents[2]  # quant-lab/
    files = [
        root / "runtime" / "tradelocker_demo_readonly.py",
        root / "execution_runtime" / "tradelocker" / "readonly.py",
        root / "execution_runtime" / "tradelocker" / "auth.py",
        root / "execution_runtime" / "tradelocker" / "client.py",
    ]
    for path in files:
        for lit in _string_literals(path):
            if "@" in lit and "." in lit and "tradelocker.com" not in lit:
                pytest.fail(f"possible email literal in {path.name}: {lit}")
            if lit in ("s3cret", "hunter2", "password123"):
                pytest.fail(f"possible password literal in {path.name}: {lit}")


def test_r5_1_no_auth_headers_logged():
    # source audit (code-only): the real provider modules never print or use
    # the logging module, so Authorization headers cannot leak to logs.
    pkg = Path(__file__).resolve().parents[2] / "execution_runtime" / "tradelocker"
    offenders = []
    for path in sorted(pkg.rglob("*.py")):
        if path.name == "fake_server.py":
            continue
        names = []
        with tokenize.open(str(path)) as f:
            for tok in tokenize.generate_tokens(f.readline):
                if tok.type == tokenize.NAME and tok.string in ("print", "logging"):
                    names.append(tok.string)
        if names:
            offenders.append((path.name, sorted(set(names))))
    assert offenders == []


# ── waiting path ─────────────────────────────────────────────────────────


def test_r5_1_waiting_mode_no_credentials(monkeypatch, tmp_path, capsys):
    for k in ("TRADELOCKER_EMAIL", "TRADELOCKER_PASSWORD", "TRADELOCKER_SERVER",
              "TRADELOCKER_DEV_API_KEY", "QL_R5_1_BASE_COMMIT"):
        monkeypatch.delenv(k, raising=False)
    # quant-lab is already on sys.path (_QL insert above); the runner must NOT
    # be shadowed by the unrelated execution_runtime/runtime package.
    from runtime.tradelocker_demo_readonly import main

    rc = main(["--out", str(tmp_path)])
    assert rc == 0
    decision = json.loads(
        (tmp_path / "QL_EXEC_R5_1_DECISION.json").read_text(encoding="utf-8")
    )
    assert decision["status"] == "WAITING_TRADELOCKER_DEMO_ACCESS"
    assert decision["real_tradelocker_demo_connected"] is False
    assert decision["broker_write_calls"] == 0
    out = capsys.readouterr().out
    assert "WAITING_TRADELOCKER_DEMO_ACCESS" in out


# ── 32. production false ─────────────────────────────────────────────────


def test_r5_1_production_never_authorized():
    audit = _audit(_seeded_fake()).run()
    assert audit.get("live_execution_authorized", False) is False
    assert audit.get("production_authorized", False) is False
    assert audit.get("r5_2_authorized", False) is False


def _req(method: str, url: str, body: dict = None):
    from execution_runtime.tradelocker.transport import HttpRequest

    return HttpRequest(method=method, url=url, json_body=body)


def _intent():
    from execution_runtime.enums import OrderSide, QuantityUnit

    return OrderIntent(
        intent_id="ro-1",
        account_id="101",
        symbol="EURUSD",
        side=OrderSide.BUY,
        volume=0.1,
        quantity_unit=QuantityUnit.LOT,
        ownership_tag="R5_1",
    )
