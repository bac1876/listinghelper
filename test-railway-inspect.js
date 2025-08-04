const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true 
  });
  const page = await browser.newPage();
  
  // Enable verbose console logging
  page.on('console', async msg => {
    const args = await Promise.all(
      msg.args().map(arg => arg.jsonValue().catch(() => arg.toString()))
    );
    console.log(`[${msg.type().toUpperCase()}]`, msg.text(), args.length > 1 ? args : '');
  });

  page.on('pageerror', error => {
    console.error('[PAGE ERROR]', error.message);
  });

  page.on('requestfailed', request => {
    console.error('[FAILED]', request.method(), request.url(), '-', request.failure()?.errorText);
  });

  console.log('=== Railway Deployment Inspection ===\n');
  
  await page.goto('https://virtual-tour-generator-production.up.railway.app/');
  
  // Wait for page to fully load
  await page.waitForLoadState('networkidle');
  
  // Inspect Test Connection button
  console.log('1. Inspecting Test Connection button...');
  const testBtn = await page.$('#test-btn');
  if (testBtn) {
    const btnInfo = await testBtn.evaluate(el => ({
      id: el.id,
      className: el.className,
      textContent: el.textContent,
      isVisible: el.offsetParent !== null,
      display: window.getComputedStyle(el).display,
      visibility: window.getComputedStyle(el).visibility,
      opacity: window.getComputedStyle(el).opacity,
      position: window.getComputedStyle(el).position,
      zIndex: window.getComputedStyle(el).zIndex,
      parentDisplay: el.parentElement ? window.getComputedStyle(el.parentElement).display : 'none'
    }));
    console.log('Test button info:', btnInfo);
    
    // Force show the button
    await page.evaluate(() => {
      const btn = document.getElementById('test-btn');
      if (btn) {
        btn.style.display = 'inline-block';
        btn.style.visibility = 'visible';
        btn.style.opacity = '1';
        console.log('Forced test button to be visible');
      }
    });
    
    // Try clicking it now
    console.log('\nClicking Test Connection button...');
    await testBtn.click();
    await page.waitForTimeout(3000);
  } else {
    console.log('Test Connection button not found');
  }
  
  // Upload test images
  console.log('\n2. Testing image upload...');
  const fileInput = await page.$('input[type="file"]');
  if (fileInput) {
    // Create test images
    const fs = require('fs');
    const path = require('path');
    
    const testImage = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
    const imagePath1 = path.join(__dirname, 'test1.png');
    const imagePath2 = path.join(__dirname, 'test2.png');
    
    fs.writeFileSync(imagePath1, testImage);
    fs.writeFileSync(imagePath2, testImage);
    
    console.log('Uploading test images...');
    await fileInput.setInputFiles([imagePath1, imagePath2]);
    
    await page.waitForTimeout(2000);
    
    // Click generate button
    const generateBtn = await page.$('button:has-text("Generate Virtual Tour")');
    if (generateBtn) {
      console.log('Clicking Generate Virtual Tour...');
      await generateBtn.click();
      
      // Wait and capture any errors
      await page.waitForTimeout(5000);
    }
    
    // Clean up
    fs.unlinkSync(imagePath1);
    fs.unlinkSync(imagePath2);
  }
  
  // Check for any error messages on the page
  console.log('\n3. Checking for error messages...');
  const errorElements = await page.$$('text=/error/i, text=/fail/i, .error, .alert');
  for (const element of errorElements) {
    const text = await element.textContent();
    console.log('Found error element:', text);
  }
  
  // Get all network activity
  console.log('\n4. Capturing network activity...');
  const client = await page.context().newCDPSession(page);
  await client.send('Network.enable');
  
  // Log any failed requests
  client.on('Network.loadingFailed', event => {
    console.log('Network loading failed:', event.errorText, '-', event.url);
  });
  
  // Check localStorage/sessionStorage
  console.log('\n5. Checking storage...');
  const storage = await page.evaluate(() => ({
    localStorage: Object.fromEntries(Object.entries(localStorage)),
    sessionStorage: Object.fromEntries(Object.entries(sessionStorage))
  }));
  console.log('Storage:', storage);
  
  // Final state
  console.log('\n=== Final Page State ===');
  const pageTitle = await page.title();
  const pageURL = page.url();
  console.log('Title:', pageTitle);
  console.log('URL:', pageURL);
  
  // Take screenshot
  await page.screenshot({ path: 'railway-detailed-test.png', fullPage: true });
  console.log('Screenshot saved as railway-detailed-test.png');
  
  console.log('\n=== Keeping browser open for inspection ===');
  await page.waitForTimeout(60000);
  
  await browser.close();
})();