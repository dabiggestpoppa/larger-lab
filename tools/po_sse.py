"""
PO SSE Server — Server-Sent Events push for live PO events.

Run: python tools/po_sse.py
Exposes: GET /stream (EventSource clients)
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn
from threading import Thread, Lock
from queue import Queue, Empty
import time
import json
import sys
from pathlib import Path
# ensure repo root on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from core.observer import observer_persistence
from pathlib import Path

HOST = '127.0.0.1'
PORT = 8780

clients = []
clients_lock = Lock()

def format_sse(data: str, event: str | None = None) -> bytes:
    lines = []
    if event:
        lines.append(f"event: {event}")
    for l in data.splitlines():
        lines.append(f"data: {l}")
    lines.append("")
    return ("\n".join(lines) + "\n").encode('utf-8')

class SSEHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/stream':
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        q = Queue()
        with clients_lock:
            clients.append(q)

        try:
            # Keep connection open and flush when there is data
            while True:
                try:
                    msg = q.get(timeout=15)
                    self.wfile.write(msg)
                    self.wfile.flush()
                except Empty:
                    # heartbeat to keep connection alive
                    try:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                    except Exception:
                        break
        except Exception:
            pass
        finally:
            with clients_lock:
                try:
                    clients.remove(q)
                except ValueError:
                    pass

def broadcaster(poll_interval=2):
    last_id = 0
    while True:
        try:
            rows = observer_persistence.query_recent_events(200)
            # rows are (id, event_type, source, timestamp, data)
            # they are returned newest-first
            new = [r for r in reversed(rows) if r[0] > last_id]
            for r in new:
                eid, event_type, source, ts, data = r
                payload = json.dumps({
                    'id': eid,
                    'type': event_type,
                    'source': source,
                    'timestamp': ts,
                    'data': json.loads(data or '{}')
                })
                msg = format_sse(payload, event='po_event')
                with clients_lock:
                    for q in list(clients):
                        try:
                            q.put_nowait(msg)
                        except Exception:
                            pass
                last_id = eid
            time.sleep(poll_interval)
        except Exception:
            time.sleep(poll_interval)

def run():
    t = Thread(target=broadcaster, daemon=True)
    t.start()
    server = ThreadingHTTPServer((HOST, PORT), SSEHandler)
    print(f'PO SSE server running at http://{HOST}:{PORT}/stream')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    run()
