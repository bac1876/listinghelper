#!/usr/bin/env python3
"""
Test Cloudinary connection using Railway app
"""

import requests
import json

print("🔍 Testing Cloudinary through Railway app...\n")

# Your Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Test with a simple image URL
test_data = {
    "images": ["https://via.placeholder.com/150"],
    "test_cloudinary": True
}

print("Sending test request to Railway app...")
response = requests.post(
    f"{app_url}/api/virtual-tour/test-cloudinary",
    json=test_data
)

if response.status_code == 404:
    print("❌ Test endpoint not found")
    print("\nThis suggests the Cloudinary credentials in GitHub Secrets")
    print("don't match the ones in Railway.")
    print("\nTo fix this:")
    print("1. Go to your Cloudinary dashboard")
    print("2. Copy the EXACT credentials")
    print("3. Update both:")
    print("   - GitHub Secrets (for Actions)")
    print("   - Railway environment variables")
    print("\nMake sure they're EXACTLY the same, including:")
    print("   - No extra spaces")
    print("   - Correct capitalization")
    print("   - Complete secret (not truncated)")
else:
    print(f"Response: {response.status_code}")
    print(response.text)