#!/usr/bin/env python3
"""
Test with correct data format for GitHub Actions
"""

import requests
import json
import time

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Correct format - using 'images' not 'url_images'
test_data = {
    "images": [
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1920&h=1080&fit=crop"
    ],
    "property_details": {
        "address": "789 Sunset Boulevard",
        "city": "Beverly Hills, CA 90210",
        "details1": "Call (310) 555-1234 for viewing",
        "details2": "Exclusive Listing",
        "agent_name": "Sarah Williams",
        "agent_email": "sarah@luxuryestates.com",
        "agent_phone": "(310) 555-1234",
        "brand_name": "Luxury Estates LA"
    },
    "settings": {
        "durationPerImage": 6,
        "effectSpeed": "medium",
        "transitionDuration": 1.5
    }
}

print("Testing with correct format...")
print(f"Property: {test_data['property_details']['address']}")
print(f"Images: {len(test_data['images'])}")
print("")

response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    job_id = result.get('job_id')
    print(f"[SUCCESS] Job created: {job_id}")
    
    # Check status after a delay
    print("\nWaiting for GitHub Actions to trigger...")
    time.sleep(10)
    
    status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
    
    if status_resp.status_code == 200:
        status = status_resp.json()
        print(f"\nStatus: {status.get('status')}")
        print(f"Progress: {status.get('progress')}%")
        print(f"Step: {status.get('current_step')}")
        print(f"GitHub Job ID: {status.get('github_job_id')}")
        
        if status.get('github_job_id'):
            cloud_name = "dib3kbifc"
            video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{status['github_job_id']}.mp4"
            print(f"\nExpected video URL: {video_url}")
            print("\nCheck GitHub Actions at:")
            print("https://github.com/bac1876/listinghelper/actions")
        else:
            print("\n[WARNING] No GitHub job ID - GitHub Actions may not be configured")
    else:
        print(f"Status check failed: {status_resp.status_code}")
else:
    print(f"[ERROR] Job creation failed: {response.status_code}")
    print(response.text)