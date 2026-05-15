#!/usr/bin/env python3
"""Provision Kamatera server via API"""
import requests
import json
import sys

API_KEY = "84908b7a4714aacd25c51715e0efe96e"
API_SECRET = "9cd519e13f62ef5522736cb103328ba8"

def create_server():
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
    
    print(f"Creating server: {payload['name']}")
    print(f"Datacenter: {payload['datacenter']}")
    print(f"Image: {payload['image']}")
    print(f"CPU: {payload['cpu']}, RAM: {payload['ram']}MB")
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=(API_KEY, API_SECRET),
            timeout=120
        )
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nServer created successfully!")
            print(f"Server ID: {data.get('id', 'N/A')}")
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def list_servers():
    url = "https://cloudapi.kamatera.com/v1/server"
    
    try:
        response = requests.get(
            url,
            auth=(API_KEY, API_SECRET),
            timeout=60
        )
        print(f"Status: {response.status_code}")
        print(f"Servers: {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_servers()
    else:
        create_server()