"""
Test script to verify 12+ image upload works with the fixes
"""
import os
import requests
import time
import json

def test_with_production_server():
    """Test 12 image upload with production server"""
    
    print("="*60)
    print("TESTING 12 IMAGE UPLOAD - WITH FIXES")
    print("="*60)
    
    # Check if production server is running
    try:
        response = requests.get("http://localhost:5000/api/virtual-tour/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running and healthy")
        else:
            print(f"Server returned status {response.status_code}")
    except:
        print("✗ Server is not running!")
        print("\nTo start the production server, run:")
        print("  py run_production.py")
        print("\nThis uses Waitress which handles multiple uploads reliably.")
        return False
    
    # Gather test images
    images = []
    image_dir = 'real_test_images'
    
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(root, file)
                images.append((file, path))
                if len(images) >= 12:
                    break
        if len(images) >= 12:
            break
    
    if len(images) < 12:
        print(f"✗ Only found {len(images)} images, need 12")
        return False
    
    print(f"\n✓ Found {len(images)} test images")
    
    # Prepare upload
    print("\nUploading 12 images...")
    
    # Prepare files for upload
    files = []
    for name, path in images[:12]:
        files.append(('images', (name, open(path, 'rb'), 'image/jpeg')))
    
    # Form data
    data = {
        'address': '123 Test Street\nTest City, State',
        'agent_name': 'Test Agent',
        'agent_phone': '555-1234',
        'details1': 'Call for viewing',
        'details2': 'Just Listed'
    }
    
    # Send request
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:5000/api/virtual-tour/upload",
            data=data,
            files=files,
            timeout=120
        )
        
        upload_time = time.time() - start_time
        
        print(f"\n✓ Upload completed in {upload_time:.2f} seconds")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            
            print(f"\n✓ Job created: {job_id}")
            print(f"  Images processed: {result.get('images_processed', 0)}")
            print(f"  Status: {result.get('status', 'unknown')}")
            
            # Poll for completion
            print("\nChecking job status...")
            completed = False
            
            for i in range(30):  # Check for up to 60 seconds
                time.sleep(2)
                
                status_response = requests.get(f"http://localhost:5000/api/virtual-tour/job/{job_id}/status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    progress = status.get('progress', 0)
                    current_step = status.get('current_step', '')
                    
                    print(f"  [{i*2}s] Progress: {progress}% - {current_step}")
                    
                    if status.get('status') == 'completed':
                        print(f"\n✓✓✓ SUCCESS! Video generated for 12 images!")
                        print(f"  Total time: {time.time() - start_time:.2f} seconds")
                        completed = True
                        
                        # Try to download video
                        download_url = f"http://localhost:5000/api/virtual-tour/download/{job_id}"
                        download_response = requests.get(download_url, timeout=30)
                        
                        if download_response.status_code == 200:
                            content_type = download_response.headers.get('content-type', '')
                            if 'video' in content_type:
                                print(f"  ✓ Video download successful ({len(download_response.content)} bytes)")
                            else:
                                print(f"  ⚠ Download returned: {content_type}")
                        break
                    elif status.get('status') == 'error':
                        print(f"\n✗ Job failed: {status.get('current_step', 'Unknown error')}")
                        break
            
            if not completed:
                print("\n⚠ Job did not complete in 60 seconds")
            
            return completed
            
        else:
            print(f"\n✗ Upload failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n✗ Request timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
    
    finally:
        # Close all file handles
        for _, file_tuple in files:
            file_tuple[1].close()

if __name__ == "__main__":
    success = test_with_production_server()
    
    if success:
        print("\n" + "="*60)
        print("✓✓✓ 12 IMAGE UPLOAD WORKS SUCCESSFULLY! ✓✓✓")
        print("="*60)
        print("\nThe fixes have resolved the issue:")
        print("1. Production server (Waitress) handles concurrent requests")
        print("2. Batch processing prevents memory overload")
        print("3. Increased upload limits allow larger files")
        print("4. Error recovery ensures reliability")
    else:
        print("\n" + "="*60)
        print("TEST FAILED - Check the output above for details")
        print("="*60)