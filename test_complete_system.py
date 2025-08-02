#!/usr/bin/env python3
"""
Complete end-to-end test of the real estate video system
"""

import requests
import json
import time

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Different set of real estate photos for testing
test_images = [
    # Modern kitchen
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1920&h=1080&fit=crop",
    # Luxurious living room
    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1920&h=1080&fit=crop",
    # Beautiful bedroom
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1920&h=1080&fit=crop",
    # Modern bathroom
    "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=1920&h=1080&fit=crop",
    # House exterior
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1920&h=1080&fit=crop",
    # Backyard pool
    "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=1920&h=1080&fit=crop"
]

# Property details
test_data = {
    "url_images": test_images,
    "address": "456 Modern Estate Drive",
    "city": "Malibu, CA 90265", 
    "details1": "Schedule your private tour today",
    "details2": "Newly Renovated - Move-in Ready",
    "agent_name": "Michael Johnson",
    "agent_email": "michael@premiumestates.com",
    "agent_phone": "(310) 555-8899",
    "brand_name": "Premium Estates International",
    "quality": "high",  # High quality for better results
    "use_github_actions": True
}

print("=== Complete System Test ===")
print(f"Property: {test_data['address']}, {test_data['city']}")
print(f"Agent: {test_data['agent_name']} - {test_data['brand_name']}")
print(f"Images: {len(test_images)} high-resolution photos")
print("")

# Step 1: Submit job
print("[1/4] Submitting job to Railway app...")
response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"[ERROR] Failed to submit job: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
railway_job_id = result.get('job_id')
print(f"[SUCCESS] Railway job created: {railway_job_id}")

# Step 2: Check job status
print("\n[2/4] Checking job status...")
time.sleep(5)  # Initial wait

max_attempts = 30  # 5 minutes max
attempt = 0
github_job_id = None

while attempt < max_attempts:
    status_response = requests.get(f"{app_url}/api/virtual-tour/job/{railway_job_id}/status")
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        progress = status_data.get('progress', 0)
        current_step = status_data.get('current_step', '')
        github_job_id = status_data.get('github_job_id')
        
        print(f"Progress: {progress}% - {current_step}")
        
        if status_data.get('status') == 'completed':
            print("[SUCCESS] Job completed!")
            break
        elif status_data.get('status') == 'failed':
            print(f"[ERROR] Job failed: {status_data.get('error')}")
            exit(1)
    
    time.sleep(10)
    attempt += 1

# Step 3: Get video URL
print("\n[3/4] Retrieving video URL...")
if github_job_id:
    print(f"GitHub Actions job ID: {github_job_id}")
    
    # Check if video URL is in status response
    if 'video_url' in status_data:
        video_url = status_data['video_url']
        print(f"[SUCCESS] Video URL from status: {video_url}")
    else:
        # Construct Cloudinary URL
        cloud_name = "dib3kbifc"
        video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{github_job_id}.mp4"
        print(f"[INFO] Constructed video URL: {video_url}")
else:
    print("[WARNING] No GitHub job ID found")
    video_url = None

# Step 4: Verify video exists
if video_url:
    print("\n[4/4] Verifying video availability...")
    video_response = requests.head(video_url, timeout=5)
    
    if video_response.status_code == 200:
        print(f"\n{'='*50}")
        print("[SUCCESS] Real estate video is ready!")
        print(f"\nVideo URL: {video_url}")
        print(f"\nProperty: {test_data['address']}, {test_data['city']}")
        print(f"Agent: {test_data['agent_name']} ({test_data['agent_phone']})")
        print(f"Quality: High (30fps, 6 sec/image)")
        print(f"\nOpen this URL in your browser to view the video!")
        print(f"{'='*50}")
    else:
        print(f"[WARNING] Video not accessible yet (status: {video_response.status_code})")
        print("The video may still be processing on Cloudinary.")
else:
    print("[ERROR] No video URL available")

# Additional info
print(f"\nJob IDs:")
print(f"- Railway: {railway_job_id}")
print(f"- GitHub: {github_job_id or 'Not available'}")
print(f"\nCheck GitHub Actions: https://github.com/bac1876/listinghelper/actions")