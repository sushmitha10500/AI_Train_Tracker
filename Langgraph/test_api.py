import requests

BASE = "https://railradar.in/api/v1"

def call_railradar(endpoint, params=None):
    url = f"{BASE}{endpoint}"
    try:
        res = requests.get(url, params=params, timeout=15)
        print(f"URL: {res.url}")
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:200]}")
        return res.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

print("Checking NDLS to NDLS:")
call_railradar("/trains/between", params={"from": "NDLS", "to": "NDLS"})

print("\nChecking NDLS to BCT:")
call_railradar("/trains/between", params={"from": "NDLS", "to": "BCT"})
