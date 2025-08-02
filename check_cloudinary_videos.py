#!/usr/bin/env python3
"""
Check what videos are actually in your Cloudinary account
"""

import os
import cloudinary
import cloudinary.api
from datetime import datetime

# Configure Cloudinary
cloudinary.config(
    cloud_name="dib3bbifc",  # Your cloud name from the screenshot
    api_key="245376524171559",  # Your API key from Railway
    api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'your_api_secret_here')
)

def list_all_videos():
    """List all videos in Cloudinary account"""
    print("🔍 Searching for all videos in your Cloudinary account...\n")
    
    try:
        # Get all videos
        result = cloudinary.api.resources(
            type='upload',
            resource_type='video',
            max_results=50
        )
        
        if result.get('resources'):
            print(f"Found {len(result['resources'])} videos:\n")
            
            for video in result['resources']:
                print(f"📹 Video: {video['public_id']}")
                print(f"   URL: {video['secure_url']}")
                print(f"   Created: {video['created_at']}")
                print(f"   Size: {video.get('bytes', 0) / 1024 / 1024:.2f} MB")
                print(f"   Format: {video.get('format', 'unknown')}")
                print()
                
            # Also check specific folders
            print("\n🔍 Checking 'tours' folder specifically...")
            tours_result = cloudinary.api.resources(
                type='upload',
                resource_type='video',
                prefix='tours/',
                max_results=50
            )
            
            if tours_result.get('resources'):
                print(f"\nFound {len(tours_result['resources'])} videos in 'tours' folder")
            else:
                print("\nNo videos found in 'tours' folder")
                
        else:
            print("❌ No videos found in your Cloudinary account")
            
        # Also list recent uploads
        print("\n📅 Recent uploads (all types):")
        recent = cloudinary.api.resources(
            type='upload',
            max_results=10,
            direction='desc'
        )
        
        for item in recent.get('resources', []):
            print(f"   • {item['public_id']} ({item['resource_type']}) - {item['created_at']}")
            
    except Exception as e:
        print(f"❌ Error accessing Cloudinary: {e}")
        print("\nMake sure to set CLOUDINARY_API_SECRET environment variable:")
        print("$env:CLOUDINARY_API_SECRET='your_secret_here'")

if __name__ == "__main__":
    list_all_videos()