#!/usr/bin/env python3
"""
Get the video URL from the completed GitHub Actions workflow
"""

import requests
import json
import zipfile
import io

# Your GitHub token
GITHUB_TOKEN = "ghp_WGl0gx0srE0jGN7TC6oUWwcTvP1bvY3QqKUk"

def get_video_url():
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get the latest successful workflow run
    url = 'https://api.github.com/repos/bac1876/listinghelper/actions/runs?status=success&per_page=1'
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        print("❌ Authentication failed. Token may have expired.")
        print("Please create a new token at: https://github.com/settings/tokens/new")
        return
    
    if response.status_code != 200:
        print(f"❌ Failed to get workflow runs: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    if not data['workflow_runs']:
        print("❌ No successful workflow runs found")
        return
    
    run = data['workflow_runs'][0]
    print(f"✅ Found workflow run: {run['display_title']}")
    print(f"   Completed: {run['updated_at']}")
    
    # Get artifacts
    artifacts_url = f"https://api.github.com/repos/bac1876/listinghelper/actions/runs/{run['id']}/artifacts"
    artifacts_response = requests.get(artifacts_url, headers=headers)
    
    if artifacts_response.status_code != 200:
        print(f"❌ Failed to get artifacts: {artifacts_response.status_code}")
        return
    
    artifacts = artifacts_response.json()
    
    # Find the result artifact
    for artifact in artifacts['artifacts']:
        if 'render-result' in artifact['name']:
            print(f"\n📦 Downloading result: {artifact['name']}")
            
            # Download artifact
            download_url = f"https://api.github.com/repos/bac1876/listinghelper/actions/artifacts/{artifact['id']}/zip"
            download = requests.get(download_url, headers=headers)
            
            if download.status_code == 200:
                # Extract result.json from zip
                with zipfile.ZipFile(io.BytesIO(download.content)) as z:
                    with z.open('result.json') as f:
                        result = json.load(f)
                        
                        print(f"\n🎬 VIDEO READY!")
                        print(f"="*50)
                        print(f"Video URL: {result.get('videoUrl')}")
                        print(f"="*50)
                        print(f"\nDuration: {result.get('duration')} seconds")
                        print(f"Rendered at: {result.get('timestamp')}")
                        
                        return result.get('videoUrl')
    
    print("❌ No result artifact found")

if __name__ == "__main__":
    get_video_url()