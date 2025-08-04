const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true 
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture all network requests
  const networkRequests = [];
  page.on('request', request => {
    networkRequests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers(),
      timestamp: new Date().toISOString()
    });
  });

  // Capture all network responses
  const networkResponses = [];
  page.on('response', response => {
    networkResponses.push({
      url: response.url(),
      status: response.status(),
      statusText: response.statusText(),
      timestamp: new Date().toISOString()
    });
    if (response.status() >= 400) {
      console.log(`[HTTP ${response.status()}] ${response.url()}`);
    }
  });

  // Collect console logs with more detail
  page.on('console', async msg => {
    const args = await Promise.all(msg.args().map(arg => arg.jsonValue().catch(() => arg.toString())));
    console.log(`[CONSOLE ${msg.type().toUpperCase()}] ${msg.text()}`, args.length > 1 ? args : '');
  });

  // Collect page errors
  page.on('pageerror', error => {
    console.error(`[PAGE ERROR] ${error.message}`);
  });

  console.log('=== Starting Detailed Railway Test ===\n');
  
  try {
    // Navigate to the app
    console.log('Navigating to: https://virtual-tour-generator-production.up.railway.app/');
    await page.goto('https://virtual-tour-generator-production.up.railway.app/', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Check for Test Connection button
    console.log('\nLooking for Test Connection button...');
    const testConnectionButton = await page.locator('button:has-text("Test Connection"), button:has-text("test connection")', { hasText: /test.*connection/i });
    
    if (await testConnectionButton.count() > 0) {
      console.log('Found Test Connection button!');
      await testConnectionButton.first().click();
      await page.waitForTimeout(3000);
    } else {
      console.log('Test Connection button not found on the page');
      
      // Try to find it in the browser console or look for hidden elements
      const allButtons = await page.locator('button').all();
      console.log(`\nFound ${allButtons.length} buttons on the page:`);
      for (const button of allButtons) {
        const text = await button.textContent();
        const isVisible = await button.isVisible();
        console.log(`  - "${text?.trim()}" (visible: ${isVisible})`);
      }
    }

    // Try clicking Generate Virtual Tour to see what happens
    console.log('\nTrying to click Generate Virtual Tour button...');
    const generateButton = await page.locator('button:has-text("Generate Virtual Tour")').first();
    if (await generateButton.isVisible()) {
      await generateButton.click();
      console.log('Clicked Generate Virtual Tour button');
      await page.waitForTimeout(3000);
    }

    // Check for any API endpoints or configuration
    console.log('\nChecking page for API configuration...');
    const pageContent = await page.content();
    
    // Look for API URLs in the page
    const apiMatches = pageContent.match(/https?:\/\/[^\s"']+api[^\s"']*/gi);
    if (apiMatches) {
      console.log('Found API references:');
      [...new Set(apiMatches)].forEach(url => console.log(`  - ${url}`));
    }

    // Check network requests for API calls
    console.log('\nAPI Requests made:');
    const apiRequests = networkRequests.filter(req => 
      req.url.includes('api') || 
      req.url.includes('webhook') || 
      req.url.includes('instantdeco') ||
      req.method !== 'GET'
    );
    
    if (apiRequests.length === 0) {
      console.log('  No API requests detected');
    } else {
      apiRequests.forEach(req => {
        console.log(`  ${req.method} ${req.url}`);
      });
    }

    // Check for errors in responses
    console.log('\nHTTP Errors:');
    const errorResponses = networkResponses.filter(res => res.status >= 400);
    if (errorResponses.length === 0) {
      console.log('  No HTTP errors');
    } else {
      errorResponses.forEach(res => {
        console.log(`  ${res.status} ${res.statusText} - ${res.url}`);
      });
    }

    // Try to upload images and capture the process
    console.log('\nAttempting file upload...');
    const fileInput = await page.locator('input[type="file"]').first();
    
    // Create a simple test file
    await page.evaluate(() => {
      // Try to trigger any file selection events
      const input = document.querySelector('input[type="file"]');
      if (input) {
        const event = new Event('change', { bubbles: true });
        input.dispatchEvent(event);
      }
    });

    await page.waitForTimeout(2000);

    // Final summary
    console.log('\n=== Final Network Summary ===');
    console.log(`Total requests: ${networkRequests.length}`);
    console.log(`Total responses: ${networkResponses.length}`);
    console.log(`Error responses: ${errorResponses.length}`);
    
    // Get all text content to check for error messages
    const bodyText = await page.locator('body').textContent();
    if (bodyText.includes('error') || bodyText.includes('Error')) {
      console.log('\nError messages found in page content!');
    }

  } catch (error) {
    console.error('\n[TEST ERROR]', error);
  }
  
  console.log('\n=== Test Complete - Keeping browser open ===');
  await page.waitForTimeout(60000);
  
  await browser.close();
})();