#!/usr/bin/env python3
"""
Recover a job that timed out in the UI
"""

import requests
import sys

if len(sys.argv) < 2:
    print("Usage: python recover_timed_out_job.py <job_id>")
    print("\nThis script helps recover jobs that timed out in the UI")
    print("but may have completed in GitHub Actions.")
    sys.exit(1)

job_id = sys.argv[1]
app_url = "https://virtual-tour-generator-production.up.railway.app"

print(f"Checking job: {job_id}")

# Check status
status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")

if status_resp.status_code == 200:
    status = status_resp.json()
    print(f"\nJob Status: {status.get('status')}")
    print(f"Progress: {status.get('progress')}%")
    print(f"GitHub Job ID: {status.get('github_job_id')}")
    
    if status.get('github_job_id'):
        github_job_id = status['github_job_id']
        video_url = f"https://res.cloudinary.com/dib3kbifc/video/upload/tours/{github_job_id}.mp4"
        
        print(f"\nChecking if video exists...")
        video_resp = requests.head(video_url)
        
        if video_resp.status_code == 200:
            print(f"\nSUCCESS! Your video is ready:")
            print(video_url)
            print(f"\nFile size: {int(video_resp.headers.get('Content-Length', 0)) / 1024 / 1024:.1f} MB")
            print("\nYou can download it directly from the URL above.")
        else:
            print(f"\nVideo not found (status: {video_resp.status_code})")
            print("The rendering may have failed or is still in progress.")
            print("\nCheck GitHub Actions:")
            print("https://github.com/bac1876/listinghelper/actions")
    else:
        print("\nNo GitHub job ID found.")
        print("The job may not have triggered GitHub Actions.")
else:
    print(f"Job not found: {status_resp.status_code}")