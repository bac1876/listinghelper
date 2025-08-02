#!/usr/bin/env python3
"""
Check Cloudinary with version identifiers
"""

import requests
import time

# Job ID from the test
job_id = "909fcbc3-6970-4211-83b3-979bc28ccc27"
cloud_name = "dib3kbifc"

print(f"Checking for real estate video with version identifiers: {job_id}\n")

# Current timestamp and recent version
current_version = f"v{int(time.time())}"
recent_version = f"v{int(time.time()) - 300}"  # 5 minutes ago

# Try different URL patterns with versions
urls_to_try = [
    # With version identifier (Cloudinary adds this)
    f"https://res.cloudinary.com/{cloud_name}/video/upload/v1/tours/{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/{current_version}/tours/{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/{recent_version}/tours/{job_id}.mp4",
    # Try with auto version
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}",
    # Direct resource URL
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4",
]

# Also try fetching the resource info
print("Checking various Cloudinary URL patterns:\n")

found = False
for url in urls_to_try:
    print(f"Trying: {url}")
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            print(f"\n[SUCCESS] Video found!")
            print(f"Final URL: {response.url}")
            print(f"\nYour luxury real estate tour is ready!")
            print("Property: 123 Luxury Lane, Beverly Hills, CA 90210")
            print("8 professional photos with Ken Burns effects")
            found = True
            break
        else:
            print(f"  Status: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

if not found:
    print("\nTrying to construct the standard Cloudinary URL...")
    # Cloudinary typically uses a version timestamp
    # Let's try a range of recent timestamps
    base_time = int(time.time())
    for offset in range(0, 600, 60):  # Check last 10 minutes
        version = base_time - offset
        url = f"https://res.cloudinary.com/{cloud_name}/video/upload/v{version}/tours/{job_id}.mp4"
        try:
            response = requests.head(url, timeout=2, allow_redirects=True)
            if response.status_code == 200:
                print(f"\n[FOUND] Video at: {url}")
                found = True
                break
        except:
            pass