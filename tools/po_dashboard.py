"""
Serve the PO Tracker static dashboard.
Run: python tools/po_dashboard.py
"""
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
from pathlib import Path
import urllib.request
import urllib.error
import json

HOST = '127.0.0.1'
PORT = 8770
ROOT = Path(__file__).parent / 'po_dashboard'
os.chdir(str(ROOT))

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # allow local fetches to talk to po_api
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        # Proxy API requests to local PO API to avoid CORS in browser
        if self.path.startswith('/api/'):
            target = 'http://127.0.0.1:8765' + self.path[len('/api'):]
            try:
                with urllib.request.urlopen(target, timeout=5) as r:
                    data = r.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                err = {'error': str(e)}
                body = json.dumps(err).encode('utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'application/json')
                err = {'error': str(e)}
                body = json.dumps(err).encode('utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return

        # Proxy SSE stream from po_sse server
        if self.path == '/stream':
            try:
                req = urllib.request.Request('http://127.0.0.1:8780/stream')
                with urllib.request.urlopen(req, timeout=30) as r:
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self.end_headers()
                    # Stream chunks
                    while True:
                        chunk = r.read(4096)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
            except Exception as e:
                self.send_response(502)
                self.send_header('Content-Type', 'text/plain')
                msg = f'SSE proxy error: {e}'.encode('utf-8')
                self.send_header('Content-Length', str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
            return

        return super().do_GET()

if __name__ == '__main__':
    print(f"Serving PO Tracker from http://{HOST}:{PORT}/index.html")
    server = HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
