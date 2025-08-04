#!/usr/bin/env python3
"""
Real user test using Playwright - Updated for actual UI
"""

import asyncio
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright
import requests

# Test configuration
APP_URL = "https://virtual-tour-generator-production.up.railway.app"
DOWNLOAD_DIR = os.path.join(os.getcwd(), "playwright_downloads")

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Test images (real estate photos from Unsplash)
TEST_IMAGES = [
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def download_test_images():
    """Download test images for upload"""
    log("Downloading test images...")
    image_files = []
    
    for i, url in enumerate(TEST_IMAGES):
        # Add parameters for high quality
        full_url = f"{url}?w=1920&h=1080&fit=crop&q=80"
        filename = f"test_image_{i+1}.jpg"
        
        response = requests.get(full_url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            image_files.append(os.path.abspath(filename))
            log(f"Downloaded: {filename}")
        else:
            log(f"Failed to download image {i+1}")
    
    return image_files

async def test_as_real_user():
    """Test the app like a real user would"""
    log("Starting Playwright user test V2")
    
    # Download test images first
    image_files = await download_test_images()
    if len(image_files) < 2:
        log("ERROR: Not enough test images downloaded")
        return
    
    async with async_playwright() as p:
        # Launch browser (visible for debugging)
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        # Create context with download handling
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to the app
            log(f"Navigating to: {APP_URL}")
            await page.goto(APP_URL, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)  # Let page fully load
            
            # Take screenshot of initial state
            await page.screenshot(path="test_1_initial_page.png")
            log("Screenshot: Initial page state")
            
            # Click "Select Photos" button
            select_photos_btn = page.locator('button:has-text("Select Photos")')
            if await select_photos_btn.is_visible():
                log("Found 'Select Photos' button")
                
                # Get the hidden file input that the button triggers
                file_input = page.locator('input[type="file"]')
                
                # Upload files directly to the input
                log(f"Uploading {len(image_files)} images...")
                await file_input.set_files(image_files)
                await page.wait_for_timeout(2000)
                
                # Take screenshot after file selection
                await page.screenshot(path="test_2_files_selected.png")
                log("Screenshot: Files selected")
            else:
                log("ERROR: 'Select Photos' button not found")
                await page.screenshot(path="error_no_select_button.png")
                return
            
            # Wait for property details form to appear or scroll down
            await page.wait_for_timeout(1000)
            
            # Try to scroll down to see if form appears
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)
            
            # Fill in property details - try multiple strategies
            log("Looking for property details form...")
            
            # Strategy 1: Try visible text inputs
            inputs = await page.locator('input[type="text"]:visible').all()
            if inputs:
                log(f"Found {len(inputs)} text inputs")
                
                # Fill them in order (usually address, city, agent name, phone)
                if len(inputs) >= 1:
                    await inputs[0].fill("123 Sunset Boulevard")
                    log("Filled first input (likely address)")
                if len(inputs) >= 2:
                    await inputs[1].fill("Beverly Hills, CA 90210") 
                    log("Filled second input (likely city)")
                if len(inputs) >= 3:
                    await inputs[2].fill("John Smith")
                    log("Filled third input (likely agent name)")
                if len(inputs) >= 4:
                    await inputs[3].fill("(555) 123-4567")
                    log("Filled fourth input (likely phone)")
            
            # Take screenshot of filled form
            await page.screenshot(path="test_3_form_filled.png")
            log("Screenshot: Form filled")
            
            # Look for generate/create button
            generate_btn = None
            button_texts = ["Generate Virtual Tour", "Generate Tour", "Create Tour", "Generate", "Create", "Submit", "Start"]
            
            for text in button_texts:
                btn = page.locator(f'button:has-text("{text}")')
                if await btn.is_visible():
                    generate_btn = btn
                    log(f"Found button: '{text}'")
                    break
            
            if not generate_btn:
                log("ERROR: No generate button found")
                await page.screenshot(path="error_no_generate_button.png")
                return
            
            # Click generate button
            log("Clicking generate button...")
            await generate_btn.click()
            
            # Wait for processing
            await page.wait_for_timeout(3000)
            await page.screenshot(path="test_4_processing_started.png")
            log("Screenshot: Processing started")
            
            # Monitor for completion
            start_time = time.time()
            max_wait = 900  # 15 minutes
            download_completed = False
            
            while (time.time() - start_time) < max_wait:
                # Check for various completion indicators
                
                # Look for download link/button
                download_selectors = [
                    'a[download]',
                    'a:has-text("Download")',
                    'button:has-text("Download")',
                    'a[href*=".mp4"]',
                    '.download-button',
                    '#downloadBtn'
                ]
                
                for selector in download_selectors:
                    elem = page.locator(selector)
                    if await elem.is_visible():
                        log(f"Found download element: {selector}")
                        
                        # Take screenshot before download
                        await page.screenshot(path="test_5_download_ready.png")
                        
                        # Start download
                        log("Starting download...")
                        async with page.expect_download() as download_info:
                            await elem.click()
                            download = await download_info.value
                            
                            # Save the file
                            suggested_name = download.suggested_filename
                            download_path = os.path.join(DOWNLOAD_DIR, suggested_name)
                            await download.save_as(download_path)
                            
                            log(f"Downloaded: {suggested_name}")
                            log(f"Saved to: {download_path}")
                            
                            # Verify the download
                            if os.path.exists(download_path):
                                file_size = os.path.getsize(download_path) / (1024 * 1024)
                                log(f"File size: {file_size:.2f} MB")
                                
                                # Check if it's a valid MP4
                                with open(download_path, 'rb') as f:
                                    header = f.read(12)
                                    if b'ftyp' in header:
                                        log("✓ VERIFIED: Valid MP4 file!")
                                        download_completed = True
                                    else:
                                        log("✗ WARNING: May not be a valid MP4")
                            else:
                                log("ERROR: Downloaded file not found")
                        
                        break
                
                if download_completed:
                    break
                
                # Check for errors
                error_selectors = ['.error', '.alert-danger', '[class*="error"]', '.error-message']
                for selector in error_selectors:
                    error_elem = page.locator(selector)
                    if await error_elem.is_visible():
                        error_text = await error_elem.text_content()
                        log(f"ERROR detected: {error_text}")
                        await page.screenshot(path="test_error_message.png")
                        return
                
                # Check for progress updates
                progress_selectors = ['.progress', '#progress', '[class*="progress"]', '.status-message']
                for selector in progress_selectors:
                    progress_elem = page.locator(selector).first
                    if await progress_elem.is_visible():
                        try:
                            progress_text = await progress_elem.text_content()
                            log(f"Status: {progress_text}")
                        except:
                            pass
                
                # Periodic screenshots
                elapsed = int(time.time() - start_time)
                if elapsed % 60 == 0 and elapsed > 0:  # Every minute
                    await page.screenshot(path=f"test_progress_{elapsed}s.png")
                    log(f"Progress screenshot at {elapsed}s")
                
                await page.wait_for_timeout(5000)  # Check every 5 seconds
            
            # Final screenshot
            await page.screenshot(path="test_final_state.png")
            
            # Summary
            total_time = time.time() - start_time
            log(f"\nTest completed in {total_time:.1f} seconds")
            
            if download_completed:
                log("✓ SUCCESS: Video downloaded and verified!")
            else:
                log("✗ TIMEOUT: No download completed within 15 minutes")
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            await page.screenshot(path="test_exception_error.png")
            
        finally:
            # Keep browser open for 5 seconds to see final state
            await page.wait_for_timeout(5000)
            await browser.close()
            
            # Clean up test images
            for img in image_files:
                if os.path.exists(img):
                    os.remove(img)

async def main():
    """Run the test"""
    log("="*60)
    log("REAL USER TEST V2 - Virtual Tour Generator")
    log("="*60)
    
    await test_as_real_user()
    
    # List all downloaded files
    log("\nDownloaded files:")
    if os.path.exists(DOWNLOAD_DIR):
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            for f in files:
                path = os.path.join(DOWNLOAD_DIR, f)
                size = os.path.getsize(path) / (1024 * 1024)
                log(f"- {f} ({size:.2f} MB)")
        else:
            log("- No files downloaded")
    
    log("\nScreenshots created:")
    screenshots = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.png')]
    for s in screenshots:
        log(f"- {s}")
    
    log("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())