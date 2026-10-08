"""B5-I03D adversarial red-team pass (directive: deliberate adversarial review
before ratification).  Covers the fourteen required case classes against the
committed resolver + registry.  Every case asserts the expected law; observed
behavior is printed for the implementation evidence document.

Run from quant-lab:  PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/b5_i03_redteam.py
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

RESULTS_PATH = Path(__file__).resolve().with_name("b5_i03_redteam_results.json")

sys.path.insert(0, "src")

from crypto_sensor_fabric.normalization.enums import PayoffType  # noqa: E402
import crypto_sensor_fabric.normalization.identity as I  # noqa: E402

UTC = timezone.utc
SHA = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
T0 = datetime(2023, 1, 1, 12, tzinfo=UTC)
T1 = datetime(2024, 1, 1, 12, tzinfo=UTC)
T2 = datetime(2025, 1, 1, 12, tzinfo=UTC)
PROV, VEN = "PROV", "EXA_FUT"
OTHERVEN = "OTHER_FUT"
ST = I.IdentityResolutionStatus

def asset(aid="BTC", sym="BTC"):
    return I.CanonicalAsset(asset_id=aid, symbol_canonical=sym, asset_type="CRYPTO", metadata_version="1")

def econ(ecid="EC-BTCUSDT-PERP-A", underlying="BTC"):
    return I.EconomicContract(
        economic_contract_id=ecid, underlying_asset_id=underlying,
        quote_asset_id="USDT", settlement_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE", perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR)

def ven(vid=VEN):
    return I.Venue(venue_id=vid)

def vi(native="XBTUSDT", pid="PID-1", vid=VEN, first=T0, last=T2):
    return I.VenueInstrument(provider=PROV, venue=vid, native_symbol=native,
        provider_instrument_id=pid, instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA, first_seen_at=first, last_seen_at=last)

def ci(id_="CI-A", native="XBTUSDT", vfrom=T0, vto=T1, kfrom=None, vid=VEN):
    return I.ContractInstance(
        contract_instance_id=id_, provider=PROV, venue=vid, native_symbol=native,
        economic_contract_id="EC-BTCUSDT-PERP-A", valid_from=vfrom, valid_to=vto,
        known_from=kfrom or (vfrom - timedelta(days=2)), known_to=None,
        contract_multiplier=Decimal("1"), multiplier_unit="CONTRACT",
        price_unit="USDT", quantity_unit="BTC", settlement_asset_id="USDT",
        payoff_type=PayoffType.LINEAR, inverse_flag=False, quanto_flag=False,
        tick_size=Decimal("0.1"), lot_size=Decimal("0.0001"),
        contract_terms_version="1", source_evidence_refs=("provider-docs:base",))

def al(text, atype, iid="CI-A", vfrom=T0, vto=None, kfrom=None, prov=PROV, ven_id=VEN, alid=None):
    return I.InstrumentAlias(
        alias_id=alid or ("AL:" + iid + ":" + text + ":" + atype.value),
        provider=prov, venue=ven_id, alias_text=text, alias_type=atype,
        contract_instance_id=iid, valid_from=vfrom, valid_to=vto,
        known_from=kfrom or (vfrom - timedelta(days=1)),
        source_evidence_refs=("provider-docs:alias",), confidence="operator-curated")

def le(state, iid="CI-A", vfrom=T0, vto=None, kfrom=None, vid=VEN):
    return I.InstrumentLifecycle(
        provider=PROV, venue=vid, contract_instance_id=iid, lifecycle_state=state,
        valid_from=vfrom, valid_to=vto, known_from=kfrom or (vfrom - timedelta(days=1)),
        source_evidence_refs=("provider-docs:lc",))

def snap(version="rt", instances=(), aliases=(), lifecycles=(), venues=None, instruments=None):
    return I.IdentityRegistrySnapshot(
        registry_version=version, assets=(asset(), asset("USDT", "USDT")),
        venues=tuple(venues) if venues else (ven(),),
        economic_contracts=(econ(),),
        venue_instruments=tuple(instruments) if instruments is not None else (vi(),),
        contract_instances=instances, aliases=aliases, lifecycle_events=lifecycles)

def resolve(s, native, ev, kc, pid=None):
    return I.resolve_instrument(s, provider=PROV, venue=VEN, native_symbol=native,
        event_time=ev, knowledge_cutoff=kc, optional_provider_instrument_id=pid)

def no_ids(r):
    return (r.contract_instance_id is None and r.economic_contract_id is None
            and r.canonical_asset_id is None and r.matched_alias_id is None
            and r.terms_version is None and not r.source_evidence_refs)

def flags(r):
    return sorted(f.value for f in r.quality_flags)

results = []
def case(cid, klass, probe, check):
    try:
        observed = check()
        ok, detail = observed
    except Exception as exc:  # a refusal IS a valid observed outcome
        ok, detail = False, "UNEXPECTED EXCEPTION: " + type(exc).__name__ + ": " + str(exc)[:200]
    results.append({"case_id": cid, "class": klass, "probe": probe,
                    "observed": detail, "result": "PASS" if ok else "FAIL"})
    print(("PASS " if ok else "FAIL ") + cid + " :: " + detail[:160])

# ---------------------------------------------------------------------------
# A1 multiple candidates inside the same tier
# ---------------------------------------------------------------------------
def a1a():
    s = snap(instances=(ci("CI-A"), ci("CI-B", native="BBTA", vfrom=T0, vto=None)),
             aliases=(al("AMBT", I.AliasType.API_SYMBOL, iid="CI-A"),
                      al("AMBT", I.AliasType.DISPLAY_SYMBOL, iid="CI-B")))
    r = resolve(s, "AMBT", T0 + timedelta(days=1), T2)
    return (r.status is ST.AMBIGUOUS and no_ids(r),
            "two same-text carriers -> " + r.status.value + ", ids carried: " + str(not no_ids(r)))
case("A1a", "multiple candidates same tier (alias scan)",
     "two same-text alias rows -> different instances, both PIT-valid: refuse a winner", a1a)

def a1b():
    s = snap(instances=(ci("CI-A"),),
             aliases=(al("SAMEI", I.AliasType.API_SYMBOL, iid="CI-A"),
                      al("SAMEI", I.AliasType.LEGACY_SYMBOL, iid="CI-A")))
    r = resolve(s, "SAMEI", T0 + timedelta(days=1), T2)
    return (r.status is ST.RESOLVED_ALIAS and r.contract_instance_id == "CI-A",
            "two same-text carriers -> SAME instance: unique identity " + r.status.value + " -> " + str(r.contract_instance_id))
case("A1b", "multiple candidates same tier (alias scan)",
     "two same-text alias rows -> SAME instance: not ambiguity, deterministic unique identity", a1b)

def a1c():
    try:
        snap(instances=(ci("CI-A"), ci("CI-B", vfrom=T0 + timedelta(days=1), vto=T2)))
        return (False, "overlapping active terms were ACCEPTED (registry front line broken)")
    except Exception as exc:
        return (True, "overlapping active terms for one native symbol refused at the registry: " + type(exc).__name__)
case("A1c", "multiple candidates same tier (symbol tier unreachable by construction)",
     "two overlapping instances for the same (provider, venue, symbol): the registry must refuse, so tier-2 dual-candidate ambiguity is unreachable by construction", a1c)

def a1d():
    s = snap(instances=(ci("CI-A", vfrom=T0, vto=T1), ci("CI-B", vfrom=T1, vto=T2)))
    r = resolve(s, "XBTUSDT", T1, T2)  # boundary instant: A exclusive-end, B inclusive-start
    return (r.status is ST.RESOLVED_EXACT and r.contract_instance_id == "CI-B",
            "adjacent terms at the shared boundary instant -> unique " + str(r.contract_instance_id))
case("A1d", "multiple candidates same tier (boundary)",
     "adjacent instances abutting at T1: event exactly T1 must resolve uniquely to the NEW instance (no double-claim)", a1d)

# ---------------------------------------------------------------------------
# A2 alias overlap
# ---------------------------------------------------------------------------
def a2a():
    s = snap(instances=(ci("CI-A"),),
             aliases=(al("OVLP", I.AliasType.API_SYMBOL, iid="CI-A", vfrom=T0, vto=None),
                      al("OVLP", I.AliasType.WEBSOCKET_SYMBOL, iid="CI-A", vfrom=T0, vto=None)))
    r = resolve(s, "OVLP", T0 + timedelta(days=1), T2)
    return (r.status is ST.RESOLVED_ALIAS and r.contract_instance_id == "CI-A",
            "overlapping windows, same instance -> " + r.status.value + " -> " + str(r.contract_instance_id))
case("A2a", "alias overlap",
     "overlapping alias windows on the SAME instance collapse to one unique identity", a2a)

def a2b():
    s = snap(instances=(ci("CI-A"), ci("CI-B", native="BBTA", vfrom=T0, vto=None)),
             aliases=(al("OVLP2", I.AliasType.API_SYMBOL, iid="CI-A", vfrom=T0, vto=T0 + timedelta(days=5)),
                      al("OVLP2", I.AliasType.DISPLAY_SYMBOL, iid="CI-B", vfrom=T0 + timedelta(days=2), vto=None)))
    r_mid = resolve(s, "OVLP2", T0 + timedelta(days=3), T2)   # both windows open
    r_late = resolve(s, "OVLP2", T0 + timedelta(days=6), T2)  # only B's window open
    return (r_mid.status is ST.AMBIGUOUS and r_late.status is ST.RESOLVED_ALIAS
            and r_late.contract_instance_id == "CI-B" and no_ids(r_mid),
            "overlap window: both open -> " + r_mid.status.value + " (no ids); one open -> " + r_late.status.value + " -> " + str(r_late.contract_instance_id))
case("A2b", "alias overlap",
     "partially overlapping alias windows: ambiguous only while BOTH carriers are valid; unique after one expires", a2b)

# ---------------------------------------------------------------------------
# A3 alias validity-window boundaries
# ---------------------------------------------------------------------------
def a3():
    s = snap(instances=(ci("CI-A"),),
             aliases=(al("BND", I.AliasType.API_SYMBOL, vfrom=T0 + timedelta(days=1), vto=T1),))
    r_start = resolve(s, "BND", T0 + timedelta(days=1), T2)      # == valid_from
    r_end = resolve(s, "BND", T1, T2)                             # == valid_to (exclusive)
    r_before = resolve(s, "BND", T0, T2)                          # < valid_from
    r_open = snap(instances=(ci("CI-A", vto=None),),
                  aliases=(al("BND", I.AliasType.API_SYMBOL, vfrom=T0 + timedelta(days=1), vto=None),))
    r_after_end = resolve(r_open, "BND", T2 + timedelta(days=1), T2 + timedelta(days=1))
    ok = (r_start.status is ST.RESOLVED_ALIAS and r_end.status is ST.UNKNOWN_SYMBOL
          and r_before.status is ST.UNKNOWN_SYMBOL
          and r_after_end.status is ST.RESOLVED_ALIAS)
    return (ok, "start-inclusive " + r_start.status.value + " | end-exclusive " + r_end.status.value
            + " | before " + r_before.status.value + " | open-ended-still-valid " + r_after_end.status.value)
case("A3", "alias validity-window boundaries",
     "[valid_from, valid_to) half-open law + open-ended valid_to, probed exactly at both boundaries", a3)

# ---------------------------------------------------------------------------
# A4 provider-ID conflict
# ---------------------------------------------------------------------------
def a4a():
    s = snap(instances=(ci("CI-A"), ci("CI-ETH", native="ETHUSDT", vfrom=T0, vto=None)),
             instruments=(vi("XBTUSDT", "PID-1"), vi("ETHUSDT", "PID-2")))
    r = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2, pid="PID-2")
    return (r.status is ST.RESOLVED_EXACT and r.contract_instance_id == "CI-ETH",
            "pid PID-2 anchors the ETHUSDT instrument: tier 1 resolves the ANCHORED instance (" + str(r.contract_instance_id) + "), queried text does not override")
case("A4a", "provider-ID conflict (id vs symbol text)",
     "queried text XBTUSDT but pid PID-2 anchored to ETHUSDT: the ID anchors the instrument (directive 15)", a4a)

def a4b():
    s = snap(instances=(ci("CI-A"),))
    r = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2, pid="PID-NOPE")
    return (r.status is ST.RESOLVED_EXACT and r.contract_instance_id == "CI-A",
            "nonexistent pid falls through to the symbol tiers -> " + r.status.value + " via symbol")
case("A4b", "provider-ID conflict (missing id)",
     "nonexistent provider id is not a lifeline: falls through to symbol tiers", a4b)

def a4c():
    s = snap(instances=(ci("CI-A", kfrom=T1),))
    r = resolve(s, "XBTUSDT", T0, T0, pid="PID-1")
    return (r.status is ST.PIT_KNOWLEDGE_BLOCKED and no_ids(r),
            "pid present but instance unknown at cutoff -> " + r.status.value + " (no identity leak through the id)")
case("A4c", "provider-ID conflict (late instance behind id)",
     "the id alone must not leak an instance the cutoff has not caught up with", a4c)

# ---------------------------------------------------------------------------
# A5 venue mismatch
# ---------------------------------------------------------------------------
def a5():
    s = snap(instances=(ci("CI-A"),),
             aliases=(al("WRONGV", I.AliasType.API_SYMBOL, ven_id=OTHERVEN),),
             venues=(I.Venue(venue_id=VEN), I.Venue(venue_id=OTHERVEN)))
    r = resolve(s, "WRONGV", T0 + timedelta(days=1), T2)
    r_sym = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2)
    return (r.status is ST.UNKNOWN_SYMBOL and r_sym.status is ST.RESOLVED_EXACT,
            "alias on OTHER_FUT invisible from EXA_FUT (" + r.status.value + "); own-venue symbol still resolves (" + r_sym.status.value + ")")
case("A5", "venue mismatch",
     "registry-valid cross-venue fixture: venue gate is exact, never cross-venue", a5)

# ---------------------------------------------------------------------------
# A6 nonexistent instance references
# ---------------------------------------------------------------------------
def a6a():
    try:
        snap(aliases=(al("GHOSTREF", I.AliasType.API_SYMBOL, iid="CI-NOPE"),))
        return (False, "alias -> missing instance was ACCEPTED")
    except Exception as exc:
        return (True, "alias -> unregistered instance refused: " + type(exc).__name__)
case("A6a", "nonexistent instance references",
     "alias row pointing at an unregistered contract instance must fail snapshot validation", a6a)

def a6b():
    try:
        snap(lifecycles=(le(I.LifecycleState.ACTIVE, iid="CI-NOPE"),))
        return (False, "lifecycle -> missing instance was ACCEPTED")
    except Exception as exc:
        return (True, "lifecycle -> unregistered instance refused: " + type(exc).__name__)
case("A6b", "nonexistent instance references",
     "lifecycle row pointing at an unregistered contract instance must fail snapshot validation", a6b)

# ---------------------------------------------------------------------------
# A7 lifecycle-state incompatibility
# ---------------------------------------------------------------------------
def a7a():
    try:
        snap(instances=(ci("CI-A"),),
             lifecycles=(le(I.LifecycleState.SUSPENDED, vfrom=T0, vto=T1),
                         le(I.LifecycleState.SUSPENDED, vfrom=T0 + timedelta(days=1), vto=None)))
        return (False, "overlapping same-state lifecycle windows were ACCEPTED")
    except Exception as exc:
        return (True, "overlapping SUSPENDED windows for one instance refused: " + type(exc).__name__)
case("A7a", "lifecycle-state incompatibility",
     "two overlapping windows of the SAME state for one instance: contradictory evidence refused", a7a)

def a7b():
    s = snap(instances=(ci("CI-A"),),
             lifecycles=(le(I.LifecycleState.DELISTED, vfrom=T0, vto=None),))
    r = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2)
    return (r.status is ST.RESOLVED_EXACT,
            "DELISTED lifecycle row over a PIT-valid instance is inert evidence; interval law governs -> " + r.status.value)
case("A7b", "lifecycle-state incompatibility (inert states)",
     "a DELISTED lifecycle row covering a live instance does not block or warn: only SUSPENDED/DELISTING_ANNOUNCED carry resolver semantics (documented choice)", a7b)

def a7c():
    s = snap(instances=(ci("CI-A"),),
             lifecycles=(le(I.LifecycleState.SUSPENDED, vfrom=T0, vto=None, kfrom=T2 + timedelta(days=1)),))
    r = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2)
    return (r.status is ST.RESOLVED_EXACT and "IDENTITY_LIFECYCLE_BOUNDARY" not in flags(r),
            "SUSPENDED row known only AFTER the cutoff: no warning leak -> " + r.status.value + " flags=" + str(flags(r)))
case("A7c", "lifecycle-state incompatibility (late knowledge)",
     "a suspension the cutoff has not caught up with must not downgrade the resolution", a7c)

# ---------------------------------------------------------------------------
# A8 event-vs-knowledge disagreement
# ---------------------------------------------------------------------------
def a8a():
    s = snap(instances=(ci("CI-A", kfrom=T0 + timedelta(days=10)),))
    r = resolve(s, "XBTUSDT", T0 - timedelta(days=5), T0 + timedelta(days=5))
    return (r.status is ST.PIT_KNOWLEDGE_BLOCKED and no_ids(r),
            "event before valid_from AND instance known after cutoff -> " + r.status.value + " (blocked, not NOT_YET_LISTED)")
case("A8a", "event-vs-knowledge disagreement",
     "temporal verdicts require knowledge: pre-listing event with late-known instance is PIT-blocked, not NOT_YET_LISTED", a8a)

def a8b():
    s = snap(instances=(ci("CI-A", kfrom=T0 - timedelta(days=10)),))
    r_before = resolve(s, "XBTUSDT", T0 - timedelta(days=5), T0 - timedelta(days=3))
    return (r_before.status is ST.NOT_YET_LISTED,
            "same pre-listing event but instance known by cutoff -> " + r_before.status.value + " (knowledge decides the verdict form)")
case("A8b", "event-vs-knowledge disagreement",
     "identical event, earlier knowledge: NOT_YET_LISTED verdict becomes reachable only once the row is known", a8b)

# ---------------------------------------------------------------------------
# A9 information not yet known at evaluation time
# ---------------------------------------------------------------------------
def a9a():
    s = snap(instances=(ci("CI-A"),),
             aliases=(al("LATEAL", I.AliasType.API_SYMBOL, kfrom=T2 + timedelta(days=1)),))
    r = resolve(s, "LATEAL", T0 + timedelta(days=1), T2)
    return (r.status is ST.PIT_KNOWLEDGE_BLOCKED and no_ids(r),
            "registered-but-late alias -> " + r.status.value + " (fail-closed sweep, never silent unknown)")
case("A9a", "information not yet known",
     "alias row registered after the cutoff: PIT_KNOWLEDGE_BLOCKED via the tier-5 sweep", a9a)

def a9b():
    s = snap(instances=(ci("CI-A"),),
             instruments=(vi(first=T2 + timedelta(days=1), last=T2 + timedelta(days=2)),))
    r = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2, pid="PID-1")
    return (r.status is ST.RESOLVED_EXACT,
            "instrument row first_seen after the event: tier 1 still resolves because the IDENTITY carrier (instance) is knowledge-gated; VenueInstrument has no known_from field in the frozen model (documented observation)")
case("A9b", "information not yet known (instrument metadata)",
     "VenueInstrument.first_seen_at is discovery metadata, not a validity law: the dual-clock gate lives on the ContractInstance (documented, not silently assumed)", a9b)

# ---------------------------------------------------------------------------
# A10 missing evidence / reference
# ---------------------------------------------------------------------------
def a10a():
    s = snap(instances=(ci("CI-A"),), aliases=(al("EVID", I.AliasType.API_SYMBOL),))
    r_exact = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2)
    r_alias = resolve(s, "EVID", T0 + timedelta(days=1), T2)
    r_unres = resolve(s, "NOTHING", T0 + timedelta(days=1), T2)
    ok = (r_exact.source_evidence_refs == ("provider-docs:base",)
          and r_alias.source_evidence_refs == ("provider-docs:alias", "provider-docs:base")
          and not r_unres.source_evidence_refs and no_ids(r_unres))
    return (ok, "exact evidence " + str(r_exact.source_evidence_refs) + " | alias evidence " + str(r_alias.source_evidence_refs) + " | unresolved evidence " + str(r_unres.source_evidence_refs))
case("A10", "missing evidence / reference",
     "resolved answers name their evidence; alias matches prepend alias evidence; unresolved answers carry none", a10a)

# ---------------------------------------------------------------------------
# A11 conflicting signals between resolver tiers
# ---------------------------------------------------------------------------
def a11():
    s = snap(instances=(ci("CI-A"), ci("CI-B", native="BBTA", vfrom=T0, vto=None)),
             aliases=(al("BBTA", I.AliasType.API_SYMBOL, iid="CI-B"),
                      al("TIERW", I.AliasType.API_SYMBOL, iid="CI-A")))
    r1 = resolve(s, "BBTA", T0 + timedelta(days=1), T2)     # native symbol of CI-B AND alias of CI-B
    r2 = resolve(s, "TIERW", T0 + timedelta(days=1), T2)    # alias only
    r3 = resolve(s, "XBTUSDT", T0 + timedelta(days=1), T2, pid="PID-1")  # tier1
    ok = (r1.status is ST.RESOLVED_EXACT and r1.contract_instance_id == "CI-B"
          and r2.status is ST.RESOLVED_ALIAS and r3.status is ST.RESOLVED_EXACT)
    return (ok, "alias-text==native-symbol -> tier2 (" + r1.status.value + "); alias-only -> tier3 (" + r2.status.value + "); pid present -> tier1 (" + r3.status.value + ")")
case("A11", "conflicting signals between tiers",
     "one text registered as both native symbol and alias; alias-only text; pid+symbol: tier order decides every conflict", a11)

# ---------------------------------------------------------------------------
# A12 equivalent-input permutation determinism
# ---------------------------------------------------------------------------
def a12():
    # first: the red-team DEFECT probe - alias match inside a SUSPENDED window
    # must downgrade to RESOLVED_WITH_WARNING (matched_alias_id dropped,
    # provenance kept), never crash on the I03 validator law.
    s_w = snap(instances=(ci("CI-A"),),
               aliases=(al("WRND", I.AliasType.API_SYMBOL),),
               lifecycles=(le(I.LifecycleState.SUSPENDED, vfrom=T0, vto=None),))
    r_w = resolve(s_w, "WRND", T0 + timedelta(days=1), T2)
    warn_ok = (r_w.status is ST.RESOLVED_WITH_WARNING
               and r_w.matched_alias_id is None
               and r_w.contract_instance_id == "CI-A"
               and "IDENTITY_ALIAS_USED" in flags(r_w)
               and "IDENTITY_LIFECYCLE_BOUNDARY" in flags(r_w)
               and "provider-docs:alias" in r_w.source_evidence_refs)
    inst = (ci("CI-A"), ci("CI-B", native="BBTA", vfrom=T1, vto=None))
    als = (al("P1", I.AliasType.API_SYMBOL, iid="CI-A"),
           al("P2", I.AliasType.LEGACY_SYMBOL, iid="CI-B", vfrom=T1))
    lcs = (le(I.LifecycleState.SUSPENDED, iid="CI-A", vfrom=T0 + timedelta(days=1), vto=T0 + timedelta(days=2)),)
    s1 = snap("perm", instances=inst, aliases=als, lifecycles=lcs)
    s2 = snap("perm", instances=tuple(reversed(inst)), aliases=tuple(reversed(als)), lifecycles=tuple(reversed(lcs)))
    queries = [("XBTUSDT", T0 + timedelta(days=1)), ("BBTA", T1 + timedelta(days=1)),
               ("P1", T0 + timedelta(days=1)), ("P2", T1 + timedelta(days=1)), ("GHOST", T0)]
    diffs = []
    for text, ev in queries:
        for kc in (T0 + timedelta(days=2), T2 + timedelta(days=1)):
            r1 = resolve(s1, text, ev, kc)
            r2 = resolve(s2, text, ev, kc)
            if r1.model_dump() != r2.model_dump():
                diffs.append((text, ev.isoformat()))
    same_bytes = (I.serialize_identity_registry_yaml(s1) == I.serialize_identity_registry_yaml(s2))
    return (warn_ok and not diffs and same_bytes,
            "alias+suspension -> " + r_w.status.value + " (matched_alias_id dropped, provenance kept); "
            "10 query x cutoff pairs identical across permutations; YAML byte-identical: " + str(same_bytes))
case("A12", "equivalent-input permutation determinism",
     "same logical snapshot in shuffled collection order: every resolution field-identical, serialization byte-identical", a12)

# ---------------------------------------------------------------------------
# A13 duplicate registry records
# ---------------------------------------------------------------------------
def a13():
    refusals = []
    probes = [
        ("duplicate alias identity", lambda: snap(instances=(ci("CI-A"),),
            aliases=(al("DUP", I.AliasType.API_SYMBOL), al("DUP", I.AliasType.API_SYMBOL)))),
        ("duplicate contract_instance_id", lambda: snap(instances=(ci("CI-A"), ci("CI-A")))),
        ("duplicate lifecycle row", lambda: snap(instances=(ci("CI-A"),),
            lifecycles=(le(I.LifecycleState.ACTIVE), le(I.LifecycleState.ACTIVE)))),
        ("duplicate venue instrument key", lambda: snap(instruments=(vi(), vi()))),
        ("duplicate venue_id", lambda: snap(venues=(I.Venue(venue_id=VEN), I.Venue(venue_id=VEN)))),
        ("duplicate asset_id", lambda: I.IdentityRegistrySnapshot(
            registry_version="d", assets=(asset(), asset()),
            venues=(ven(),), economic_contracts=(econ(),), venue_instruments=(vi(),),
            contract_instances=(ci("CI-A"),))),
    ]
    for name, build in probes:
        try:
            build()
            refusals.append(name + "=ACCEPTED(BAD)")
        except Exception:
            refusals.append(name + "=refused")
    ok = all(r.endswith("refused") for r in refusals)
    return (ok, "; ".join(refusals))
case("A13", "duplicate registry records",
     "every duplicate identity (alias row, instance id, lifecycle row, instrument key, venue id, asset id) refused at the snapshot boundary", a13)

# ---------------------------------------------------------------------------
# A14 referential-integrity failure
# ---------------------------------------------------------------------------
def a14():
    refusals = []
    probes = [
        ("alias->unregistered venue", lambda: snap(instances=(ci("CI-A"),),
            aliases=(al("RV", I.AliasType.API_SYMBOL, ven_id="GHOSTVEN"),))),
        ("instance->unregistered venue", lambda: snap(instances=(ci("CI-A", vid="GHOSTVEN"),))),
        ("instance->unregistered economic contract", lambda: snap(instances=(
            I.ContractInstance(
                contract_instance_id="CI-X", provider=PROV, venue=VEN,
                native_symbol="XBTUSDT", economic_contract_id="EC-GHOST",
                valid_from=T0, valid_to=T1, known_from=T0, known_to=None,
                contract_multiplier=Decimal("1"), multiplier_unit="CONTRACT",
                price_unit="USDT", quantity_unit="BTC", settlement_asset_id="USDT",
                payoff_type=PayoffType.LINEAR, inverse_flag=False, quanto_flag=False,
                tick_size=Decimal("0.1"), lot_size=Decimal("0.0001"),
                contract_terms_version="1", source_evidence_refs=("provider-docs:x",))),)),
        ("instrument->unregistered venue", lambda: snap(instruments=(vi(vid="GHOSTVEN"),))),
        ("lifecycle->unregistered venue", lambda: snap(instances=(ci("CI-A"),),
            lifecycles=(le(I.LifecycleState.ACTIVE, vid="GHOSTVEN"),))),
    ]
    for name, build in probes:
        try:
            build()
            refusals.append(name + "=ACCEPTED(BAD)")
        except Exception:
            refusals.append(name + "=refused")
    ok = all(r.endswith("refused") for r in refusals)
    return (ok, "; ".join(refusals))
case("A14", "referential-integrity failure",
     "dangling references (alias/instance/instrument/lifecycle -> unregistered venue, instance -> unregistered economic contract) all refused", a14)

# ---------------------------------------------------------------------------
print("")
fails = [r["case_id"] for r in results if r["result"] == "FAIL"]
print("RED-TEAM SUMMARY: " + str(len(results) - len(fails)) + "/" + str(len(results)) + " PASS" + (" | FAILURES: " + ", ".join(fails) if fails else ""))
with open(RESULTS_PATH, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"created": "2026-10-07", "checkpoint": "SENSOR-B5-I03",
               "summary": {"cases": len(results), "passed": len(results) - len(fails),
                            "all_pass": not fails},
               "rows": results}, f, indent=2, ensure_ascii=False, sort_keys=True)
    f.write("\n")
print("results -> " + str(RESULTS_PATH))
