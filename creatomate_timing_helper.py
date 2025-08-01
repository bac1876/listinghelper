"""
Simplified Creatomate timing adjustment helper
"""
from playwright.sync_api import sync_playwright
import time

def help_adjust_timing():
    """Guide through adjusting Creatomate template timing"""
    
    template_url = "https://creatomate.com/projects/561802cc-1851-4993-8742-55b2dc4fcd1d/templates/5c2eca01-84b8-4302-bad2-9189db4dae70"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Opening Creatomate template editor...")
        page.goto(template_url)
        
        print("\nWaiting for page to load...")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Check if login is needed
        if "login" in page.url.lower():
            print("\nLOGIN REQUIRED")
            print("Please log in to Creatomate in the browser window.")
            print("Press Enter after you've logged in...")
            input()
            
            # Go back to template
            page.goto(template_url)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
        
        print("\nTaking screenshot of template editor...")
        page.screenshot(path="template_editor_full.png")
        
        print("\nINSTRUCTIONS FOR ADJUSTING TIMING:")
        print("\n1. FIND THE TIMELINE")
        print("   - Look at the bottom of the editor for a timeline")
        print("   - You should see 5 'Photo' blocks in the timeline")
        
        print("\n2. ADJUST EACH PHOTO DURATION")
        print("   - Click on 'Photo-1' in the timeline")
        print("   - Look for a duration field (might show '12.00s')")
        print("   - Change it to '20.00s' or '24.00s' for slower display")
        print("   - Repeat for Photo-2, Photo-3, Photo-4, and Photo-5")
        
        print("\n3. ADJUST TRANSITIONS (if visible)")
        print("   - Look for transition markers between photos")
        print("   - These might be adjustable too")
        
        print("\n4. SAVE YOUR CHANGES")
        print("   - Click the 'Save' or 'Update' button")
        print("   - Usually in the top-right corner")
        
        print("\n" + "="*60)
        print("Make these adjustments in the browser window.")
        print("Press Enter when you're done...")
        input()
        
        # Take a final screenshot
        page.screenshot(path="template_editor_after_changes.png")
        print("\nScreenshot saved: template_editor_after_changes.png")
        
        print("\nDONE! Your template should now have slower timing.")
        print("Generate a new video to test the changes.")
        
        browser.close()

if __name__ == "__main__":
    print("Creatomate Template Timing Helper")
    print("="*40)
    help_adjust_timing()