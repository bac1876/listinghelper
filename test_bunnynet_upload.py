#!/usr/bin/env python3
"""
Test script to verify Bunny.net upload is working
Run this to debug upload issues
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_bunnynet_config():
    """Test if Bunny.net configuration is correct"""
    print("=" * 60)
    print("TESTING BUNNY.NET CONFIGURATION")
    print("=" * 60)
    
    # Check environment variables
    storage_zone = os.environ.get('BUNNY_STORAGE_ZONE_NAME')
    access_key = os.environ.get('BUNNY_ACCESS_KEY')
    pull_zone = os.environ.get('BUNNY_PULL_ZONE_URL')
    
    print(f"BUNNY_STORAGE_ZONE_NAME: {'✓ Set' if storage_zone else '✗ Missing'}")
    print(f"BUNNY_ACCESS_KEY: {'✓ Set' if access_key else '✗ Missing'}")
    print(f"BUNNY_PULL_ZONE_URL: {'✓ Set' if pull_zone else '✗ Missing'}")
    
    if not all([storage_zone, access_key, pull_zone]):
        print("\n❌ Missing required Bunny.net configuration!")
        print("Please set the environment variables in Railway or .env file")
        return False
    
    print(f"\nStorage Zone: {storage_zone}")
    print(f"Pull Zone URL: {pull_zone}")
    print(f"Access Key: {'*' * 10 + access_key[-4:] if len(access_key) > 4 else '***'}")
    
    return True

def test_bunnynet_upload():
    """Test actual upload to Bunny.net"""
    print("\n" + "=" * 60)
    print("TESTING BUNNY.NET UPLOAD")
    print("=" * 60)
    
    try:
        from bunnynet_integration import BunnyNetIntegration
        
        # Initialize Bunny.net
        print("Initializing Bunny.net...")
        bunny = BunnyNetIntegration()
        print("✓ Bunny.net initialized successfully")
        
        # Create a test file
        test_file_path = "test_upload.txt"
        with open(test_file_path, 'w') as f:
            f.write("This is a test upload to Bunny.net")
        print(f"✓ Created test file: {test_file_path}")
        
        # Upload the test file
        print("\nUploading test file...")
        result = bunny.upload_file(test_file_path, "test_upload.txt", "tours/test/")
        
        if result.get('success'):
            print(f"✓ Upload successful!")
            print(f"  URL: {result.get('url')}")
            print(f"  Storage path: {result.get('storage_path')}")
            print(f"  Size: {result.get('size')} bytes")
            
            # Test if URL is accessible
            import requests
            response = requests.head(result.get('url'))
            if response.status_code == 200:
                print(f"✓ URL is accessible (HTTP {response.status_code})")
            else:
                print(f"⚠ URL returned HTTP {response.status_code}")
        else:
            print(f"✗ Upload failed: {result.get('error')}")
            return False
            
        # Clean up
        os.remove(test_file_path)
        print("\n✓ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_adapter():
    """Test the storage adapter"""
    print("\n" + "=" * 60)
    print("TESTING STORAGE ADAPTER")
    print("=" * 60)
    
    try:
        from storage_adapter import get_storage
        
        print("Getting storage instance...")
        storage = get_storage()
        backend_name = storage.get_backend_name()
        print(f"✓ Storage adapter initialized with: {backend_name}")
        
        # Create a test file
        test_file_path = "test_adapter.txt"
        with open(test_file_path, 'w') as f:
            f.write("Testing storage adapter upload")
        
        # Test upload through adapter
        print(f"\nUploading through storage adapter ({backend_name})...")
        result = storage.upload_file(test_file_path, "test_adapter.txt", "tours/test/")
        
        if result.get('success'):
            print(f"✓ Upload successful through adapter!")
            print(f"  URL: {result.get('url')}")
        else:
            print(f"✗ Upload failed: {result.get('error')}")
            return False
            
        # Clean up
        os.remove(test_file_path)
        return True
        
    except Exception as e:
        print(f"\n✗ Error testing storage adapter: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run tests
    config_ok = test_bunnynet_config()
    
    if config_ok:
        upload_ok = test_bunnynet_upload()
        adapter_ok = test_storage_adapter()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Configuration: {'✓ Passed' if config_ok else '✗ Failed'}")
        print(f"Direct Upload: {'✓ Passed' if upload_ok else '✗ Failed'}")
        print(f"Storage Adapter: {'✓ Passed' if adapter_ok else '✗ Failed'}")
        
        if all([config_ok, upload_ok, adapter_ok]):
            print("\n✅ All tests passed! Bunny.net is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the errors above.")
    else:
        print("\n❌ Cannot proceed without proper configuration.")