#!/usr/bin/env python3
"""
html_viewer.py — HTML Viewer for Agent Memory

Serves the converted HTML files via a local HTTP server and opens in browser.
Provides a visual interface for agents to browse workspace documentation.

Usage:
    python tools/html_viewer.py                  # Serve + open browser
    python tools/html_viewer.py --port 8080      # Custom port
    python tools/html_viewer.py --rebuild        # Rebuild HTML then serve
    python tools/html_viewer.py --no-browser     # Serve only, don't open browser
"""

import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
HTML_DIR = WORKSPACE / "html-viewer"


def rebuild():
    """Rebuild all HTML files."""
    print("[REBUILD] Converting markdown to html...")
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "tools" / "md_to_html.py"), "--all"],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr[:500]}")
        return False
    return True


def serve(port=8080, open_browser=True):
    """Start HTTP server and open browser."""
    if not HTML_DIR.exists():
        print(f"[ERROR] HTML directory not found: {HTML_DIR}")
        print("[INFO] Run with --rebuild first")
        return False

    os.chdir(HTML_DIR)

    handler = SimpleHTTPRequestHandler
    server = HTTPServer(("127.0.0.1", port), handler)

    url = f"http://127.0.0.1:{port}/index.html"
    print(f"\n🌐 HTML Viewer running at {url}")
    print(f"   Serving: {HTML_DIR}")
    print(f"   Press Ctrl+C to stop\n")

    if open_browser:
        # Open browser after a short delay
        def _open():
            time.sleep(0.5)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped")
        server.shutdown()

    return True


def main():
    parser = argparse.ArgumentParser(description="HTML Viewer for Agent Memory")
    parser.add_argument("--port", type=int, default=8080, help="Server port (default: 8080)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild HTML before serving")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")

    args = parser.parse_args()

    if args.rebuild:
        if not rebuild():
            sys.exit(1)

    serve(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
