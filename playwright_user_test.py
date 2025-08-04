#!/usr/bin/env python3
"""
Real user test using Playwright
Tests the app exactly as a user would experience it
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
    log("Starting Playwright user test")
    
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
            
            # Check if page loaded correctly
            title = await page.title()
            log(f"Page title: {title}")
            
            # Look for the file input
            file_input = page.locator('input[type="file"]')
            if not await file_input.is_visible():
                log("ERROR: File input not found")
                await page.screenshot(path="error_no_file_input.png")
                return
            
            # Upload images
            log(f"Uploading {len(image_files)} images...")
            await file_input.set_files(image_files)
            await page.wait_for_timeout(1000)
            
            # Fill in property details
            log("Filling property details...")
            
            # Try different possible field selectors
            await page.fill('input[placeholder*="address" i], input[name*="address" i], #address', 
                          "123 Sunset Boulevard")
            await page.fill('input[placeholder*="city" i], input[name*="city" i], #city', 
                          "Beverly Hills, CA 90210")
            await page.fill('input[placeholder*="agent" i][placeholder*="name" i], input[name*="agent_name" i], #agent_name', 
                          "John Smith")
            await page.fill('input[placeholder*="phone" i], input[name*="phone" i], #agent_phone', 
                          "(555) 123-4567")
            
            # Take screenshot before submission
            await page.screenshot(path="test_2_filled_form.png")
            log("Screenshot: Filled form")
            
            # Look for generate button
            generate_button = page.locator('button:has-text("Generate"), button:has-text("Create"), button:has-text("Submit")')
            if not await generate_button.is_visible():
                log("ERROR: Generate button not found")
                await page.screenshot(path="error_no_generate_button.png")
                return
            
            # Click generate button
            log("Clicking generate button...")
            await generate_button.click()
            
            # Wait for processing to start
            await page.wait_for_timeout(3000)
            await page.screenshot(path="test_3_processing_started.png")
            log("Screenshot: Processing started")
            
            # Monitor progress
            start_time = time.time()
            max_wait = 900  # 15 minutes
            last_progress = 0
            
            while (time.time() - start_time) < max_wait:
                # Look for progress indicators
                progress_elem = page.locator('.progress-bar, [class*="progress"], #progress')
                error_elem = page.locator('.error, .alert-danger, [class*="error"]')
                download_elem = page.locator('a[download], button:has-text("Download"), a:has-text("Download")')
                
                # Check for errors
                if await error_elem.is_visible():
                    error_text = await error_elem.text_content()
                    log(f"ERROR detected: {error_text}")
                    await page.screenshot(path="test_error_occurred.png")
                    break
                
                # Check for download button
                if await download_elem.is_visible():
                    log("Download button appeared!")
                    await page.screenshot(path="test_4_download_ready.png")
                    
                    # Start download
                    log("Starting download...")
                    async with page.expect_download() as download_info:
                        await download_elem.click()
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
                                else:
                                    log("✗ WARNING: May not be a valid MP4")
                        else:
                            log("ERROR: Download file not found")
                    
                    break
                
                # Check progress
                if await progress_elem.is_visible():
                    progress_text = await progress_elem.text_content()
                    if progress_text != last_progress:
                        log(f"Progress: {progress_text}")
                        last_progress = progress_text
                
                # Periodic screenshots
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0:  # Every 30 seconds
                    await page.screenshot(path=f"test_progress_{elapsed}s.png")
                
                await page.wait_for_timeout(5000)  # Check every 5 seconds
            
            # Final screenshot
            await page.screenshot(path="test_final_state.png")
            
            # Summary
            total_time = time.time() - start_time
            log(f"\nTest completed in {total_time:.1f} seconds")
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            await page.screenshot(path="test_exception_error.png")
            
        finally:
            # Cleanup
            await browser.close()
            
            # Clean up test images
            for img in image_files:
                if os.path.exists(img):
                    os.remove(img)

async def main():
    """Run the test"""
    log("="*60)
    log("REAL USER TEST - Virtual Tour Generator")
    log("="*60)
    
    await test_as_real_user()
    
    # List all downloaded files
    log("\nDownloaded files:")
    if os.path.exists(DOWNLOAD_DIR):
        files = os.listdir(DOWNLOAD_DIR)
        for f in files:
            path = os.path.join(DOWNLOAD_DIR, f)
            size = os.path.getsize(path) / (1024 * 1024)
            log(f"- {f} ({size:.2f} MB)")
    
    log("\nScreenshots created:")
    screenshots = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.png')]
    for s in screenshots:
        log(f"- {s}")
    
    log("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())