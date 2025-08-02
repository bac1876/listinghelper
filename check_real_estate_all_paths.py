#!/usr/bin/env python3
"""
Check all possible paths for the real estate video
"""

import requests

# Job ID from the test
job_id = "909fcbc3-6970-4211-83b3-979bc28ccc27"
cloud_name = "dib3kbifc"

print(f"Checking for real estate video: {job_id}\n")

# Try different URL patterns
urls_to_try = [
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/tour-{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/tour-{job_id}.mp4",
    f"https://res.cloudinary.com/{cloud_name}/video/upload/{job_id}.mp4"
]

print("Trying different URL patterns:\n")

for url in urls_to_try:
    print(f"Checking: {url}")
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            print(f"\n[SUCCESS] Real estate video found!")
            print(f"\nYour luxury property tour is ready at:")
            print(url)
            print("\nProperty: 123 Luxury Lane, Beverly Hills, CA 90210")
            print("Agent: Jane Smith - Luxury Real Estate Group")
            print("\nVideo features:")
            print("- 8 professional property photos")
            print("- Cinematic Ken Burns effects")
            print("- Property information overlay")
            print("- Medium speed transitions")
            break
        else:
            print(f"  Status: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")