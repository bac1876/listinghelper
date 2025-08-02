#!/usr/bin/env python3
"""
Verify what's actually in Cloudinary and test upload
"""

import os
import cloudinary
import cloudinary.api
import cloudinary.uploader

# Your actual Cloudinary credentials from Railway
CLOUD_NAME = "dib3bbifc"
API_KEY = "245376524171559"
API_SECRET = "vyEwHjmTS9ssOX89c43vEuqTY"  # From your Railway screenshot

# Configure
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)

print("🔍 Checking your Cloudinary account...\n")

try:
    # List all videos
    print("📹 All videos in your account:")
    videos = cloudinary.api.resources(
        resource_type='video',
        type='upload',
        max_results=20
    )
    
    if videos.get('resources'):
        for video in videos['resources']:
            print(f"  • {video['public_id']}")
            print(f"    URL: {video['secure_url']}")
            print(f"    Created: {video['created_at']}")
            print()
    else:
        print("  No videos found")
    
    # Check tours folder specifically
    print("\n📁 Checking 'tours' folder:")
    tours = cloudinary.api.resources(
        resource_type='video',
        type='upload',
        prefix='tours',
        max_results=20
    )
    
    if tours.get('resources'):
        for video in tours['resources']:
            print(f"  • {video['public_id']}")
            print(f"    URL: {video['secure_url']}")
    else:
        print("  No videos in tours folder")
    
    # List ALL resources (not just videos)
    print("\n📋 Recent uploads (all types):")
    all_resources = cloudinary.api.resources(
        max_results=10
    )
    
    for resource in all_resources.get('resources', []):
        print(f"  • {resource['public_id']} ({resource['resource_type']})")
        if resource['resource_type'] == 'video':
            print(f"    VIDEO URL: {resource['secure_url']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
print("\n💡 If no videos are showing, the GitHub Actions upload might be failing.")
print("   Check the GitHub Actions logs for the actual error.")