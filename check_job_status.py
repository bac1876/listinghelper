#!/usr/bin/env python3
"""
Check job status from Railway app
"""

import requests

# Job ID from the test
job_id = "909fcbc3-6970-4211-83b3-979bc28ccc27"

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

print(f"Checking job status for: {job_id}\n")

try:
    response = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Progress: {data.get('progress')}%")
        print(f"Current step: {data.get('current_step')}")
        
        if data.get('video_url'):
            print(f"\n[SUCCESS] Video available at:")
            print(data['video_url'])
            
        if data.get('error'):
            print(f"\nError: {data['error']}")
            
    else:
        print(f"Status check failed: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")