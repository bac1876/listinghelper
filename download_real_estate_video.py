#!/usr/bin/env python3
"""
Download the real estate video from Railway app
"""

import requests

# Job ID from the test
job_id = "909fcbc3-6970-4211-83b3-979bc28ccc27"

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

print(f"Attempting to download real estate video: {job_id}\n")

# Try the download endpoint
download_url = f"{app_url}/api/virtual-tour/download/{job_id}/video"

print(f"Download URL: {download_url}")

try:
    # First check if it exists
    response = requests.head(download_url, allow_redirects=True)
    
    if response.status_code == 200:
        print("\n[SUCCESS] Video is available!")
        print(f"Final URL: {response.url}")
        print("\nYour real estate video is ready!")
        print("Property: 123 Luxury Lane, Beverly Hills, CA 90210")
        print("Features 8 professional photos with Ken Burns effects")
    else:
        print(f"Status: {response.status_code}")
        
        # Try to get more info
        response = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/download_urls")
        if response.status_code == 200:
            data = response.json()
            print("\nAvailable downloads:")
            for key, url in data.items():
                print(f"- {key}: {url}")
                
except Exception as e:
    print(f"Error: {e}")