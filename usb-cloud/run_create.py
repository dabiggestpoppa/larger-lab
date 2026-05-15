import requests
import json

API_KEY = "84908b7a4714aacd25c51715e0efe96e"
API_SECRET = "9cd519e13f62ef5522736cb103328ba8"

url = "https://cloudapi.kamatera.com/v1/server"
payload = {
    "name": "larger-lab-agent",
    "datacenter": "US-NY2",
    "image": "Ubuntu 24.04",
    "cpu": "2B",
    "ram": 4096,
    "disk": [{"size": 50}],
    "network": [{"name": "wan", "ip": "auto"}],
    "password": "TempPass123!"
}

print("Creating server...")
r = requests.post(url, json=payload, auth=(API_KEY, API_SECRET), timeout=120)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")