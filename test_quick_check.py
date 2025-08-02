#!/usr/bin/env python3
"""
Quick test to check GitHub Actions integration
"""

import requests
import json
import time

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Simple test with 3 images
test_data = {
    "url_images": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1920&h=1080&fit=crop"
    ],
    "address": "Quick Test Property",
    "agent_name": "Test Agent",
    "quality": "medium",
    "use_github_actions": True
}

print("Submitting quick test job...")
response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    job_id = result.get('job_id')
    print(f"Job created: {job_id}")
    
    # Immediate status check
    print("\nChecking status immediately...")
    status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
    
    if status_resp.status_code == 200:
        status = status_resp.json()
        print(json.dumps(status, indent=2))
        
        # Wait and check again
        print("\nWaiting 15 seconds...")
        time.sleep(15)
        
        status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
        if status_resp.status_code == 200:
            status = status_resp.json()
            print("\nStatus after waiting:")
            print(json.dumps(status, indent=2))
            
            if status.get('github_job_id'):
                print(f"\nGitHub job ID found: {status['github_job_id']}")
                cloud_name = "dib3kbifc"
                video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{status['github_job_id']}.mp4"
                print(f"Expected video URL: {video_url}")
    else:
        print(f"Status check failed: {status_resp.status_code}")
else:
    print(f"Job creation failed: {response.status_code}")
    print(response.text)