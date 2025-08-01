#!/usr/bin/env python3
"""
Use Playwright to automatically debug GitHub Actions workflow failures
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def debug_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser so you can see what's happening
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔍 Opening GitHub Actions page...")
        
        # Go to the Actions page
        await page.goto('https://github.com/bac1876/listinghelper/actions')
        
        # Wait for the page to load
        await page.wait_for_load_state('networkidle')
        
        print("📋 Looking for failed workflows...")
        
        # Click on the most recent failed workflow
        # Look for the first workflow with a failure indicator
        failed_workflow = page.locator('a[href*="/actions/runs/"]').first
        await failed_workflow.click()
        
        # Wait for workflow details to load
        await page.wait_for_load_state('networkidle')
        
        print("🔍 Checking workflow details...")
        
        # Click on the failed job (render-video)
        failed_job = page.locator('text=render-video').first
        await failed_job.click()
        
        # Wait for job details to expand
        await page.wait_for_timeout(2000)
        
        # Click on the failed step to see the error
        # The failed step has a red X icon
        failed_step = page.locator('svg[aria-label="Failed"]').first
        
        # Click the parent element of the failed step to expand it
        await failed_step.locator('..').click()
        
        # Wait for error details to show
        await page.wait_for_timeout(2000)
        
        print("📝 Extracting error information...")
        
        # Get the error text
        error_section = page.locator('.js-checks-log-line-text')
        error_lines = await error_section.all_text_contents()
        
        print("\n❌ ERROR DETAILS:")
        print("-" * 50)
        for line in error_lines[-20:]:  # Show last 20 lines
            if line.strip():
                print(line.strip())
        
        # Also check for specific error patterns
        page_content = await page.content()
        
        if "syntax error" in page_content.lower():
            print("\n⚠️  Found syntax error in the workflow file")
        elif "npm ERR!" in page_content:
            print("\n⚠️  NPM installation error detected")
        elif "Cannot find module" in page_content:
            print("\n⚠️  Missing module error detected")
        
        # Take a screenshot of the error
        await page.screenshot(path='github_actions_error.png')
        print("\n📸 Screenshot saved as github_actions_error.png")
        
        input("\nPress Enter to close the browser...")
        await browser.close()

if __name__ == "__main__":
    print("🚀 Starting GitHub Actions debugger with Playwright...")
    asyncio.run(debug_workflow())