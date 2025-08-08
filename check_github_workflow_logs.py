#!/usr/bin/env python3
"""
Check GitHub Actions workflow logs to identify why videos aren't being created.
"""

import os
import sys
import io

# Set stdout to handle UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests
from datetime import datetime, timedelta

def check_workflow_logs():
    """Check recent GitHub Actions workflow logs for errors."""
    
    # Get GitHub token from environment or .env file
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        # Try to load from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            github_token = os.environ.get('GITHUB_TOKEN')
        except ImportError:
            pass
    
    if not github_token:
        # Try to read directly from .env file
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('GITHUB_TOKEN='):
                        github_token = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            pass
    
    if not github_token:
        print("[ERROR] GitHub token required to check workflow logs")
        print("Set GITHUB_TOKEN environment variable or add to .env file")
        print("Create a token at: https://github.com/settings/tokens")
        return
    
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Repository information
    owner = 'bac1876'
    repo = 'listinghelper'
    workflow_file = 'render-video.yml'
    
    print("=" * 60)
    print("GitHub Actions Workflow Analysis")
    print("=" * 60)
    
    # Get recent workflow runs
    runs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_file}/runs'
    params = {'per_page': 10}
    
    try:
        response = requests.get(runs_url, headers=headers, params=params)
        
        if response.status_code == 401:
            print("[ERROR] Invalid GitHub token")
            return
        elif response.status_code != 200:
            print(f"[ERROR] Failed to fetch workflow runs: {response.status_code}")
            return
        
        runs_data = response.json()
        workflow_runs = runs_data.get('workflow_runs', [])
        
        if not workflow_runs:
            print("No recent workflow runs found")
            return
        
        print(f"\nFound {len(workflow_runs)} recent workflow runs:")
        print("-" * 60)
        
        # Analyze each run
        for run in workflow_runs[:5]:  # Check last 5 runs
            run_id = run['id']
            run_number = run['run_number']
            status = run['status']
            conclusion = run['conclusion']
            created_at = run['created_at']
            updated_at = run['updated_at']
            
            # Parse times
            start_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n### Run #{run_number} (ID: {run_id})")
            print(f"  Status: {status}")
            print(f"  Conclusion: {conclusion}")
            print(f"  Started: {created_at}")
            print(f"  Duration: {duration:.1f} seconds")
            
            # Check if run was too fast (indicates early failure)
            if duration < 120:  # Less than 2 minutes
                print(f"  WARNING: Run completed in {duration:.1f}s (too fast for video rendering)")
            
            # Get jobs for this run
            jobs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs'
            jobs_response = requests.get(jobs_url, headers=headers)
            
            if jobs_response.status_code == 200:
                jobs_data = jobs_response.json()
                jobs = jobs_data.get('jobs', [])
                
                for job in jobs:
                    job_name = job['name']
                    job_status = job['status']
                    job_conclusion = job['conclusion']
                    
                    print(f"\n  Job: {job_name}")
                    print(f"    Status: {job_status}")
                    print(f"    Conclusion: {job_conclusion}")
                    
                    # Check for failed steps
                    steps = job.get('steps', [])
                    failed_steps = [s for s in steps if s.get('conclusion') not in ['success', 'skipped', None]]
                    
                    if failed_steps:
                        print("    [X] FAILED STEPS:")
                        for step in failed_steps:
                            print(f"      - {step['name']}: {step['conclusion']}")
                    
                    # Look for specific steps that should exist
                    step_names = [s['name'] for s in steps]
                    critical_steps = [
                        'Upload to ImageKit',
                        'Render video with Remotion', 
                        'Upload result as artifact'
                    ]
                    
                    for critical in critical_steps:
                        if not any(critical in name for name in step_names):
                            print(f"    [!] Missing critical step: {critical}")
                        else:
                            # Find and check the step
                            for step in steps:
                                if critical in step['name']:
                                    if step['conclusion'] != 'success':
                                        print(f"    [X] {critical}: {step['conclusion']}")
                                    else:
                                        print(f"    [OK] {critical}: success")
            
            # Try to get logs for failed runs
            if conclusion == 'failure':
                print(f"\n  Attempting to fetch error logs...")
                logs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs'
                # Note: Logs require special permissions and return a redirect
                print(f"  View full logs at: https://github.com/{owner}/{repo}/actions/runs/{run_id}")
        
        # Summary
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY:")
        print("=" * 60)
        
        # Count conclusions
        success_count = sum(1 for r in workflow_runs if r['conclusion'] == 'success')
        failure_count = sum(1 for r in workflow_runs if r['conclusion'] == 'failure')
        
        print(f"Recent runs: {success_count} successful, {failure_count} failed")
        
        # Check for pattern
        all_fast = all((datetime.fromisoformat(r['updated_at'].replace('Z', '+00:00')) - 
                       datetime.fromisoformat(r['created_at'].replace('Z', '+00:00'))).total_seconds() < 120 
                      for r in workflow_runs[:3])
        
        if all_fast:
            print("\n[WARNING] All recent runs completed too quickly!")
            print("This suggests workflows are failing before video rendering.")
            print("\nLikely causes:")
            print("1. Missing ImageKit secrets in GitHub repository")
            print("2. Remotion rendering failing immediately")
            print("3. Dependencies not installing correctly")
            
            print("\n[ACTION REQUIRED]:")
            print("Add these secrets to GitHub (Settings → Secrets → Actions):")
            print("  - IMAGEKIT_PRIVATE_KEY")
            print("  - IMAGEKIT_PUBLIC_KEY")
            print("  - IMAGEKIT_URL_ENDPOINT")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    check_workflow_logs()