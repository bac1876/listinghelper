#!/usr/bin/env python3
"""
Get the video URL from a completed GitHub Actions workflow
"""

import requests
import json
import os

def get_latest_video():
    """Get the video URL from the most recent successful workflow"""
    
    # GitHub API setup
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN environment variable not set")
        print("Set it with: set GITHUB_TOKEN=ghp_WGl0gx0srE0jGN7TC6oUWwcTvP1bvY3QqKUk")
        return
        
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get recent workflow runs
    url = 'https://api.github.com/repos/bac1876/listinghelper/actions/workflows/render-video.yml/runs'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get workflow runs: {response.status_code}")
        return
    
    runs = response.json()
    
    # Find the most recent successful run
    for run in runs['workflow_runs']:
        if run['status'] == 'completed' and run['conclusion'] == 'success':
            print(f"✅ Found successful run: {run['name']}")
            print(f"   Run ID: {run['id']}")
            print(f"   Completed: {run['updated_at']}")
            
            # Get artifacts for this run
            artifacts_url = run['artifacts_url']
            artifacts_response = requests.get(artifacts_url, headers=headers)
            
            if artifacts_response.status_code == 200:
                artifacts = artifacts_response.json()
                
                # Look for result artifact
                for artifact in artifacts['artifacts']:
                    if 'render-result' in artifact['name']:
                        print(f"\n📦 Found result artifact: {artifact['name']}")
                        
                        # Download the artifact
                        download_url = artifact['archive_download_url']
                        download_response = requests.get(download_url, headers=headers)
                        
                        if download_response.status_code == 200:
                            # Extract result.json from zip
                            import zipfile
                            import io
                            
                            with zipfile.ZipFile(io.BytesIO(download_response.content)) as z:
                                with z.open('result.json') as f:
                                    result = json.load(f)
                                    
                                    print(f"\n🎬 Video Details:")
                                    print(f"   Success: {result.get('success')}")
                                    print(f"   Video URL: {result.get('videoUrl')}")
                                    print(f"   Duration: {result.get('duration')} seconds")
                                    print(f"   Render Time: {result.get('renderTime')}")
                                    print(f"   Timestamp: {result.get('timestamp')}")
                                    
                                    if result.get('videoUrl'):
                                        print(f"\n✅ Your video is ready at:")
                                        print(f"   {result['videoUrl']}")
                                    
                                    return result
            break
    
    print("❌ No successful runs found")

if __name__ == "__main__":
    print("🔍 Checking GitHub Actions for completed videos...\n")
    get_latest_video()