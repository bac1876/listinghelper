#!/usr/bin/env python3
"""
Verify that all required GitHub secrets are configured for the repository.
"""

import os
import sys
import io
import requests

# Set stdout to handle UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def load_github_token():
    """Load GitHub token from environment or .env file."""
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
    
    return github_token

def verify_github_secrets():
    """Check if all required secrets are set in the GitHub repository."""
    
    print("=" * 60)
    print("GitHub Repository Secrets Verification")
    print("=" * 60)
    
    # Get GitHub token
    github_token = load_github_token()
    if not github_token:
        print("[ERROR] GitHub token not found!")
        print("Please set GITHUB_TOKEN in your .env file or environment")
        return False
    
    # Repository details
    owner = 'bac1876'
    repo = 'listinghelper'
    
    # Required secrets
    required_secrets = {
        'ImageKit': [
            'IMAGEKIT_PRIVATE_KEY',
            'IMAGEKIT_PUBLIC_KEY', 
            'IMAGEKIT_URL_ENDPOINT'
        ],
        'Cloudinary (Optional)': [
            'CLOUDINARY_CLOUD_NAME',
            'CLOUDINARY_API_KEY',
            'CLOUDINARY_API_SECRET'
        ]
    }
    
    # Headers for GitHub API
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    print(f"\nChecking repository: {owner}/{repo}")
    print("-" * 60)
    
    # Get repository secrets
    secrets_url = f'https://api.github.com/repos/{owner}/{repo}/actions/secrets'
    
    try:
        response = requests.get(secrets_url, headers=headers)
        
        if response.status_code == 404:
            print("[ERROR] Repository not found or you don't have access")
            print("Make sure the GitHub token has 'repo' scope")
            return False
        elif response.status_code == 403:
            print("[ERROR] Access denied - token may not have 'repo' scope")
            print("Create a new token with 'repo' permissions at:")
            print("https://github.com/settings/tokens")
            return False
        elif response.status_code != 200:
            print(f"[ERROR] Failed to fetch secrets: HTTP {response.status_code}")
            return False
        
        data = response.json()
        existing_secrets = [secret['name'] for secret in data.get('secrets', [])]
        
        print(f"\nFound {len(existing_secrets)} secrets in repository")
        
        all_good = True
        missing_critical = []
        
        # Check each category
        for category, secrets_list in required_secrets.items():
            print(f"\n{category}:")
            
            for secret_name in secrets_list:
                if secret_name in existing_secrets:
                    print(f"  [OK] {secret_name}")
                else:
                    if 'Optional' not in category:
                        print(f"  [MISSING] {secret_name} - CRITICAL!")
                        missing_critical.append(secret_name)
                        all_good = False
                    else:
                        print(f"  [MISSING] {secret_name} (optional)")
        
        # Summary
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS:")
        print("=" * 60)
        
        if all_good:
            print("\n[SUCCESS] All required secrets are configured!")
            print("\nYour GitHub Actions should work properly now.")
            print("Test by creating a new virtual tour and checking:")
            print("  1. GitHub Actions page: https://github.com/bac1876/listinghelper/actions")
            print("  2. Workflow should take 2-5 minutes (not 35 seconds)")
            print("  3. Video should appear in ImageKit: https://imagekit.io/dashboard")
        else:
            print("\n[CRITICAL] Missing required secrets!")
            print("\nMissing secrets that MUST be added:")
            for secret in missing_critical:
                print(f"  - {secret}")
            
            print("\nTo add these secrets:")
            print("1. Go to: https://github.com/bac1876/listinghelper/settings/secrets/actions")
            print("2. Click 'New repository secret' for each missing secret")
            print("3. Copy the values from GITHUB_SECRETS_REQUIRED.md")
            
            print("\nWithout these secrets:")
            print("  - Videos will render but won't upload to ImageKit")
            print("  - Workflows will fail after 35-40 seconds")
            print("  - No videos will be available for download")
        
        # Check last workflow status
        print("\n" + "-" * 60)
        print("Recent Workflow Status:")
        print("-" * 60)
        
        workflow_url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/render-video.yml/runs'
        params = {'per_page': 1}
        
        workflow_response = requests.get(workflow_url, headers=headers, params=params)
        if workflow_response.status_code == 200:
            runs = workflow_response.json().get('workflow_runs', [])
            if runs:
                last_run = runs[0]
                print(f"  Last run: #{last_run['run_number']}")
                print(f"  Status: {last_run['conclusion'] or last_run['status']}")
                print(f"  View at: https://github.com/{owner}/{repo}/actions/runs/{last_run['id']}")
        
        return all_good
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

if __name__ == "__main__":
    success = verify_github_secrets()
    sys.exit(0 if success else 1)