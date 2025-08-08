#!/usr/bin/env python3
"""
Test if ImageKit images are publicly accessible (as GitHub Actions would need).
"""

import requests
import json
import os
from datetime import datetime

def test_imagekit_access():
    """Test if ImageKit images are publicly accessible."""
    
    print("=" * 60)
    print("ImageKit Public Access Test")
    print("=" * 60)
    
    # Sample ImageKit URLs from the logs
    test_urls = [
        # These should be actual ImageKit URLs from recent uploads
        "https://ik.imagekit.io/brianosris/tours/images/",  # Base path
    ]
    
    # Try to get actual image URLs from recent uploads
    try:
        # Check if we have a recent job log
        log_file = "logs/railwaylog.md"
        if os.path.exists(log_file):
            print("\nChecking recent uploads from logs...")
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Look for ImageKit URLs in the logs
            import re
            imagekit_pattern = r'https://ik\.imagekit\.io/brianosris/[^\s"\']+\.(jpg|jpeg|png|webp)'
            found_urls = re.findall(imagekit_pattern, content)
            
            if found_urls:
                # Get unique URLs (first 3)
                unique_urls = list(set(['https://ik.imagekit.io/brianosris/' + url[0] if not url[0].startswith('http') else url[0] for url in found_urls[:3]]))
                print(f"Found {len(unique_urls)} unique ImageKit URLs in logs")
                test_urls = unique_urls[:3]
    except Exception as e:
        print(f"Could not parse logs: {e}")
    
    # Test a known working ImageKit URL
    test_urls.append("https://ik.imagekit.io/brianosris/tours/images/tour_1754676543_f3f037e0_0.jpg")
    
    print(f"\nTesting {len(test_urls)} URLs for public access...")
    print("-" * 60)
    
    accessible_count = 0
    failed_count = 0
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n[{i}] Testing: {url}")
        
        try:
            # Test with a simple GET request (like GitHub Actions would do)
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                print(f"    [OK] Status: {response.status_code} - Publicly accessible")
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                print(f"    Content-Type: {content_type}")
                
                # Check if CORS headers are present
                cors_header = response.headers.get('Access-Control-Allow-Origin', 'Not set')
                print(f"    CORS: {cors_header}")
                
                accessible_count += 1
            else:
                print(f"    [FAIL] Status: {response.status_code}")
                failed_count += 1
                
        except requests.exceptions.RequestException as e:
            print(f"    [ERROR] {type(e).__name__}: {e}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    print(f"Accessible: {accessible_count}/{len(test_urls)}")
    print(f"Failed: {failed_count}/{len(test_urls)}")
    
    if accessible_count == len(test_urls):
        print("\n[SUCCESS] All ImageKit URLs are publicly accessible")
        print("GitHub Actions should be able to access these images.")
    elif accessible_count > 0:
        print("\n[PARTIAL] Some ImageKit URLs are accessible")
        print("There might be inconsistent access settings.")
    else:
        print("\n[FAILURE] No ImageKit URLs are publicly accessible")
        print("This is why GitHub Actions cannot render videos!")
        print("\nPossible solutions:")
        print("1. Check ImageKit dashboard for public access settings")
        print("2. Ensure images are in a public folder")
        print("3. Check if authentication is required")
    
    # Test from Python (simulating Remotion's access pattern)
    print("\n" + "-" * 60)
    print("Testing image download (like Remotion would):")
    print("-" * 60)
    
    if test_urls:
        test_url = test_urls[0]
        print(f"Downloading: {test_url}")
        
        try:
            response = requests.get(test_url, timeout=30)
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"[SUCCESS] Downloaded {content_length} bytes")
                
                # Save a test image
                with open("test_imagekit_download.jpg", "wb") as f:
                    f.write(response.content)
                print("Saved as test_imagekit_download.jpg")
            else:
                print(f"[FAILED] Status: {response.status_code}")
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    test_imagekit_access()