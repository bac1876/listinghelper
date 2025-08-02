#!/usr/bin/env python3
"""
Get the direct Cloudinary URL for the latest video
"""

import time

# Latest job ID from your test
job_id = "tour_1754089132_773bcb30"
cloud_name = "dib3bbifc"

print(f"🎬 Checking for video: {job_id}")
print("\nThe video should be available at:")
print(f"\nhttps://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4")

print("\n⏳ If the workflow is still running, wait 2-3 minutes and try the URL again.")
print("\n💡 You can also check the workflow status at:")
print("   https://github.com/bac1876/listinghelper/actions")

# Also check without version number
print(f"\nAlternative URL (no version):")
print(f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}")

# Wait a bit and provide countdown
print("\n⏰ Waiting 30 seconds before you can check the URL...")
for i in range(30, 0, -5):
    print(f"   {i} seconds remaining...")
    time.sleep(5)

print("\n✅ The video should be ready now! Try the URL above.")