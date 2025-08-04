#!/usr/bin/env python3
"""
Final browser test with correct Playwright API
"""

import asyncio
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright
import requests

APP_URL = "https://virtual-tour-generator-production.up.railway.app"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "final_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def test_virtual_tour():
    """Test the virtual tour generator as a real user"""
    log("Starting final browser test")
    
    # Download test images
    log("Preparing test images...")
    image_files = []
    urls = [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1920&h=1080",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1920&h=1080"
    ]
    
    for i, url in enumerate(urls):
        filename = f"house_{i+1}.jpg"
        resp = requests.get(url)
        if resp.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(resp.content)
            image_files.append(os.path.abspath(filename))
            log(f"Prepared: {filename}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Enable downloads
        await page.context.set_default_timeout(60000)
        
        try:
            # Navigate to app
            log("Navigating to app...")
            await page.goto(APP_URL)
            await page.wait_for_load_state('networkidle')
            
            # Screenshot
            await page.screenshot(path="final_1_loaded.png")
            
            # Method 1: Direct file input
            file_inputs = page.locator('input[type="file"]')
            count = await file_inputs.count()
            log(f"Found {count} file inputs")
            
            if count > 0:
                # Upload to first file input
                await file_inputs.first.set_files(image_files)
                log("Files uploaded via input")
                await page.wait_for_timeout(2000)
                await page.screenshot(path="final_2_uploaded.png")
            else:
                # Method 2: Try drop zone click
                drop_zone = page.locator('#drop-zone, .drop-zone').first
                if await drop_zone.is_visible():
                    log("Trying drop zone click")
                    await drop_zone.click()
                    await page.wait_for_timeout(1000)
            
            # Check if form appeared
            await page.evaluate('window.scrollTo(0, 1000)')
            await page.wait_for_timeout(1000)
            
            # Fill any visible inputs
            text_inputs = page.locator('input[type="text"]:visible')
            input_count = await text_inputs.count()
            log(f"Found {input_count} text inputs")
            
            if input_count > 0:
                # Fill inputs
                await text_inputs.nth(0).fill("789 Beachfront Avenue")
                if input_count > 1:
                    await text_inputs.nth(1).fill("Santa Monica, CA 90401")
                if input_count > 2:
                    await text_inputs.nth(2).fill("Mike Wilson")
                if input_count > 3:
                    await text_inputs.nth(3).fill("(424) 555-9876")
                log("Form filled")
            
            await page.screenshot(path="final_3_form.png")
            
            # Find and click submit
            buttons = page.locator('button:visible')
            button_count = await buttons.count()
            log(f"Found {button_count} buttons")
            
            submit_clicked = False
            for i in range(button_count):
                btn = buttons.nth(i)
                text = await btn.text_content()
                log(f"  Button {i}: '{text}'")
                if any(word in text.lower() for word in ['generate', 'create', 'submit']):
                    await btn.click()
                    submit_clicked = True
                    log(f"Clicked: {text}")
                    break
            
            if submit_clicked:
                # Wait for processing
                await page.wait_for_timeout(5000)
                await page.screenshot(path="final_4_processing.png")
                
                # Monitor for download
                log("Monitoring for video...")
                start = time.time()
                video_found = False
                
                while (time.time() - start) < 300:  # 5 minutes
                    # Check for download link
                    download_links = page.locator('a[href*=".mp4"], a:has-text("Download")')
                    if await download_links.count() > 0:
                        log("Download link appeared!")
                        link = download_links.first
                        href = await link.get_attribute('href')
                        
                        if href and '.mp4' in href:
                            log(f"Video URL: {href}")
                            await page.screenshot(path="final_5_ready.png")
                            
                            # Download video
                            full_url = href if href.startswith('http') else f"{APP_URL}{href}"
                            video_resp = requests.get(full_url)
                            if video_resp.status_code == 200:
                                video_path = os.path.join(DOWNLOAD_DIR, f"tour_{int(time.time())}.mp4")
                                with open(video_path, 'wb') as f:
                                    f.write(video_resp.content)
                                size_mb = len(video_resp.content) / 1024 / 1024
                                log(f"✓ Downloaded video: {size_mb:.2f} MB")
                                
                                # Verify MP4
                                with open(video_path, 'rb') as f:
                                    if b'ftyp' in f.read(12):
                                        log("✓ VERIFIED: Valid MP4 file!")
                                        video_found = True
                                break
                        else:
                            # Click to download
                            await link.click()
                            log("Clicked download link")
                            await page.wait_for_timeout(5000)
                            break
                    
                    # Check status
                    status_text = await page.text_content('body')
                    if 'error' in status_text.lower() and 'timeout' in status_text.lower():
                        log("Timeout error detected")
                        await page.screenshot(path="final_error_timeout.png")
                    
                    elapsed = int(time.time() - start)
                    if elapsed % 30 == 0:
                        log(f"Still waiting... {elapsed}s")
                    
                    await page.wait_for_timeout(5000)
                
                if not video_found:
                    log("No video download completed")
                    await page.screenshot(path="final_timeout.png")
            else:
                log("Could not find submit button")
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            await page.screenshot(path="final_error.png")
        
        finally:
            await browser.close()
            # Cleanup
            for img in image_files:
                if os.path.exists(img):
                    os.remove(img)

    # Summary
    log("\n" + "="*60)
    log("FINAL TEST RESULTS")
    log("="*60)
    
    if os.path.exists(DOWNLOAD_DIR):
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            log("\n✓ Downloaded Videos:")
            for f in files:
                path = os.path.join(DOWNLOAD_DIR, f)
                size = os.path.getsize(path) / 1024 / 1024
                log(f"  - {f} ({size:.2f} MB)")
        else:
            log("\n✗ No videos downloaded")
    
    screenshots = sorted([f for f in os.listdir('.') if f.startswith('final_') and f.endswith('.png')])
    log(f"\nCreated {len(screenshots)} screenshots:")
    for s in screenshots:
        log(f"  - {s}")

if __name__ == "__main__":
    asyncio.run(test_virtual_tour())