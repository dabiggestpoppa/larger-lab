"""Add WebSocket endpoint to main.py"""
import pathlib

f = pathlib.Path(r"c:\Users\wifik\Desktop\projects\larger-lab\oce\backend\main.py")
content = f.read_text(encoding="utf-8")

# Add WebSocket import
old_imp = "from .adaptive_compression import get_adaptive_compression, AdaptiveCompression"
new_imp = "from .adaptive_compression import get_adaptive_compression, AdaptiveCompression\nfrom fastapi import WebSocket, WebSocketDisconnect"
content = content.replace(old_imp, new_imp, 1)

# Add WebSocket endpoint after CORS
old_cors = ")\n\n\n@app.exception_handler(Exception)"
new_cors = """)\n\n\n# --- WebSocket Endpoint ---\n\n@app.websocket(\"/ws/observers\")\nasync def websocket_observers(websocket: WebSocket):\n    \"\"\"WebSocket endpoint for OC2 gateway and observer streaming.\"\"\"\n    await websocket.accept()\n    try:\n        while True:\n            data = await websocket.receive_text()\n            await websocket.send_text(json.dumps({\"type\": \"ack\", \"data\": data}))\n    except WebSocketDisconnect:\n        logger.info(\"WebSocket client disconnected\")\n    except Exception as e:\n        logger.error(f\"WebSocket error: {e}\")\n\n\n@app.exception_handler(Exception)"""
content = content.replace(old_cors, new_cors, 1)

f.write_text(content, encoding="utf-8")
print("Added WebSocket endpoint to main.py")
