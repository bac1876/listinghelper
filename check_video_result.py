#!/usr/bin/env python3
"""
Check the status of a GitHub Actions video render job
"""

import requests
import json
import sys

def check_job_status(job_id):
    """Check the status of a video render job"""
    
    app_url = "https://virtual-tour-generator-production.up.railway.app"
    
    print(f"🔍 Checking status for job: {job_id}")
    
    # Check GitHub job status
    response = requests.get(f"{app_url}/api/virtual-tour/check-github-job/{job_id}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            print(f"\n✅ Job Status: {result.get('status')}")
            
            if result.get('video_url'):
                print(f"\n🎬 Video URL: {result['video_url']}")
                print(f"\nYou can view/download the video at the URL above!")
                print(f"Duration: {result.get('duration')} seconds")
                print(f"Rendered at: {result.get('timestamp')}")
            else:
                print("\n⏳ Video is still being processed...")
                print("Try again in a minute.")
        else:
            print(f"\n❌ Error: {result.get('error')}")
    else:
        print(f"\n❌ Failed to check status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Use the job ID from the last test
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
    else:
        # Use the most recent job ID
        job_id = "tour_1754086678_19d094f3"
    
    check_job_status(job_id)