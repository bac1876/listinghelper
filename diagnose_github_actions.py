#!/usr/bin/env python3
"""
GitHub Actions Diagnostic Tool
Helps diagnose issues with video rendering via GitHub Actions
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from github_actions_integration import GitHubActionsIntegration

def check_github_config():
    """Check if GitHub configuration is set up correctly"""
    print("🔍 Checking GitHub Configuration...")
    print("=" * 60)
    
    required_vars = ['GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO']
    config_ok = True
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive info
            if var == 'GITHUB_TOKEN':
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            config_ok = False
    
    return config_ok

def check_recent_workflows(github_api):
    """Check recent workflow runs"""
    print("\n🔍 Checking Recent Workflow Runs...")
    print("=" * 60)
    
    try:
        runs_url = f"{github_api.base_url}/actions/workflows/{github_api.workflow_file}/runs"
        response = requests.get(runs_url, headers=github_api.headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch workflow runs: {response.status_code}")
            return []
        
        runs = response.json().get('workflow_runs', [])[:5]  # Last 5 runs
        
        print(f"Found {len(runs)} recent runs:\n")
        
        job_ids = []
        for i, run in enumerate(runs, 1):
            print(f"{i}. Run #{run['run_number']}")
            print(f"   Status: {run['status']} ({run['conclusion'] or 'in progress'})")
            print(f"   Created: {run['created_at']}")
            print(f"   URL: {run['html_url']}")
            
            # Try to extract job ID from run name or artifacts
            if run['status'] == 'completed':
                artifacts_response = requests.get(run['artifacts_url'], headers=github_api.headers)
                if artifacts_response.status_code == 200:
                    artifacts = artifacts_response.json().get('artifacts', [])
                    for artifact in artifacts:
                        if 'render-result-' in artifact['name']:
                            job_id = artifact['name'].replace('render-result-', '')
                            job_ids.append(job_id)
                            print(f"   Job ID: {job_id}")
            
            print()
        
        return job_ids
        
    except Exception as e:
        print(f"❌ Error checking workflows: {e}")
        return []

def diagnose_job(github_api, job_id):
    """Diagnose a specific job"""
    print(f"\n🔍 Diagnosing Job: {job_id}")
    print("=" * 60)
    
    # Check job status
    result = github_api.check_job_status(job_id)
    
    print(f"\nJob Status Check:")
    print(json.dumps(result, indent=2))
    
    if result.get('success'):
        if result.get('status') == 'completed':
            print(f"\n✅ Job completed successfully")
            print(f"   Video URL: {result.get('video_url', 'N/A')}")
        else:
            print(f"\n⏳ Job status: {result.get('status')}")
    else:
        print(f"\n❌ Job check failed: {result.get('error')}")
        
        # Check for raw content if JSON parsing failed
        if 'raw_content' in result:
            print(f"\nRaw result.json content:")
            print(result['raw_content'])
            
            # Try to identify the issue
            if '"videoUrl":,' in result['raw_content'] or '"videoUrl": ,' in result['raw_content']:
                print("\n🔴 ISSUE IDENTIFIED: Empty VIDEO_URL in result.json")
                print("   This means Cloudinary upload likely failed")
                print("\n   Possible causes:")
                print("   1. Cloudinary credentials mismatch")
                print("   2. Video file too large")
                print("   3. Network timeout during upload")
                print("   4. Invalid video format")
    
    return result

def check_cloudinary_config():
    """Check if Cloudinary is properly configured"""
    print("\n🔍 Checking Cloudinary Configuration...")
    print("=" * 60)
    
    cloudinary_vars = ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET']
    config_ok = True
    
    for var in cloudinary_vars:
        value = os.environ.get(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:]
                print(f"✅ {var}: {masked}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            config_ok = False
    
    return config_ok

def main():
    print("""
GitHub Actions Diagnostic Tool
==============================

This tool helps diagnose issues with GitHub Actions video rendering.
""")
    
    # Check GitHub config
    if not check_github_config():
        print("\n❌ GitHub configuration is incomplete!")
        print("\nTo fix this, set the following environment variables:")
        print("- GITHUB_TOKEN: Your GitHub personal access token")
        print("- GITHUB_OWNER: Your GitHub username or org")
        print("- GITHUB_REPO: Your repository name")
        return
    
    # Check Cloudinary config
    cloudinary_ok = check_cloudinary_config()
    if not cloudinary_ok:
        print("\n⚠️ Cloudinary configuration is incomplete!")
        print("This may cause video upload failures.")
    
    try:
        # Initialize GitHub API
        github_api = GitHubActionsIntegration()
        
        # Check workflow status
        workflow_status = github_api.get_workflow_status()
        if workflow_status.get('success'):
            print(f"\n✅ Workflow is {workflow_status['workflow']['state']}")
        else:
            print(f"\n❌ Failed to check workflow: {workflow_status.get('error')}")
        
        # Check recent runs
        recent_job_ids = check_recent_workflows(github_api)
        
        # Offer to diagnose specific job
        print("\nOptions:")
        print("1. Enter a specific job ID to diagnose")
        if recent_job_ids:
            print("2. Diagnose most recent job")
            print("3. Diagnose all recent jobs")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            job_id = input("Enter job ID: ").strip()
            if job_id:
                diagnose_job(github_api, job_id)
        elif choice == '2' and recent_job_ids:
            diagnose_job(github_api, recent_job_ids[0])
        elif choice == '3' and recent_job_ids:
            for job_id in recent_job_ids:
                diagnose_job(github_api, job_id)
                print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()