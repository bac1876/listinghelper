#!/usr/bin/env python3
"""
Check all videos stored in ImageKit to verify if videos are being generated.
"""

import os
import json
from datetime import datetime

# Set ImageKit credentials
os.environ['IMAGEKIT_PRIVATE_KEY'] = 'private_4NFY9DlW7DaZwHW1j+k5FsYoIhY='
os.environ['IMAGEKIT_PUBLIC_KEY'] = 'public_wnhOBpqBUB1ReFbqsfOWgFcRnvU='
os.environ['IMAGEKIT_URL_ENDPOINT'] = 'https://ik.imagekit.io/brianosris/'

def check_imagekit_videos():
    """List all videos in ImageKit."""
    try:
        from imagekitio import ImageKit
        
        # Initialize ImageKit
        imagekit = ImageKit(
            private_key=os.environ['IMAGEKIT_PRIVATE_KEY'],
            public_key=os.environ['IMAGEKIT_PUBLIC_KEY'],
            url_endpoint=os.environ['IMAGEKIT_URL_ENDPOINT']
        )
        
        print("=" * 60)
        print("ImageKit Video Check")
        print("=" * 60)
        
        # List all files in tours/videos folder
        print("\nChecking /tours/videos/ folder...")
        
        try:
            # List files with video type
            result = imagekit.list_files(
                options={
                    "path": "/tours/videos/",
                    "file_type": "video"
                }
            )
            
            # Handle both dict and object responses
            if result:
                if isinstance(result, dict):
                    files = result.get('response', [])
                elif hasattr(result, 'response_metadata'):
                    files = result.response_metadata.get('raw', [])
                else:
                    files = []
                
                if files:
                    print(f"\nFound {len(files)} videos:")
                    print("-" * 60)
                    
                    for video in files:
                        name = video.get('name', 'Unknown')
                        size_mb = video.get('size', 0) / (1024 * 1024)
                        created = video.get('createdAt', 'Unknown')
                        url = video.get('url', 'No URL')
                        file_id = video.get('fileId', 'No ID')
                        
                        print(f"\nVideo: {name}")
                        print(f"  Size: {size_mb:.2f} MB")
                        print(f"  Created: {created}")
                        print(f"  File ID: {file_id}")
                        print(f"  URL: {url}")
                        
                        # Try to extract job_id from filename
                        if 'tour_' in name:
                            job_id = name.replace('.mp4', '')
                            print(f"  Job ID: {job_id}")
                else:
                    print("\nNo videos found in /tours/videos/")
            else:
                print("\nCould not retrieve file list")
                
        except Exception as e:
            print(f"\nError listing videos: {e}")
            
        # Also check all folders for any videos
        print("\n" + "=" * 60)
        print("Checking all folders for videos...")
        
        try:
            # List all files of type video
            result = imagekit.list_files(
                options={
                    "file_type": "video",
                    "limit": 100
                }
            )
            
            # Handle both dict and object responses
            if result:
                if isinstance(result, dict):
                    files = result.get('response', [])
                elif hasattr(result, 'response_metadata'):
                    files = result.response_metadata.get('raw', [])
                else:
                    files = []
                
                if files:
                    # Group by folder
                    folders = {}
                    for video in files:
                        folder = video.get('filePath', '/').rsplit('/', 1)[0]
                        if folder not in folders:
                            folders[folder] = []
                        folders[folder].append(video)
                    
                    print(f"\nFound videos in {len(folders)} folders:")
                    for folder, videos in folders.items():
                        print(f"\n{folder}/ ({len(videos)} videos)")
                        for video in videos[:3]:  # Show first 3
                            name = video.get('name', 'Unknown')
                            size_mb = video.get('size', 0) / (1024 * 1024)
                            print(f"  - {name} ({size_mb:.2f} MB)")
                        if len(videos) > 3:
                            print(f"  ... and {len(videos) - 3} more")
                else:
                    print("\nNo videos found in ImageKit")
                    
        except Exception as e:
            print(f"\nError scanning all folders: {e}")
            
        # Check recent uploads
        print("\n" + "=" * 60)
        print("Checking recent uploads (all file types)...")
        
        try:
            result = imagekit.list_files(
                options={
                    "sort": "createdAt",
                    "limit": 10
                }
            )
            
            # Handle both dict and object responses
            if result:
                if isinstance(result, dict):
                    files = result.get('response', [])
                elif hasattr(result, 'response_metadata'):
                    files = result.response_metadata.get('raw', [])
                else:
                    files = []
                
                if files:
                    print(f"\n10 Most recent uploads:")
                    for f in files:
                        name = f.get('name', 'Unknown')
                        file_type = f.get('fileType', 'unknown')
                        created = f.get('createdAt', 'Unknown')
                        path = f.get('filePath', '/')
                        
                        print(f"\n  [{file_type}] {name}")
                        print(f"    Path: {path}")
                        print(f"    Created: {created}")
                        
        except Exception as e:
            print(f"\nError checking recent uploads: {e}")
            
    except ImportError:
        print("[ERROR] imagekitio library not installed")
        print("Run: pip install imagekitio")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ImageKit: {e}")

if __name__ == "__main__":
    check_imagekit_videos()