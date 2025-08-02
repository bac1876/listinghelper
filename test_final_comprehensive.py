#!/usr/bin/env python3
"""
Final comprehensive test of the complete system
"""

import requests
import json
import time

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Professional real estate photos
test_data = {
    "images": [
        # Stunning kitchen
        "https://images.unsplash.com/photo-1556911220-bff31c812dba?w=1920&h=1080&fit=crop",
        # Elegant living room
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1920&h=1080&fit=crop", 
        # Master bedroom
        "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=1920&h=1080&fit=crop",
        # Luxury bathroom
        "https://images.unsplash.com/photo-1552321554-5fefe8c9ef14?w=1920&h=1080&fit=crop",
        # Beautiful exterior
        "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=1920&h=1080&fit=crop",
        # Pool and patio
        "https://images.unsplash.com/photo-1575517111478-7f6afd0973db?w=1920&h=1080&fit=crop",
        # Home office
        "https://images.unsplash.com/photo-1565182999561-18d7dc61c393?w=1920&h=1080&fit=crop",
        # Dining room
        "https://images.unsplash.com/photo-1615874959474-d609969a20ed?w=1920&h=1080&fit=crop"
    ],
    "property_details": {
        "address": "1234 Ocean View Drive",
        "city": "Laguna Beach, CA 92651",
        "details1": "Schedule your exclusive showing: (949) 555-7890",
        "details2": "Price: $3,995,000 | Just Listed",
        "agent_name": "Alexandra Chen",
        "agent_email": "achen@coastalluxury.com",
        "agent_phone": "(949) 555-7890",
        "brand_name": "Coastal Luxury Properties"
    },
    "settings": {
        "durationPerImage": 8,      # Premium quality - 8 seconds per image
        "effectSpeed": "slow",      # Slow, cinematic movements
        "transitionDuration": 2     # Smooth transitions
    }
}

print("=== FINAL COMPREHENSIVE SYSTEM TEST ===")
print(f"\nProperty: {test_data['property_details']['address']}")
print(f"Location: {test_data['property_details']['city']}")
print(f"Price: $3,995,000")
print(f"Agent: {test_data['property_details']['agent_name']} - {test_data['property_details']['brand_name']}")
print(f"Photos: {len(test_data['images'])} professional images")
print(f"Quality: Premium (8 sec/image, slow Ken Burns, smooth transitions)")
print("\n" + "="*50 + "\n")

# Submit the job
print("[STEP 1] Submitting to Railway app...")
start_time = time.time()

response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"[ERROR] Failed to submit: {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
railway_job_id = result.get('job_id')
print(f"[SUCCESS] Railway job ID: {railway_job_id}")

# Monitor the job
print("\n[STEP 2] Monitoring job progress...")
github_job_id = None
max_wait = 300  # 5 minutes max
check_interval = 5

while (time.time() - start_time) < max_wait:
    status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{railway_job_id}/status")
    
    if status_resp.status_code == 200:
        status = status_resp.json()
        progress = status.get('progress', 0)
        step = status.get('current_step', 'Processing')
        github_job_id = status.get('github_job_id')
        
        print(f"Progress: {progress}% - {step}")
        
        if status.get('status') == 'completed' and github_job_id:
            print(f"\n[SUCCESS] GitHub Actions job ID: {github_job_id}")
            break
        elif status.get('status') == 'failed':
            print(f"\n[ERROR] Job failed: {status.get('error')}")
            exit(1)
    
    time.sleep(check_interval)

# Get the video URL
if github_job_id:
    print("\n[STEP 3] Retrieving video URL...")
    cloud_name = "dib3kbifc"
    video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{github_job_id}.mp4"
    
    # Also check if it's in the status response
    if 'video_url' in status:
        video_url = status['video_url']
        print(f"[INFO] Using video URL from status response")
    
    # Verify the video
    print(f"\n[STEP 4] Verifying video availability...")
    video_resp = requests.head(video_url, timeout=10)
    
    if video_resp.status_code == 200:
        content_length = int(video_resp.headers.get('Content-Length', 0))
        size_mb = content_length / (1024 * 1024)
        
        print("\n" + "="*60)
        print("✅ SYSTEM TEST SUCCESSFUL!")
        print("="*60)
        print(f"\n🎥 Video URL: {video_url}")
        print(f"📊 File size: {size_mb:.1f} MB")
        print(f"⏱️ Total time: {time.time() - start_time:.1f} seconds")
        print(f"\n🏠 Property: {test_data['property_details']['address']}, {test_data['property_details']['city']}")
        print(f"💰 Price: $3,995,000")
        print(f"👤 Agent: {test_data['property_details']['agent_name']} ({test_data['property_details']['agent_phone']})")
        print(f"\n📋 Job IDs:")
        print(f"   - Railway: {railway_job_id}")
        print(f"   - GitHub: {github_job_id}")
        print(f"\n🔗 GitHub Actions: https://github.com/bac1876/listinghelper/actions")
        print(f"\n✨ Your premium real estate video is ready!")
        print("="*60)
    else:
        print(f"\n[WARNING] Video not accessible (status: {video_resp.status_code})")
        print("The video may still be processing.")
else:
    print("\n[ERROR] No GitHub job ID received")
    print("GitHub Actions may not have been triggered.")

# Download links
if github_job_id:
    print(f"\n📥 Download Links:")
    print(f"   Video: {app_url}/api/virtual-tour/download/{railway_job_id}/video")
    print(f"   Description: {app_url}/api/virtual-tour/download/{railway_job_id}/description")
    print(f"   Script: {app_url}/api/virtual-tour/download/{railway_job_id}/script")