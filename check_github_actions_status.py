#!/usr/bin/env python3
"""
Check if GitHub Actions is being triggered properly
"""

import requests
import json
import time

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

print("Testing GitHub Actions trigger...")

# Create a minimal test job
test_data = {
    "images": [
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop"
    ],
    "property_details": {
        "address": "Test Property",
        "agent_name": "Test Agent",
        "agent_phone": "(555) 111-2222"
    },
    "settings": {
        "durationPerImage": 3,
        "effectSpeed": "fast"
    }
}

print("\nCreating test job...")
response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
job_id = result.get('job_id')
print(f"Job created: {job_id}")

# Check status multiple times
for i in range(5):
    time.sleep(3)
    print(f"\nChecking status (attempt {i+1}/5)...")
    
    status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
    
    if status_resp.status_code == 200:
        status = status_resp.json()
        print(f"Status: {status.get('status')}")
        print(f"Progress: {status.get('progress')}%")
        print(f"Step: {status.get('current_step')}")
        print(f"GitHub Job: {status.get('github_job_id')}")
        
        if status.get('github_job_id'):
            print("\n✅ GitHub Actions triggered successfully!")
            print(f"Job ID: {status.get('github_job_id')}")
            print("\nThe timeout issue may be due to:")
            print("1. GitHub Actions taking longer than 10 minutes")
            print("2. Webhook not updating status properly")
            print("3. GitHub Actions workflow failing")
            print("\nCheck workflow at:")
            print("https://github.com/bac1876/listinghelper/actions")
            break
    else:
        print(f"Error: {status_resp.status_code}")

# Final check
if not status.get('github_job_id'):
    print("\n❌ GitHub Actions NOT triggered!")
    print("\nPossible issues:")
    print("1. USE_GITHUB_ACTIONS not set to 'true' in Railway")
    print("2. GitHub credentials missing or invalid")
    print("3. github_actions object not initialized")
    
# Check if we can see the health endpoint
print("\n\nChecking app health...")
health_resp = requests.get(f"{app_url}/health")
if health_resp.status_code == 200:
    print("✅ App is running")
else:
    print("❌ App health check failed")