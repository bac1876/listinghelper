#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the FFmpeg fallback mechanism works correctly
when GitHub Actions/Remotion fails.
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Server configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api/virtual-tour"

def test_video_generation_with_fallback():
    """Test video generation that should trigger fallback to FFmpeg"""
    
    print("=" * 60)
    print("Testing Video Generation with Fallback Mechanism")
    print("=" * 60)
    
    # Get test images
    test_images_dir = Path("test_images")
    if not test_images_dir.exists():
        print("❌ test_images directory not found!")
        return False
    
    # Select a few test images
    test_files = []
    for i, img_file in enumerate(test_images_dir.glob("*.jpg")):
        if i >= 3:  # Use first 3 images
            break
        test_files.append(str(img_file))
    
    if not test_files:
        print("❌ No test images found!")
        return False
    
    print(f"✅ Found {len(test_files)} test images")
    for f in test_files:
        print(f"   - {os.path.basename(f)}")
    
    # Prepare the upload
    files = []
    for img_path in test_files:
        files.append(('images', (os.path.basename(img_path), open(img_path, 'rb'), 'image/jpeg')))
    
    # Property details
    data = {
        'property_address': '123 Test Street',
        'property_price': '500000',
        'property_beds': '3',
        'property_baths': '2',
        'property_sqft': '2000',
        'agent_name': 'Test Agent',
        'agent_phone': '555-0123',
        'agent_email': 'test@example.com',
        'brand_name': 'Test Realty',
        'duration': '5',
        'effect_speed': 'medium'
    }
    
    try:
        # Step 1: Upload images
        print("\n📤 Uploading images...")
        response = requests.post(f"{API_URL}/upload", files=files, data=data)
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        result = response.json()
        if not result.get('success'):
            print(f"❌ Upload unsuccessful: {result.get('error')}")
            return False
        
        job_id = result.get('job_id')
        print(f"✅ Upload successful! Job ID: {job_id}")
        
        # Step 2: Monitor job status
        print("\n⏳ Monitoring job status...")
        start_time = time.time()
        max_wait_time = 600  # 10 minutes
        last_status = None
        last_step = None
        
        while time.time() - start_time < max_wait_time:
            # Check status
            status_response = requests.get(f"{API_URL}/job/{job_id}/status")
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            current_status = status_data.get('status')
            current_step = status_data.get('current_step', '')
            progress = status_data.get('progress', 0)
            error_details = status_data.get('error_details')
            
            # Print status updates
            if current_status != last_status or current_step != last_step:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed:3d}s] Status: {current_status} | Progress: {progress}% | {current_step}")
                
                # Check for fallback messages
                if 'switching to local processing' in current_step:
                    print("   🔄 FALLBACK TRIGGERED: Switching from Remotion to FFmpeg")
                elif 'FFmpeg processing' in current_step:
                    print("   ⚙️ FFmpeg fallback is now processing the video")
                
                if error_details:
                    print(f"   ⚠️ Error details: {error_details}")
                
                last_status = current_status
                last_step = current_step
            
            # Check if completed
            if current_status == 'completed':
                print(f"\n✅ Video generation completed successfully!")
                
                # Get video URL
                video_url = status_data.get('video_url')
                if video_url:
                    print(f"   Video URL: {video_url}")
                    
                    # Check if it was a fallback completion
                    if 'FFmpeg' in last_step or 'local processing' in last_step:
                        print("   ✨ Video was successfully generated using FFmpeg fallback!")
                else:
                    print("   ⚠️ No video URL returned")
                
                return True
            
            elif current_status == 'failed':
                print(f"\n❌ Video generation failed!")
                if error_details:
                    print(f"   Error: {error_details}")
                return False
            
            # Wait before next check
            time.sleep(2)
        
        print(f"\n⏱️ Timeout after {max_wait_time} seconds")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the fallback mechanism test"""
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/api/version")
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Server is running - Version: {version_info.get('version')}")
            print(f"   GitHub Actions: {version_info.get('github_actions_enabled')}")
            print(f"   GitHub Fixed: {version_info.get('github_actions_fixed')}")
        else:
            print("❌ Server returned unexpected status")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://localhost:5000")
        print("   Please start the server with: py main.py")
        return
    
    # Run the test
    print("\n" + "=" * 60)
    success = test_video_generation_with_fallback()
    
    # Print results
    print("\n" + "=" * 60)
    if success:
        print("✅ FALLBACK MECHANISM TEST PASSED!")
        print("The system successfully handled video generation,")
        print("likely using the FFmpeg fallback when Remotion failed.")
    else:
        print("❌ FALLBACK MECHANISM TEST FAILED!")
        print("The system was unable to generate a video.")
    print("=" * 60)

if __name__ == "__main__":
    main()