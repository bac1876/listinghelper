"""
Test GitHub connection and verify everything is configured for Remotion rendering
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_github_token():
    """Test if GitHub token is valid and has correct permissions"""
    print("="*60)
    print("TESTING GITHUB CONNECTION")
    print("="*60)
    
    token = os.environ.get('GITHUB_TOKEN')
    owner = os.environ.get('GITHUB_OWNER')
    repo = os.environ.get('GITHUB_REPO')
    
    # Check if variables are set
    print("\n1. Checking environment variables:")
    
    if not token:
        print("  X GITHUB_TOKEN is not set!")
        print("  -> Follow instructions in GITHUB_TOKEN_SETUP.md")
        return False
    else:
        print(f"  OK GITHUB_TOKEN is set ({len(token)} characters)")
    
    if not owner:
        print("  X GITHUB_OWNER is not set!")
        return False
    else:
        print(f"  OK GITHUB_OWNER = {owner}")
    
    if not repo:
        print("  X GITHUB_REPO is not set!")
        return False
    else:
        print(f"  OK GITHUB_REPO = {repo}")
    
    # Test token validity
    print("\n2. Testing GitHub token validity:")
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Test 1: Check if token is valid
    user_url = 'https://api.github.com/user'
    try:
        response = requests.get(user_url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"  OK Token is valid! Authenticated as: {user_data.get('login')}")
        else:
            print(f"  X Token is invalid! Status: {response.status_code}")
            if response.status_code == 401:
                print("  -> Token may be expired or incorrect")
            return False
    except Exception as e:
        print(f"  X Error testing token: {e}")
        return False
    
    # Test 2: Check repository access
    print("\n3. Testing repository access:")
    repo_url = f'https://api.github.com/repos/{owner}/{repo}'
    try:
        response = requests.get(repo_url, headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            print(f"  OK Can access repository: {repo_data.get('full_name')}")
            print(f"     Private: {repo_data.get('private')}")
        else:
            print(f"  X Cannot access repository! Status: {response.status_code}")
            if response.status_code == 404:
                print(f"  -> Repository {owner}/{repo} not found or no access")
            return False
    except Exception as e:
        print(f"  X Error accessing repository: {e}")
        return False
    
    # Test 3: Check workflow file exists
    print("\n4. Checking GitHub Actions workflow:")
    workflow_url = f'https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows/render-video.yml'
    try:
        response = requests.get(workflow_url, headers=headers)
        if response.status_code == 200:
            print(f"  OK Workflow file exists: render-video.yml")
        else:
            print(f"  X Workflow file not found!")
            print(f"  -> The Remotion workflow may not be set up")
            return False
    except Exception as e:
        print(f"  X Error checking workflow: {e}")
        return False
    
    # Test 4: Check if we can trigger workflows
    print("\n5. Checking workflow permissions:")
    workflows_url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows'
    try:
        response = requests.get(workflows_url, headers=headers)
        if response.status_code == 200:
            workflows = response.json()
            workflow_count = workflows.get('total_count', 0)
            print(f"  OK Can access workflows ({workflow_count} found)")
            
            # Find our render workflow
            for workflow in workflows.get('workflows', []):
                if 'render' in workflow.get('name', '').lower():
                    print(f"  OK Found render workflow: {workflow.get('name')}")
                    break
        else:
            print(f"  X Cannot access workflows! Status: {response.status_code}")
            print(f"  -> Your token may need 'workflow' scope")
            return False
    except Exception as e:
        print(f"  X Error checking workflows: {e}")
        return False
    
    # Test 5: Check GitHub secrets (we can't see values, just if they exist)
    print("\n6. Checking GitHub secrets for Cloudinary:")
    secrets_url = f'https://api.github.com/repos/{owner}/{repo}/actions/secrets'
    try:
        response = requests.get(secrets_url, headers=headers)
        if response.status_code == 200:
            secrets_data = response.json()
            secret_names = [s['name'] for s in secrets_data.get('secrets', [])]
            
            required = ['CLOUDINARY_CLOUD_NAME', 'CLOUDINARY_API_KEY', 'CLOUDINARY_API_SECRET']
            for secret in required:
                if secret in secret_names:
                    print(f"  OK {secret} is configured")
                else:
                    print(f"  X {secret} is NOT configured in GitHub!")
        else:
            print(f"  ? Cannot check secrets (need admin access)")
            print(f"    Make sure these are set in GitHub repository secrets:")
            print(f"    - CLOUDINARY_CLOUD_NAME")
            print(f"    - CLOUDINARY_API_KEY")
            print(f"    - CLOUDINARY_API_SECRET")
    except Exception as e:
        print(f"  X Error checking secrets: {e}")
    
    return True

def main():
    print("\nGITHUB + REMOTION CONFIGURATION TEST")
    print("="*60)
    
    # Check USE_GITHUB_ACTIONS
    if os.environ.get('USE_GITHUB_ACTIONS', '').lower() != 'true':
        print("WARNING: USE_GITHUB_ACTIONS is not set to 'true'")
        print("GitHub Actions rendering will not be used!")
    else:
        print("OK: USE_GITHUB_ACTIONS is enabled")
    
    # Run tests
    success = test_github_token()
    
    print("\n" + "="*60)
    if success:
        print("SUCCESS! GitHub is properly configured for Remotion rendering")
        print("\nYour app can now:")
        print("  1. Trigger GitHub Actions to render videos")
        print("  2. Use Remotion for high-quality output")
        print("  3. Upload videos to Cloudinary")
        print("\nMake sure to add these to Railway environment variables too!")
    else:
        print("CONFIGURATION INCOMPLETE!")
        print("\nTo fix:")
        print("  1. Create a GitHub token: https://github.com/settings/tokens/new")
        print("  2. Add it to .env: GITHUB_TOKEN=ghp_xxxxx")
        print("  3. Run this test again")
        print("\nSee GITHUB_TOKEN_SETUP.md for detailed instructions")
    print("="*60)

if __name__ == "__main__":
    main()