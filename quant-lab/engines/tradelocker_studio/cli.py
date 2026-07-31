"""
TradeLocker Studio CLI — Write strategy code, run backtest, read results.
========================================================================
Uses CDP (Chrome DevTools Protocol) to control the TradeLocker Desktop app.

Usage:
    python cli.py write                    # Write strategy to Studio editor
    python cli.py backtest                 # Click Backtest button, wait for results
    python cli.py results                  # Read backtest results from DOM
    python cli.py run                      # Write + Backtest + Results (full pipeline)
    python cli.py --help

Prerequisites:
    - TradeLocker Desktop running with CDP on port 9222
    - Studio page open in the browser
"""
import argparse
import json
import sys
import time
from pathlib import Path

# ─── Ensure repo root is on path ───
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import http.client
import websocket


CDP_HOST = "localhost"
CDP_PORT = 9222
STUDIO_URL_PATTERN = "studio"


def get_studio_ws_url():
    """Find the Studio page's WebSocket debugger URL via CDP HTTP API."""
    conn = http.client.HTTPConnection(CDP_HOST, CDP_PORT)
    conn.request("GET", "/json/list")
    resp = conn.getresponse()
    targets = json.loads(resp.read())
    conn.close()

    for t in targets:
        if STUDIO_URL_PATTERN in t.get("url", ""):
            return t["webSocketDebuggerUrl"], t["id"]
    raise RuntimeError(
        "Studio page not found. Open TradeLocker Studio in the browser first."
    )


class CDPSession:
    """Minimal CDP WebSocket client for Studio automation."""

    def __init__(self):
        self.ws_url, self.target_id = get_studio_ws_url()
        # Suppress the Origin header to avoid CDP 403 Forbidden
        self.ws = websocket.create_connection(
            self.ws_url,
            timeout=30,
            origin="",
        )
        self._msg_id = 0
        self._pending = {}
        self._lock = None
        self._setup_listener()

    def _setup_listener(self):
        """Start background listener for CDP responses."""
        import threading
        self._lock = threading.Lock()
        self._listener = threading.Thread(target=self._listen, daemon=True)
        self._listener.start()

    def _listen(self):
        while True:
            try:
                msg = self.ws.recv()
                data = json.loads(msg)
                if "id" in data:
                    with self._lock:
                        self._pending[data["id"]] = data
            except Exception:
                break

    def send(self, method, params=None):
        self._msg_id += 1
        msg_id = self._msg_id
        with self._lock:
            self._pending[msg_id] = None
        self.ws.send(json.dumps({
            "id": msg_id,
            "method": method,
            "params": params or {}
        }))
        # Wait for response
        for _ in range(300):  # 30 seconds max
            with self._lock:
                if self._pending.get(msg_id) is not None:
                    return self._pending.pop(msg_id)
            time.sleep(0.1)
        raise TimeoutError(f"CDP call {method} timed out")

    def evaluate(self, expression, await_promise=False):
        """Evaluate JS expression and return the result value."""
        params = {
            "expression": expression,
            "returnByValue": True,
        }
        if await_promise:
            params["awaitPromise"] = True
        result = self.send("Runtime.evaluate", params)
        # CDP response structure: {"id":N,"result":{"result":{"type":"...","value":...}}}
        try:
            inner = result.get("result", {}).get("result", {})
            if "value" in inner:
                return inner["value"]
            if "exceptionDetails" in result.get("result", {}):
                exc = result["result"]["exceptionDetails"]
                raise RuntimeError(f"JS error: {exc.get('text', str(exc))}")
            # Return type info if no value
            return inner.get("type", "unknown")
        except (KeyError, TypeError):
            return result

    def enable_runtime(self):
        self.send("Runtime.enable")
        self.send("Page.enable")
        self.send("DOM.enable")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


class StudioClient:
    """High-level client for TradeLocker Studio automation."""

    def __init__(self):
        self.cdp = CDPSession()
        self.cdp.enable_runtime()

    def get_page_info(self):
        """Get current page URL and title."""
        url = self.cdp.evaluate("window.location.href")
        title = self.cdp.evaluate("document.title")
        return {"url": url, "title": title}

    def is_studio_open(self):
        """Check if Studio page is loaded."""
        try:
            # Check URL pattern — more reliable than JS global
            url = self.cdp.evaluate("window.location.href")
            if url and 'studio' in str(url):
                return True
            # Fallback: check for monaco editor
            has_monaco = self.cdp.evaluate("window.monaco ? 1 : 0")
            return has_monaco == 1
        except Exception:
            return False

    def get_monaco_code(self):
        """Get current code from the Monaco editor."""
        return self.cdp.evaluate("""
            (() => {
                const editors = window.monaco && window.monaco.editor.getEditors();
                if (editors && editors.length > 0) {
                    return editors[0].getValue();
                }
                return null;
            })()
        """)

    def set_monaco_code(self, code: str):
        """Write code into the Monaco editor."""
        # Escape the code for JS string interpolation
        escaped = json.dumps(code)
        result = self.cdp.evaluate(f"""
            (() => {{
                const editors = window.monaco && window.monaco.editor.getEditors();
                if (!editors || editors.length === 0) {{
                    return {{ error: 'No Monaco editor found' }};
                }}
                const model = editors[0].getModel();
                if (!model) {{
                    return {{ error: 'No editor model found' }};
                }}
                model.setValue({escaped});
                return {{ success: true, length: model.getValue().length }};
            }})()
        """)
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(result["error"])
        return result

    def click_button(self, button_text: str):
        """Click a button by its text content (case-insensitive regex match)."""
        escaped_text = button_text.replace("'", "\\'").replace('"', '\\"')
        result = self.cdp.evaluate(f"""
            (() => {{
                // Check buttons
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {{
                    const text = btn.textContent.trim();
                    if (text.toLowerCase().includes('{escaped_text}')) {{
                        btn.click();
                        return {{ clicked: true, text: text, tag: 'button' }};
                    }}
                }}
                // Check other clickable elements (divs, spans with click handlers)
                const all = document.querySelectorAll('[role="button"], [onclick], .btn, [class*="button"], [class*="btn"]');
                for (const el of all) {{
                    const text = el.textContent.trim();
                    if (text.toLowerCase().includes('{escaped_text}') && text.length < 80) {{
                        el.click();
                        return {{ clicked: true, text: text, tag: el.tagName }};
                    }}
                }}
                return {{ clicked: false, error: 'Button not found: {escaped_text}' }};
            }})()
        """)
        return result

    def get_backtest_results(self):
        """Scrape backtest results from the DOM."""
        return self.cdp.evaluate("""
            (() => {
                // Try multiple selectors for results panel
                const selectors = [
                    '[data-testid="backtest-results"]',
                    '.backtest-results',
                    '.results-panel',
                    '.results-container',
                    '[class*="backtest"]',
                    '[class*="results"]',
                ];
                
                let panel = null;
                for (const sel of selectors) {
                    panel = document.querySelector(sel);
                    if (panel) break;
                }
                
                if (!panel) {
                    // Fallback: get all text from the right panel area
                    const rightPanel = document.querySelector('[class*="right"]') || 
                                       document.querySelector('[class*="panel"]');
                    if (rightPanel) {
                        return {
                            found: true,
                            method: 'fallback',
                            text: rightPanel.textContent.substring(0, 2000)
                        };
                    }
                    return { found: false, error: 'No results panel found' };
                }
                
                // Extract metrics
                const metrics = {};
                const metricEls = panel.querySelectorAll('[class*="metric"], [class*="stat"], [class*="value"]');
                metricEls.forEach(el => {
                    const label = el.querySelector('[class*="label"], [class*="name"]');
                    const value = el.querySelector('[class*="value"]');
                    if (label && value) {
                        metrics[label.textContent.trim()] = value.textContent.trim();
                    }
                });
                
                return {
                    found: true,
                    method: 'selector',
                    text: panel.textContent.substring(0, 2000),
                    metrics: metrics
                };
            })()
        """)

    def get_all_buttons(self):
        """List all visible buttons on the page."""
        return self.cdp.evaluate("""
            (() => {
                const buttons = document.querySelectorAll('button');
                return Array.from(buttons)
                    .map(b => b.textContent.trim())
                    .filter(t => t.length > 0 && t.length < 50);
            })()
        """)

    def get_page_text(self, max_length=2000):
        """Get visible text content of the page."""
        return self.cdp.evaluate(f"""
            (() => {{
                return document.body ? document.body.textContent.substring(0, {max_length}) : '';
            }})()
        """)

    def wait_for_results(self, timeout=120, poll_interval=5):
        """Wait for backtest results to appear."""
        print(f"  Waiting for backtest results (timeout: {timeout}s)...")
        elapsed = 0
        while elapsed < timeout:
            result = self.cdp.evaluate("""
                (() => {
                    const panel = document.querySelector('[class*="backtest"]') ||
                                   document.querySelector('[class*="results"]');
                    if (panel && panel.textContent.length > 50) {
                        return { ready: true };
                    }
                    return { ready: false };
                })()
            """)
            if isinstance(result, dict) and result.get("ready"):
                return True
            time.sleep(poll_interval)
            elapsed += poll_interval
            if elapsed % 15 == 0:
                print(f"  ... {elapsed}s elapsed")
        return False

    def close(self):
        self.cdp.close()


def cmd_write(args):
    """Write strategy code to Studio editor."""
    client = StudioClient()

    # Check Studio is open
    if not client.is_studio_open():
        print("ERROR: TradeLocker Studio is not open.")
        print("Open Studio in TradeLocker Desktop first.")
        sys.exit(1)

    # Read strategy file
    strategy_path = Path(args.file)
    if not strategy_path.exists():
        print(f"ERROR: Strategy file not found: {strategy_path}")
        sys.exit(1)

    code = strategy_path.read_text(encoding="utf-8")
    print(f"Strategy: {strategy_path.name} ({len(code)} chars)")

    # Write to editor
    print("Writing to Monaco editor...")
    result = client.set_monaco_code(code)
    print(f"  Result: {json.dumps(result, indent=2)}")

    # Verify
    written_code = client.get_monaco_code()
    if written_code and len(written_code) > 100:
        print(f"  ✓ Code written successfully ({len(written_code)} chars)")
    else:
        print("  ⚠ Verification failed — editor may be empty")

    client.close()


def cmd_backtest(args):
    """Click Backtest button and wait for results."""
    client = StudioClient()

    print("Looking for Backtest button...")
    buttons = client.get_all_buttons()
    print(f"  Available buttons: {buttons}")

    # Click the backtest/run button
    result = client.click_button("backtest")
    if isinstance(result, dict):
        if result.get("clicked"):
            print(f"  ✓ Clicked: '{result.get('text', 'backtest')}'")
        else:
            # Try alternative button names
            for alt in ["run", "start", "test", "Run Backtest", "Start Bot"]:
                result = client.click_button(alt)
                if isinstance(result, dict) and result.get("clicked"):
                    print(f"  ✓ Clicked: '{result.get('text', alt)}'")
                    break
            else:
                print("  ⚠ Could not find Backtest button")
                print("  Available buttons:", buttons)

    # Wait for results
    if client.wait_for_results(timeout=args.timeout):
        print("  ✓ Backtest completed!")
    else:
        print("  ⚠ Timeout waiting for results")

    client.close()


def cmd_results(args):
    """Read backtest results from Studio."""
    client = StudioClient()

    results = client.get_backtest_results()
    if isinstance(results, dict):
        if results.get("found"):
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print("No results found. Did the backtest complete?")
            print("Page text preview:")
            print(client.get_page_text(1000))
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    client.close()


def cmd_run(args):
    """Full pipeline: Write + Backtest + Results."""
    client = StudioClient()

    # 1. Check Studio
    if not client.is_studio_open():
        print("ERROR: TradeLocker Studio is not open.")
        sys.exit(1)

    # 2. Write strategy
    strategy_path = Path(args.file)
    if not strategy_path.exists():
        print(f"ERROR: Strategy file not found: {strategy_path}")
        sys.exit(1)

    code = strategy_path.read_text(encoding="utf-8")
    print(f"[1/3] Writing strategy: {strategy_path.name} ({len(code)} chars)")
    result = client.set_monaco_code(code)
    print(f"  Result: {json.dumps(result, indent=2)}")

    # 3. Click Backtest
    print("[2/3] Running backtest...")
    buttons = client.get_all_buttons()
    print(f"  Buttons: {buttons}")

    clicked = False
    for btn_name in ["backtest", "run", "start"]:
        result = client.click_button(btn_name)
        if isinstance(result, dict) and result.get("clicked"):
            print(f"  ✓ Clicked: '{result.get('text', btn_name)}'")
            clicked = True
            break

    if not clicked:
        print("  ⚠ Could not find Backtest button. Available:", buttons)
        client.close()
        sys.exit(1)

    # 4. Wait for results
    print(f"[3/3] Waiting for results (timeout: {args.timeout}s)...")
    if client.wait_for_results(timeout=args.timeout):
        print("  ✓ Backtest completed!")
        results = client.get_backtest_results()
        print("\n=== RESULTS ===")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("  ⚠ Timeout. Current page text:")
        print(client.get_page_text(1000))

    client.close()


def main():
    parser = argparse.ArgumentParser(
        description="TradeLocker Studio CLI — Automate strategy testing"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # write
    p_write = subparsers.add_parser("write", help="Write strategy to Studio editor")
    p_write.add_argument("--file", "-f", required=True, help="Strategy file path")

    # backtest
    p_bt = subparsers.add_parser("backtest", help="Click Backtest and wait")
    p_bt.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")

    # results
    subparsers.add_parser("results", help="Read backtest results")

    # run (full pipeline)
    p_run = subparsers.add_parser("run", help="Write + Backtest + Results")
    p_run.add_argument("--file", "-f", required=True, help="Strategy file path")
    p_run.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")

    args = parser.parse_args()

    if args.command == "write":
        cmd_write(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "results":
        cmd_results(args)
    elif args.command == "run":
        cmd_run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
