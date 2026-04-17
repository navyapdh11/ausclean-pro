#!/usr/bin/env python3
"""Provision Grafana dashboards for AusClean Pro."""
import requests
import os
import json
import sys

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
API_KEY = os.getenv("GRAFANA_API_KEY", "ausclean2026")

DASHBOARD_FILE = os.path.join(os.path.dirname(__file__), "grafana/dashboards/ausclean.json")

def provision():
    if not os.path.exists(DASHBOARD_FILE):
        print(f"Dashboard file not found: {DASHBOARD_FILE}")
        sys.exit(1)
    
    with open(DASHBOARD_FILE) as f:
        dashboard_config = json.load(f)
    
    url = f"{GRAFANA_URL}/api/dashboards/db"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        resp = requests.post(url, json=dashboard_config, headers=headers)
        if resp.status_code in (200, 201):
            result = resp.json()
            print(f"✅ Dashboard provisioned: {result.get('slug', 'ausclean-pro')}")
            print(f"   URL: {GRAFANA_URL}/d/{result.get('uid', '')}")
        else:
            print(f"❌ Failed to provision dashboard: {resp.status_code}")
            print(resp.text)
            sys.exit(1)
    except requests.ConnectionError:
        print(f"❌ Cannot connect to Grafana at {GRAFANA_URL}")
        print("   Is Grafana running? docker compose up -d grafana")
        sys.exit(1)

if __name__ == "__main__":
    provision()
