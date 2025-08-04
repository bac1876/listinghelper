#!/usr/bin/env python3
"""
Test uploading multiple images to see if all are processed
"""

import requests
import json
import time

# Test with 5 images
test_images = [
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1920&h=1080",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1920&h=1080", 
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1920&h=1080",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1920&h=1080",
    "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=1920&h=1080"
]

print(f"Testing with {len(test_images)} images...")

# Submit job
response = requests.post(
    "https://virtual-tour-generator-production.up.railway.app/api/virtual-tour/upload",
    json={
        "images": test_images,
        "property_details": {
            "address": "Multi-Image Test Property",
            "city": "Test City, CA 90210",
            "agent_name": "Test Agent",
            "agent_phone": "(555) 123-4567"
        },
        "settings": {
            "durationPerImage": 3,
            "effectSpeed": "fast"
        }
    }
)

if response.status_code == 200:
    result = response.json()
    job_id = result['job_id']
    print(f"Job created: {job_id}")
    print(f"GitHub job: {result.get('github_job_id')}")
    
    # Wait and check status
    print("\nWaiting for processing...")
    time.sleep(30)
    
    # Check status
    status_resp = requests.get(
        f"https://virtual-tour-generator-production.up.railway.app/api/virtual-tour/job/{job_id}/status"
    )
    
    if status_resp.status_code == 200:
        status = status_resp.json()
        print(f"\nJob Status: {status.get('status')}")
        print(f"Progress: {status.get('progress')}%")
        print(f"GitHub Job ID: {status.get('github_job_id')}")
        
        # If completed, show video URL
        if status.get('video_url'):
            print(f"\nVideo URL: {status['video_url']}")
            
            # Check video header to see duration
            video_resp = requests.head(status['video_url'])
            if video_resp.status_code == 200:
                content_length = int(video_resp.headers.get('Content-Length', 0))
                print(f"Video size: {content_length / 1024 / 1024:.2f} MB")
                
                # Download a small part to check
                partial_resp = requests.get(status['video_url'], headers={'Range': 'bytes=0-1000'})
                if partial_resp.status_code == 206:
                    print("Video is accessible and streamable")
else:
    print(f"Error: {response.status_code}")
    print(response.text)