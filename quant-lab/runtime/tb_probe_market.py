#!/usr/bin/env python3
"""Live probe: replicate the worker cycle and report WHY the feed is
failing closed (STALE_SIGNAL_BAR / NO_COMMON_CLOSED_BAR / MISSING_LEG)."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

RT = Path(__file__).resolve().parent
sys.path.insert(0, str(RT))
sys.path.insert(0, str(RT.parent))

from tb_runtime_config import STATE_DIR  # noqa: E402
from engines.tb_r6_demo_canary import DemoEnvironment  # noqa: E402
from tb_live.snapshot import (  # noqa: E402
    SynchronizedTriangleFeed, SymbolResolver, CANONICAL_SYMBOLS)
from tb_live.market_data import TBMarketDataConfig  # noqa: E402


def now_iso():
    return datetime.now(timezone.utc).isoformat()


print(f"=== probe start {now_iso()} ===")
env = DemoEnvironment()
print(f"connect: {env.connect()}")
if not env.connected:
    print("FATAL: cannot connect to MT5 terminal")
    sys.exit(1)
print(f"identity gate: {env.identity_check().get('identity_gate_pass')}")

env.calibrate()
off = env.adapter.server_offset_seconds()
print(f"server_offset_s: {off} (expected ~ +3h = +10800)")

resolver = SymbolResolver(env.adapter)
res = resolver.require_resolved()
print(f"symbol mapping: {json.dumps(res.mapping, indent=2)}")
for canon, broker in res.mapping.items():
    info = res.metadata.get(canon, {})
    print(f"  {canon} -> {broker} contract={info.get('contract_size')} "
          f"trade_mode={info.get('trade_mode')}")

cfg = TBMarketDataConfig()
feed = SynchronizedTriangleFeed(env.adapter, config=cfg, resolver=resolver)
ref = env.adapter.server_reference(datetime.now(timezone.utc))
print(f"reference_time: {ref} (server-labeled) | real now: {datetime.now(timezone.utc)}")

for canon in CANONICAL_SYMBOLS:
    broker = res.mapping.get(canon)
    if not broker:
        continue
    bars = env.adapter.get_recent_bars(broker, "M5", count=5) or []
    tk = env.adapter.get_tick(broker)
    if bars:
        last = bars[-1]
        age_s = (ref - last.bar_close_time).total_seconds()
        print(f"  {canon}: last closed bar open={last.bar_open_time} "
              f"close={last.bar_close_time} age_s={age_s:.0f}")
    else:
        print(f"  {canon}: NO BARS from adapter")
    if tk:
        print(f"    tick: time={tk.tick_time} age_ms={tk.quote_age_ms:.0f} "
              f"valid={tk.valid} bid={tk.bid}")
    else:
        print(f"    tick: NONE")

snap = feed.get_synchronized_closed_triangle(reference_time=ref)
print(f"signal_snapshot_valid: {snap.signal_snapshot_valid}")
if not snap.signal_snapshot_valid:
    code = snap.failure_code.value if snap.failure_code else "NO_CODE"
    print(f"FAILURE CODE: {code}")
    print(f"failure detail: {snap.failure_detail}")
else:
    print(f"signal bar close: {snap.signal_bar_close_time}")
print(f"=== probe end ===")
