#!/usr/bin/env python3
"""
Test file upload with the fixed field name
"""

import requests
import time
import os

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Create test image files (you'll need to use actual image files)
print("Testing file upload fix...")
print("\nNOTE: This test requires actual image files.")
print("Please ensure you have image files to upload through the web interface.\n")

# Instructions for testing
print("To test the fix:")
print("1. Open the web interface: " + app_url)
print("2. Upload 3-4 image files")
print("3. Fill in required fields (address, agent name, phone)")
print("4. Click 'Generate Virtual Tour'")
print("5. Wait for processing (should show GitHub Actions progress)")
print("6. When complete, try downloading the video")
print("\nThe fix ensures:")
print("- Files are properly received by the backend")
print("- GitHub Actions is triggered for rendering")
print("- Job stays in 'processing' state until video is ready")
print("- Download returns proper error if video isn't ready yet")
print("\nExpected behavior:")
print("- Progress should go to 75% and wait for GitHub Actions")
print("- Total time should be 1-2 minutes (not 30 seconds)")
print("- Download should give you an MP4 file, not JSON")

# Alternative: Test via API
print("\n" + "="*50)
print("Alternative: Test via API with URL images")
print("="*50)

test_data = {
    "images": [
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800",
        "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=800",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=800"
    ],
    "property_details": {
        "address": "Test Fix Property",
        "agent_name": "Test Agent",
        "agent_phone": "(555) 000-0000"
    },
    "settings": {
        "durationPerImage": 4,
        "effectSpeed": "medium"
    }
}

response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    job_id = result.get('job_id')
    print(f"\nTest job created: {job_id}")
    print("Status should be 'processing' not 'completed'")
    print(f"GitHub job ID: {result.get('github_job_id')}")
    
    # Check status
    time.sleep(5)
    status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
    if status_resp.status_code == 200:
        status = status_resp.json()
        print(f"\nJob status: {status.get('status')}")
        print(f"Progress: {status.get('progress')}%")
        print(f"Current step: {status.get('current_step')}")
        
        if status.get('status') == 'processing' and status.get('github_job_id'):
            print("\n✅ Fix confirmed working! Job is waiting for GitHub Actions.")
        elif status.get('status') == 'completed' and not status.get('github_job_id'):
            print("\n❌ Issue persists - job completed without GitHub Actions")
else:
    print(f"Error: {response.status_code}")
    print(response.text)