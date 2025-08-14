#!/usr/bin/env python3
"""
Direct test of Bunny.net upload functionality
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("DIRECT BUNNY.NET UPLOAD TEST")
print("=" * 60)

# Get Bunny.net credentials
storage_zone = os.environ.get('BUNNY_STORAGE_ZONE_NAME', 'listinghelper')
access_key = os.environ.get('BUNNY_ACCESS_KEY', '966f1c23-4af1-4f87-a5dedd45cf6e-4fd2-432f')
pull_zone_url = os.environ.get('BUNNY_PULL_ZONE_URL', 'https://listinghelper-cdn.b-cdn.net')
region = os.environ.get('BUNNY_REGION', 'ny')

print(f"Storage Zone: {storage_zone}")
print(f"Access Key: {access_key[:20]}...")
print(f"Pull Zone URL: {pull_zone_url}")
print(f"Region: {region}")

# Construct storage API URL
base_url = "storage.bunnycdn.com"
if region and region != 'default':
    base_url = f"{region}.{base_url}"
storage_api_url = f"https://{base_url}/{storage_zone}"

print(f"\nStorage API URL: {storage_api_url}")

# Create a test file
test_content = "This is a test upload to Bunny.net"
test_file_name = "test_upload.txt"
test_path = f"tours/test/{test_file_name}"

# Full upload URL
upload_url = f"{storage_api_url}/{test_path}"
print(f"Upload URL: {upload_url}")

# Prepare headers
headers = {
    "AccessKey": access_key,
    "Content-Type": "application/octet-stream",
    "accept": "application/json"
}

print("\nAttempting upload...")

try:
    # Upload the file
    response = requests.put(upload_url, headers=headers, data=test_content.encode())
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code in [200, 201]:
        print("\n✅ UPLOAD SUCCESSFUL!")
        cdn_url = f"{pull_zone_url}/{test_path}"
        print(f"CDN URL: {cdn_url}")
        
        # Try to access the file
        print("\nVerifying file access...")
        get_response = requests.get(cdn_url)
        print(f"GET Status: {get_response.status_code}")
        if get_response.status_code == 200:
            print(f"Content: {get_response.text}")
            print("✅ File is accessible!")
        else:
            print(f"❌ File not accessible: {get_response.text}")
    else:
        print(f"\n❌ UPLOAD FAILED!")
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)