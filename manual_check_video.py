#!/usr/bin/env python3
"""
Manually check for your video on Cloudinary
"""

print("🎬 Your video should be available at one of these URLs:\n")

# The job IDs from your tests
job_ids = [
    "tour_1754086678_19d094f3",
    "tour_1754085152_10a42c60",
    "tour_1754084696_1efc301c"
]

# Your Cloudinary cloud name
cloud_name = "dib3bbifc"

print("Check these URLs in your browser:\n")

for job_id in job_ids:
    url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_id}.mp4"
    print(f"• {url}")

print("\n💡 The most recent successful render was likely:")
print(f"   https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job_ids[0]}.mp4")

print("\nIf these don't work, check your Cloudinary dashboard at:")
print(f"   https://console.cloudinary.com/console/{cloud_name}/media_library/folders/tours")