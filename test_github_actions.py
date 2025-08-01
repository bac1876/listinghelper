#!/usr/bin/env python3
"""
Test script for GitHub Actions integration
This script tests the GitHub Actions workflow for Remotion video rendering
"""

import os
import time
import json
from github_actions_integration import GitHubActionsIntegration

def test_github_actions():
    print("=== Testing GitHub Actions Integration ===\n")
    
    # Check environment variables
    required_vars = ['GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables and try again.")
        return
    
    try:
        # Initialize GitHub Actions integration
        print("🔧 Initializing GitHub Actions integration...")
        github = GitHubActionsIntegration()
        print("✅ GitHub Actions integration initialized\n")
        
        # Check workflow status
        print("📊 Checking workflow status...")
        status = github.get_workflow_status()
        if status['success']:
            print(f"✅ Workflow found: {status['workflow']['name']}")
            print(f"   State: {status['workflow']['state']}")
        else:
            print(f"❌ Error checking workflow: {status['error']}")
            return
        
        # Test with sample images
        print("\n🎬 Triggering test video render...")
        test_images = [
            "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1920&h=1080&fit=crop",
            "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=1920&h=1080&fit=crop"
        ]
        
        test_property = {
            "address": "123 Test Street",
            "city": "Test City, CA",
            "details1": "Beautiful Test Property",
            "details2": "Testing GitHub Actions",
            "agent_name": "Test Agent",
            "agent_email": "test@example.com",
            "agent_phone": "(555) 123-4567",
            "brand_name": "Test Real Estate"
        }
        
        test_settings = {
            "durationPerImage": 5,
            "effectSpeed": "medium",
            "transitionDuration": 1
        }
        
        # Trigger the workflow
        result = github.trigger_video_render(test_images, test_property, test_settings)
        
        if result['success']:
            job_id = result['job_id']
            print(f"✅ Workflow triggered successfully!")
            print(f"   Job ID: {job_id}")
            print(f"\n📍 Check progress at:")
            print(f"   https://github.com/{os.environ['GITHUB_OWNER']}/{os.environ['GITHUB_REPO']}/actions")
            
            # Poll for completion
            print("\n⏳ Waiting for video to render (this may take 2-5 minutes)...")
            print("   Polling every 30 seconds...\n")
            
            max_attempts = 20  # 10 minutes max
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(30)
                attempt += 1
                
                status = github.check_job_status(job_id)
                print(f"   Attempt {attempt}/{max_attempts}: {status.get('status', 'unknown')}")
                
                if status.get('status') == 'completed':
                    print(f"\n✅ Video rendered successfully!")
                    print(f"   Video URL: {status.get('video_url')}")
                    print(f"   Duration: {status.get('duration')} seconds")
                    print(f"   Render time: {status.get('render_time')}")
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Video rendering failed")
                    print(f"   Error: {status.get('error')}")
                    break
            else:
                print(f"\n⏱️ Timeout: Video is still rendering. Check GitHub Actions for status.")
        else:
            print(f"❌ Failed to trigger workflow: {result['error']}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_github_actions()