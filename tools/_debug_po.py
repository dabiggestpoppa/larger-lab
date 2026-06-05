"""Debug POAgent behavior"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from core.observer.po_agent import POAgent, TOOL_DEFINITIONS, MODEL_CHAIN

agent = POAgent()
print("Models:", MODEL_CHAIN)

msg = [{"role": "user", "content": "run git status and tell me what files are modified"}]

for model in MODEL_CHAIN:
    print(f"\n=== Model: {model} ===")
    resp, tool_calls, used_model, err = agent._call_llm(msg, tools=TOOL_DEFINITIONS)
    print(f"  With tools - resp: {repr(resp)[:100] if resp else None}, tc: {tool_calls}, err: {str(err)[:80] if err else None}")
    
    if err and "http_400" in str(err):
        print("  -> Retrying without tools...")
        resp2, tc2, _, err2 = agent._call_llm(msg, tools=None)
        print(f"  Without tools - resp: {repr(resp2)[:150] if resp2 else None}")
        if resp2:
            has_tool = "```tool" in resp2 or "<tool>" in resp2
            print(f"  Has tool blocks: {has_tool}")
