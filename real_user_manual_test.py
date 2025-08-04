#!/usr/bin/env python3
"""
Manual user test - opens browser and waits for user to complete actions
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os

async def manual_user_test():
    print("\n" + "="*60)
    print("MANUAL USER TEST - Virtual Tour Generator")
    print("="*60)
    print("\nThis test will:")
    print("1. Open the app in a browser")
    print("2. Take screenshots at key moments")
    print("3. Monitor for video completion")
    print("4. Download any videos that appear")
    print("\nYOU need to manually:")
    print("- Click 'Select Photos' and choose images")
    print("- Fill in the property details form")
    print("- Click the Generate button")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Navigate to app
        print("\n[TEST] Opening app...")
        await page.goto("https://virtual-tour-generator-production.up.railway.app")
        await page.wait_for_load_state('networkidle')
        
        print("[TEST] App loaded - please upload images and fill the form")
        await page.screenshot(path="manual_1_initial.png")
        
        # Wait for user to upload files and submit
        print("\n[WAITING] Please complete these steps:")
        print("1. Click 'Select Photos' and choose 2-3 images")
        print("2. Fill in property address, city, agent name, phone")
        print("3. Click the Generate/Create button")
        print("\nMonitoring for changes...")
        
        # Monitor for processing
        last_screenshot = time.time()
        start_time = time.time()
        video_found = False
        
        while (time.time() - start_time) < 600:  # 10 minutes max
            try:
                # Take periodic screenshots
                if time.time() - last_screenshot > 30:
                    await page.screenshot(path=f"manual_progress_{int(time.time())}.png")
                    last_screenshot = time.time()
                
                # Check for download link
                download_links = await page.locator('a[href*=".mp4"], a:has-text("Download")').count()
                if download_links > 0 and not video_found:
                    print("\n[FOUND] Download link detected!")
                    await page.screenshot(path="manual_download_ready.png")
                    
                    # Get the download link
                    link = page.locator('a[href*=".mp4"], a:has-text("Download")').first
                    href = await link.get_attribute('href')
                    
                    if href:
                        print(f"[DOWNLOAD] Video URL: {href}")
                        video_found = True
                        
                        # Try to click download
                        try:
                            async with page.expect_download(timeout=30000) as download_info:
                                await link.click()
                                download = await download_info.value
                                filename = download.suggested_filename
                                download_path = os.path.join(os.getcwd(), filename)
                                await download.save_as(download_path)
                                print(f"[SUCCESS] Downloaded: {filename}")
                                
                                # Verify it's an MP4
                                if os.path.exists(download_path):
                                    size = os.path.getsize(download_path) / 1024 / 1024
                                    with open(download_path, 'rb') as f:
                                        header = f.read(12)
                                        if b'ftyp' in header:
                                            print(f"[VERIFIED] Valid MP4 file ({size:.2f} MB)")
                                        else:
                                            print(f"[WARNING] File may not be valid MP4")
                        except Exception as e:
                            print(f"[INFO] Download via click failed, URL is: {href}")
                            print("[INFO] You can download manually from the browser")
                    
                    break
                
                # Check for errors
                error_msgs = await page.locator('.error, .alert-danger, [class*="error"]').count()
                if error_msgs > 0:
                    error_text = await page.locator('.error, .alert-danger, [class*="error"]').first.text_content()
                    if 'timeout' in error_text.lower():
                        print(f"\n[ERROR] Timeout detected: {error_text}")
                        await page.screenshot(path="manual_timeout_error.png")
                
                # Show status updates
                status_elems = await page.locator('.progress-text, .status, [class*="progress"]').count()
                if status_elems > 0:
                    try:
                        status_text = await page.locator('.progress-text, .status, [class*="progress"]').first.text_content()
                        if status_text and status_text.strip():
                            print(f"\r[STATUS] {status_text}", end='', flush=True)
                    except:
                        pass
                
                await page.wait_for_timeout(2000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                
        # Final screenshot
        await page.screenshot(path="manual_final.png")
        
        print("\n\n[TEST] Test complete!")
        print("\nResults:")
        if video_found:
            print("✅ Video generation successful!")
        else:
            print("❌ No video download found within 10 minutes")
        
        print("\nScreenshots created:")
        screenshots = [f for f in os.listdir('.') if f.startswith('manual_') and f.endswith('.png')]
        for s in sorted(screenshots):
            print(f"  - {s}")
        
        print("\n[BROWSER] Keeping browser open for 30 seconds...")
        print("You can interact with the page or close when ready.")
        await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(manual_user_test())