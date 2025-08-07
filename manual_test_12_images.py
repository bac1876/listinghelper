"""
Manual test for 12 image upload issue
This script manually uploads 12 images to identify the exact failure point
"""
import os
import requests
import time
import json
from datetime import datetime

def test_12_image_upload():
    """Test uploading exactly 12 images as reported by user"""
    
    # Load test images
    images = []
    image_dir = 'real_test_images'
    
    # Get first 12 images
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
        print(f"Error: Only {len(images)} images found, need 12")
        return
    
    print(f"Testing with {len(images)} images:")
    for name, path in images[:12]:
        size = os.path.getsize(path) / (1024 * 1024)
        print(f"  - {name}: {size:.2f} MB")
    
    total_size = sum(os.path.getsize(p) / (1024 * 1024) for _, p in images[:12])
    print(f"\nTotal size: {total_size:.2f} MB")
    
    # Test direct API upload
    url = "http://localhost:5000/api/virtual-tour/upload"
    
    # Prepare multipart form data
    files = []
    for i, (name, path) in enumerate(images[:12]):
        with open(path, 'rb') as f:
            files.append(('images', (name, f.read(), 'image/jpeg')))
    
    # Form data
    data = {
        'address': '123 Test Street, Test City',
        'agent_name': 'Test Agent',
        'agent_phone': '555-1234',
        'details1': 'Call 555-1234 to schedule a showing',
        'price': '$500,000',
        'beds': '4',
        'baths': '3',
        'sqft': '2500'
    }
    
    print("\nSending POST request to /generate...")
    start_time = time.time()
    
    try:
        # Send request
        response = requests.post(
            url, 
            data=data,
            files=[('images', (name, open(path, 'rb'), 'image/jpeg')) for name, path in images[:12]],
            timeout=120
        )
        
        elapsed = time.time() - start_time
        print(f"Response received in {elapsed:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        # Check response
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                result = response.json()
                print(f"JSON Response: {json.dumps(result, indent=2)}")
                
                # Check job status
                job_id = result.get('job_id')
                if job_id:
                    print(f"\nJob ID: {job_id}")
                    
                    # Poll for completion
                    print("Polling for completion...")
                    for i in range(60):  # Poll for up to 60 seconds
                        time.sleep(2)
                        status_response = requests.get(f"http://localhost:5000/status/{job_id}")
                        if status_response.status_code == 200:
                            status = status_response.json()
                            print(f"  [{i*2}s] Status: {status.get('status')}, Progress: {status.get('progress')}%")
                            
                            if status.get('status') == 'completed':
                                print("\nVideo generation completed!")
                                
                                # Try to download
                                download_url = f"http://localhost:5000/download/{job_id}"
                                download_response = requests.get(download_url, timeout=30)
                                download_type = download_response.headers.get('content-type', '')
                                
                                print(f"Download response:")
                                print(f"  - Status: {download_response.status_code}")
                                print(f"  - Content-Type: {download_type}")
                                print(f"  - Content-Length: {len(download_response.content)} bytes")
                                
                                if 'video' in download_type:
                                    print("SUCCESS: Video downloaded successfully!")
                                    with open(f"test_video_{job_id}.mp4", 'wb') as f:
                                        f.write(download_response.content)
                                    print(f"Video saved as test_video_{job_id}.mp4")
                                else:
                                    print(f"FAILURE: Expected video but got {download_type}")
                                    # Save whatever we got for inspection
                                    if 'json' in download_type:
                                        print("Content:", download_response.text[:500])
                                    elif 'html' in download_type:
                                        print("HTML content received (first 500 chars):", download_response.text[:500])
                                break
                            elif status.get('status') == 'failed':
                                print(f"\nFAILED: {status.get('error', 'Unknown error')}")
                                break
                        else:
                            print(f"  Status check failed: {status_response.status_code}")
            else:
                print(f"Unexpected content type: {content_type}")
                print(f"Response (first 500 chars): {response.text[:500]}")
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 120 seconds")
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Connection failed - {e}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("="*60)
    print("MANUAL TEST: 12 IMAGE UPLOAD")
    print("="*60)
    
    # First check if server is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("Server is running")
    except:
        print("ERROR: Server is not running. Please start with: py main.py")
        print("Then run this test in another terminal")
        exit(1)
    
    test_12_image_upload()