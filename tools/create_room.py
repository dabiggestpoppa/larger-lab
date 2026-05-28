"""Create Observer Core team room in OCE command center."""
import requests
import json

# Create team room
r = requests.post('http://localhost:8000/command-center/rooms', json={
    "name": "Observer Core Team",
    "description": "Coordination room for O-1 through O-7 development. CC, PM1, AS, RL, OC2.",
    "agent_ids": ["hermes", "oc2", "pm1", "as", "rl"],
    "persistent": True
})
print('Room creation:', r.status_code)
if r.status_code == 200:
    room = r.json()
    print(f'Room ID: {room.get("room_id", "N/A")}')
    print(f'Room name: {room.get("name", "N/A")}')
else:
    print(r.text)

# List all rooms
r = requests.get('http://localhost:8000/command-center/rooms')
print('\nAll rooms:')
for key, room in r.json()['rooms'].items():
    print(f'  {key}: {room["name"]} ({len(room.get("agent_ids", []))} agents)')
