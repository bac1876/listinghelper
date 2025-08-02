#!/usr/bin/env python3
"""
Check GitHub Actions logs to find the actual video URL
"""

import webbrowser

print("📋 To find your video URL from GitHub Actions:\n")

print("1. Go to your latest successful workflow:")
print("   https://github.com/bac1876/listinghelper/actions\n")

print("2. Click on the successful run (green checkmark)\n")

print("3. Click on 'render-video' job\n")

print("4. Expand the 'Upload to Cloudinary' step\n")

print("5. Look for a line that says:")
print("   • 'Successfully uploaded to: [URL]'")
print("   • or 'VIDEO_URL=[URL]'\n")

print("The URL shown there is your actual video URL!\n")

open_browser = input("Would you like me to open GitHub Actions in your browser? (y/n): ")
if open_browser.lower() == 'y':
    webbrowser.open("https://github.com/bac1876/listinghelper/actions")
    
print("\n💡 Alternative: Check your Cloudinary dashboard directly:")
print("   https://console.cloudinary.com/console/c-95a009c94be3af017172dc0e5d34a5/media_library/folders/home")

open_cloudinary = input("\nOpen Cloudinary dashboard? (y/n): ")
if open_cloudinary.lower() == 'y':
    webbrowser.open("https://console.cloudinary.com/console/c-95a009c94be3af017172dc0e5d34a5/media_library/folders/home")