"""
Test watermark functionality using Playwright
"""

import asyncio
import os
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_IMAGES_DIR = Path("test_images")

async def test_watermark_upload():
    """Test the complete watermark upload and video generation flow"""
    
    print("Starting watermark test...")
    
    # Navigate to the application
    print(f"1. Navigating to {BASE_URL}")
    # Note: We'll use the MCP Playwright commands instead of Python Playwright
    
    # For now, let's create a simple test that verifies the watermark API
    import requests
    
    # Test 1: Check if watermark API is available
    print("\n2. Testing watermark API health...")
    response = requests.get(f"{BASE_URL}/api/watermark/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Watermark API is healthy")
        print(f"   - Storage path: {data.get('storage_path')}")
        print(f"   - Storage writable: {data.get('storage_writable')}")
        print(f"   - Existing watermarks: {data.get('watermark_count')}")
    else:
        print(f"   [FAIL] Watermark API health check failed: {response.status_code}")
        return False
    
    # Test 2: Upload a test watermark
    print("\n3. Creating test watermark image...")
    
    # Create a simple test watermark image
    from PIL import Image, ImageDraw, ImageFont
    
    watermark_img = Image.new('RGBA', (200, 50), (255, 255, 255, 0))
    draw = ImageDraw.Draw(watermark_img)
    
    # Draw text
    try:
        # Try to use a nice font, fallback to default if not available
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 10), "TEST LOGO", fill=(255, 0, 0, 200), font=font)
    
    # Save watermark
    watermark_path = "test_watermark.png"
    watermark_img.save(watermark_path)
    watermark_img.close()  # Close the image to release the file
    print(f"   [OK] Created test watermark: {watermark_path}")
    
    # Test 3: Upload watermark via API
    print("\n4. Uploading watermark via API...")
    
    with open(watermark_path, 'rb') as f:
        files = {'watermark': ('test_watermark.png', f, 'image/png')}
        data = {
            'position': 'bottom-right',
            'opacity': '0.7',
            'scale': '0.15',
            'margin_x': '20',
            'margin_y': '20',
            'duration': 'full'
        }
        
        response = requests.post(f"{BASE_URL}/api/watermark/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            watermark_id = result.get('watermark_id')
            print(f"   [OK] Watermark uploaded successfully")
            print(f"   - Watermark ID: {watermark_id}")
            
            # Clean up
            try:
                os.remove(watermark_path)
            except:
                pass  # Ignore if file is locked
            
            return watermark_id
        else:
            print(f"   [FAIL] Watermark upload failed: {response.status_code}")
            print(f"   - Error: {response.text}")
            try:
                os.remove(watermark_path)
            except:
                pass  # Ignore if file is locked
            return None

def test_video_generation_with_watermark(watermark_id):
    """Test video generation with watermark"""
    import requests
    
    print("\n5. Testing video generation with watermark...")
    
    # Prepare test data
    form_data = {
        'address': '123 Test Street\nTest City, CA 90210',
        'details1': '$1,250,000',
        'details2': 'Just Listed',
        'agent_name': 'Test Agent',
        'agent_phone': '(555) 123-4567',
        'agent_email': 'test@realestate.com',
        'brand_name': 'Test Real Estate',
        'duration_per_image': '8',
        'effect_speed': 'medium',
        'transition_duration': '1.5',
        'watermark_id': watermark_id  # Include the watermark ID
    }
    
    # Add test images
    test_images = []
    for img_file in TEST_IMAGES_DIR.glob("*.jpg"):
        test_images.append(('files', (img_file.name, open(img_file, 'rb'), 'image/jpeg')))
    
    if not test_images:
        print("   [FAIL] No test images found in test_images directory")
        return False
    
    print(f"   - Using {len(test_images)} test images")
    print(f"   - Including watermark ID: {watermark_id}")
    
    # Send request
    response = requests.post(f"{BASE_URL}/api/virtual-tour/upload", data=form_data, files=test_images)
    
    # Close file handles
    for _, (_, file_handle, _) in test_images:
        file_handle.close()
    
    if response.status_code == 200:
        result = response.json()
        job_id = result.get('job_id')
        github_job_id = result.get('github_job_id')
        
        print(f"   [OK] Video generation started")
        print(f"   - Job ID: {job_id}")
        print(f"   - GitHub Job ID: {github_job_id}")
        
        # Poll for status
        print("\n6. Checking job status...")
        max_attempts = 30
        for i in range(max_attempts):
            time.sleep(10)
            status_response = requests.get(f"{BASE_URL}/api/virtual-tour/job/{job_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                current_step = status_data.get('current_step', '')
                
                print(f"   [{i+1}/{max_attempts}] Status: {status} ({progress}%) - {current_step}")
                
                if status == 'completed':
                    print(f"\n   [OK] Video generation completed!")
                    if 'video_url' in status_data:
                        print(f"   - Video URL: {status_data['video_url']}")
                    return True
                elif status == 'error':
                    print(f"\n   [FAIL] Video generation failed")
                    print(f"   - Error: {status_data.get('error', 'Unknown error')}")
                    return False
        
        print("\n   [WARN] Timeout waiting for video generation")
        return False
    else:
        print(f"   [FAIL] Failed to start video generation: {response.status_code}")
        print(f"   - Error: {response.text}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("WATERMARK FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test watermark upload
    watermark_id = await test_watermark_upload()
    
    if watermark_id:
        print(f"\n[OK] Watermark upload test passed!")
        
        # Test video generation with watermark
        success = test_video_generation_with_watermark(watermark_id)
        
        if success:
            print("\n[OK] Video generation with watermark test passed!")
        else:
            print("\n[FAIL] Video generation with watermark test failed!")
    else:
        print("\n[FAIL] Watermark upload test failed!")

if __name__ == "__main__":
    asyncio.run(main())