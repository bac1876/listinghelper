#!/usr/bin/env python3
"""
Check if the video exists on Cloudinary directly
"""

import requests

# Latest job ID from your test
job_id = "tour_1754140427_0dff97a1"
cloud_name = "dib3kbifc"

print(f"Checking for video: {job_id}\n")

# Try different URL patterns
urls_to_try = [
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/v1/{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/{job_id}.mp4"
]

print("Trying different URL patterns:\n")

for url in urls_to_try:
    print(f"Checking: {url}")
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            print(f"[SUCCESS] Video found at: {url}")
            print(f"\nYour video is ready! Open this URL in your browser:")
            print(url)
            break
        else:
            print(f"  Status: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

print("\nIf none of these work, the video upload likely failed.")
print("Check the GitHub Actions logs manually for the error.")