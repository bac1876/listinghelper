#!/usr/bin/env python3
"""
Automated GitHub Secrets Setup using Playwright
This script automates the process of adding Cloudinary secrets to your GitHub repository
"""

import os
import sys
import asyncio
from playwright.async_api import async_playwright
import getpass

async def setup_github_secrets():
    # Get required information
    print("=== GitHub Secrets Setup for Remotion Video Rendering ===\n")
    
    # Check for environment variables first
    github_username = os.environ.get('GITHUB_USERNAME') or input("Enter your GitHub username: ")
    github_repo = os.environ.get('GITHUB_REPO') or input("Enter your repository name: ")
    
    # Cloudinary credentials
    print("\n--- Cloudinary Credentials ---")
    cloudinary_cloud = os.environ.get('CLOUDINARY_CLOUD_NAME') or input("Enter Cloudinary Cloud Name: ")
    cloudinary_key = os.environ.get('CLOUDINARY_API_KEY') or input("Enter Cloudinary API Key: ")
    cloudinary_secret = os.environ.get('CLOUDINARY_API_SECRET') or getpass.getpass("Enter Cloudinary API Secret: ")
    
    # GitHub authentication
    print("\n--- GitHub Authentication ---")
    print("We'll need to log in to GitHub to add the secrets.")
    github_password = getpass.getpass("Enter your GitHub password (or Personal Access Token): ")
    
    # Optional 2FA code
    use_2fa = input("Do you use 2FA? (y/n): ").lower() == 'y'
    
    async with async_playwright() as p:
        # Launch browser in non-headless mode so user can see what's happening
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to GitHub login
            print("\n🔄 Navigating to GitHub...")
            await page.goto('https://github.com/login')
            
            # Login to GitHub
            print("🔐 Logging in...")
            await page.fill('input[name="login"]', github_username)
            await page.fill('input[name="password"]', github_password)
            await page.click('input[type="submit"]')
            
            # Handle 2FA if needed
            if use_2fa:
                print("📱 Waiting for 2FA code...")
                # Wait for 2FA page
                await page.wait_for_selector('input[name="otp"]', timeout=10000)
                two_fa_code = input("Enter your 2FA code: ")
                await page.fill('input[name="otp"]', two_fa_code)
                await page.press('input[name="otp"]', 'Enter')
            
            # Wait for login to complete
            await page.wait_for_load_state('networkidle')
            
            # Navigate to repository settings
            repo_url = f'https://github.com/{github_username}/{github_repo}/settings/secrets/actions'
            print(f"\n🔧 Navigating to repository secrets: {repo_url}")
            await page.goto(repo_url)
            
            # Function to add a secret
            async def add_secret(name, value):
                print(f"➕ Adding secret: {name}")
                
                # Click "New repository secret" button
                await page.click('a:has-text("New repository secret")')
                await page.wait_for_load_state('networkidle')
                
                # Fill in secret details
                await page.fill('input[name="secret_name"]', name)
                await page.fill('textarea[name="secret_value"]', value)
                
                # Submit
                await page.click('button:has-text("Add secret")')
                await page.wait_for_load_state('networkidle')
                
                print(f"✅ Added secret: {name}")
            
            # Add all three secrets
            await add_secret('CLOUDINARY_CLOUD_NAME', cloudinary_cloud)
            await add_secret('CLOUDINARY_API_KEY', cloudinary_key)
            await add_secret('CLOUDINARY_API_SECRET', cloudinary_secret)
            
            print("\n✅ All secrets added successfully!")
            
            # Create Personal Access Token
            print("\n🔑 Now let's create a Personal Access Token for Railway...")
            create_token = input("Would you like to create a GitHub Personal Access Token? (y/n): ").lower() == 'y'
            
            if create_token:
                # Navigate to token creation page
                await page.goto('https://github.com/settings/tokens/new')
                
                # Fill token details
                token_name = f"Railway Video Render - {github_repo}"
                await page.fill('input[name="oauth_access[description]"]', token_name)
                
                # Select required scopes
                await page.check('input[value="repo"]')  # Full repo access
                await page.check('input[value="workflow"]')  # Workflow access
                
                # Set expiration (optional - for security)
                await page.select_option('select[name="oauth_access[expiration]"]', '90')  # 90 days
                
                print("\n⚠️  IMPORTANT: Copy the token when it appears on the next page!")
                print("You won't be able to see it again!")
                input("\nPress Enter when ready to generate token...")
                
                # Generate token
                await page.click('button:has-text("Generate token")')
                await page.wait_for_load_state('networkidle')
                
                # Wait for user to copy token
                print("\n📋 Copy your Personal Access Token now!")
                print("You'll need to add it to Railway as GITHUB_TOKEN")
                input("\nPress Enter when you've copied the token...")
            
            # Generate Railway environment variables
            print("\n📝 Add these to your Railway environment variables:")
            print("=" * 50)
            print(f"USE_GITHUB_ACTIONS=true")
            print(f"GITHUB_TOKEN=<your_personal_access_token>")
            print(f"GITHUB_OWNER={github_username}")
            print(f"GITHUB_REPO={github_repo}")
            print("=" * 50)
            
            print("\n🎉 Setup complete! Your GitHub repository is now configured for Remotion video rendering.")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please complete the setup manually using GITHUB_ACTIONS_SETUP.md")
        
        finally:
            input("\nPress Enter to close the browser...")
            await browser.close()

def main():
    """Main entry point"""
    print("This script will help you set up GitHub Secrets for Remotion video rendering.")
    print("Make sure you have your Cloudinary credentials ready.\n")
    
    # Check if playwright is installed
    try:
        import playwright
    except ImportError:
        print("❌ Playwright not installed. Installing now...")
        os.system("pip install playwright")
        os.system("playwright install chromium")
        print("✅ Playwright installed. Please run this script again.")
        sys.exit(0)
    
    # Run the async function
    asyncio.run(setup_github_secrets())

if __name__ == "__main__":
    main()