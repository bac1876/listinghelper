import requests
import json
import time

# Your Railway app URL
APP_URL = "https://virtual-tour-generator-production.up.railway.app"

# Test data with image URLs
test_data = {
    "images": [
        "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=1920&h=1080&fit=crop"
    ],
    "property_details": {
        "address": "123 Test Street",
        "city": "Test City, CA",
        "details1": "Beautiful Home",
        "details2": "Just Listed",
        "agent_name": "Test Agent",
        "agent_email": "test@example.com",
        "agent_phone": "(555) 123-4567",
        "brand_name": "Test Real Estate"
    },
    "settings": {
        "durationPerImage": 5,
        "effectSpeed": "medium",
        "transitionDuration": 1.5
    }
}

print("🚀 Testing GitHub Actions video rendering...")
print(f"Sending request to: {APP_URL}/api/virtual-tour/upload")

# Send the request
response = requests.post(
    f"{APP_URL}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    print(f"\n✅ Success! Job ID: {result.get('job_id')}")
    print(f"Processing time: {result.get('processing_time', 'N/A')}")
    
    if result.get('github_job_id'):
        print(f"\n🎬 GitHub Actions Job ID: {result['github_job_id']}")
        print(f"Check progress at: https://github.com/bac1876/listinghelper/actions")
        print("\nThis should take 2-5 minutes to render with Remotion.")
    else:
        print("\n⚠️  No GitHub Actions job was triggered.")
        print("The app might have used local rendering instead.")
    
    print(f"\nFull response: {json.dumps(result, indent=2)}")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(f"Response: {response.text}")

print("\n📌 Next steps:")
print("1. Check https://github.com/bac1876/listinghelper/actions for the running workflow")
print("2. Wait 2-5 minutes for the video to render")
print("3. Check the job status with the job_id returned above")