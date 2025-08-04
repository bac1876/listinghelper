#!/usr/bin/env python3
"""
Fully automated user test - acts like a real user
"""

import asyncio
from playwright.async_api import async_playwright
import os
import time
import requests

async def act_like_real_user():
    print("\nAUTOMATED USER TEST - Acting like a real person")
    print("="*60)
    
    # Download test images first
    print("\nPreparing test images...")
    test_images = []
    for i in range(3):
        url = f"https://images.unsplash.com/photo-{['1600596542815-ffad4c1539a9', '1600585154340-be6161a56a0c', '1600607687939-ce8a6c25118c'][i]}?w=1920&h=1080"
        filename = f"home_{i+1}.jpg"
        resp = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(resp.content)
        test_images.append(os.path.abspath(filename))
        print(f"  [OK] Downloaded {filename}")
    
    async with async_playwright() as p:
        # Launch browser visibly
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100  # Slow down actions to be more human-like
        )
        page = await browser.new_page()
        
        try:
            # 1. Navigate to the website
            print("\n Opening Virtual Tour Generator...")
            await page.goto("https://virtual-tour-generator-production.up.railway.app")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)  # Human pause
            
            print("  [OK] Page loaded")
            await page.screenshot(path="user_1_homepage.png")
            
            # 2. Upload images using the file input directly
            print("\n Uploading property images...")
            
            # Find the file input (even if hidden)
            file_input = page.locator('input[type="file"]').first
            
            # Upload files
            await file_input.set_files(test_images)
            print("  [OK] Selected 3 property images")
            await page.wait_for_timeout(2000)  # Human pause
            
            await page.screenshot(path="user_2_images_selected.png")
            
            # 3. Scroll to see the form
            print("\n Looking for property details form...")
            await page.evaluate('window.scrollBy(0, 500)')
            await page.wait_for_timeout(1000)
            
            # 4. Fill in property details - find all text inputs
            print("  Filling out property information...")
            
            # Get all visible text inputs
            inputs = page.locator('input[type="text"]:visible, input[type="tel"]:visible')
            input_count = await inputs.count()
            print(f"  Found {input_count} input fields")
            
            # Fill them based on typical order
            if input_count >= 1:
                await inputs.nth(0).click()
                await inputs.nth(0).fill("742 Evergreen Terrace")
                print("  [OK] Entered address")
                await page.wait_for_timeout(500)
                
            if input_count >= 2:
                await inputs.nth(1).click()
                await inputs.nth(1).fill("Springfield, IL 62701")
                print("  [OK] Entered city")
                await page.wait_for_timeout(500)
                
            if input_count >= 3:
                await inputs.nth(2).click()
                await inputs.nth(2).fill("Homer Simpson")
                print("  [OK] Entered agent name")
                await page.wait_for_timeout(500)
                
            if input_count >= 4:
                await inputs.nth(3).click()
                await inputs.nth(3).fill("(555) 867-5309")
                print("  [OK] Entered phone number")
                await page.wait_for_timeout(500)
            
            await page.screenshot(path="user_3_form_filled.png")
            
            # 5. Find and click the generate button
            print("\n Looking for Generate button...")
            
            # Try multiple button selectors
            button_found = False
            for selector in ['button:has-text("Generate")', 'button:has-text("Create")', 'button[type="submit"]']:
                btn = page.locator(selector).first
                if await btn.is_visible():
                    print(f"  [OK] Found button: {await btn.text_content()}")
                    await btn.click()
                    button_found = True
                    print("  [OK] Clicked Generate button!")
                    break
            
            if not button_found:
                print("  [FAILED] Could not find Generate button")
                return
            
            # 6. Wait for processing
            print("\n Waiting for video generation...")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="user_4_processing.png")
            
            # Monitor for completion
            start_time = time.time()
            video_downloaded = False
            
            while (time.time() - start_time) < 300:  # 5 minutes max
                # Check for download link
                download_link = page.locator('a[href*=".mp4"], a:has-text("Download")').first
                if await download_link.is_visible():
                    print("\n Video is ready!")
                    await page.screenshot(path="user_5_download_ready.png")
                    
                    # Get video URL
                    href = await download_link.get_attribute('href')
                    if href:
                        print(f"  Video URL: {href}")
                        
                        # Download the video
                        if '.mp4' in href:
                            full_url = href if href.startswith('http') else f"https://virtual-tour-generator-production.up.railway.app{href}"
                            print(f"\n Downloading video...")
                            video_resp = requests.get(full_url)
                            if video_resp.status_code == 200:
                                video_filename = f"user_test_video_{int(time.time())}.mp4"
                                with open(video_filename, 'wb') as f:
                                    f.write(video_resp.content)
                                size_mb = len(video_resp.content) / 1024 / 1024
                                print(f"  [OK] Downloaded: {video_filename} ({size_mb:.2f} MB)")
                                
                                # Verify it's a real MP4
                                with open(video_filename, 'rb') as f:
                                    header = f.read(12)
                                    if b'ftyp' in header:
                                        print("  [OK] VERIFIED: This is a real MP4 video file!")
                                        video_downloaded = True
                                    else:
                                        print("  [FAILED] File doesn't appear to be a valid MP4")
                        break
                
                # Check for errors
                error = page.locator('.error, .alert-danger').first
                if await error.is_visible():
                    error_text = await error.text_content()
                    print(f"\nWARNING:  Error: {error_text}")
                    if 'timeout' in error_text.lower():
                        print("  The UI timed out, but video might still be processing...")
                
                # Progress update
                elapsed = int(time.time() - start_time)
                if elapsed % 15 == 0:
                    print(f"    {elapsed} seconds elapsed...")
                
                await page.wait_for_timeout(3000)
            
            # Final summary
            print("\n" + "="*60)
            print(" TEST SUMMARY")
            print("="*60)
            
            if video_downloaded:
                print("[SUCCESS] SUCCESS: Acted like a real user and downloaded a video!")
                print("[SUCCESS] The Virtual Tour Generator works correctly!")
            else:
                print("[FAILED] No video was downloaded within 5 minutes")
            
            await page.screenshot(path="user_6_final_state.png")
            
        except Exception as e:
            print(f"\n[FAILED] Error: {str(e)}")
            await page.screenshot(path="user_error.png")
            
        finally:
            print("\n Test complete - browser will close in 10 seconds...")
            await page.wait_for_timeout(10000)
            await browser.close()
            
            # Cleanup test images
            for img in test_images:
                if os.path.exists(img):
                    os.remove(img)
            
            # Show all screenshots
            print("\n Screenshots captured:")
            screenshots = sorted([f for f in os.listdir('.') if f.startswith('user_') and f.endswith('.png')])
            for s in screenshots:
                print(f"  - {s}")

if __name__ == "__main__":
    asyncio.run(act_like_real_user())