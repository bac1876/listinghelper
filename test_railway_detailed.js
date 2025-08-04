const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Capture ALL console logs
  const allLogs = [];
  page.on('console', msg => {
    const log = {
      type: msg.type(),
      text: msg.text(),
      args: msg.args().length,
      time: new Date().toISOString()
    };
    allLogs.push(log);
    console.log(`[${msg.type()}] ${msg.text()}`);
  });
  
  // Capture ALL network activity
  const allRequests = [];
  page.on('request', request => {
    const req = {
      url: request.url(),
      method: request.method(),
      resourceType: request.resourceType(),
      time: new Date().toISOString()
    };
    allRequests.push(req);
    console.log(`[${request.method()}] ${request.url()}`);
  });
  
  const allResponses = [];
  page.on('response', response => {
    const res = {
      url: response.url(),
      status: response.status(),
      statusText: response.statusText(),
      time: new Date().toISOString()
    };
    allResponses.push(res);
    console.log(`[${response.status()}] ${response.url()}`);
  });
  
  try {
    console.log('\n=== NAVIGATING TO APP ===');
    await page.goto('https://virtual-tour-generator-production.up.railway.app/', {
      waitUntil: 'networkidle'
    });
    
    // Wait for page to fully load
    await page.waitForTimeout(3000);
    
    console.log('\n=== CHECKING PAGE STRUCTURE ===');
    
    // Check what's actually visible on the page
    const visibleText = await page.evaluate(() => {
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
      );
      const texts = [];
      let node;
      while (node = walker.nextNode()) {
        const text = node.textContent.trim();
        if (text.length > 0) {
          texts.push(text);
        }
      }
      return texts;
    });
    console.log('Visible text on page:', visibleText.slice(0, 20)); // First 20 text elements
    
    // Check for buttons
    const buttons = await page.$$eval('button', elements => 
      elements.map(el => ({
        text: el.textContent,
        visible: el.offsetWidth > 0 && el.offsetHeight > 0,
        disabled: el.disabled,
        className: el.className,
        onclick: el.onclick ? 'has onclick' : 'no onclick'
      }))
    );
    console.log('\nButtons found:', buttons);
    
    // Check form structure
    const forms = await page.$$eval('form', elements => 
      elements.map(el => ({
        id: el.id,
        className: el.className,
        action: el.action,
        method: el.method
      }))
    );
    console.log('\nForms found:', forms);
    
    // Try to find the Generate button with various selectors
    console.log('\n=== LOOKING FOR GENERATE BUTTON ===');
    const generateSelectors = [
      'button:has-text("Generate")',
      'button[type="submit"]',
      '#generate-button',
      '.generate-btn',
      'button'
    ];
    
    let generateButton = null;
    for (const selector of generateSelectors) {
      const btn = await page.$(selector);
      if (btn) {
        const text = await btn.textContent();
        if (text && text.toLowerCase().includes('generate')) {
          generateButton = btn;
          console.log(`Found generate button with selector: ${selector}, text: ${text}`);
          break;
        }
      }
    }
    
    if (generateButton) {
      // Clear logs before clicking
      allLogs.length = 0;
      allRequests.length = 0;
      allResponses.length = 0;
      
      console.log('\n=== CLICKING GENERATE BUTTON ===');
      
      // Add event listener to capture any JavaScript errors
      await page.evaluate(() => {
        window.addEventListener('error', (e) => {
          console.error('Window error:', e.message, e.filename, e.lineno, e.colno);
        });
        window.addEventListener('unhandledrejection', (e) => {
          console.error('Unhandled promise rejection:', e.reason);
        });
      });
      
      await generateButton.click();
      
      // Wait and monitor for 15 seconds
      console.log('Monitoring for 15 seconds...');
      for (let i = 0; i < 15; i++) {
        await page.waitForTimeout(1000);
        
        // Check current status
        const statusElements = await page.$$eval('[class*="status"], [class*="message"], [class*="error"], .status, .message, .error', elements =>
          elements.map(el => ({
            text: el.textContent,
            className: el.className,
            visible: el.offsetWidth > 0 && el.offsetHeight > 0
          }))
        );
        
        if (statusElements.length > 0) {
          console.log(`[${i+1}s] Status elements:`, statusElements.filter(s => s.visible));
        }
      }
      
      // Final screenshot
      await page.screenshot({ path: 'final_state.png', fullPage: true });
      
    } else {
      console.log('Generate button not found!');
    }
    
    // Generate detailed report
    const report = {
      timestamp: new Date().toISOString(),
      pageStructure: {
        buttons,
        forms,
        visibleTextSample: visibleText.slice(0, 20)
      },
      afterClickActivity: {
        consoleLogs: allLogs,
        networkRequests: allRequests.filter(r => r.time > allLogs[0]?.time),
        networkResponses: allResponses.filter(r => r.time > allLogs[0]?.time)
      }
    };
    
    fs.writeFileSync('detailed_report.json', JSON.stringify(report, null, 2));
    console.log('\n=== TEST COMPLETE ===');
    console.log('Check detailed_report.json for full details');
    
  } catch (error) {
    console.error('Test error:', error);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();