#!/usr/bin/env python3
"""
Use Playwright to check GitHub Actions workflow results
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def check_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Opening GitHub Actions...")
        
        # Go to the specific workflow run
        workflow_url = "https://github.com/bac1876/listinghelper/actions"
        await page.goto(workflow_url)
        
        # Wait for page to load
        await page.wait_for_load_state('networkidle')
        
        print("📋 Looking for the latest workflow run...")
        
        try:
            # Click on the first (most recent) workflow run
            await page.click('h3.Link--primary', timeout=10000)
            await page.wait_for_load_state('networkidle')
            
            print("🔍 Checking workflow status...")
            
            # Wait a bit for the page to fully load
            await page.wait_for_timeout(2000)
            
            # Look for the render-video job and click it
            try:
                await page.click('text=render-video', timeout=5000)
                await page.wait_for_timeout(2000)
            except:
                print("⏳ Workflow might still be running...")
            
            # Try to expand the "Upload to Cloudinary" step
            try:
                # Look for and click the Upload to Cloudinary step
                upload_step = page.locator('text=Upload to Cloudinary').first
                await upload_step.click()
                await page.wait_for_timeout(2000)
                
                print("📝 Extracting Cloudinary upload logs...")
                
                # Get the content of the expanded step
                # Look for log lines in the expanded section
                log_content = await page.locator('.js-checks-step-logs').inner_text()
                
                print("\n--- Cloudinary Upload Logs ---")
                print(log_content)
                
                # Look for specific patterns
                if "Successfully uploaded to:" in log_content:
                    # Extract the URL
                    url_match = re.search(r'Successfully uploaded to: (https://[^\s]+)', log_content)
                    if url_match:
                        video_url = url_match.group(1)
                        print(f"\n✅ VIDEO SUCCESSFULLY UPLOADED!")
                        print(f"🎬 Video URL: {video_url}")
                        print(f"\nYou can watch your video at: {video_url}")
                elif "VIDEO_URL=" in log_content:
                    # Alternative pattern
                    url_match = re.search(r'VIDEO_URL=(https://[^\s]+)', log_content)
                    if url_match:
                        video_url = url_match.group(1)
                        print(f"\n✅ VIDEO SUCCESSFULLY UPLOADED!")
                        print(f"🎬 Video URL: {video_url}")
                elif "Upload failed:" in log_content:
                    print("\n❌ UPLOAD FAILED!")
                    error_match = re.search(r'Upload failed: (.+)', log_content)
                    if error_match:
                        print(f"Error: {error_match.group(1)}")
                elif "401" in log_content or "api_secret" in log_content:
                    print("\n❌ AUTHENTICATION FAILED!")
                    print("The Cloudinary credentials in GitHub Secrets don't match your account.")
                else:
                    print("\n⚠️  Could not determine upload status from logs")
                    
            except Exception as e:
                print(f"⚠️  Could not find Upload to Cloudinary step: {e}")
                print("The workflow might still be running or in a different state.")
                
                # Take a screenshot for debugging
                await page.screenshot(path='workflow_status.png')
                print("📸 Screenshot saved as workflow_status.png")
            
        except Exception as e:
            print(f"❌ Error navigating workflow: {e}")
            
            # Check if we need to log in
            if "login" in page.url.lower():
                print("\n🔐 GitHub login required!")
                print("Please log in manually in the browser window...")
                await page.wait_for_timeout(30000)  # Wait 30 seconds for manual login
                
        print("\n💡 Tip: If the workflow is still running, wait a minute and run this script again.")
        
        input("\nPress Enter to close the browser...")
        await browser.close()

if __name__ == "__main__":
    print("Checking GitHub Actions workflow with Playwright...\n")
    asyncio.run(check_workflow())