#!/usr/bin/env python3
"""
Test multiple scenarios with different configurations
"""

import requests
import time
import os
import json
from datetime import datetime

app_url = "https://virtual-tour-generator-production.up.railway.app"
results = []

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_scenario(name, num_images, quality, duration_per_image):
    """Test a specific configuration"""
    log(f"\n{'='*50}")
    log(f"Testing: {name}")
    log(f"Images: {num_images}, Quality: {quality}, Duration: {duration_per_image}s/image")
    
    # Select images based on quantity needed
    all_images = [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1280&h=720&fit=crop", 
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=1280&h=720&fit=crop",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1280&h=720&fit=crop"
    ]
    
    test_data = {
        "images": all_images[:num_images],
        "property_details": {
            "address": f"{name} - 456 Test Avenue",
            "city": "Beverly Hills, CA 90210",
            "agent_name": "Test Agent",
            "agent_phone": "(555) 123-4567",
            "brand_name": "Luxury Real Estate"
        },
        "settings": {
            "durationPerImage": duration_per_image,
            "effectSpeed": quality,
            "transitionDuration": 1.5
        }
    }
    
    start_time = time.time()
    
    # Submit job
    response = requests.post(
        f"{app_url}/api/virtual-tour/upload",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        log(f"ERROR: Failed to submit job: {response.status_code}")
        results.append({
            'name': name,
            'status': 'failed',
            'error': 'Job submission failed'
        })
        return
    
    result = response.json()
    job_id = result.get('job_id')
    github_job_id = None
    
    log(f"Job created: {job_id}")
    
    # Wait for GitHub Actions
    for i in range(20):  # Check for up to 200 seconds
        time.sleep(10)
        status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
        
        if status_resp.status_code == 200:
            status = status_resp.json()
            github_job_id = status.get('github_job_id')
            progress = status.get('progress', 0)
            
            log(f"Progress: {progress}% - {status.get('current_step', '')}")
            
            if github_job_id:
                break
    
    if not github_job_id:
        log("ERROR: GitHub Actions not triggered")
        results.append({
            'name': name,
            'status': 'failed', 
            'error': 'GitHub Actions not triggered',
            'job_id': job_id
        })
        return
    
    video_url = f"https://res.cloudinary.com/dib3kbifc/video/upload/tours/{github_job_id}.mp4"
    log(f"GitHub job: {github_job_id}")
    log("Waiting for video...")
    
    # Wait for video with exponential backoff
    video_ready = False
    max_attempts = 30
    
    for attempt in range(max_attempts):
        wait_time = min(20, 5 + attempt * 2)  # Start at 5s, increase by 2s each time, max 20s
        time.sleep(wait_time)
        
        response = requests.head(video_url)
        if response.status_code == 200:
            video_ready = True
            video_size = int(response.headers.get('Content-Length', 0)) / 1024 / 1024
            elapsed = time.time() - start_time
            
            log(f"SUCCESS! Video ready: {video_size:.2f} MB")
            log(f"Total time: {elapsed:.1f} seconds")
            
            results.append({
                'name': name,
                'status': 'success',
                'job_id': job_id,
                'github_job_id': github_job_id,
                'video_url': video_url,
                'size_mb': video_size,
                'elapsed_seconds': elapsed,
                'images': num_images,
                'quality': quality
            })
            break
        else:
            log(f"Attempt {attempt + 1}/{max_attempts} - Not ready (waited {wait_time}s)")
    
    if not video_ready:
        log("ERROR: Video generation timed out")
        results.append({
            'name': name,
            'status': 'timeout',
            'job_id': job_id,
            'github_job_id': github_job_id
        })

# Test scenarios
scenarios = [
    # Fast tests (should complete quickly)
    {'name': '2 Images Fast', 'images': 2, 'quality': 'fast', 'duration': 3},
    {'name': '3 Images Fast', 'images': 3, 'quality': 'fast', 'duration': 3},
    
    # Medium tests
    {'name': '4 Images Medium', 'images': 4, 'quality': 'medium', 'duration': 6},
    {'name': '5 Images Medium', 'images': 5, 'quality': 'medium', 'duration': 6},
    
    # Premium test (fewer images to avoid timeout)
    {'name': '3 Images Premium', 'images': 3, 'quality': 'slow', 'duration': 8},
]

# Run tests
log("Starting Multiple Scenario Tests")
log(f"Total scenarios: {len(scenarios)}")

for scenario in scenarios:
    test_scenario(
        scenario['name'],
        scenario['images'],
        scenario['quality'],
        scenario['duration']
    )
    
    # Wait between tests to avoid overloading
    if scenarios.index(scenario) < len(scenarios) - 1:
        log("\nWaiting 30 seconds before next test...")
        time.sleep(30)

# Summary
log("\n" + "="*60)
log("TEST SUMMARY")
log("="*60)

successful = [r for r in results if r['status'] == 'success']
failed = [r for r in results if r['status'] == 'failed']
timeout = [r for r in results if r['status'] == 'timeout']

log(f"Total tests: {len(results)}")
log(f"Successful: {len(successful)}")
log(f"Failed: {len(failed)}")
log(f"Timeout: {len(timeout)}")

if successful:
    log("\nSuccessful Videos:")
    for r in successful:
        log(f"- {r['name']}")
        log(f"  URL: {r['video_url']}")
        log(f"  Size: {r['size_mb']:.2f} MB")
        log(f"  Time: {r['elapsed_seconds']:.1f}s")
        log(f"  Speed: {r['elapsed_seconds']/r['images']:.1f}s per image")

# Save results
with open('test_results_scenarios.json', 'w') as f:
    json.dump(results, f, indent=2)

log(f"\nResults saved to: test_results_scenarios.json")

# Download one video as proof
if successful:
    log("\nDownloading sample video as proof...")
    sample = successful[0]
    download_resp = requests.get(sample['video_url'], stream=True)
    
    if download_resp.status_code == 200:
        filename = f"sample_video_{sample['name'].replace(' ', '_')}.mp4"
        with open(filename, 'wb') as f:
            for chunk in download_resp.iter_content(chunk_size=8192):
                f.write(chunk)
        log(f"Sample video saved: {filename} ({os.path.getsize(filename)/1024/1024:.2f} MB)")