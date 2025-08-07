"""
Simple API test to diagnose video generation issues
"""
import os
import requests
import time
import json
from datetime import datetime

def test_api():
    """Test the API with minimal images"""
    
    print("="*60)
    print("SIMPLE API TEST - DIAGNOSING VIDEO GENERATION")
    print("="*60)
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:5000/api/virtual-tour/health", timeout=5)
        print(f"Server health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print("Server is running\n")
        else:
            print("Server returned unexpected status")
    except Exception as e:
        print(f"Warning: Health check failed ({e})")
        print("Attempting to continue anyway...\n")
    
    # Get 3 test images
    images = []
    image_dir = 'real_test_images'
    
    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(root, file)
                images.append((file, path))
                if len(images) >= 3:
                    break
        if len(images) >= 3:
            break
    
    if len(images) < 3:
        print(f"Only found {len(images)} images, need at least 3")
        return False
    
    print(f"Using {len(images)} test images:")
    for name, path in images:
        size = os.path.getsize(path) / (1024 * 1024)
        print(f"  - {name}: {size:.2f} MB")
    
    # Prepare upload
    print("\n" + "-"*40)
    print("UPLOADING IMAGES")
    print("-"*40)
    
    url = "http://localhost:5000/api/virtual-tour/upload"
    
    # Prepare files
    files = []
    for name, path in images:
        files.append(('images', (name, open(path, 'rb'), 'image/jpeg')))
    
    # Form data
    data = {
        'address': 'Test Property 123',
        'agent_name': 'Test Agent',
        'agent_phone': '555-1234',
        'details1': 'Test Details',
        'city': 'Test City'
    }
    
    # Send request
    start_time = time.time()
    
    try:
        print(f"Sending POST to {url}...")
        response = requests.post(url, data=data, files=files, timeout=120)
        
        upload_time = time.time() - start_time
        print(f"Response received in {upload_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nUpload Response:")
            print(json.dumps(result, indent=2))
            
            job_id = result.get('job_id')
            if not job_id:
                print("ERROR: No job_id in response")
                return False
            
            print(f"\n" + "-"*40)
            print(f"JOB CREATED: {job_id}")
            print("-"*40)
            
            # Key information
            print(f"Status: {result.get('status')}")
            print(f"GitHub Job ID: {result.get('github_job_id', 'NOT SET')}")
            print(f"Images Processed: {result.get('images_processed')}")
            print(f"Video Available: {result.get('video_available')}")
            print(f"Cloudinary Video: {result.get('cloudinary_video')}")
            
            # Poll for completion
            print(f"\n" + "-"*40)
            print("POLLING FOR COMPLETION")
            print("-"*40)
            
            completed = False
            last_progress = 0
            
            for i in range(90):  # Poll for up to 3 minutes
                time.sleep(2)
                
                status_url = f"http://localhost:5000/api/virtual-tour/job/{job_id}/status"
                status_response = requests.get(status_url)
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    progress = status.get('progress', 0)
                    
                    # Only print when progress changes
                    if progress != last_progress or i % 10 == 0:
                        print(f"[{i*2:3}s] Progress: {progress:3}% | {status.get('status'):10} | {status.get('current_step', '')}")
                        
                        # Log important fields
                        if status.get('github_job_id') and i == 0:
                            print(f"       GitHub Job: {status.get('github_job_id')}")
                        if status.get('cloudinary_video'):
                            print(f"       Cloudinary: {status.get('cloudinary_video')}")
                        
                        last_progress = progress
                    
                    if status.get('status') == 'completed':
                        completed = True
                        print(f"\n" + "="*40)
                        print("JOB COMPLETED!")
                        print("="*40)
                        
                        # Try to download
                        download_url = f"http://localhost:5000/api/virtual-tour/download/{job_id}"
                        print(f"\nAttempting download from: {download_url}")
                        
                        download_response = requests.get(download_url, timeout=30, allow_redirects=False)
                        
                        print(f"Download Status: {download_response.status_code}")
                        print(f"Download Headers:")
                        for key, value in download_response.headers.items():
                            if key.lower() in ['content-type', 'location', 'content-length']:
                                print(f"  {key}: {value}")
                        
                        # Check what we got
                        if download_response.status_code == 302:
                            # Redirect to Cloudinary
                            location = download_response.headers.get('location', '')
                            print(f"\nRedirect to: {location}")
                            if 'cloudinary.com' in location:
                                print("SUCCESS: Redirecting to Cloudinary video!")
                                
                                # Follow redirect
                                final_response = requests.head(location)
                                print(f"Cloudinary response: {final_response.status_code}")
                                if final_response.status_code == 200:
                                    print("SUCCESS: Video exists on Cloudinary!")
                                else:
                                    print(f"ERROR: Cloudinary returned {final_response.status_code}")
                            else:
                                print("ERROR: Unexpected redirect location")
                        else:
                            content_type = download_response.headers.get('content-type', '')
                            
                            if 'video' in content_type:
                                print(f"SUCCESS: Got video! Size: {len(download_response.content)} bytes")
                            elif 'json' in content_type:
                                print("ERROR: Got JSON instead of video!")
                                json_data = download_response.json()
                                print("JSON content:", json.dumps(json_data, indent=2))
                            elif 'html' in content_type:
                                print("ERROR: Got HTML instead of video!")
                                print("HTML preview:", download_response.text[:500])
                            else:
                                print(f"ERROR: Unexpected content type: {content_type}")
                        
                        break
                    
                    elif status.get('status') == 'error':
                        print(f"\nERROR: Job failed!")
                        print(f"Error: {status.get('current_step', 'Unknown error')}")
                        break
                else:
                    print(f"Status check failed: {status_response.status_code}")
            
            if not completed:
                print("\nTIMEOUT: Job did not complete in 3 minutes")
                
                # Get final status
                final_status = requests.get(f"http://localhost:5000/api/virtual-tour/job/{job_id}/status")
                if final_status.status_code == 200:
                    final = final_status.json()
                    print("\nFinal Status:")
                    print(json.dumps(final, indent=2))
            
            return completed
            
        else:
            print(f"Upload failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()

if __name__ == "__main__":
    print("Starting API test...")
    print("Make sure server is running: py run_production.py\n")
    
    success = test_api()
    
    print("\n" + "="*60)
    if success:
        print("TEST COMPLETED SUCCESSFULLY")
    else:
        print("TEST FAILED - Check output above")
    print("="*60)