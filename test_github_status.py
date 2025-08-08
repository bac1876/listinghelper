#!/usr/bin/env python3
"""
Test GitHub Actions workflow status detection with the fixed code.
"""

import os
import sys

# Set GitHub credentials
os.environ['GITHUB_TOKEN'] = input("Enter GitHub token (or press Enter to skip): ").strip()
os.environ['GITHUB_OWNER'] = 'bac1876'
os.environ['GITHUB_REPO'] = 'listinghelper'

if not os.environ.get('GITHUB_TOKEN'):
    print("[INFO] No GitHub token provided, some tests will be skipped")
    print("To get a token: https://github.com/settings/tokens")
    sys.exit(1)

def test_workflow_status():
    """Test the fixed GitHub Actions status detection."""
    
    from github_actions_integration import GitHubActionsIntegration
    
    print("=" * 60)
    print("Testing GitHub Actions Workflow Status Detection")
    print("=" * 60)
    
    try:
        gh = GitHubActionsIntegration()
        
        if not gh.is_valid:
            print("[FAIL] GitHub token is invalid")
            return
        
        print("[OK] Connected to GitHub")
        
        # Test with known job IDs from our ImageKit check
        test_jobs = [
            'tour_1754654028_26a2e553',  # Has video in ImageKit
            'tour_1754655315_c197aad2',  # Has video in ImageKit  
            'tour_1754656315_0d6ba5bd',  # Has video in ImageKit
            'tour_1754671966_c924fead',  # From the Railway logs
        ]
        
        print("\nTesting workflow status for known jobs:")
        print("-" * 60)
        
        for job_id in test_jobs:
            print(f"\nJob ID: {job_id}")
            
            # Test the fixed get_workflow_status method
            status = gh.get_workflow_status(job_id)
            print(f"  Status: {status}")
            
            if status == 'completed':
                print("  [OK] Workflow detected as completed")
                
                # Try to get the artifact
                artifact = gh.get_workflow_artifact(job_id)
                if artifact:
                    print(f"  [OK] Found artifact with video URL: {artifact.get('videoUrl', 'N/A')}")
                else:
                    print("  [INFO] No artifact found (might be expired)")
                    
            elif status == 'queued':
                print("  [WARNING] Still showing as queued (old bug)")
            elif status == 'unknown':
                print("  [INFO] Workflow not found or too old")
            else:
                print(f"  [INFO] Status: {status}")
        
        # Also check recent workflows
        print("\n" + "=" * 60)
        print("Checking recent workflow runs:")
        print("-" * 60)
        
        info = gh.get_workflow_info()
        if info.get('success'):
            print(f"Workflow: {info.get('workflow_name')}")
            print(f"Recent runs: {info.get('recent_runs_count', 0)}")
            
            recent = info.get('recent_runs', [])
            for run in recent[:5]:
                print(f"\n  Run #{run.get('run_number', 'N/A')}")
                print(f"    Status: {run.get('status')}")
                print(f"    Conclusion: {run.get('conclusion')}")
                print(f"    Created: {run.get('created_at')}")
                
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow_status()