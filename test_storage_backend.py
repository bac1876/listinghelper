#!/usr/bin/env python3
"""
Test script to verify which storage backend is being used
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("STORAGE BACKEND DIAGNOSTIC")
print("=" * 60)

# Check environment variables
env_vars = {
    'USE_BUNNYNET': os.environ.get('USE_BUNNYNET'),
    'BUNNY_STORAGE_ZONE_NAME': os.environ.get('BUNNY_STORAGE_ZONE_NAME'),
    'BUNNY_ACCESS_KEY': os.environ.get('BUNNY_ACCESS_KEY'),
    'BUNNY_PULL_ZONE_URL': os.environ.get('BUNNY_PULL_ZONE_URL'),
    'BUNNY_REGION': os.environ.get('BUNNY_REGION'),
    'IMAGEKIT_PRIVATE_KEY': os.environ.get('IMAGEKIT_PRIVATE_KEY'),
    'IMAGEKIT_PUBLIC_KEY': os.environ.get('IMAGEKIT_PUBLIC_KEY'),
    'IMAGEKIT_URL_ENDPOINT': os.environ.get('IMAGEKIT_URL_ENDPOINT'),
}

print("\n1. Environment Variables:")
for key, value in env_vars.items():
    if value:
        if 'KEY' in key or 'PRIVATE' in key:
            masked = f"{value[:10]}..." if len(value) > 10 else "SET"
        else:
            masked = value
        print(f"  {key}: {masked}")
    else:
        print(f"  {key}: NOT SET")

# Test storage adapter initialization
print("\n2. Storage Adapter Test:")
try:
    from storage_adapter import get_storage, test_storage_initialization
    
    ready, backend = test_storage_initialization()
    print(f"  Storage Ready: {ready}")
    print(f"  Backend: {backend}")
    
    if ready:
        storage = get_storage()
        print(f"  Instance Type: {type(storage)}")
        print(f"  Backend Name: {storage.get_backend_name()}")
        
        # Check the actual backend instance
        if hasattr(storage, 'backend'):
            print(f"  Backend Instance: {type(storage.backend)}")
            if hasattr(storage.backend, '__class__'):
                print(f"  Backend Class: {storage.backend.__class__.__name__}")
        
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test Bunny.net directly
print("\n3. Direct Bunny.net Test:")
try:
    from bunnynet_integration import test_bunnynet_initialization
    result = test_bunnynet_initialization()
    print(f"  Bunny.net Ready: {result}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test ImageKit directly
print("\n4. Direct ImageKit Test:")
try:
    from imagekit_integration import test_imagekit_initialization
    result = test_imagekit_initialization()
    print(f"  ImageKit Ready: {result}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("CONCLUSION:")

# Determine what should be used
if os.environ.get('BUNNY_ACCESS_KEY'):
    print("  Bunny.net credentials are present")
    if os.environ.get('USE_BUNNYNET', '').lower() == 'true':
        print("  USE_BUNNYNET=true - should use Bunny.net")
    else:
        print("  USE_BUNNYNET not set to 'true' - may fall back to ImageKit")
else:
    print("  No Bunny.net credentials found")

if os.environ.get('IMAGEKIT_PRIVATE_KEY'):
    print("  ImageKit credentials are present")
else:
    print("  No ImageKit credentials found")

print("=" * 60)