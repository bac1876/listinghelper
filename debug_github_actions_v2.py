#!/usr/bin/env python3
"""
Use Playwright to debug GitHub Actions - improved version
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def debug_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🔍 Opening latest failed workflow directly...")
        
        # Go directly to the most recent workflow run
        await page.goto('https://github.com/bac1876/listinghelper/actions/runs/12646605457')
        
        # Wait for page to load
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        
        print("📋 Expanding failed job details...")
        
        # Click on the render-video job to expand it
        try:
            # Try different selectors for the job
            job_selectors = [
                'text=render-video',
                'h3:has-text("render-video")',
                'summary:has-text("render-video")',
                '[aria-label*="render-video"]'
            ]
            
            for selector in job_selectors:
                try:
                    await page.locator(selector).first.click()
                    print(f"✅ Clicked job using selector: {selector}")
                    break
                except:
                    continue
                    
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"⚠️  Could not expand job: {e}")
        
        print("🔍 Looking for error details...")
        
        # Try to find and click on the failed step (Parse inputs)
        try:
            # Look for the Parse inputs step that failed
            failed_step = page.locator('text=Parse inputs').first
            await failed_step.click()
            await page.wait_for_timeout(1000)
            print("✅ Clicked on Parse inputs step")
        except:
            print("⚠️  Could not click Parse inputs step")
        
        # Take a screenshot to see current state
        await page.screenshot(path='github_workflow_state.png', full_page=True)
        print("📸 Screenshot saved as github_workflow_state.png")
        
        # Try to extract visible error text
        print("\n📝 Extracting visible error information...")
        
        # Look for error messages in various places
        error_selectors = [
            '.ansi-red-fg',  # Red colored text
            'pre:has-text("error")',
            'pre:has-text("Error")',
            'code:has-text("error")',
            '.js-checks-log-line-text',
            'text=/error.*/i',
            'text=/syntax error.*/i'
        ]
        
        found_errors = []
        for selector in error_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip():
                        found_errors.append(text.strip())
            except:
                continue
        
        if found_errors:
            print("\n❌ ERRORS FOUND:")
            print("-" * 50)
            for error in set(found_errors):  # Remove duplicates
                print(error)
        else:
            print("No specific errors extracted, check the screenshot")
        
        # Also get the full page text to search for errors
        page_text = await page.inner_text('body')
        
        # Look for the specific error from your screenshot
        if "syntax error near unexpected token" in page_text:
            print("\n⚠️  FOUND THE ISSUE: JSON parsing error in workflow")
            print("The workflow is receiving malformed JSON in the inputs")
            
            # Try to find the exact line
            lines = page_text.split('\n')
            for i, line in enumerate(lines):
                if "syntax error" in line.lower():
                    print(f"\nError context:")
                    # Show lines around the error
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    for j in range(start, end):
                        print(f"  {lines[j]}")
        
        print("\n✅ Diagnosis complete!")
        print("\nBased on the error in Parse inputs step, the issue is:")
        print("The JSON inputs are not being properly escaped when passed to the workflow.")
        print("This is causing a shell syntax error when trying to parse them.")
        
        input("\nPress Enter to close the browser...")
        await browser.close()

if __name__ == "__main__":
    print("🚀 Starting improved GitHub Actions debugger...")
    asyncio.run(debug_workflow())