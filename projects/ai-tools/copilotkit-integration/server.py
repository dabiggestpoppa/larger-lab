"""
FastAPI server for Hermes Agent State
Provides REST API for the dashboard to fetch agent state
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import datetime
from pathlib import Path
import json
from dataclasses import dataclass, asdict

STATE_FILE = Path(__file__).parent / "agent_state.json"

app = FastAPI(title="Hermes Agent API", version="1.0.0")

# Enable CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_state() -> dict:
    """Load state from JSON file"""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {
        "hermes_status": "idle",
        "hermes_iteration": 0,
        "hermes_profitable_strategies": 0,
        "hermes_target_strategies": 5,
        "openclaw_status": "idle",
        "openclaw_task": "",
        "openclaw_progress": "",
        "last_updated": datetime.now().isoformat(),
        "active_pair": "EURUSD",
        "backtest_results": []
    }


@app.get("/")
async def root():
    return {"message": "Hermes Agent API", "status": "running"}


@app.get("/dashboard", response_class="HTMLResponse")
async def dashboard_html():
    """Dashboard HTML page"""
    state = load_state()
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Hermes Agent Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ background: #16213e; padding: 20px; margin: 10px 0; border-radius: 8px; }}
        .status {{ color: #4ade80; }}
        .chat-box {{ height: 400px; overflow-y: auto; background: #0f0f23; padding: 10px; border-radius: 4px; }}
        .message {{ margin: 10px 0; }}
        .user {{ color: #60a5fa; }}
        .agent {{ color: #4ade80; }}
        input {{ width: 80%; padding: 10px; background: #16213e; color: #fff; border: 1px solid #333; border-radius: 4px; }}
        button {{ padding: 10px 20px; background: #4ade80; color: #000; border: none; border-radius: 4px; cursor: pointer; }}
        .strategy {{ display: inline-block; background: #4ade80; color: #000; padding: 5px 10px; margin: 5px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Hermes Agent Dashboard</h1>
        
        <div class="card">
            <h2>Hermes Status</h2>
            <p><strong>Status:</strong> <span class="status">{state.get('hermes_status', 'idle')}</span></p>
            <p><strong>Iteration:</strong> {state.get('hermes_iteration', 0)}</p>
            <p><strong>Profitable Strategies:</strong> {state.get('hermes_profitable_strategies', 0)}/{state.get('hermes_target_strategies', 5)}</p>
            <p><strong>Active Pair:</strong> {state.get('active_pair', 'EURUSD')}</p>
        </div>
        
        <div class="card">
            <h2>Backtest Results</h2>
            {''.join([f'<span class="strategy">{r["strategy"]}: {r["return_pct"]}%</span>' for r in state.get('backtest_results', [])])}
        </div>
        
        <div class="card">
            <h2>Chat with Hermes</h2>
            <div class="chat-box" id="chatBox">
                <div class="message agent">Hermes: Hello! I'm running and ready to chat. How can I help you?</div>
            </div>
            <div style="margin-top: 10px;">
                <input type="text" id="messageInput" placeholder="Type a message..." onkeypress="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        async function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value;
            if (!message) return;
            
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += '<div class="message user">You: ' + message + '</div>';
            input.value = '';
            
            // Call API
            const response = await fetch('/api/chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{message: message}})
            }});
            const data = await response.json();
            chatBox.innerHTML += '<div class="message agent">Hermes: ' + data.response + '</div>';
            chatBox.scrollTop = chatBox.scrollHeight;
        }}
    </script>
</body>
</html>
"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@app.get("/dashboard")
async def dashboard():
    """Dashboard endpoint"""
    state = load_state()
    return {
        "hermes": {
            "status": state.get("hermes_status", "idle"),
            "iteration": state.get("hermes_iteration", 0),
            "profitable_strategies": state.get("hermes_profitable_strategies", 0),
            "target_strategies": state.get("hermes_target_strategies", 5)
        },
        "openclaw": {
            "status": state.get("openclaw_status", "idle"),
            "task": state.get("openclaw_task", ""),
            "progress": state.get("openclaw_progress", "")
        },
        "last_updated": state.get("last_updated", ""),
        "active_pair": state.get("active_pair", "EURUSD"),
        "backtest_results": state.get("backtest_results", [])
    }


@app.get("/api/state")
async def get_state():
    """Get current agent state"""
    return load_state()


@app.get("/api/hermes")
async def get_hermes_state():
    """Get Hermes agent state"""
    state = load_state()
    return {
        "status": state.get("hermes_status", "idle"),
        "iteration": state.get("hermes_iteration", 0),
        "profitable_strategies": state.get("hermes_profitable_strategies", 0),
        "target_strategies": state.get("hermes_target_strategies", 5),
        "last_updated": state.get("last_updated", "")
    }


@app.get("/api/openclaw")
async def get_openclaw_state():
    """Get OpenClaw agent state"""
    state = load_state()
    return {
        "status": state.get("openclaw_status", "idle"),
        "task": state.get("openclaw_task", ""),
        "progress": state.get("openclaw_progress", "")
    }


# Dashboard API endpoints
@app.get("/api/sessions")
async def get_sessions():
    """Get sessions list"""
    return []


@app.get("/api/sessions")
async def get_sessions_with_params(limit: int = 200, offset: int = 0):
    """Get sessions list with pagination"""
    return []


@app.get("/api/dashboard/overview")
async def get_dashboard_overview(days: int = 30, achievements: int = 5):
    """Get dashboard overview"""
    state = load_state()
    return {
        "hermes": {
            "status": state.get("hermes_status", "idle"),
            "iteration": state.get("hermes_iteration", 0),
            "profitable_strategies": state.get("hermes_profitable_strategies", 0)
        },
        "openclaw": {
            "status": state.get("openclaw_status", "idle"),
            "task": state.get("openclaw_task", ""),
            "progress": state.get("openclaw_progress", "")
        }
    }


@app.get("/api/connection-status")
async def get_connection_status():
    """Get connection status"""
    return {"connected": True, "status": "running"}


@app.get("/api/gateway-status")
async def get_gateway_status():
    """Get gateway status"""
    return {"status": "running", "port": 18789}


@app.get("/api/claude-proxy/health")
async def get_claude_proxy_health():
    """Get claude proxy health"""
    return {"status": "healthy"}


@app.get("/api/session-status")
async def get_session_status(sessionKey: str = "main"):
    """Get session status"""
    return {"status": "active", "sessionKey": sessionKey}


@app.get("/api/provider-usage")
async def get_provider_usage():
    """Get provider usage"""
    return {"providers": []}


@app.post("/api/hermes/update")
async def update_hermes(status: str = None, iteration: int = None, profitable_strategies: int = None):
    """Update Hermes state"""
    state = load_state()
    if status is not None:
        state["hermes_status"] = status
    if iteration is not None:
        state["hermes_iteration"] = iteration
    if profitable_strategies is not None:
        state["hermes_profitable_strategies"] = profitable_strategies
    state["last_updated"] = datetime.now().isoformat()
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    return {"message": "State updated", "state": state}


@app.post("/api/chat")
async def chat(request: Request):
    """Chat with Hermes agent"""
    body = await request.json()
    message = body.get("message", "")
    # Simple echo response for now
    return {"response": f"Received: {message}. Hermes is running and processing your request."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)