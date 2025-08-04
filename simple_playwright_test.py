#!/usr/bin/env python3
"""
Simple Playwright test to check if app is working
"""

import asyncio
from playwright.async_api import async_playwright
import os
import time

async def simple_test():
    print("[TEST] Starting simple Playwright test...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to the app
        print("[TEST] Opening Railway app...")
        await page.goto("https://virtual-tour-generator-production.up.railway.app")
        await page.wait_for_load_state('networkidle')
        
        # Take screenshot
        await page.screenshot(path="simple_test_1.png")
        print("[TEST] Screenshot taken: simple_test_1.png")
        
        # Check page title
        title = await page.title()
        print(f"[TEST] Page title: {title}")
        
        # Check if error message exists
        body_text = await page.text_content('body')
        if 'application error' in body_text.lower():
            print("[ERROR] Application error detected!")
            await page.screenshot(path="simple_test_error.png")
        elif 'cannot' in body_text.lower() and 'get' in body_text.lower():
            print("[ERROR] Routing error detected!")
            await page.screenshot(path="simple_test_routing_error.png")
        else:
            print("[TEST] Page loaded successfully")
            
            # Try to find file input
            file_inputs = await page.locator('input[type="file"]').count()
            print(f"[TEST] File inputs found: {file_inputs}")
            
            # Try to find buttons
            buttons = await page.locator('button').all()
            print(f"[TEST] Buttons found: {len(buttons)}")
            for i, btn in enumerate(buttons[:3]):
                text = await btn.text_content()
                print(f"  Button {i}: '{text}'")
        
        # Wait a bit then close
        await page.wait_for_timeout(3000)
        await browser.close()
    
    print("[TEST] Test complete!")
    
    # List screenshots
    screenshots = [f for f in os.listdir('.') if f.startswith('simple_test_') and f.endswith('.png')]
    if screenshots:
        print(f"\n[TEST] Screenshots created:")
        for s in screenshots:
            print(f"  - {s}")

if __name__ == "__main__":
    asyncio.run(simple_test())