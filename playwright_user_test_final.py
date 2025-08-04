#!/usr/bin/env python3
"""
Real user test using Playwright - Final version
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
    log("Starting Playwright user test - Final")
    
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
            
            # Method 1: Try clicking Select Photos button to trigger file dialog
            select_photos_btn = page.locator('button:has-text("Select Photos")')
            if await select_photos_btn.is_visible():
                log("Found 'Select Photos' button")
                
                # Set up file chooser before clicking
                async with page.expect_file_chooser() as fc_info:
                    await select_photos_btn.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(image_files)
                    log(f"Selected {len(image_files)} files via file chooser")
                
                await page.wait_for_timeout(2000)
                
                # Take screenshot after file selection
                await page.screenshot(path="test_2_files_selected.png")
                log("Screenshot: Files selected")
            else:
                # Method 2: Try drag and drop
                log("Select Photos button not found, trying drag-drop area")
                drop_zone = page.locator('.dropzone, [class*="drop"], #dropzone').first
                if await drop_zone.is_visible():
                    # This would require more complex implementation
                    log("Drop zone found but file upload via drag-drop not implemented")
                    return
            
            # Wait for form or next step to appear
            await page.wait_for_timeout(2000)
            
            # Scroll to see more content
            await page.evaluate('window.scrollTo(0, 500)')
            await page.wait_for_timeout(1000)
            
            # Take screenshot to see current state
            await page.screenshot(path="test_3_after_upload.png")
            log("Screenshot: After upload")
            
            # Look for property details inputs
            log("Looking for property details form...")
            
            # Try to find and fill visible text inputs
            # Address
            address_input = page.locator('input[placeholder*="address" i], input[name*="address" i], input#address').first
            if await address_input.is_visible():
                await address_input.fill("123 Sunset Boulevard")
                log("Filled address")
            
            # City
            city_input = page.locator('input[placeholder*="city" i], input[name*="city" i], input#city').first
            if await city_input.is_visible():
                await city_input.fill("Beverly Hills, CA 90210")
                log("Filled city")
            
            # Agent Name
            agent_input = page.locator('input[placeholder*="agent" i][placeholder*="name" i], input[name*="agent_name" i], input#agent_name').first
            if await agent_input.is_visible():
                await agent_input.fill("John Smith")
                log("Filled agent name")
            
            # Phone
            phone_input = page.locator('input[placeholder*="phone" i], input[name*="phone" i], input#agent_phone').first
            if await phone_input.is_visible():
                await phone_input.fill("(555) 123-4567")
                log("Filled phone")
            
            # Take screenshot of filled form
            await page.screenshot(path="test_4_form_filled.png")
            log("Screenshot: Form filled")
            
            # Find and click generate button
            generate_btn = None
            button_selectors = [
                'button:has-text("Generate Virtual Tour")',
                'button:has-text("Generate Tour")', 
                'button:has-text("Create Tour")',
                'button:has-text("Generate")',
                'button:has-text("Create")',
                'button[type="submit"]',
                '.generate-button',
                '#generateBtn'
            ]
            
            for selector in button_selectors:
                btn = page.locator(selector).first
                if await btn.is_visible():
                    generate_btn = btn
                    log(f"Found generate button: {selector}")
                    break
            
            if not generate_btn:
                log("ERROR: No generate button found")
                await page.screenshot(path="error_no_generate_button.png")
                # List all visible buttons
                buttons = await page.locator('button:visible').all()
                log(f"Visible buttons: {len(buttons)}")
                for i, btn in enumerate(buttons[:5]):  # First 5 buttons
                    try:
                        text = await btn.text_content()
                        log(f"  Button {i}: '{text}'")
                    except:
                        pass
                return
            
            # Click generate button
            log("Clicking generate button...")
            await generate_btn.click()
            
            # Wait for processing
            await page.wait_for_timeout(5000)
            await page.screenshot(path="test_5_processing.png")
            log("Screenshot: Processing")
            
            # Monitor for completion
            start_time = time.time()
            max_wait = 900  # 15 minutes
            download_completed = False
            last_status = ""
            
            while (time.time() - start_time) < max_wait:
                # Check page content
                page_content = await page.content()
                
                # Check for download link
                if "download" in page_content.lower() or ".mp4" in page_content:
                    # Look for download elements
                    download_link = page.locator('a[href*=".mp4"], a:has-text("Download"), button:has-text("Download")').first
                    if await download_link.is_visible():
                        log("Found download link!")
                        await page.screenshot(path="test_6_download_ready.png")
                        
                        # Get href if it's a link
                        href = await download_link.get_attribute('href')
                        if href and href.endswith('.mp4'):
                            log(f"Direct download link: {href}")
                            # Download directly
                            download_resp = requests.get(href if href.startswith('http') else f"{APP_URL}{href}")
                            if download_resp.status_code == 200:
                                filename = f"video_{int(time.time())}.mp4"
                                filepath = os.path.join(DOWNLOAD_DIR, filename)
                                with open(filepath, 'wb') as f:
                                    f.write(download_resp.content)
                                log(f"Downloaded: {filename}")
                                download_completed = True
                                break
                        else:
                            # Click to download
                            async with page.expect_download() as download_info:
                                await download_link.click()
                                download = await download_info.value
                                suggested_name = download.suggested_filename
                                download_path = os.path.join(DOWNLOAD_DIR, suggested_name)
                                await download.save_as(download_path)
                                log(f"Downloaded: {suggested_name}")
                                download_completed = True
                                break
                
                # Check for errors
                if "error" in page_content.lower() or "failed" in page_content.lower():
                    error_elem = page.locator('.error, .alert, [class*="error"]').first
                    if await error_elem.is_visible():
                        error_text = await error_elem.text_content()
                        if error_text != last_status:
                            log(f"Status update: {error_text}")
                            last_status = error_text
                            await page.screenshot(path=f"test_status_{int(time.time())}.png")
                
                # Check for progress
                progress_elem = page.locator('.progress-text, .status, [class*="progress"]').first
                if await progress_elem.is_visible():
                    try:
                        progress_text = await progress_elem.text_content()
                        if progress_text != last_status and progress_text.strip():
                            log(f"Progress: {progress_text}")
                            last_status = progress_text
                    except:
                        pass
                
                # Periodic status check
                elapsed = int(time.time() - start_time)
                if elapsed % 30 == 0 and elapsed > 0:
                    log(f"Still waiting... ({elapsed}s elapsed)")
                    await page.screenshot(path=f"test_waiting_{elapsed}s.png")
                
                await page.wait_for_timeout(5000)
            
            # Final screenshot
            await page.screenshot(path="test_final_state.png")
            
            # Summary
            total_time = time.time() - start_time
            log(f"\nTest completed in {total_time:.1f} seconds")
            
            if download_completed:
                log("✓ SUCCESS: Video downloaded!")
                # Verify downloaded files
                if os.path.exists(DOWNLOAD_DIR):
                    files = os.listdir(DOWNLOAD_DIR)
                    for f in files:
                        filepath = os.path.join(DOWNLOAD_DIR, f)
                        size = os.path.getsize(filepath) / (1024 * 1024)
                        # Check MP4 header
                        with open(filepath, 'rb') as file:
                            header = file.read(12)
                            if b'ftyp' in header:
                                log(f"✓ {f} - Valid MP4 ({size:.2f} MB)")
                            else:
                                log(f"✗ {f} - Invalid MP4 ({size:.2f} MB)")
            else:
                log("✗ TIMEOUT: No download completed")
            
        except Exception as e:
            log(f"ERROR: {str(e)}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            await page.screenshot(path="test_exception_error.png")
            
        finally:
            # Keep browser open briefly
            await page.wait_for_timeout(3000)
            await browser.close()
            
            # Clean up test images
            for img in image_files:
                if os.path.exists(img):
                    os.remove(img)

async def main():
    """Run the test"""
    log("="*60)
    log("REAL USER TEST FINAL - Virtual Tour Generator")
    log("="*60)
    
    await test_as_real_user()
    
    # Summary
    log("\n" + "="*60)
    log("TEST SUMMARY")
    log("="*60)
    
    # Downloaded files
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
    else:
        log("- Download directory not found")
    
    # Screenshots
    log("\nScreenshots created:")
    screenshots = sorted([f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.png')])
    for s in screenshots:
        log(f"- {s}")
    
    log("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())