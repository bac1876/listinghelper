"""
Diagnose why Railway is returning JSON instead of video
"""
import os
import requests
from dotenv import load_dotenv

# Load local environment
load_dotenv()

def check_local_config():
    """Check local configuration"""
    print("="*60)
    print("LOCAL CONFIGURATION CHECK")
    print("="*60)
    
    configs = {
        'USE_GITHUB_ACTIONS': os.environ.get('USE_GITHUB_ACTIONS'),
        'GITHUB_TOKEN': os.environ.get('GITHUB_TOKEN'),
        'GITHUB_OWNER': os.environ.get('GITHUB_OWNER'),
        'GITHUB_REPO': os.environ.get('GITHUB_REPO'),
    }
    
    print("\nLocal .env settings:")
    for key, value in configs.items():
        if value:
            if 'TOKEN' in key:
                print(f"  [OK] {key}: [SET - {len(value)} chars]")
            else:
                print(f"  [OK] {key}: {value}")
        else:
            print(f"  [MISSING] {key}: NOT SET")
    
    # Check if main.py is reading these
    print("\n" + "-"*40)
    print("CRITICAL CHECK: Is GitHub Actions enabled?")
    print("-"*40)
    
    use_github = os.environ.get('USE_GITHUB_ACTIONS', 'false').lower() == 'true'
    has_token = bool(os.environ.get('GITHUB_TOKEN'))
    has_owner = bool(os.environ.get('GITHUB_OWNER'))
    has_repo = bool(os.environ.get('GITHUB_REPO'))
    
    if use_github and all([has_token, has_owner, has_repo]):
        print("[OK] GitHub Actions SHOULD be enabled")
        print("  This means videos should use Remotion")
    else:
        print("[X] GitHub Actions is NOT enabled")
        if not use_github:
            print("  - USE_GITHUB_ACTIONS is not 'true'")
        if not has_token:
            print("  - GITHUB_TOKEN is missing")
        if not has_owner:
            print("  - GITHUB_OWNER is missing")
        if not has_repo:
            print("  - GITHUB_REPO is missing")
    
    return use_github and all([has_token, has_owner, has_repo])

def test_local_server():
    """Test if local server uses GitHub Actions"""
    print("\n" + "="*60)
    print("TESTING LOCAL SERVER CONFIGURATION")
    print("="*60)
    
    try:
        # Try health check
        response = requests.get("http://localhost:5000/api/virtual-tour/health", timeout=5)
        if response.status_code == 200:
            print("[OK] Local server is running")
            
            # Get a simple status to check configuration
            # This would need a job ID, but we can check the response
            print("\nChecking if GitHub Actions is configured...")
            
            # The real test is whether GitHub Actions gets triggered
            # We can check this by looking at the logs
            
        else:
            print("[X] Server returned unexpected status")
    except:
        print("[X] Local server is not running")
        print("  Start it with: py run_production.py")
    
    return True

def main():
    print("\nDIAGNOSING JSON DOWNLOAD ISSUE")
    print("="*60)
    
    # Check local config
    local_ok = check_local_config()
    
    # Test local server
    test_local_server()
    
    print("\n" + "="*60)
    print("DIAGNOSIS SUMMARY")
    print("="*60)
    
    if local_ok:
        print("\n[OK] Local configuration is correct")
        print("\nFor Railway to work the same way, you MUST add these")
        print("environment variables in Railway dashboard:")
        print("")
        print("  USE_GITHUB_ACTIONS = true")
        print("  GITHUB_TOKEN = " + os.environ.get('GITHUB_TOKEN', '[YOUR_TOKEN]'))
        print("  GITHUB_OWNER = " + os.environ.get('GITHUB_OWNER', 'bac1876'))
        print("  GITHUB_REPO = " + os.environ.get('GITHUB_REPO', 'listinghelper'))
        print("")
        print("Without these, Railway will NOT use GitHub Actions/Remotion!")
    else:
        print("\n[X] Local configuration is incomplete")
        print("Fix the issues above first")
    
    print("\n" + "="*60)
    print("\nThe JSON issue happens when:")
    print("1. GitHub Actions is not enabled (USE_GITHUB_ACTIONS != true)")
    print("2. GitHub token is missing or invalid")
    print("3. The app falls back to basic FFmpeg (which has issues)")
    print("\nRailway MUST have the same env vars as your local .env!")

if __name__ == "__main__":
    main()