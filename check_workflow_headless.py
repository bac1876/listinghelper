#!/usr/bin/env python3
"""
Check GitHub Actions workflow in headless mode
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def check_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Headless mode
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Checking GitHub Actions...")
        await page.goto("https://github.com/bac1876/listinghelper/actions")
        
        try:
            # Wait for workflow list
            await page.wait_for_selector('h3.Link--primary', timeout=5000)
            
            # Get the latest workflow text
            latest_workflow = await page.locator('h3.Link--primary').first.inner_text()
            print(f"Latest workflow: {latest_workflow}")
            
            # Click it
            await page.click('h3.Link--primary')
            await page.wait_for_timeout(2000)
            
            # Check status
            try:
                status = await page.locator('.octicon-check-circle-fill').count()
                if status > 0:
                    print("Status: SUCCESS")
                else:
                    fail_status = await page.locator('.octicon-x-circle-fill').count()
                    if fail_status > 0:
                        print("Status: FAILED")
                    else:
                        print("Status: IN PROGRESS")
            except:
                print("Status: UNKNOWN")
            
            # Try to find the video URL in logs
            try:
                await page.click('text=render-video')
                await page.wait_for_timeout(1000)
                
                await page.click('text=Upload to Cloudinary')
                await page.wait_for_timeout(1000)
                
                logs = await page.locator('.js-checks-step-logs').inner_text()
                
                if "Successfully uploaded to:" in logs:
                    match = re.search(r'Successfully uploaded to: (https://[^\s]+)', logs)
                    if match:
                        url = match.group(1)
                        print(f"\nVideo URL found: {url}")
                else:
                    print("\nNo video URL found in logs")
                    
            except Exception as e:
                print(f"Could not extract logs: {e}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

asyncio.run(check_workflow())