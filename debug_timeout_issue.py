#!/usr/bin/env python3
"""
Debug the timeout issue - check what's happening with jobs
"""

import requests
import json

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

print("Debugging timeout issue...")
print("\nLet's check a recent job status manually.")
print("Please provide a job ID from your recent attempt, or press Enter to create a test job:")

job_id = input("Job ID (or Enter for new test): ").strip()

if not job_id:
    # Create a simple test job
    print("\nCreating a test job with minimal images...")
    test_data = {
        "images": [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop"
        ],
        "property_details": {
            "address": "Debug Test Property",
            "agent_name": "Debug Agent",
            "agent_phone": "(555) 111-2222"
        },
        "settings": {
            "durationPerImage": 3,
            "effectSpeed": "fast"
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
        print(f"Initial response: {json.dumps(result, indent=2)}")
    else:
        print(f"Error creating job: {response.status_code}")
        print(response.text)
        exit(1)

# Check job status
print(f"\nChecking status for job: {job_id}")
status_url = f"{app_url}/api/virtual-tour/job/{job_id}/status"

response = requests.get(status_url)

if response.status_code == 200:
    status = response.json()
    print("\nJob Status:")
    print(f"- Status: {status.get('status')}")
    print(f"- Progress: {status.get('progress')}%")
    print(f"- Current Step: {status.get('current_step')}")
    print(f"- GitHub Job ID: {status.get('github_job_id')}")
    print(f"- Video Available: {status.get('video_available')}")
    print(f"- Error: {status.get('error')}")
    
    if status.get('github_job_id'):
        print(f"\n✅ GitHub Actions was triggered: {status.get('github_job_id')}")
        print("Check: https://github.com/bac1876/listinghelper/actions")
    else:
        print("\n❌ No GitHub job ID - GitHub Actions may not have been triggered")
        
    # Try to check environment
    print("\n\nChecking if GitHub Actions is properly configured...")
    print("The app should have these environment variables:")
    print("- USE_GITHUB_ACTIONS=true")
    print("- GITHUB_TOKEN")
    print("- GITHUB_OWNER")
    print("- GITHUB_REPO")
    
elif response.status_code == 404:
    print(f"\n❌ Job not found: {job_id}")
else:
    print(f"\nError checking status: {response.status_code}")
    print(response.text)