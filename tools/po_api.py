"""
PO API — lightweight HTTP interface to query observer actions DB.

Endpoints:
  GET /events?limit=100  -> recent events
  GET /chat?limit=100    -> recent chat messages
  GET /state?limit=100   -> recent state changes

Run: python tools/po_api.py
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path so 'core' package imports work
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from core.observer import observer_persistence

HOST = '127.0.0.1'
PORT = 8765

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        data = json.dumps(obj, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        # Allow cross-origin requests from local dashboard
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        q = urlparse.parse_qs(parsed.query)
        limit = int(q.get('limit', ['100'])[0])

        if parsed.path == '/events':
            rows = observer_persistence.query_recent_events(limit)
            out = [dict(id=r[0], event_type=r[1], source=r[2], timestamp=r[3], data=json.loads(r[4] or '{}')) for r in rows]
            self._send_json(out)
            return

        if parsed.path == '/chat':
            # simple query via sqlite
            conn = observer_persistence._get_conn()
            cur = conn.cursor()
            cur.execute('SELECT id, timestamp, source, message, raw FROM chat_messages ORDER BY id DESC LIMIT ?', (limit,))
            rows = cur.fetchall()
            conn.close()
            out = [dict(id=r[0], timestamp=r[1], source=r[2], message=r[3], raw=json.loads(r[4] or '{}')) for r in rows]
            self._send_json(out)
            return

        if parsed.path == '/state':
            conn = observer_persistence._get_conn()
            cur = conn.cursor()
            cur.execute('SELECT id, key, old_value, new_value, timestamp FROM state_changes ORDER BY id DESC LIMIT ?', (limit,))
            rows = cur.fetchall()
            conn.close()
            out = [dict(id=r[0], key=r[1], old=json.loads(r[2] or 'null') if r[2] else None, new=json.loads(r[3] or 'null') if r[3] else None, timestamp=r[4]) for r in rows]
            self._send_json(out)
            return

        self._send_json({'error': 'unknown endpoint'}, status=404)

def run():
    server = HTTPServer((HOST, PORT), Handler)
    print(f'PO API running on http://{HOST}:{PORT} (endpoints: /events,/chat,/state)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    run()
