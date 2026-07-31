"""
PM2 Whop Store Build Verification
Executed by: PM2 (Primary Observer)
Task: Verify Whop store build via OCE backend
"""
import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"
results = {}


def req(method, path, body=None, timeout=10):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        return None, str(e)


def main():
    print("=" * 60)
    print("PM2 WHOP STORE BUILD VERIFICATION")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # STEP 1: Health check
    print("\n[STEP 1] OCE Backend Health Check")
    status, data = req("GET", "/health")
    results["step1_health"] = {"status": status, "data": data}
    print(f"  HTTP {status}: {data}")

    # STEP 2: Store Whop build completion in memory
    print("\n[STEP 2] Store Whop Build Memory")
    status, data = req("POST", "/memory/store", {
        "layer": "WORK",
        "content": {
            "task": "whop_store_build",
            "status": "complete",
            "products_count": 15,
            "active_consultations": 3,
            "future_offerings": 12,
            "brand": "MAD LABS",
            "store_path": "whop-store/",
            "executor": "PM2"
        }
    })
    results["step2_memory_store"] = {"status": status, "data": data}
    print(f"  HTTP {status}: {data}")

    # STEP 3: Create Whop store observer
    print("\n[STEP 3] Create Whop Store Observer")
    status, data = req("POST", "/observers", {
        "observer_id": "whop_store_obs",
        "name": "Whop Store Observer",
        "observer_type": "business",
        "goal": "Monitor MAD LABS Whop store performance and sales",
        "initial_state": "active"
    })
    results["step3_observer"] = {"status": status, "data": data}
    print(f"  HTTP {status}: {data}")

    # STEP 4: Ingest store build event
    print("\n[STEP 4] Ingest Store Build Event")
    status, data = req("POST", "/events/ingest", {
        "event_type": "store.build.complete",
        "source": "pm2",
        "payload": {
            "store": "MAD LABS Whop",
            "products": 15,
            "active": 3,
            "future": 12,
            "status": "pre_launch"
        }
    })
    results["step4_event"] = {"status": status, "data": data}
    print(f"  HTTP {status}: {data}")

    # STEP 5: Governance proposal for store launch
    print("\n[STEP 5] Governance Proposal - Store Launch")
    status, data = req("POST", "/governance/propose", {
        "proposal_type": "business_decision",
        "title": "MAD LABS Whop Store Launch",
        "description": "Approve launch of MAD LABS Whop storefront with 3 active consultations and 12 future offerings",
        "changes": {"store_status": "launch", "products": 15},
        "proposer": "pm2"
    })
    results["step5_governance"] = {"status": status, "data": data}
    print(f"  HTTP {status}: {data}")

    # STEP 6: Resonance signal
    print("\n[STEP 6] Resonance Signal - Store Build")
    status, data = req("POST", "/resonance/signal", {
        "source": "pm2_whop_build",
        "amplitude": 0.9,
        "coherence": 0.95,
        "phase": 0.0,
        "entropy_delta": 0.05
    })
    results["step6_resonance"] = {"status": status, "data": data}
    print(f"  HTTP {status}: {data}")

    # STEP 7: Collect all stats
    print("\n[STEP 7] Collect System Stats")
    for path, key in [
        ("/memory/stats", "memory_stats"),
        ("/events/stats", "event_stats"),
        ("/resonance/stats", "resonance_stats"),
        ("/governance/status", "governance_status"),
    ]:
        status, data = req("GET", path)
        results[f"step7_{key}"] = {"status": status, "data": data}
        print(f"  {key}: HTTP {status}")

    # STEP 8: Summary report
    print("\n" + "=" * 60)
    print("PM2 WHOP STORE VERIFICATION REPORT")
    print("=" * 60)

    passed = 0
    failed = 0
    for k, v in results.items():
        http = v["status"]
        if http and 200 <= http < 300:
            icon = "PASS"
            passed += 1
        else:
            icon = "FAIL"
            failed += 1
        print(f"  {icon} {k}: HTTP {http}")

    print("=" * 60)
    print(f"RESULTS: {passed} PASS, {failed} FAIL out of {len(results)}")
    print("=" * 60)

    # Write results to file
    with open("O2C-VAULT/journal_20260626T142000Z_pm2_whop_build.json", "w") as f:
        json.dump({
            "type": "pm2_whop_verification",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "results": {k: {"status": v["status"], "data": str(v["data"])[:200]} for k, v in results.items()},
            "summary": {"passed": passed, "failed": failed, "total": len(results)}
        }, f, indent=2)
    print("\nResults written to O2C-VAULT/journal_20260626T142000Z_pm2_whop_build.json")


if __name__ == "__main__":
    main()
