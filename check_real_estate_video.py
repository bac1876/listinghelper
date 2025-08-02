#!/usr/bin/env python3
"""
Check if the real estate video exists on Cloudinary
"""

import requests

# Job ID from the test
job_id = "909fcbc3-6970-4211-83b3-979bc28ccc27"
cloud_name = "dib3kbifc"

print(f"Checking for real estate video: {job_id}\n")

# Try the expected URL
url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4"

print(f"Checking: {url}")
try:
    response = requests.head(url, timeout=5)
    if response.status_code == 200:
        print(f"\n[SUCCESS] Real estate video is ready!")
        print(f"\nYour luxury property video is available at:")
        print(url)
        print("\nThis video includes:")
        print("- 8 professional property photos")
        print("- Ken Burns pan & zoom effects")
        print("- Property details overlay")
        print("- Medium speed transitions")
    else:
        print(f"Status: {response.status_code}")
        if response.status_code == 404:
            print("\nVideo not ready yet. GitHub Actions might still be processing.")
            print("Check: https://github.com/bac1876/listinghelper/actions")
except Exception as e:
    print(f"Error: {e}")