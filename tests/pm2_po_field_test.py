"""
PM2 PO Field Test — All 40 tests from CC assignment.
Run: python tests/pm2_po_field_test.py
"""
import urllib.request
import json
import time
import sys

BASE = "http://127.0.0.1:8000"
results = []


def test(name, method, path, body=None, timeout=8):
    try:
        url = BASE + path
        if body:
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                url, data=data, method=method,
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(url, method=method)
        r = urllib.request.urlopen(req, timeout=timeout)
        status = r.status
        resp = r.read().decode()[:120]
        results.append(("PASS", name, status, resp))
        print(f"PASS | {name} | {status}")
    except Exception as e:
        err = str(e)[:100]
        results.append(("FAIL", name, 0, err))
        print(f"FAIL | {name} | {err}")


def main():
    print("=" * 60)
    print("PM2 PO FIELD TEST — 40 Tests")
    print(f"Backend: {BASE}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print("\n--- TESTS 1-13: Memory, Agent Execute, PO Tools ---")

    # Test 1: Memory Store WORK
    test("1: memory/store WORK", "POST", "/memory/store",
         {"layer": "WORK", "content": {"key": "pm2_test", "value": "test_from_pm2"}})

    # Test 2: Memory Store LEARNED
    test("2: memory/store LEARNED", "POST", "/memory/store",
         {"layer": "LEARNED", "content": {"finding": "PO tools functional", "confidence": 0.95}})

    # Test 3: Memory Store KNOWLEDGE
    test("3: memory/store KNOWLEDGE", "POST", "/memory/store",
         {"layer": "KNOWLEDGE", "content": {"fact": "OCE backend has 69 PO tools"}})

    # Test 4: Agent Execute read_file
    test("4: agent/execute read_file", "POST", "/agent/execute",
         {"action": "read_file", "params": {"path": "README.md"}})

    # Test 5: Agent Execute write_file
    test("5: agent/execute write_file", "POST", "/agent/execute",
         {"action": "write_file", "params": {"path": "tests/_pm2_test.txt", "content": "PM2 test entry safe to delete"}})

    # Test 6: Agent Execute edit_file
    test("6: agent/execute edit_file", "POST", "/agent/execute",
         {"action": "edit_file", "params": {"path": "tests/_pm2_test.txt", "old_text": "PM2 test entry", "new_text": "PM2 test entry edited"}})

    # Test 7: Agent Execute run_python
    test("7: agent/execute run_python", "POST", "/agent/execute",
         {"action": "run_python", "params": {"code": "print('pm2_python_exec_ok')"}})

    # Test 8: Agent Execute git_op log
    test("8: agent/execute git_op log", "POST", "/agent/execute",
         {"action": "git_op", "params": {"operation": "log", "args": ["--oneline", "-5"]}})

    # Test 9: Agent Execute git_op diff
    test("9: agent/execute git_op diff", "POST", "/agent/execute",
         {"action": "git_op", "params": {"operation": "diff", "args": ["--stat"]}})

    # Test 10: PO Tool git_log
    test("10: PO git_log", "POST", "/api/po/tools/execute",
         {"tool_name": "git_log", "arguments": {"count": 5}})

    # Test 11: PO Tool search_content
    test("11: PO search_content", "POST", "/api/po/tools/execute",
         {"tool_name": "search_content", "arguments": {"pattern": "FastAPI", "file_pattern": "*.py", "path": "oce/backend"}})

    # Test 12: PO Tool write_file
    test("12: PO write_file", "POST", "/api/po/tools/execute",
         {"tool_name": "write_file", "arguments": {"path": "tests/_pm2_po_test.txt", "content": "PO tool write test from PM2"}})

    # Test 13: PO Tool execute_python
    test("13: PO execute_python", "POST", "/api/po/tools/execute",
         {"tool_name": "execute_python", "arguments": {"code": "print('pm2_po_python_exec_ok')"}})

    print("\n--- TESTS 14-19: Memory + PO Chat ---")

    # Test 14: Memory Search
    test("14: memory/search", "GET", "/memory/search?q=pm2_test")

    # Test 15: Memory Compress
    test("15: memory/compress", "POST", "/memory/compress",
         {"layer": "WORK", "max_entries": 50})

    # Test 16: Memory Export
    test("16: memory/export", "GET", "/memory/export")

    # Test 17: Memory Stats
    test("17: memory/stats", "GET", "/memory/stats")

    # Test 18: PO Chat non-streaming
    test("18: PO chat", "POST", "/api/po/chat",
         {"messages": [{"role": "user", "content": "What is your current status?"}], "stream": False},
         timeout=15)

    # Test 19: PO Chat streaming
    test("19: PO chat stream", "POST", "/api/po/chat",
         {"messages": [{"role": "user", "content": "Say hello"}], "stream": True},
         timeout=10)

    print("\n--- TESTS 20-28: Rate Limits, Events, Topology ---")

    # Test 20: Rate Limit Status
    test("20: rate-limit/status", "GET", "/rate-limit/status")

    # Test 21: Rate Limit Errors
    test("21: rate-limit/errors", "GET", "/rate-limit/errors")

    # Test 22: Events Ingest
    test("22: events/ingest", "POST", "/events/ingest",
         {"event_type": "test.pm2", "source": "pm2_test", "payload": {"test_id": 22}})

    # Test 23: Events Types
    test("23: events/types", "GET", "/events/types")

    # Test 24: Events Stats
    test("24: events/stats", "GET", "/events/stats")

    # Test 25: Events Persistence Stats
    test("25: events/persistence/stats", "GET", "/events/persistence/stats")

    # Test 26: Events Persistence Compress
    test("26: events/persistence/compress", "POST", "/events/persistence/compress")

    # Test 27: Topology Edge Create
    test("27: topology/edge", "POST", "/topology/edge",
         {"source": "pm2", "target": "po", "weight": 0.8, "type": "test"})

    # Test 28: Topology Stats
    test("28: topology/stats", "GET", "/topology/stats")

    print("\n--- TESTS 29-36: Observer CRUD ---")

    # Test 29: Observer Create
    test("29: observers POST", "POST", "/observers",
         {"observer_id": "pm2_test_observer", "goal": "Test observer creation", "initial_state": "active"})

    # Test 30: Observer Get
    test("30: observers GET", "GET", "/observers/pm2_test_observer")

    # Test 31: Observer Health
    test("31: observer health", "GET", "/observers/pm2_test_observer/health")

    # Test 32: Observer Activate
    test("32: observer activate", "POST", "/observers/pm2_test_observer/activate")

    # Test 33: Observer Suspend
    test("33: observer suspend", "POST", "/observers/pm2_test_observer/suspend")

    # Test 34: Observer Subscribe
    test("34: observer subscribe", "POST", "/observers/pm2_test_observer/subscribe",
         {"event_types": ["test.pm2"]})

    # Test 35: Observer Stats
    test("35: observers/stats", "GET", "/observers/stats")

    # Test 36: Observer Delete
    test("36: observer delete", "DELETE", "/observers/pm2_test_observer")

    print("\n--- TESTS 37-40: Governance + Resonance ---")

    # Test 37: Governance Propose
    test("37: governance/propose", "POST", "/governance/propose",
         {"proposal_type": "policy_change", "title": "PM2 Test Proposal",
          "description": "Test governance flow", "changes": {"test": True}, "proposer": "pm2"})

    # Test 38: Governance list proposals
    test("38: governance/proposals", "GET", "/governance/proposals")

    # Test 39: Resonance Signal Inject
    test("39: resonance/signal", "POST", "/resonance/signal",
         {"source": "pm2_test", "amplitude": 0.5, "coherence": 0.8, "phase": 0.0, "entropy_delta": 0.1})

    # Test 40: Resonance Score
    test("40: resonance/score", "POST", "/resonance/score",
         {"observer_id": "pm2_test", "observer_phase": 0.0, "observer_coherence": 0.7, "signal_source": "test"})

    # Summary
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    total = len(results)

    print("\n" + "=" * 60)
    print(f"PM2 PO FIELD TEST RESULTS: {passed} PASS, {failed} FAIL out of {total}")
    print("=" * 60)

    if failed > 0:
        print("\nFAILURES:")
        for r in results:
            if r[0] == "FAIL":
                print(f"  {r[1]}: {r[3]}")

    # Return exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
