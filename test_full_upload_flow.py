"""
Test the complete upload flow with Playwright to diagnose JSON download issue
"""
import os
import time
import subprocess
import json
from datetime import datetime

def start_server():
    """Start the Flask server"""
    print("Starting Flask server...")
    server = subprocess.Popen(
        ['py', 'main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(5)
    return server

def create_playwright_test():
    """Create and run Playwright test"""
    test_script = """
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
    console.log('Starting Playwright test...');
    const browser = await chromium.launch({ 
        headless: false,
        devtools: true 
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable detailed logging
    page.on('console', msg => {
        if (msg.type() !== 'debug') {
            console.log('PAGE LOG:', msg.text());
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`API Response: ${response.url()} - Status: ${response.status()}`);
        }
    });
    
    page.on('request', request => {
        if (request.url().includes('/api/') && request.method() === 'POST') {
            console.log(`API Request: ${request.url()}`);
        }
    });
    
    try {
        console.log('\\nNavigating to app...');
        await page.goto('http://localhost:5000', { timeout: 30000 });
        
        // Get test images
        const testImageDir = 'real_test_images';
        let imageFiles = [];
        
        if (fs.existsSync(testImageDir)) {
            const files = fs.readdirSync(testImageDir);
            imageFiles = files
                .filter(f => f.toLowerCase().endsWith('.jpg') || f.toLowerCase().endsWith('.png'))
                .slice(0, 3)  // Just use 3 images for quick test
                .map(f => path.join(testImageDir, f));
        }
        
        if (imageFiles.length === 0) {
            console.log('ERROR: No test images found');
            process.exit(1);
        }
        
        console.log(`\\nUploading ${imageFiles.length} test images...`);
        
        // Upload images
        await page.setInputFiles('#file-input', imageFiles);
        await page.waitForTimeout(2000);
        
        // Fill form
        await page.fill('#property-address', 'Test Property 123\\nTest City, State');
        await page.fill('#agent-name', 'Test Agent');
        await page.fill('#agent-phone', '555-1234');
        
        console.log('\\nClicking generate button...');
        await page.click('#generate-btn');
        
        // Monitor the upload request
        const uploadResponse = await page.waitForResponse(
            response => response.url().includes('/api/virtual-tour/upload'),
            { timeout: 30000 }
        );
        
        console.log(`\\nUpload response status: ${uploadResponse.status()}`);
        const uploadData = await uploadResponse.json();
        console.log('Upload response data:', JSON.stringify(uploadData, null, 2));
        
        const jobId = uploadData.job_id;
        console.log(`\\nJob ID: ${jobId}`);
        
        // Poll for completion
        let completed = false;
        let lastStatus = null;
        
        for (let i = 0; i < 60; i++) {
            await page.waitForTimeout(2000);
            
            // Check job status
            const statusResponse = await page.request.get(`http://localhost:5000/api/virtual-tour/job/${jobId}/status`);
            const statusData = await statusResponse.json();
            
            if (statusData.current_step !== lastStatus) {
                console.log(`[${i*2}s] Status: ${statusData.status} | Progress: ${statusData.progress}% | ${statusData.current_step}`);
                lastStatus = statusData.current_step;
            }
            
            // Log important transitions
            if (statusData.github_job_id) {
                console.log(`  GitHub Job ID: ${statusData.github_job_id}`);
            }
            if (statusData.cloudinary_video) {
                console.log(`  Cloudinary video: ${statusData.cloudinary_video}`);
            }
            
            if (statusData.status === 'completed') {
                completed = true;
                console.log('\\n[SUCCESS] Job completed!');
                
                // Try to download
                console.log('\\nAttempting download...');
                const downloadUrl = `http://localhost:5000/api/virtual-tour/download/${jobId}`;
                const downloadResponse = await page.request.get(downloadUrl);
                
                console.log(`Download status: ${downloadResponse.status()}`);
                console.log(`Download headers:`, downloadResponse.headers());
                
                const contentType = downloadResponse.headers()['content-type'];
                if (contentType.includes('json')) {
                    const jsonContent = await downloadResponse.json();
                    console.log('\\n[ERROR] Got JSON instead of video!');
                    console.log('JSON content:', JSON.stringify(jsonContent, null, 2));
                } else if (contentType.includes('html')) {
                    console.log('\\n[ERROR] Got HTML instead of video!');
                    const htmlContent = await downloadResponse.text();
                    console.log('HTML preview:', htmlContent.substring(0, 500));
                } else if (contentType.includes('video')) {
                    console.log('\\n[SUCCESS] Got video file!');
                } else {
                    console.log(`\\n? Unknown content type: ${contentType}`);
                }
                
                break;
            } else if (statusData.status === 'error') {
                console.log(`\\n[ERROR] Job failed: ${statusData.current_step}`);
                break;
            }
        }
        
        if (!completed) {
            console.log('\\n[WARNING] Job did not complete within 2 minutes');
        }
        
    } catch (error) {
        console.error('\\nTest failed:', error);
        process.exit(1);
    } finally {
        await page.screenshot({ path: 'test_result.png', fullPage: true });
        await browser.close();
    }
    
    process.exit(0);
})();
"""
    
    # Write test script
    with open('playwright_test.js', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    # Run test
    print("\nRunning Playwright test...")
    result = subprocess.run(
        ['node', 'playwright_test.js'],
        capture_output=True,
        text=True,
        timeout=180
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def check_env_setup():
    """Check environment setup"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*60)
    print("ENVIRONMENT CHECK")
    print("="*60)
    
    checks = {
        'USE_GITHUB_ACTIONS': os.environ.get('USE_GITHUB_ACTIONS'),
        'GITHUB_TOKEN': os.environ.get('GITHUB_TOKEN'),
        'GITHUB_OWNER': os.environ.get('GITHUB_OWNER'),
        'GITHUB_REPO': os.environ.get('GITHUB_REPO'),
        'CLOUDINARY_CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'CLOUDINARY_API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    }
    
    all_good = True
    for key, value in checks.items():
        if value:
            if 'TOKEN' in key or 'KEY' in key or 'SECRET' in key:
                print(f"[OK] {key}: [SET - {len(value)} chars]")
            else:
                print(f"[OK] {key}: {value}")
        else:
            print(f"[MISSING] {key}: NOT SET")
            all_good = False
    
    if not all_good:
        print("\n[WARNING] Some environment variables are missing!")
        print("Check your .env file and make sure GITHUB_TOKEN is uncommented")
    
    return all_good

def main():
    print("="*60)
    print("FULL UPLOAD FLOW TEST")
    print("="*60)
    
    # Check environment
    env_ok = check_env_setup()
    
    if not env_ok:
        print("\n[ERROR] Fix environment variables first!")
        print("Especially check that GITHUB_TOKEN is uncommented in .env")
        return
    
    # Start server
    server = start_server()
    
    try:
        # Run Playwright test
        success = create_playwright_test()
        
        if success:
            print("\n[SUCCESS] Test completed successfully")
        else:
            print("\n[FAILED] Test failed - check output above")
            
    finally:
        # Stop server
        server.terminate()
        print("\nServer stopped")
        
        # Clean up
        if os.path.exists('playwright_test.js'):
            os.remove('playwright_test.js')

if __name__ == "__main__":
    main()