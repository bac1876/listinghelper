const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true // This will open developer tools
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enable console log capture
  const consoleLogs = [];
  page.on('console', msg => {
    consoleLogs.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      time: new Date().toISOString()
    });
    console.log(`Console ${msg.type()}: ${msg.text()}`);
  });
  
  // Capture page errors
  const pageErrors = [];
  page.on('pageerror', error => {
    pageErrors.push({
      message: error.message,
      stack: error.stack,
      time: new Date().toISOString()
    });
    console.log(`Page error: ${error.message}`);
  });
  
  // Capture network failures
  const networkErrors = [];
  page.on('requestfailed', request => {
    networkErrors.push({
      url: request.url(),
      method: request.method(),
      failure: request.failure(),
      time: new Date().toISOString()
    });
    console.log(`Request failed: ${request.url()} - ${request.failure()?.errorText}`);
  });
  
  // Capture all network requests
  const networkRequests = [];
  page.on('request', request => {
    if (request.url().includes('api') || request.url().includes('upload')) {
      networkRequests.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        postData: request.postData(),
        time: new Date().toISOString()
      });
      console.log(`API Request: ${request.method()} ${request.url()}`);
    }
  });
  
  // Capture network responses
  const networkResponses = [];
  page.on('response', response => {
    if (response.url().includes('api') || response.url().includes('upload')) {
      networkResponses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers(),
        time: new Date().toISOString()
      });
      console.log(`API Response: ${response.status()} ${response.url()}`);
    }
  });
  
  try {
    console.log('Navigating to Railway app...');
    await page.goto('https://virtual-tour-generator-production.up.railway.app/', {
      waitUntil: 'networkidle'
    });
    
    console.log('Page loaded. Waiting for form...');
    await page.waitForTimeout(2000);
    
    // Take a screenshot of initial state
    await page.screenshot({ path: 'initial_state.png', fullPage: true });
    
    // Check if Test Connection button is visible
    console.log('Checking for Test Connection button...');
    const testButton = await page.$('button:has-text("Test Connection")');
    if (testButton) {
      const isVisible = await testButton.isVisible();
      const boundingBox = await testButton.boundingBox();
      console.log(`Test Connection button found - Visible: ${isVisible}, BoundingBox:`, boundingBox);
      
      // Check computed styles
      const styles = await testButton.evaluate(el => {
        const computed = window.getComputedStyle(el);
        return {
          display: computed.display,
          visibility: computed.visibility,
          opacity: computed.opacity,
          position: computed.position,
          zIndex: computed.zIndex
        };
      });
      console.log('Test button styles:', styles);
    } else {
      console.log('Test Connection button NOT found in DOM');
    }
    
    // Fill in the form
    console.log('Filling in form fields...');
    
    // Try multiple selectors for property address
    try {
      const addressInput = await page.$('input[placeholder*="address" i], input[name*="address" i], input[id*="address" i], #propertyAddress');
      if (addressInput) {
        await addressInput.fill('123 Test Street');
        console.log('Filled property address');
      } else {
        console.log('Property address input not found');
        // Log all input elements for debugging
        const inputs = await page.$$eval('input', elements => 
          elements.map(el => ({
            placeholder: el.placeholder,
            name: el.name,
            id: el.id,
            type: el.type,
            className: el.className
          }))
        );
        console.log('All inputs on page:', inputs);
      }
      
      const agentInput = await page.$('input[placeholder*="agent" i]:not([placeholder*="phone" i]), input[name*="agent" i]:not([name*="phone" i]), #agentName');
      if (agentInput) {
        await agentInput.fill('Test Agent');
        console.log('Filled agent name');
      }
      
      const phoneInput = await page.$('input[placeholder*="phone" i], input[type="tel"], input[name*="phone" i], #agentPhone');
      if (phoneInput) {
        await phoneInput.fill('(555) 123-4567');
        console.log('Filled agent phone');
      }
    } catch (error) {
      console.log('Error filling form:', error.message);
    }
    
    // Create test images
    console.log('Creating test images...');
    const testImage1 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==', 'base64');
    const testImage2 = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
    
    fs.writeFileSync('test1.png', testImage1);
    fs.writeFileSync('test2.png', testImage2);
    
    // Upload images
    console.log('Uploading test images...');
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      await fileInput.setInputFiles(['test1.png', 'test2.png']);
      console.log('Images uploaded');
    } else {
      console.log('File input not found');
    }
    
    await page.waitForTimeout(1000);
    
    // Take screenshot before clicking generate
    await page.screenshot({ path: 'before_generate.png', fullPage: true });
    
    // Click Generate Virtual Tour button
    console.log('Clicking Generate Virtual Tour button...');
    const generateButton = await page.$('button:has-text("Generate Virtual Tour")');
    
    if (generateButton) {
      // Clear console logs before clicking
      consoleLogs.length = 0;
      
      await generateButton.click();
      console.log('Button clicked, waiting for response...');
      
      // Wait and observe what happens
      await page.waitForTimeout(10000); // Wait 10 seconds
      
      // Take screenshot after clicking
      await page.screenshot({ path: 'after_generate.png', fullPage: true });
      
      // Check for any status messages
      const statusElement = await page.$('.status-message, .error-message, [class*="status"], [class*="error"], [class*="message"]');
      if (statusElement) {
        const statusText = await statusElement.textContent();
        console.log('Status message found:', statusText);
      }
      
      // Check if still showing "Initializing..."
      const initializingText = await page.$('text=Initializing');
      if (initializingText) {
        const isVisible = await initializingText.isVisible();
        console.log('Initializing text still visible:', isVisible);
      }
      
    } else {
      console.log('Generate Virtual Tour button not found!');
    }
    
    // Final report
    console.log('\n=== FINAL REPORT ===');
    console.log('\nConsole Logs:', JSON.stringify(consoleLogs, null, 2));
    console.log('\nPage Errors:', JSON.stringify(pageErrors, null, 2));
    console.log('\nNetwork Errors:', JSON.stringify(networkErrors, null, 2));
    console.log('\nAPI Requests:', JSON.stringify(networkRequests, null, 2));
    console.log('\nAPI Responses:', JSON.stringify(networkResponses, null, 2));
    
    // Write detailed report
    const report = {
      timestamp: new Date().toISOString(),
      consoleLogs,
      pageErrors,
      networkErrors,
      apiRequests: networkRequests,
      apiResponses: networkResponses
    };
    
    fs.writeFileSync('test_report.json', JSON.stringify(report, null, 2));
    
  } catch (error) {
    console.error('Test error:', error);
  } finally {
    // Clean up test images
    if (fs.existsSync('test1.png')) fs.unlinkSync('test1.png');
    if (fs.existsSync('test2.png')) fs.unlinkSync('test2.png');
    
    console.log('\nTest complete. Check screenshots and test_report.json for details.');
    await page.waitForTimeout(5000); // Keep browser open for 5 seconds
    await browser.close();
  }
})();