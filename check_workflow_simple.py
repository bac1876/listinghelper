#!/usr/bin/env python3
"""
Check GitHub Actions workflow results with Playwright
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def check_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Opening GitHub Actions...")
        await page.goto("https://github.com/bac1876/listinghelper/actions")
        await page.wait_for_load_state('networkidle')
        
        try:
            # Click the first workflow
            print("Looking for latest workflow...")
            await page.click('h3.Link--primary', timeout=10000)
            await page.wait_for_timeout(3000)
            
            # Click render-video job
            await page.click('text=render-video')
            await page.wait_for_timeout(2000)
            
            # Click Upload to Cloudinary step
            print("Checking Cloudinary upload step...")
            await page.click('text=Upload to Cloudinary')
            await page.wait_for_timeout(2000)
            
            # Get logs
            logs = await page.locator('.js-checks-step-logs').inner_text()
            print("\n--- Cloudinary Upload Logs ---")
            print(logs)
            
            # Check results
            if "Successfully uploaded to:" in logs:
                match = re.search(r'Successfully uploaded to: (https://[^\s]+)', logs)
                if match:
                    url = match.group(1)
                    print(f"\n[SUCCESS] Video uploaded!")
                    print(f"Video URL: {url}")
            elif "Upload failed" in logs or "401" in logs:
                print("\n[FAILED] Upload failed - check credentials")
            
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path='workflow_status.png')
            print("Screenshot saved as workflow_status.png")
        
        input("\nPress Enter to close...")
        await browser.close()

asyncio.run(check_workflow())