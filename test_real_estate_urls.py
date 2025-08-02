#!/usr/bin/env python3
"""
Test GitHub Actions with real estate photos using the upload endpoint
"""

import requests
import json
import os

# Railway app URL
app_url = "https://virtual-tour-generator-production.up.railway.app"

# Real estate photo URLs from Unsplash
real_estate_images = [
    # Living room
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1920&h=1080&fit=crop",
    # Kitchen  
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1920&h=1080&fit=crop",
    # Master bedroom
    "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=1920&h=1080&fit=crop",
    # Bathroom
    "https://images.unsplash.com/photo-1620626011761-996317b8d101?w=1920&h=1080&fit=crop",
    # Exterior
    "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=1920&h=1080&fit=crop",
    # Dining room
    "https://images.unsplash.com/photo-1617806118233-18e1de247200?w=1920&h=1080&fit=crop",
    # Home office
    "https://images.unsplash.com/photo-1611048267451-e6ed903d4a38?w=1920&h=1080&fit=crop",
    # Pool area
    "https://images.unsplash.com/photo-1601760562234-9814eea6663a?w=1920&h=1080&fit=crop"
]

# Property details for a luxury home
test_data = {
    "url_images": real_estate_images,
    "address": "123 Luxury Lane, Beverly Hills, CA 90210",
    "details1": "Call (555) 123-4567 to schedule a showing",
    "details2": "Just Listed - Won't Last Long!",
    "agent_name": "Jane Smith",
    "agent_email": "jane@luxuryrealestate.com",
    "agent_phone": "(555) 123-4567",
    "brand_name": "Luxury Real Estate Group",
    "quality": "medium",  # medium speed for testing
    "use_github_actions": True
}

print("Testing GitHub Actions with real estate photos...")
print(f"Property: {test_data['address']}")
print(f"Agent: {test_data['agent_name']}")
print(f"Images: {len(real_estate_images)} professional property photos")
print("")

# Try the upload endpoint with JSON data
response = requests.post(
    f"{app_url}/api/virtual-tour/upload",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    job_id = result.get('job_id')
    print(f"[SUCCESS] Job created: {job_id}")
    print("")
    print("GitHub Actions will now:")
    print("1. Render video with Ken Burns effects")
    print("2. Add property details overlay")
    print("3. Upload to Cloudinary")
    print("")
    print(f"Expected video URL (once complete):")
    print(f"https://res.cloudinary.com/dib3kbifc/video/upload/tours/{job_id}.mp4")
    print("")
    print("Check status at:")
    print("https://github.com/bac1876/listinghelper/actions")
    print("")
    print("Or run: python check_workflow_simple.py")
else:
    print(f"[ERROR] Request failed: {response.status_code}")
    print(response.text)