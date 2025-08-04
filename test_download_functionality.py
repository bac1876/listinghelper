#!/usr/bin/env python3
"""
Download Functionality Test Tool
Tests the download endpoints and diagnoses common issues
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
RAILWAY_URL = "https://virtual-tour-generator-production.up.railway.app"
LOCAL_URL = "http://localhost:5000"

def test_download_endpoint(base_url, job_id, file_type='video'):
    """Test download endpoint with detailed diagnostics"""
    print(f"\n🔍 Testing download for Job: {job_id}, Type: {file_type}")
    print(f"   URL: {base_url}/api/virtual-tour/download/{job_id}/{file_type}")
    
    try:
        # First, check job status
        status_url = f"{base_url}/api/virtual-tour/job/{job_id}/status"
        print(f"\n1. Checking job status...")
        
        status_response = requests.get(status_url, timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ Job found: Status = {status_data.get('status', 'unknown')}")
            print(f"   - Video available: {status_data.get('video_available', False)}")
            print(f"   - Cloudinary video: {status_data.get('cloudinary_video', False)}")
            print(f"   - Progress: {status_data.get('progress', 0)}%")
            
            if status_data.get('error'):
                print(f"   ⚠️ Job error: {status_data['error']}")
        else:
            print(f"   ❌ Job status check failed: {status_response.status_code}")
            print(f"   Response: {status_response.text}")
        
        # Run diagnostics
        print(f"\n2. Running diagnostics...")
        diag_url = f"{base_url}/api/virtual-tour/download/{job_id}/diagnostics"
        
        diag_response = requests.get(diag_url, timeout=10)
        if diag_response.status_code == 200:
            diag_data = diag_response.json()
            print(f"   ✅ Diagnostics successful:")
            print(f"   - Job directory exists: {diag_data.get('job_dir_exists', False)}")
            print(f"   - Files found: {diag_data.get('file_count', 0)}")
            
            if diag_data.get('files'):
                print(f"\n   Files in job directory:")
                for file_info in diag_data['files']:
                    size_mb = file_info['size'] / (1024 * 1024)
                    print(f"     - {file_info['name']} ({size_mb:.2f} MB)")
                    
            if diag_data.get('storage_space'):
                space = diag_data['storage_space']
                if isinstance(space, dict):
                    print(f"\n   Storage space:")
                    print(f"     - Free: {space.get('free_mb', 0):.1f} MB")
                    print(f"     - Used: {space.get('used_percent', 0):.1f}%")
        else:
            print(f"   ⚠️ Diagnostics endpoint not available")
        
        # Test actual download
        print(f"\n3. Testing download endpoint...")
        download_url = f"{base_url}/api/virtual-tour/download/{job_id}/{file_type}"
        
        start_time = time.time()
        download_response = requests.get(download_url, timeout=30, stream=True)
        elapsed_time = time.time() - start_time
        
        print(f"   Response status: {download_response.status_code}")
        print(f"   Response time: {elapsed_time:.2f}s")
        
        if download_response.status_code == 200:
            # Success - check file details
            content_length = download_response.headers.get('Content-Length', 'Unknown')
            content_type = download_response.headers.get('Content-Type', 'Unknown')
            
            print(f"\n   ✅ Download successful!")
            print(f"   - Content-Type: {content_type}")
            print(f"   - Content-Length: {content_length} bytes")
            
            # Check custom headers
            job_id_header = download_response.headers.get('X-Job-ID')
            file_size_header = download_response.headers.get('X-File-Size')
            request_id_header = download_response.headers.get('X-Request-ID')
            
            if job_id_header:
                print(f"   - Job ID (header): {job_id_header}")
            if file_size_header:
                print(f"   - File Size (header): {file_size_header} bytes")
            if request_id_header:
                print(f"   - Request ID: {request_id_header}")
            
            # Save a small sample to verify content
            if file_type == 'video':
                sample_file = f"download_test_{job_id}.mp4"
            else:
                sample_file = f"download_test_{job_id}.txt"
            
            with open(sample_file, 'wb') as f:
                # Write first 1KB for verification
                f.write(download_response.content[:1024])
            
            print(f"\n   Sample saved to: {sample_file}")
            
            # Verify file type
            with open(sample_file, 'rb') as f:
                header = f.read(12)
                if file_type == 'video' and b'ftyp' in header:
                    print(f"   ✅ Valid MP4 file detected")
                elif file_type != 'video':
                    print(f"   ✅ Text file downloaded")
            
            os.remove(sample_file)  # Clean up
            
        elif download_response.status_code == 202:
            print(f"\n   ⏳ File still being processed")
            try:
                data = download_response.json()
                print(f"   - Status: {data.get('status', 'unknown')}")
                print(f"   - Progress: {data.get('progress', 0)}%")
            except:
                pass
                
        elif download_response.status_code == 404:
            print(f"\n   ❌ File not found")
            try:
                error_data = download_response.json()
                print(f"   - Error: {error_data.get('error', 'Unknown')}")
                
                if error_data.get('cloudinary_available'):
                    print(f"   💡 Cloudinary URL available: {error_data.get('cloudinary_url', 'N/A')}")
                    
                if error_data.get('directory_contents'):
                    print(f"\n   Files in directory:")
                    for file in error_data['directory_contents']:
                        print(f"     - {file}")
                        
                if error_data.get('suggestion'):
                    print(f"\n   💡 Suggestion: {error_data['suggestion']}")
            except:
                print(f"   Raw response: {download_response.text[:200]}")
                
        else:
            print(f"\n   ❌ Download failed: {download_response.status_code}")
            print(f"   Response: {download_response.text[:500]}")
            
        return download_response.status_code == 200
        
    except requests.exceptions.Timeout:
        print(f"\n   ❌ Request timed out")
        return False
        
    except requests.exceptions.ConnectionError:
        print(f"\n   ❌ Connection error - is the server running?")
        return False
        
    except Exception as e:
        print(f"\n   ❌ Unexpected error: {e}")
        return False


def test_multiple_downloads(base_url, job_id):
    """Test downloading all file types for a job"""
    print(f"\n{'='*60}")
    print(f"Testing all downloads for job: {job_id}")
    print(f"{'='*60}")
    
    file_types = ['video', 'description', 'script']
    results = {}
    
    for file_type in file_types:
        results[file_type] = test_download_endpoint(base_url, job_id, file_type)
        time.sleep(1)  # Brief pause between requests
    
    # Summary
    print(f"\n{'='*60}")
    print("DOWNLOAD TEST SUMMARY")
    print(f"{'='*60}")
    
    for file_type, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{file_type.ljust(15)}: {status}")
    
    success_count = sum(1 for s in results.values() if s)
    print(f"\nTotal: {success_count}/{len(results)} downloads successful")
    
    return results


def main():
    print("""
Download Functionality Test Tool
================================

This tool tests the download endpoints and helps diagnose issues.
""")
    
    # Choose environment
    print("\nSelect environment:")
    print("1. Railway (Production)")
    print("2. Local (Development)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        base_url = RAILWAY_URL
        print(f"\nUsing Railway URL: {base_url}")
    else:
        base_url = LOCAL_URL
        print(f"\nUsing Local URL: {base_url}")
    
    # Get job ID
    job_id = input("\nEnter Job ID to test (or press Enter to test with sample): ").strip()
    
    if not job_id:
        # Use a sample job ID for testing
        job_id = "sample-job-id-for-testing"
        print(f"Using sample job ID: {job_id}")
    
    # Test health endpoint first
    print(f"\nTesting server health...")
    try:
        health_response = requests.get(f"{base_url}/api/virtual-tour/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Server is healthy")
            print(f"   - FFmpeg: {health_data.get('ffmpeg_available', False)}")
            print(f"   - Storage: {health_data.get('storage_writable', False)}")
        else:
            print(f"⚠️ Health check returned: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run tests
    while True:
        print(f"\n\nOptions:")
        print("1. Test single download (video)")
        print("2. Test all downloads for job")
        print("3. Test with different job ID")
        print("4. Exit")
        
        option = input("\nSelect option: ").strip()
        
        if option == '1':
            test_download_endpoint(base_url, job_id)
        elif option == '2':
            test_multiple_downloads(base_url, job_id)
        elif option == '3':
            job_id = input("\nEnter new Job ID: ").strip()
            if not job_id:
                print("Invalid job ID")
        elif option == '4':
            break
        else:
            print("Invalid option")
    
    print("\nTest complete!")


if __name__ == "__main__":
    main()