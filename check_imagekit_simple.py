#!/usr/bin/env python3
"""
Simple check for videos in ImageKit using direct API calls.
"""

import os
import requests
import base64
from datetime import datetime

# Set ImageKit credentials
PRIVATE_KEY = 'private_4NFY9DlW7DaZwHW1j+k5FsYoIhY='
PUBLIC_KEY = 'public_wnhOBpqBUB1ReFbqsfOWgFcRnvU='
URL_ENDPOINT = 'https://ik.imagekit.io/brianosris/'

def check_videos_api():
    """Check videos using ImageKit API directly."""
    
    print("=" * 60)
    print("ImageKit Video Check (Direct API)")
    print("=" * 60)
    
    # Create auth header
    auth_string = f"{PRIVATE_KEY}:"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_b64}'
    }
    
    # Check videos in tours/videos folder
    print("\n1. Checking /tours/videos/ folder...")
    
    url = "https://api.imagekit.io/v1/files"
    params = {
        'path': '/tours/videos',
        'fileType': 'non-image'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                videos = data
            else:
                videos = data.get('files', [])
            
            if videos:
                print(f"\nFound {len(videos)} videos:")
                print("-" * 60)
                
                for video in videos:
                    name = video.get('name', 'Unknown')
                    size_mb = video.get('size', 0) / (1024 * 1024)
                    created = video.get('createdAt', 'Unknown')
                    url = video.get('url', 'No URL')
                    
                    print(f"\nVideo: {name}")
                    print(f"  Size: {size_mb:.2f} MB")
                    print(f"  Created: {created}")
                    print(f"  URL: {url}")
            else:
                print("  No videos found in /tours/videos/")
        else:
            print(f"  API Error: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check all videos
    print("\n2. Checking all videos in ImageKit...")
    
    params = {
        'fileType': 'non-image',
        'limit': 100
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                videos = data
            else:
                videos = data.get('files', [])
            
            if videos:
                print(f"\nFound {len(videos)} total videos")
                
                # Group by folder
                folders = {}
                for video in videos:
                    path = video.get('filePath', '/')
                    folder = path.rsplit('/', 1)[0] if '/' in path else '/'
                    
                    if folder not in folders:
                        folders[folder] = []
                    folders[folder].append(video)
                
                for folder, vids in folders.items():
                    print(f"\n{folder}/ ({len(vids)} videos)")
                    for v in vids[:3]:
                        name = v.get('name', 'Unknown')
                        size_mb = v.get('size', 0) / (1024 * 1024)
                        print(f"  - {name} ({size_mb:.2f} MB)")
                    if len(vids) > 3:
                        print(f"  ... and {len(vids) - 3} more")
            else:
                print("  No videos found in ImageKit")
        else:
            print(f"  API Error: {response.status_code}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    # Check recent uploads
    print("\n3. Checking 10 most recent uploads...")
    
    params = {
        'sort': 'createdAt_DESC',
        'limit': 10
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                files = data
            else:
                files = data.get('files', [])
            
            if files:
                print("\nRecent uploads:")
                for f in files:
                    name = f.get('name', 'Unknown')
                    file_type = f.get('fileType', 'unknown')
                    created = f.get('createdAt', 'Unknown')
                    path = f.get('filePath', '/')
                    
                    # Parse and format date
                    if created != 'Unknown':
                        try:
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            created_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            created_str = created
                    else:
                        created_str = created
                    
                    print(f"\n  [{file_type:5}] {name}")
                    print(f"         Path: {path}")
                    print(f"         Created: {created_str}")
            else:
                print("  No recent uploads found")
        else:
            print(f"  API Error: {response.status_code}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_videos_api()