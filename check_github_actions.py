"""
Check GitHub Actions workflow runs to diagnose intermittent failures
"""
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def check_recent_workflows():
    """Check recent GitHub Actions workflow runs"""
    
    github_token = os.environ.get('GITHUB_TOKEN')
    github_owner = os.environ.get('GITHUB_OWNER')
    github_repo = os.environ.get('GITHUB_REPO')
    
    if not all([github_token, github_owner, github_repo]):
        print("Missing GitHub credentials in .env")
        return
    
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get recent workflow runs
    url = f'https://api.github.com/repos/{github_owner}/{github_repo}/actions/runs'
    params = {
        'per_page': 10,
        'status': 'all'  # Get all statuses
    }
    
    print("=" * 60)
    print("RECENT GITHUB ACTIONS WORKFLOW RUNS")
    print("=" * 60)
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        runs = data.get('workflow_runs', [])
        
        if not runs:
            print("No workflow runs found")
            return
        
        print(f"\nFound {len(runs)} recent workflow runs:\n")
        
        for run in runs:
            created = datetime.strptime(run['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            updated = datetime.strptime(run['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            duration = (updated - created).total_seconds()
            
            print(f"Run #{run['run_number']}: {run['name']}")
            print(f"  Status: {run['status']} | Conclusion: {run.get('conclusion', 'N/A')}")
            print(f"  Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration: {duration:.0f} seconds")
            print(f"  URL: {run['html_url']}")
            
            # Check for errors in the run
            if run.get('conclusion') == 'failure':
                print(f"  [FAILED] - Check logs at {run['html_url']}")
            elif run.get('conclusion') == 'cancelled':
                print(f"  [CANCELLED] - May indicate timeout or manual cancellation")
            elif run['status'] == 'in_progress':
                print(f"  [IN PROGRESS] - Still running")
            elif run.get('conclusion') == 'success':
                print(f"  [SUCCESS]")
            
            print()
    
    elif response.status_code == 401:
        print("[ERROR] GitHub token is invalid or expired")
        print("Generate a new token at: https://github.com/settings/tokens")
        runs = []  # Initialize empty runs list
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        runs = []  # Initialize empty runs list
    
    # Check API rate limit
    print("\n" + "=" * 60)
    print("GITHUB API RATE LIMIT")
    print("=" * 60)
    
    rate_url = "https://api.github.com/rate_limit"
    rate_response = requests.get(rate_url, headers=headers)
    
    if rate_response.status_code == 200:
        rate_data = rate_response.json()
        core = rate_data['rate']
        
        print(f"Remaining API calls: {core['remaining']}/{core['limit']}")
        
        if core['remaining'] < 100:
            print("[WARNING] Low API rate limit remaining!")
        
        reset_time = datetime.fromtimestamp(core['reset'])
        print(f"Resets at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if workflows are queued
    print("\n" + "=" * 60)
    print("WORKFLOW QUEUE STATUS")
    print("=" * 60)
    
    queued_count = sum(1 for run in runs if run['status'] == 'queued')
    in_progress_count = sum(1 for run in runs if run['status'] == 'in_progress')
    
    if queued_count > 0:
        print(f"[WARNING] {queued_count} workflows are QUEUED - may indicate concurrency limits")
    if in_progress_count > 1:
        print(f"[WARNING] {in_progress_count} workflows are IN PROGRESS - may cause delays")
    
    if queued_count == 0 and in_progress_count <= 1:
        print("[OK] No queue congestion detected")

if __name__ == "__main__":
    check_recent_workflows()