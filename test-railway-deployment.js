const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true 
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Collect console logs
  const consoleLogs = [];
  page.on('console', msg => {
    const logEntry = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      timestamp: new Date().toISOString()
    };
    consoleLogs.push(logEntry);
    console.log(`[CONSOLE ${msg.type().toUpperCase()}] ${msg.text()}`);
  });

  // Collect page errors
  const pageErrors = [];
  page.on('pageerror', error => {
    const errorEntry = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    };
    pageErrors.push(errorEntry);
    console.error(`[PAGE ERROR] ${error.message}`);
  });

  // Collect network failures
  const networkFailures = [];
  page.on('requestfailed', request => {
    const failure = {
      url: request.url(),
      method: request.method(),
      failure: request.failure(),
      timestamp: new Date().toISOString()
    };
    networkFailures.push(failure);
    console.error(`[NETWORK FAILURE] ${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
  });

  console.log('=== Starting Railway Deployment Test ===\n');
  
  try {
    // 1. Navigate to the app
    console.log('1. Navigating to the app...');
    await page.goto('https://virtual-tour-generator-production.up.railway.app/', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    console.log('   ✓ Page loaded successfully\n');

    // Wait a moment for any initial setup
    await page.waitForTimeout(2000);

    // 2. Click the "Test Connection" button
    console.log('2. Looking for Test Connection button...');
    const testButton = await page.locator('button:has-text("Test Connection")').first();
    
    if (await testButton.isVisible()) {
      console.log('   ✓ Found Test Connection button');
      await testButton.click();
      console.log('   ✓ Clicked Test Connection button');
      
      // Wait for any response
      await page.waitForTimeout(3000);
    } else {
      console.log('   ✗ Test Connection button not found');
    }
    console.log('');

    // 3. Try uploading test images
    console.log('3. Attempting to upload test images...');
    
    // Create small test images
    const testImage1 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
    const testImage2 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
    
    const tempDir = path.join(__dirname, 'temp');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir);
    }
    
    const image1Path = path.join(tempDir, 'test1.png');
    const image2Path = path.join(tempDir, 'test2.png');
    
    fs.writeFileSync(image1Path, testImage1);
    fs.writeFileSync(image2Path, testImage2);
    
    // Look for file input
    const fileInput = await page.locator('input[type="file"]').first();
    
    if (await fileInput.count() > 0) {
      console.log('   ✓ Found file input');
      
      // Upload both images
      await fileInput.setInputFiles([image1Path, image2Path]);
      console.log('   ✓ Selected 2 test images');
      
      // Wait for any upload process
      await page.waitForTimeout(5000);
      
      // Look for upload button or automatic upload
      const uploadButton = await page.locator('button:has-text("Upload"), button:has-text("Generate"), button:has-text("Create"), button:has-text("Start")').first();
      
      if (await uploadButton.isVisible()) {
        console.log(`   ✓ Found button: ${await uploadButton.textContent()}`);
        await uploadButton.click();
        console.log('   ✓ Clicked upload/generate button');
        
        // Wait for processing
        await page.waitForTimeout(10000);
      } else {
        console.log('   - No upload/generate button found (may be auto-uploading)');
      }
    } else {
      console.log('   ✗ No file input found on the page');
    }
    
    // Clean up temp files
    fs.unlinkSync(image1Path);
    fs.unlinkSync(image2Path);
    fs.rmdirSync(tempDir);
    
    console.log('\n=== Test Results Summary ===\n');
    
    // Report console logs
    console.log('Console Logs:');
    if (consoleLogs.length === 0) {
      console.log('  No console logs captured');
    } else {
      consoleLogs.forEach(log => {
        console.log(`  [${log.type}] ${log.text}`);
      });
    }
    
    console.log('\nPage Errors:');
    if (pageErrors.length === 0) {
      console.log('  No page errors');
    } else {
      pageErrors.forEach(error => {
        console.log(`  ${error.message}`);
      });
    }
    
    console.log('\nNetwork Failures:');
    if (networkFailures.length === 0) {
      console.log('  No network failures');
    } else {
      networkFailures.forEach(failure => {
        console.log(`  ${failure.method} ${failure.url} - ${failure.failure?.errorText}`);
      });
    }
    
    // Take a final screenshot
    await page.screenshot({ path: 'railway-test-final.png', fullPage: true });
    console.log('\n✓ Screenshot saved as railway-test-final.png');
    
  } catch (error) {
    console.error('\n[TEST ERROR]', error);
  }
  
  // Keep browser open for manual inspection
  console.log('\n=== Test Complete - Browser will remain open for 30 seconds ===');
  await page.waitForTimeout(30000);
  
  await browser.close();
})();