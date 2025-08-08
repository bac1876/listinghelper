const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// CHANGE THIS TO YOUR RAILWAY URL
const RAILWAY_URL = 'https://listinghelper-production.up.railway.app';
// Or if different, update it

(async () => {
    console.log('=====================================');
    console.log('TESTING RAILWAY DEPLOYMENT');
    console.log('=====================================');
    console.log(`URL: ${RAILWAY_URL}`);
    console.log('');

    const browser = await chromium.launch({ 
        headless: false,
        devtools: true 
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enable detailed logging
    page.on('console', msg => {
        if (msg.type() !== 'debug') {
            console.log('PAGE:', msg.text());
        }
    });
    
    page.on('response', response => {
        if (response.url().includes('/api/')) {
            console.log(`API Response: ${response.url()} - ${response.status()}`);
        }
    });
    
    let jobId = null;
    
    // Intercept the upload response to get job ID
    page.on('response', async response => {
        if (response.url().includes('/api/virtual-tour/upload') && response.status() === 200) {
            try {
                const data = await response.json();
                jobId = data.job_id;
                console.log('\n=== UPLOAD RESPONSE ===');
                console.log(JSON.stringify(data, null, 2));
                console.log('=======================\n');
            } catch (e) {}
        }
    });
    
    try {
        console.log('1. Navigating to Railway app...');
        await page.goto(RAILWAY_URL, { timeout: 30000 });
        console.log('   ✓ Page loaded');
        
        // Take screenshot
        await page.screenshot({ path: 'railway_test_1_loaded.png' });
        
        // Get test images
        const testImageDir = 'real_test_images';
        let imageFiles = [];
        
        if (fs.existsSync(testImageDir)) {
            const files = fs.readdirSync(testImageDir);
            imageFiles = files
                .filter(f => f.toLowerCase().endsWith('.jpg') || f.toLowerCase().endsWith('.png'))
                .slice(0, 3)  // Use 3 images
                .map(f => path.join(testImageDir, f));
        }
        
        if (imageFiles.length === 0) {
            // Create test images if none exist
            console.log('   Creating test images...');
            // This is a fallback - you should have real images
            imageFiles = ['test1.jpg', 'test2.jpg', 'test3.jpg'];
        }
        
        console.log(`\n2. Uploading ${imageFiles.length} images...`);
        
        // Upload images
        const fileInput = await page.locator('#file-input');
        await fileInput.setInputFiles(imageFiles);
        await page.waitForTimeout(2000);
        
        console.log('   ✓ Images selected');
        await page.screenshot({ path: 'railway_test_2_images.png' });
        
        // Fill form
        console.log('\n3. Filling property details...');
        await page.fill('#property-address', 'Test Property 123\nTest City, State');
        await page.fill('#agent-name', 'Test Agent');
        await page.fill('#agent-phone', '555-1234');
        console.log('   ✓ Form filled');
        
        // Click generate with force
        console.log('\n4. Clicking generate button...');
        await page.locator('#generate-btn').click({ force: true });
        console.log('   ✓ Generate clicked');
        
        // Wait for processing
        console.log('\n5. Waiting for processing...');
        await page.waitForTimeout(5000);
        
        // Take screenshot of processing
        await page.screenshot({ path: 'railway_test_3_processing.png' });
        
        // Check if results section appears
        const resultsSection = await page.locator('#results-section');
        let isVisible = false;
        
        console.log('\n6. Checking job status...');
        for (let i = 0; i < 60; i++) {
            await page.waitForTimeout(2000);
            
            isVisible = await resultsSection.isVisible();
            if (isVisible) {
                console.log('   ✓ Results section visible');
                break;
            }
            
            // Check progress
            const progressText = await page.locator('#status-message').textContent().catch(() => '');
            if (progressText && i % 5 === 0) {
                console.log(`   Progress: ${progressText}`);
            }
        }
        
        // Take final screenshot
        await page.screenshot({ path: 'railway_test_4_complete.png', fullPage: true });
        
        if (isVisible) {
            // Check if it's success or error
            const hasError = await resultsSection.evaluate(el => el.classList.contains('error'));
            
            if (hasError) {
                const errorMessage = await page.locator('#results-message').textContent();
                console.log(`\n❌ ERROR: ${errorMessage}`);
            } else {
                console.log('\n✓ Video generation completed!');
                
                // Try to download
                const downloadBtn = await page.locator('#download-btn');
                if (await downloadBtn.isVisible()) {
                    console.log('\n7. Testing download...');
                    
                    // Get onclick attribute
                    const onclick = await downloadBtn.getAttribute('onclick');
                    console.log(`   Download onclick: ${onclick}`);
                    
                    // Extract job ID from onclick
                    const match = onclick ? onclick.match(/downloadVideo\('([^']+)'\)/) : null;
                    if (match) {
                        const downloadJobId = match[1];
                        console.log(`   Job ID: ${downloadJobId}`);
                        
                        // Test the download endpoint directly
                        const downloadUrl = `${RAILWAY_URL}/api/virtual-tour/download/${downloadJobId}`;
                        console.log(`   Testing: ${downloadUrl}`);
                        
                        const downloadResponse = await page.request.get(downloadUrl);
                        const contentType = downloadResponse.headers()['content-type'];
                        
                        console.log(`   Response status: ${downloadResponse.status()}`);
                        console.log(`   Content-Type: ${contentType}`);
                        
                        if (contentType.includes('json')) {
                            const jsonData = await downloadResponse.json();
                            console.log('\n❌ PROBLEM: Download returned JSON!');
                            console.log('JSON content:', JSON.stringify(jsonData, null, 2));
                        } else if (contentType.includes('html')) {
                            console.log('\n❌ PROBLEM: Download returned HTML!');
                        } else if (contentType.includes('video')) {
                            console.log('\n✓ SUCCESS: Download returned video!');
                        }
                    }
                }
            }
        } else {
            console.log('\n⚠ Timeout: Results never appeared');
        }
        
        // If we have a job ID, check its status via API
        if (jobId) {
            console.log(`\n8. Checking job status via API: ${jobId}`);
            const statusUrl = `${RAILWAY_URL}/api/virtual-tour/job/${jobId}/status`;
            const statusResponse = await page.request.get(statusUrl);
            
            if (statusResponse.ok()) {
                const statusData = await statusResponse.json();
                console.log('\nJob Status:');
                console.log(JSON.stringify(statusData, null, 2));
            }
        }
        
    } catch (error) {
        console.error('\n❌ Test failed:', error);
        await page.screenshot({ path: 'railway_test_error.png', fullPage: true });
    } finally {
        console.log('\n=====================================');
        console.log('TEST COMPLETE');
        console.log('Screenshots saved: railway_test_*.png');
        console.log('=====================================');
        
        await browser.close();
    }
})();