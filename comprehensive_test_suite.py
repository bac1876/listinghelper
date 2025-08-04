#!/usr/bin/env python3
"""
Comprehensive Test Suite for Virtual Tour Generator
Tests multiple scenarios and verifies MP4 downloads
"""

import requests
import json
import time
import os
import subprocess
from datetime import datetime

# Configuration
app_url = "https://virtual-tour-generator-production.up.railway.app"
test_results = []

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")
    
def test_scenario(name, images, quality, expected_duration):
    """Test a specific scenario"""
    log(f"\n{'='*60}")
    log(f"Testing: {name}")
    log(f"Images: {len(images)}, Quality: {quality}")
    log(f"{'='*60}")
    
    # Prepare test data
    test_data = {
        "images": images,
        "property_details": {
            "address": f"Test Property - {name}",
            "city": "Los Angeles, CA 90210",
            "details1": "Call (555) 123-4567 for viewing",
            "details2": "Luxury Estate",
            "agent_name": "Test Agent",
            "agent_email": "agent@test.com",
            "agent_phone": "(555) 123-4567",
            "brand_name": "Premium Real Estate"
        },
        "settings": {
            "durationPerImage": expected_duration,
            "effectSpeed": quality,
            "transitionDuration": 1.5
        }
    }
    
    # Submit job
    log("Submitting job...")
    start_time = time.time()
    
    response = requests.post(
        f"{app_url}/api/virtual-tour/upload",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        log(f"ERROR: Job submission failed: {response.status_code}")
        return None
        
    result = response.json()
    job_id = result.get('job_id')
    log(f"Job created: {job_id}")
    
    # Monitor job progress
    max_wait = 900  # 15 minutes
    check_interval = 10
    github_job_id = None
    
    while (time.time() - start_time) < max_wait:
        status_resp = requests.get(f"{app_url}/api/virtual-tour/job/{job_id}/status")
        
        if status_resp.status_code == 200:
            status = status_resp.json()
            progress = status.get('progress', 0)
            current_step = status.get('current_step', '')
            github_job_id = status.get('github_job_id')
            
            log(f"Progress: {progress}% - {current_step}")
            
            if status.get('status') == 'completed' or (github_job_id and progress == 75):
                # For GitHub Actions jobs, we need to wait for actual completion
                if github_job_id and not status.get('video_url'):
                    log(f"GitHub Actions job: {github_job_id}")
                    log("Waiting for GitHub Actions to complete...")
                else:
                    log("Job completed or video URL available")
                    break
            elif status.get('status') == 'failed':
                log(f"ERROR: Job failed - {status.get('error')}")
                return None
        
        time.sleep(check_interval)
    
    # Check final video status
    if github_job_id:
        log(f"\nChecking video availability for GitHub job: {github_job_id}")
        video_url = f"https://res.cloudinary.com/dib3kbifc/video/upload/tours/{github_job_id}.mp4"
        
        # Wait for video to be available
        for i in range(30):  # Check for up to 5 minutes
            video_resp = requests.head(video_url)
            if video_resp.status_code == 200:
                log(f"Video available at: {video_url}")
                elapsed_time = time.time() - start_time
                
                # Download and verify the video
                download_path = f"test_video_{name.replace(' ', '_')}_{job_id}.mp4"
                log(f"Downloading video to: {download_path}")
                
                download_resp = requests.get(video_url, stream=True)
                if download_resp.status_code == 200:
                    with open(download_path, 'wb') as f:
                        for chunk in download_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_size = os.path.getsize(download_path) / (1024 * 1024)
                    log(f"Downloaded successfully: {file_size:.2f} MB")
                    
                    # Verify it's a valid video file
                    verification = verify_video_file(download_path)
                    
                    result = {
                        'scenario': name,
                        'job_id': job_id,
                        'github_job_id': github_job_id,
                        'video_url': video_url,
                        'download_path': download_path,
                        'file_size_mb': file_size,
                        'elapsed_time': elapsed_time,
                        'status': 'success',
                        'verification': verification
                    }
                    
                    test_results.append(result)
                    return result
                else:
                    log(f"ERROR: Failed to download video: {download_resp.status_code}")
            else:
                log(f"Video not ready yet (attempt {i+1}/30)")
                time.sleep(10)
    
    log("ERROR: Video generation failed or timed out")
    return None

def verify_video_file(filepath):
    """Verify the downloaded file is a valid MP4 video"""
    log(f"\nVerifying video file: {filepath}")
    
    verification = {
        'exists': os.path.exists(filepath),
        'size_bytes': 0,
        'is_valid_mp4': False,
        'duration': None,
        'resolution': None
    }
    
    if not verification['exists']:
        log("ERROR: File does not exist")
        return verification
        
    verification['size_bytes'] = os.path.getsize(filepath)
    
    # Try to read video properties using ffprobe if available
    try:
        # Check if file starts with MP4 signature
        with open(filepath, 'rb') as f:
            header = f.read(12)
            # MP4 files typically have 'ftyp' at bytes 4-8
            if b'ftyp' in header:
                verification['is_valid_mp4'] = True
                log("✓ Valid MP4 file signature detected")
            else:
                log("✗ Not a valid MP4 file")
                
    except Exception as e:
        log(f"Error verifying file: {e}")
    
    # Try to get video info using ffprobe (if available)
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration', '-of', 'json', filepath
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            verification['duration'] = f"{duration:.1f} seconds"
            log(f"✓ Video duration: {verification['duration']}")
    except:
        log("Note: ffprobe not available for detailed verification")
    
    return verification

# Test scenarios
scenarios = [
    # Fast rendering test
    {
        'name': 'Fast 3 Images',
        'images': [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1920&h=1080&fit=crop"
        ],
        'quality': 'fast',
        'duration': 3
    },
    # Standard quality test
    {
        'name': 'Standard 5 Images',
        'images': [
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=1920&h=1080&fit=crop"
        ],
        'quality': 'medium',
        'duration': 6
    },
    # Premium quality test (smaller to avoid timeout)
    {
        'name': 'Premium 3 Images',
        'images': [
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1920&h=1080&fit=crop"
        ],
        'quality': 'slow',
        'duration': 8
    }
]

# Run tests
log("Starting Comprehensive Test Suite")
log(f"Time: {datetime.now()}")

for scenario in scenarios:
    result = test_scenario(
        scenario['name'],
        scenario['images'],
        scenario['quality'],
        scenario['duration']
    )
    
    if result:
        log(f"\n✓ {scenario['name']} - SUCCESS")
        log(f"  Video: {result['video_url']}")
        log(f"  Size: {result['file_size_mb']:.2f} MB")
        log(f"  Time: {result['elapsed_time']:.1f} seconds")
        if result['verification']['is_valid_mp4']:
            log(f"  ✓ VERIFIED: Valid MP4 video file")
    else:
        log(f"\n✗ {scenario['name']} - FAILED")
    
    # Wait between tests
    time.sleep(30)

# Summary
log("\n" + "="*60)
log("TEST SUMMARY")
log("="*60)

successful = [r for r in test_results if r['status'] == 'success']
log(f"Total tests: {len(scenarios)}")
log(f"Successful: {len(successful)}")
log(f"Failed: {len(scenarios) - len(successful)}")

if successful:
    log("\nSuccessful Videos:")
    for result in successful:
        log(f"- {result['scenario']}")
        log(f"  File: {result['download_path']}")
        log(f"  Size: {result['file_size_mb']:.2f} MB")
        log(f"  Valid MP4: {result['verification']['is_valid_mp4']}")

# Save detailed results
with open('test_results_comprehensive.json', 'w') as f:
    json.dump(test_results, f, indent=2)
    
log(f"\nDetailed results saved to: test_results_comprehensive.json")
log(f"Test completed at: {datetime.now()}")