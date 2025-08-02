#!/usr/bin/env python3
"""
Test if GitHub Actions is properly configured
"""

import requests
import json

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Try to check configuration (if endpoint exists)
print("Checking app configuration...")

# Try various endpoints that might give us info
endpoints = [
    "/api/virtual-tour/config",
    "/api/virtual-tour/status", 
    "/api/virtual-tour/info",
    "/config",
    "/status"
]

for endpoint in endpoints:
    try:
        response = requests.get(f"{app_url}{endpoint}", timeout=3)
        if response.status_code == 200:
            print(f"\nFound endpoint: {endpoint}")
            print(json.dumps(response.json(), indent=2))
    except:
        pass

# Test with explicit GitHub Actions flag
print("\n\nTesting with explicit GitHub Actions request...")
test_data = {
    "url_images": ["https://via.placeholder.com/150"],
    "use_github_actions": True,
    "test_mode": True
}

response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)