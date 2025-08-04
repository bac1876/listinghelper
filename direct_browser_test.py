#!/usr/bin/env python3
"""
Direct browser test - interact with hidden file input
"""

import asyncio
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright
import requests

APP_URL = "https://virtual-tour-generator-production.up.railway.app"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "browser_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def download_test_images():
    """Download test images"""
    log("Downloading test images...")
    image_files = []
    
    urls = [
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c"
    ]
    
    for i, url in enumerate(urls):
        full_url = f"{url}?w=1920&h=1080&fit=crop&q=80"
        filename = f"property_{i+1}.jpg"
        
        response = requests.get(full_url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            image_files.append(os.path.abspath(filename))
            log(f"Downloaded: {filename}")
    
    return image_files

async def test_app():
    """Test the app by interacting directly with file input"""
    log("Starting direct browser test")
    
    image_files = await download_test_images()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Navigate
            log(f"Opening: {APP_URL}")
            await page.goto(APP_URL, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Screenshot initial
            await page.screenshot(path="browser_1_initial.png")
            
            # Find the hidden file input directly
            file_input = page.locator('input[type="file"]')
            
            # Check if file input exists
            if await file_input.count() > 0:
                log("Found file input")
                # Upload files directly
                await file_input.set_files(image_files)
                log("Files uploaded")
                await page.wait_for_timeout(2000)
                
                # Screenshot after upload
                await page.screenshot(path="browser_2_uploaded.png")
                
                # Scroll down to see form
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(1000)
                
                # Look for any visible inputs and fill them
                inputs = await page.locator('input[type="text"]:visible, input[type="tel"]:visible').all()
                log(f"Found {len(inputs)} visible inputs")
                
                if len(inputs) >= 4:
                    await inputs[0].fill("456 Ocean View Drive")
                    await inputs[1].fill("Malibu, CA 90265")
                    await inputs[2].fill("Sarah Johnson")
                    await inputs[3].fill("(310) 555-1234")
                    log("Filled form fields")
                
                # Screenshot form
                await page.screenshot(path="browser_3_form.png")
                
                # Find submit button - try multiple approaches
                submit_btn = None
                buttons = await page.locator('button:visible').all()
                log(f"Found {len(buttons)} visible buttons")
                
                for btn in buttons:
                    text = await btn.text_content()
                    log(f"  Button: '{text}'")
                    if any(word in text.lower() for word in ['generate', 'create', 'submit', 'start']):
                        submit_btn = btn
                        break
                
                if submit_btn:
                    log(f"Clicking button: '{await submit_btn.text_content()}'")
                    await submit_btn.click()
                    
                    # Wait and monitor
                    await page.wait_for_timeout(5000)
                    await page.screenshot(path="browser_4_processing.png")
                    
                    # Monitor for up to 5 minutes
                    start_time = time.time()
                    while (time.time() - start_time) < 300:
                        # Check page state
                        page_text = await page.text_content('body')
                        
                        # Check for download
                        if 'download' in page_text.lower():
                            download_link = page.locator('a[href*=".mp4"], a:has-text("Download")').first
                            if await download_link.is_visible():
                                log("Download link found!")
                                await page.screenshot(path="browser_5_download.png")
                                
                                # Try to download
                                href = await download_link.get_attribute('href')
                                if href:
                                    log(f"Download URL: {href}")
                                    if href.endswith('.mp4'):
                                        # Direct download
                                        full_url = href if href.startswith('http') else f"{APP_URL}{href}"
                                        resp = requests.get(full_url)
                                        if resp.status_code == 200:
                                            filename = f"tour_video_{int(time.time())}.mp4"
                                            filepath = os.path.join(DOWNLOAD_DIR, filename)
                                            with open(filepath, 'wb') as f:
                                                f.write(resp.content)
                                            log(f"Downloaded: {filename} ({len(resp.content)/1024/1024:.2f} MB)")
                                            
                                            # Verify MP4
                                            with open(filepath, 'rb') as f:
                                                header = f.read(12)
                                                if b'ftyp' in header:
                                                    log("✓ Valid MP4 file!")
                                                else:
                                                    log("✗ Not a valid MP4")
                                            break
                                else:
                                    # Click download
                                    async with page.expect_download() as download_info:
                                        await download_link.click()
                                        download = await download_info.value
                                        path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
                                        await download.save_as(path)
                                        log(f"Downloaded: {download.suggested_filename}")
                                        break
                        
                        # Check for errors
                        if 'error' in page_text.lower():
                            log(f"Error detected in page")
                            await page.screenshot(path="browser_error.png")
                        
                        # Status update every 30s
                        elapsed = int(time.time() - start_time)
                        if elapsed % 30 == 0:
                            log(f"Waiting... {elapsed}s")
                            await page.screenshot(path=f"browser_wait_{elapsed}s.png")
                        
                        await page.wait_for_timeout(5000)
                    
                else:
                    log("No submit button found")
                    
            else:
                log("No file input found on page")
                # Try JavaScript to find inputs
                inputs = await page.evaluate('''() => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    return inputs.length;
                }''')
                log(f"JavaScript found {inputs} file inputs")
            
            # Final screenshot
            await page.screenshot(path="browser_final.png")
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            await page.screenshot(path="browser_exception.png")
            
        finally:
            await page.wait_for_timeout(5000)
            await browser.close()
            
            # Cleanup
            for img in image_files:
                if os.path.exists(img):
                    os.remove(img)

async def main():
    log("="*60)
    log("DIRECT BROWSER TEST")
    log("="*60)
    
    await test_app()
    
    # Results
    log("\nTest Results:")
    if os.path.exists(DOWNLOAD_DIR):
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            log("Downloaded videos:")
            for f in files:
                size = os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) / 1024 / 1024
                log(f"  - {f} ({size:.2f} MB)")
        else:
            log("  No videos downloaded")
    
    screenshots = [f for f in os.listdir('.') if f.startswith('browser_') and f.endswith('.png')]
    log(f"\nCreated {len(screenshots)} screenshots")

if __name__ == "__main__":
    asyncio.run(main())