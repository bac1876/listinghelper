const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true 
  });
  const page = await browser.newPage();
  
  const logs = {
    console: [],
    errors: [],
    network: []
  };
  
  // Capture console
  page.on('console', msg => {
    const entry = `[${msg.type().toUpperCase()}] ${msg.text()}`;
    logs.console.push(entry);
    console.log(entry);
  });
  
  // Capture errors
  page.on('pageerror', error => {
    logs.errors.push(error.message);
    console.error('[PAGE ERROR]', error.message);
  });
  
  // Capture network
  page.on('response', response => {
    if (response.status() >= 400) {
      const entry = `${response.status()} ${response.url()}`;
      logs.network.push(entry);
      console.log('[HTTP ERROR]', entry);
    }
  });
  
  console.log('=== Testing Railway Deployment ===\n');
  
  // 1. Navigate
  console.log('1. Navigating to app...');
  await page.goto('https://virtual-tour-generator-production.up.railway.app/');
  await page.waitForLoadState('networkidle');
  console.log('   ✓ Page loaded\n');
  
  // 2. Check Test Connection button (without clicking if hidden)
  console.log('2. Checking Test Connection button...');
  const testBtn = await page.$('#test-btn');
  if (testBtn) {
    const isVisible = await testBtn.isVisible();
    console.log(`   ✓ Test Connection button found (visible: ${isVisible})`);
    
    if (isVisible) {
      console.log('   - Clicking Test Connection...');
      await testBtn.click();
      await page.waitForTimeout(3000);
    } else {
      console.log('   - Button is hidden, checking console for test functionality');
      
      // Try running test connection via console
      const testResult = await page.evaluate(async () => {
        try {
          // Check if testConnection function exists
          if (typeof window.testConnection === 'function') {
            console.log('Running testConnection() from console...');
            return await window.testConnection();
          } else {
            // Try to find and call it directly
            const response = await fetch('/api/test');
            return {
              status: response.status,
              statusText: response.statusText,
              text: await response.text()
            };
          }
        } catch (error) {
          return { error: error.message };
        }
      });
      console.log('   - Console test result:', testResult);
    }
  } else {
    console.log('   ✗ Test Connection button not found\n');
  }
  
  // 3. Upload test images
  console.log('\n3. Testing image upload...');
  const fileInput = await page.$('input[type="file"]');
  
  if (fileInput) {
    // Create small test images
    const testImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
    const img1 = path.join(__dirname, 'test1.png');
    const img2 = path.join(__dirname, 'test2.png');
    
    fs.writeFileSync(img1, testImage);
    fs.writeFileSync(img2, testImage);
    
    console.log('   - Selecting 2 test images...');
    await fileInput.setInputFiles([img1, img2]);
    await page.waitForTimeout(2000);
    
    // Try to generate
    const generateBtn = await page.$('button:has-text("Generate Virtual Tour")');
    if (generateBtn && await generateBtn.isVisible()) {
      console.log('   - Clicking Generate Virtual Tour...');
      await generateBtn.click();
      
      // Wait for any processing
      await page.waitForTimeout(10000);
      
      // Check for results or errors
      const bodyText = await page.$('body').then(el => el.textContent());
      if (bodyText.includes('error') || bodyText.includes('Error')) {
        console.log('   ✗ Error detected in page');
      }
    }
    
    // Cleanup
    fs.unlinkSync(img1);
    fs.unlinkSync(img2);
  } else {
    console.log('   ✗ No file input found');
  }
  
  // 4. Summary
  console.log('\n=== Test Summary ===');
  console.log('\nConsole logs:', logs.console.length ? logs.console : ['None']);
  console.log('\nPage errors:', logs.errors.length ? logs.errors : ['None']);
  console.log('\nHTTP errors:', logs.network.length ? logs.network : ['None']);
  
  // Check page content for API info
  const pageContent = await page.content();
  const hasTestBtn = pageContent.includes('test-btn');
  const hasAPI = pageContent.includes('/api/');
  console.log('\nPage analysis:');
  console.log(`- Has test button element: ${hasTestBtn}`);
  console.log(`- Has API references: ${hasAPI}`);
  
  // Screenshot
  await page.screenshot({ path: 'railway-final-state.png', fullPage: true });
  console.log('\n✓ Screenshot saved as railway-final-state.png');
  
  console.log('\n=== Test complete - browser will close in 10 seconds ===');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();