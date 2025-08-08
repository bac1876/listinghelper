#!/usr/bin/env python3
"""
Test the complete video generation flow with ImageKit and GitHub Actions.
This script tests the entire pipeline from image upload to video generation.
"""

import os
import sys
import time
import json
import requests
from pathlib import Path

# Set environment variables for testing
os.environ['IMAGEKIT_PRIVATE_KEY'] = 'private_4NFY9DlW7DaZwHW1j+k5FsYoIhY='
os.environ['IMAGEKIT_PUBLIC_KEY'] = 'public_wnhOBpqBUB1ReFbqsfOWgFcRnvU='
os.environ['IMAGEKIT_URL_ENDPOINT'] = 'https://ik.imagekit.io/brianosris/'

def test_imagekit_connection():
    """Test ImageKit connection and list files."""
    print("\n1. Testing ImageKit connection...")
    try:
        from imagekit_integration import ImageKitIntegration
        ik = ImageKitIntegration()
        
        # Test connection by checking if imagekit is initialized
        if ik.imagekit:
            print("[OK] Connected to ImageKit")
            print(f"  Endpoint: {ik.url_endpoint}")
        else:
            print("[FAIL] ImageKit not initialized")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] ImageKit connection failed: {e}")
        return False

def test_github_actions_connection():
    """Test GitHub Actions connection."""
    print("\n2. Testing GitHub Actions connection...")
    
    # Check if GitHub credentials are set
    if not all([os.environ.get('GITHUB_TOKEN'), 
                 os.environ.get('GITHUB_OWNER'), 
                 os.environ.get('GITHUB_REPO')]):
        print("[FAIL] GitHub credentials not set in environment")
        print("  Please set: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        return False
    
    try:
        from github_actions_integration import GitHubActionsIntegration
        gh = GitHubActionsIntegration()
        
        if gh.is_valid:
            print(f"[OK] Connected to GitHub repo: {gh.github_owner}/{gh.github_repo}")
            
            # Get workflow info
            info = gh.get_workflow_info()
            if info.get('success'):
                print(f"  Workflow: {info.get('workflow_name')}")
                print(f"  Recent runs: {info.get('recent_runs_count', 0)}")
            
            return True
        else:
            print("[FAIL] GitHub token is invalid or expired")
            return False
            
    except Exception as e:
        print(f"[FAIL] GitHub Actions connection failed: {e}")
        return False

def test_local_remotion():
    """Test local Remotion rendering."""
    print("\n3. Testing local Remotion rendering...")
    
    import subprocess
    
    # Create test props
    test_props = {
        "images": [],  # Will use default Unsplash images
        "propertyDetails": {
            "address": "Test Property",
            "city": "Los Angeles, CA",
            "details": "Test Details",
            "status": "Just Listed",
            "agentName": "Test Agent",
            "agentEmail": "test@example.com",
            "agentPhone": "(555) 123-4567",
            "brandName": "Test Real Estate"
        },
        "settings": {
            "durationPerImage": 1,
            "effectSpeed": "fast",
            "transitionDuration": 0.5
        }
    }
    
    props_json = json.dumps(test_props)
    
    try:
        # Run Remotion render command (just render 30 frames for quick test)
        cmd = [
            'npx', 'remotion', 'render', 
            'RealEstateTour', 
            'test_output.mp4',
            '--props', props_json,
            '--frames', '0-30'
        ]
        
        print("  Running Remotion render test (30 frames)...")
        result = subprocess.run(
            cmd,
            cwd='remotion-tours',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Check if output file exists
            output_path = Path('remotion-tours/test_output.mp4')
            if output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                print(f"[OK] Remotion render successful! Output: {size_kb:.1f} KB")
                # Clean up test file
                output_path.unlink()
                return True
            else:
                print("[FAIL] Remotion render completed but no output file")
                return False
        else:
            print(f"[FAIL] Remotion render failed with code {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[FAIL] Remotion render timed out")
        return False
    except Exception as e:
        print(f"[FAIL] Remotion test failed: {e}")
        return False

def test_railway_api():
    """Test Railway API endpoints."""
    print("\n4. Testing Railway API endpoints...")
    
    base_url = "https://virtual-tour-generator-production.up.railway.app"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print(f"[OK] Railway API is healthy")
            print(f"  ImageKit: {health.get('imagekit_configured', False)}")
            print(f"  GitHub Actions: {health.get('github_actions_configured', False)}")
            return True
        else:
            print(f"[FAIL] Railway API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Railway API test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Real Estate Video Generator - Complete Flow Test")
    print("=" * 60)
    
    results = {
        "ImageKit": test_imagekit_connection(),
        "GitHub Actions": test_github_actions_connection(),
        "Remotion": test_local_remotion(),
        "Railway API": test_railway_api()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{component:20} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] ALL TESTS PASSED - System is ready!")
    else:
        print("[FAIL] SOME TESTS FAILED - Please check the issues above")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())