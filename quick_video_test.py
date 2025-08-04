#!/usr/bin/env python3
"""
Quick test to generate and download a video
"""

import requests
import time
import os
from datetime import datetime

app_url = "https://virtual-tour-generator-production.up.railway.app"

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting quick video test")

# Test with just 2 images for speed
test_data = {
    "images": [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1280&h=720&fit=crop"
    ],
    "property_details": {
        "address": "123 Test Drive",
        "agent_name": "Quick Test",
        "agent_phone": "(555) 000-1111"
    },
    "settings": {
        "durationPerImage": 3,
        "effectSpeed": "fast"
    }
}

# Submit job
print("Submitting job...")
response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    exit(1)

result = response.json()
job_id = result.get('job_id')
github_job_id = None

print(f"Job created: {job_id}")
print("Waiting for GitHub Actions to start...")

# Wait for GitHub Actions to trigger
for i in range(10):
    time.sleep(5)
    status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
    
    if status_resp.status_code == 200:
        status = status_resp.json()
        github_job_id = status.get('github_job_id')
        print(f"Status: {status.get('status')} - Progress: {status.get('progress')}%")
        
        if github_job_id:
            print(f"GitHub Actions started: {github_job_id}")
            break

if not github_job_id:
    print("ERROR: GitHub Actions not triggered")
    exit(1)

# Construct video URL
video_url = f"https://res.cloudinary.com/dib3kbifc/video/upload/tours/{github_job_id}.mp4"
print(f"\nExpected video URL: {video_url}")
print("Waiting for video to be ready (this may take 2-5 minutes)...")

# Check for video availability
video_ready = False
for attempt in range(30):  # Check for up to 5 minutes
    response = requests.head(video_url)
    if response.status_code == 200:
        video_ready = True
        content_length = int(response.headers.get('Content-Length', 0))
        print(f"\nVideo is ready! Size: {content_length / 1024 / 1024:.2f} MB")
        break
    else:
        print(f"Attempt {attempt + 1}/30 - Video not ready yet")
        time.sleep(10)

if video_ready:
    # Download the video
    download_path = f"test_video_{job_id}.mp4"
    print(f"\nDownloading video to: {download_path}")
    
    download_resp = requests.get(video_url, stream=True)
    if download_resp.status_code == 200:
        with open(download_path, 'wb') as f:
            total_size = 0
            for chunk in download_resp.iter_content(chunk_size=8192):
                f.write(chunk)
                total_size += len(chunk)
                # Show progress
                print(f"\rDownloaded: {total_size / 1024 / 1024:.2f} MB", end='')
        
        print(f"\n\nSUCCESS! Video downloaded: {download_path}")
        print(f"File size: {os.path.getsize(download_path) / 1024 / 1024:.2f} MB")
        
        # Verify it's an MP4
        with open(download_path, 'rb') as f:
            header = f.read(12)
            if b'ftyp' in header:
                print("✓ Verified: Valid MP4 file")
            else:
                print("✗ Warning: May not be a valid MP4")
    else:
        print(f"ERROR: Failed to download video: {download_resp.status_code}")
else:
    print("\nERROR: Video was not ready after 5 minutes")
    print("Check GitHub Actions: https://github.com/bac1876/listinghelper/actions")