"""
Script to verify GitHub and Cloudinary configuration for video rendering
This will help identify why videos aren't being created in Cloudinary
"""
import os
import sys
import requests
import cloudinary
import cloudinary.api

def check_env_variables():
    """Check if required environment variables are set"""
    print("="*60)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("="*60)
    
    required_vars = {
        'GitHub Actions': [
            'GITHUB_TOKEN',
            'GITHUB_OWNER', 
            'GITHUB_REPO',
            'USE_GITHUB_ACTIONS'
        ],
        'Cloudinary': [
            'CLOUDINARY_CLOUD_NAME',
            'CLOUDINARY_API_KEY',
            'CLOUDINARY_API_SECRET'
        ]
    }
    
    all_good = True
    
    for category, vars in required_vars.items():
        print(f"\n{category}:")
        for var in vars:
            value = os.environ.get(var)
            if value:
                if 'SECRET' in var or 'TOKEN' in var or 'KEY' in var:
                    # Don't print sensitive values
                    print(f"  ✓ {var}: [CONFIGURED - {len(value)} chars]")
                else:
                    print(f"  ✓ {var}: {value}")
            else:
                print(f"  ✗ {var}: NOT SET")
                all_good = False
    
    return all_good

def check_github_secrets():
    """Check if GitHub repository has required secrets"""
    print("\n" + "="*60)
    print("CHECKING GITHUB REPOSITORY SECRETS")
    print("="*60)
    
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('GITHUB_OWNER')
    repo = os.environ.get('GITHUB_REPO')
    
    if not all([token, owner, repo]):
        print("✗ Cannot check GitHub secrets - missing GITHUB_TOKEN, OWNER, or REPO")
        return False
    
    # Check if we can access the repository
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get repository info
    repo_url = f'https://api.github.com/repos/{owner}/{repo}'
    try:
        response = requests.get(repo_url, headers=headers)
        if response.status_code == 200:
            print(f"✓ Repository found: {owner}/{repo}")
        else:
            print(f"✗ Cannot access repository: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error accessing GitHub API: {e}")
        return False
    
    # List secrets (we can't see values, just names)
    secrets_url = f'https://api.github.com/repos/{owner}/{repo}/actions/secrets'
    try:
        response = requests.get(secrets_url, headers=headers)
        if response.status_code == 200:
            secrets = response.json()
            secret_names = [s['name'] for s in secrets.get('secrets', [])]
            
            required_secrets = [
                'CLOUDINARY_CLOUD_NAME',
                'CLOUDINARY_API_KEY',
                'CLOUDINARY_API_SECRET'
            ]
            
            print("\nRequired GitHub Secrets:")
            all_present = True
            for secret in required_secrets:
                if secret in secret_names:
                    print(f"  ✓ {secret}: CONFIGURED")
                else:
                    print(f"  ✗ {secret}: NOT FOUND")
                    all_present = False
            
            if secret_names:
                other_secrets = [s for s in secret_names if s not in required_secrets]
                if other_secrets:
                    print(f"\nOther secrets found: {', '.join(other_secrets)}")
            
            return all_present
        else:
            print(f"✗ Cannot list repository secrets (need admin access): {response.status_code}")
            print("  You need to manually verify these secrets are set in GitHub:")
            print("  - CLOUDINARY_CLOUD_NAME")
            print("  - CLOUDINARY_API_KEY")
            print("  - CLOUDINARY_API_SECRET")
            return False
    except Exception as e:
        print(f"✗ Error checking secrets: {e}")
        return False

def check_cloudinary_connection():
    """Test Cloudinary connection and configuration"""
    print("\n" + "="*60)
    print("TESTING CLOUDINARY CONNECTION")
    print("="*60)
    
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    api_key = os.environ.get('CLOUDINARY_API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    
    if not all([cloud_name, api_key, api_secret]):
        print("✗ Missing Cloudinary credentials")
        return False
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    
    try:
        # Try to get account usage (simple API call to test connection)
        result = cloudinary.api.usage()
        print(f"✓ Cloudinary connection successful!")
        print(f"  Cloud name: {cloud_name}")
        print(f"  Plan: {result.get('plan', 'Unknown')}")
        print(f"  Credits used: {result.get('credits', {}).get('usage', 'Unknown')}")
        
        # Check if tours folder exists
        try:
            resources = cloudinary.api.resources(type='upload', prefix='tours/')
            print(f"  Tours folder has {len(resources.get('resources', []))} videos")
        except:
            print("  Tours folder not found or empty")
        
        return True
    except Exception as e:
        print(f"✗ Cloudinary connection failed: {e}")
        return False

def check_github_workflow():
    """Check if GitHub Actions workflow exists and recent runs"""
    print("\n" + "="*60)
    print("CHECKING GITHUB ACTIONS WORKFLOW")
    print("="*60)
    
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('GITHUB_OWNER')
    repo = os.environ.get('GITHUB_REPO')
    
    if not all([token, owner, repo]):
        print("✗ Cannot check workflow - missing credentials")
        return False
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Check workflow file exists
    workflow_file = '.github/workflows/render-video.yml'
    file_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{workflow_file}'
    
    try:
        response = requests.get(file_url, headers=headers)
        if response.status_code == 200:
            print(f"✓ Workflow file exists: {workflow_file}")
        else:
            print(f"✗ Workflow file not found: {workflow_file}")
            return False
    except Exception as e:
        print(f"✗ Error checking workflow file: {e}")
        return False
    
    # Check recent workflow runs
    runs_url = f'https://api.github.com/repos/{owner}/{repo}/actions/runs?per_page=5'
    try:
        response = requests.get(runs_url, headers=headers)
        if response.status_code == 200:
            runs = response.json().get('workflow_runs', [])
            
            if runs:
                print(f"\nRecent workflow runs:")
                for run in runs[:5]:
                    status = run.get('status')
                    conclusion = run.get('conclusion', 'pending')
                    created = run.get('created_at', '')[:10]
                    name = run.get('name', 'Unknown')
                    
                    status_icon = "✓" if conclusion == "success" else "✗" if conclusion == "failure" else "⏳"
                    print(f"  {status_icon} {created} - {name}: {status}/{conclusion}")
            else:
                print("  No recent workflow runs found")
                
            return True
        else:
            print(f"✗ Cannot list workflow runs: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking workflow runs: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("GITHUB ACTIONS + CLOUDINARY CONFIGURATION CHECK")
    print("="*60)
    
    # Check environment variables
    env_ok = check_env_variables()
    
    # Check GitHub secrets
    secrets_ok = check_github_secrets()
    
    # Check Cloudinary connection
    cloudinary_ok = check_cloudinary_connection()
    
    # Check GitHub workflow
    workflow_ok = check_github_workflow()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if env_ok and cloudinary_ok:
        print("✓ Local environment is properly configured")
    else:
        print("✗ Local environment needs configuration")
    
    if secrets_ok and workflow_ok:
        print("✓ GitHub Actions is properly configured")
    else:
        print("✗ GitHub Actions needs configuration")
        print("\nTo fix GitHub Actions:")
        print("1. Go to: https://github.com/{}/{}/settings/secrets/actions".format(
            os.environ.get('GITHUB_OWNER', 'YOUR_OWNER'),
            os.environ.get('GITHUB_REPO', 'YOUR_REPO')
        ))
        print("2. Add these repository secrets:")
        print("   - CLOUDINARY_CLOUD_NAME")
        print("   - CLOUDINARY_API_KEY")
        print("   - CLOUDINARY_API_SECRET")
        print("3. Use the same values from your local .env file")
    
    if not env_ok:
        print("\nTo fix local environment:")
        print("1. Create or update your .env file")
        print("2. Add the missing environment variables shown above")
        print("3. Restart your application")

if __name__ == "__main__":
    main()