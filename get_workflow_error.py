#!/usr/bin/env python3
"""
Get detailed error from the most recent failed GitHub Actions workflow.
"""

import os
import sys
import io
import requests
import json

# Set stdout to handle UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def load_github_token():
    """Load GitHub token from environment or .env file."""
    github_token = os.environ.get('GITHUB_TOKEN')
    
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
    
    return github_token

def get_workflow_error():
    """Get detailed error from failed workflow."""
    
    github_token = load_github_token()
    if not github_token:
        print("[ERROR] GitHub token not found!")
        return
    
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get the most recent workflow run
    owner = 'bac1876'
    repo = 'listinghelper'
    
    # Get the failed run #108
    run_id = 16837936182  # Run #108
    
    print("=" * 60)
    print(f"Fetching detailed logs for workflow run #{run_id}")
    print("=" * 60)
    
    # Get jobs for this run
    jobs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/jobs'
    
    try:
        response = requests.get(jobs_url, headers=headers)
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch jobs: {response.status_code}")
            return
        
        jobs_data = response.json()
        jobs = jobs_data.get('jobs', [])
        
        for job in jobs:
            print(f"\nJob: {job['name']}")
            print("-" * 40)
            
            # Find the failed step
            steps = job.get('steps', [])
            for step in steps:
                if step.get('conclusion') in ['failure', 'cancelled']:
                    print(f"\n[FAILED STEP]: {step['name']}")
                    print(f"Status: {step['status']}")
                    print(f"Conclusion: {step['conclusion']}")
                    
                    # Try to get step logs via the logs URL
                    # Note: This requires special permissions, but we can try
                    step_number = step.get('number')
                    if step_number:
                        print(f"\nTo view full logs for this step:")
                        print(f"https://github.com/{owner}/{repo}/actions/runs/{run_id}/job/{job['id']}#step:{step_number}:1")
        
        # Also try to get the workflow run details
        run_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}'
        run_response = requests.get(run_url, headers=headers)
        
        if run_response.status_code == 200:
            run_data = run_response.json()
            print("\n" + "=" * 60)
            print("Workflow Run Details:")
            print("=" * 60)
            print(f"Name: {run_data.get('name')}")
            print(f"Event: {run_data.get('event')}")
            print(f"Status: {run_data.get('status')}")
            print(f"Conclusion: {run_data.get('conclusion')}")
            print(f"URL: {run_data.get('html_url')}")
            
            # Get the workflow dispatch inputs if available
            if run_data.get('event') == 'workflow_dispatch':
                print("\n" + "-" * 40)
                print("Workflow Inputs:")
                print("-" * 40)
                
                # Try to get the workflow run attempt logs
                attempts_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/attempts/1'
                attempts_response = requests.get(attempts_url, headers=headers)
                
                if attempts_response.status_code == 200:
                    attempts_data = attempts_response.json()
                    if 'inputs' in attempts_data:
                        inputs = attempts_data.get('inputs', {})
                        print(f"Images count: {len(json.loads(inputs.get('images', '[]')))}")
                        print(f"Job ID: {inputs.get('jobId', 'N/A')}")
        
        print("\n" + "=" * 60)
        print("ANALYSIS:")
        print("=" * 60)
        print("\nBased on the workflow failing at 'Render video with Remotion':")
        print("The issue is likely one of:")
        print("1. Remotion composition has errors (check RealEstateTour.tsx)")
        print("2. Images from ImageKit are not accessible from GitHub Actions")
        print("3. Node/NPM dependency issues in the remotion-tours folder")
        print("\nTo debug further, check the workflow logs at:")
        print(f"https://github.com/{owner}/{repo}/actions/runs/{run_id}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    get_workflow_error()