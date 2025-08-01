#!/usr/bin/env python3
"""
Diagnostic script to check GitHub Actions configuration
"""

import os
import sys

def check_configuration():
    print("=== Configuration Check for Video Rendering ===\n")
    
    # Check GitHub Actions configuration
    print("1. GitHub Actions Configuration:")
    github_vars = {
        'USE_GITHUB_ACTIONS': os.environ.get('USE_GITHUB_ACTIONS', 'not set'),
        'GITHUB_TOKEN': 'set' if os.environ.get('GITHUB_TOKEN') else 'NOT SET',
        'GITHUB_OWNER': os.environ.get('GITHUB_OWNER', 'NOT SET'),
        'GITHUB_REPO': os.environ.get('GITHUB_REPO', 'NOT SET')
    }
    
    all_set = True
    for var, value in github_vars.items():
        status = "✅" if value not in ['not set', 'NOT SET'] else "❌"
        print(f"   {status} {var}: {value}")
        if value in ['not set', 'NOT SET']:
            all_set = False
    
    if all_set and github_vars['USE_GITHUB_ACTIONS'] == 'true':
        print("\n   ✅ GitHub Actions is ENABLED and configured")
    else:
        print("\n   ❌ GitHub Actions is NOT properly configured")
        print("   The app will use local FFmpeg or Cloudinary instead")
    
    # Check Cloudinary configuration
    print("\n2. Cloudinary Configuration (Fallback):")
    cloudinary_vars = {
        'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', 'NOT SET'),
        'CLOUDINARY_API_KEY': 'set' if os.environ.get('CLOUDINARY_API_KEY') else 'NOT SET',
        'CLOUDINARY_API_SECRET': 'set' if os.environ.get('CLOUDINARY_API_SECRET') else 'NOT SET'
    }
    
    cloudinary_set = True
    for var, value in cloudinary_vars.items():
        status = "✅" if value != 'NOT SET' else "❌"
        print(f"   {status} {var}: {value}")
        if value == 'NOT SET':
            cloudinary_set = False
    
    # Check Creatomate (old system)
    print("\n3. Creatomate Configuration (Old System):")
    creatomate_vars = {
        'USE_CREATOMATE': os.environ.get('USE_CREATOMATE', 'not set'),
        'CREATOMATE_API_KEY': 'set' if os.environ.get('CREATOMATE_API_KEY') else 'NOT SET',
        'CREATOMATE_TEMPLATE_ID': os.environ.get('CREATOMATE_TEMPLATE_ID', 'NOT SET')
    }
    
    for var, value in creatomate_vars.items():
        status = "⚠️" if value not in ['not set', 'NOT SET'] else "✅"
        print(f"   {status} {var}: {value}")
    
    if creatomate_vars['USE_CREATOMATE'] == 'true':
        print("\n   ⚠️ WARNING: Creatomate is still enabled! This may conflict with GitHub Actions.")
    
    # Summary
    print("\n=== Summary ===")
    if all_set and github_vars['USE_GITHUB_ACTIONS'] == 'true':
        print("✅ GitHub Actions is properly configured for video rendering")
        print("   - Videos will be rendered using Remotion on GitHub")
        print("   - You get 2,000 free minutes per month")
    elif cloudinary_set:
        print("⚠️ GitHub Actions not configured, using Cloudinary fallback")
        print("   - Videos will be created using Cloudinary transformations")
        print("   - Limited Ken Burns effects")
    else:
        print("⚠️ Only local FFmpeg rendering is available")
        print("   - Videos will be created locally")
        print("   - This is fast but basic")
    
    print("\n=== What You're Seeing ===")
    print("If you got a 0.35 second render time, the app is likely:")
    print("1. Only creating the HTML viewer (no actual video)")
    print("2. Using local FFmpeg (very fast but basic)")
    print("3. NOT using GitHub Actions (which takes 2-5 minutes)")
    
    print("\n=== Next Steps ===")
    if not all_set:
        print("To enable GitHub Actions rendering:")
        print("1. Add the GitHub secrets to your repository")
        print("2. Create a Personal Access Token")
        print("3. Add these Railway environment variables:")
        print("   - USE_GITHUB_ACTIONS=true")
        print("   - GITHUB_TOKEN=<your_token>")
        print("   - GITHUB_OWNER=bac1876")
        print("   - GITHUB_REPO=listinghelper")

if __name__ == "__main__":
    check_configuration()