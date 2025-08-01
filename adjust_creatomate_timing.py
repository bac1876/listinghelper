"""
Playwright script to automatically adjust timing in Creatomate template
"""
from playwright.sync_api import sync_playwright
import time
import os

def adjust_template_timing():
    """Navigate to Creatomate and adjust the template timing for slower image display"""
    
    # Template and project IDs
    project_id = "561802cc-1851-4993-8742-55b2dc4fcd1d"
    template_id = "5c2eca01-84b8-4302-bad2-9189db4dae70"
    template_url = f"https://creatomate.com/projects/{project_id}/templates/{template_id}"
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode so you can see what's happening
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print(f"Navigating to template: {template_url}")
            page.goto(template_url)
            
            # Wait for the page to load
            page.wait_for_load_state("networkidle")
            time.sleep(3)  # Give extra time for dynamic content
            
            # Check if we need to log in
            if "login" in page.url.lower() or "sign-in" in page.url.lower():
                print("Login required. Please log in manually.")
                print("Once logged in, press Enter to continue...")
                input()
                
                # Navigate back to template after login
                page.goto(template_url)
                page.wait_for_load_state("networkidle")
                time.sleep(3)
            
            print("Looking for timeline/duration controls...")
            
            # Take a screenshot of the current state
            page.screenshot(path="creatomate_template_editor.png")
            print("Screenshot saved as creatomate_template_editor.png")
            
            # Try to find and click on timeline or scene elements
            # Creatomate typically uses a timeline editor
            
            # Look for scene duration controls
            # These selectors will need to be adjusted based on actual UI
            possible_selectors = [
                # Common timeline/duration related selectors
                '[data-testid*="timeline"]',
                '[class*="timeline"]',
                '[class*="duration"]',
                '[class*="scene"]',
                '[class*="clip"]',
                '[aria-label*="duration"]',
                'input[type="number"]',
                '[class*="time-input"]',
                '[class*="seconds"]',
                # Look for Photo elements in the timeline
                'text=Photo-1',
                'text=Photo-2',
                'text=Photo-3',
                'text=Photo-4',
                'text=Photo-5',
            ]
            
            found_elements = []
            for selector in possible_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"Found {len(elements)} elements matching: {selector}")
                        found_elements.extend([(selector, el) for el in elements])
                except:
                    pass
            
            # Try to find duration input fields
            print("\nLooking for duration input fields...")
            
            # Check for number inputs that might be duration
            number_inputs = page.query_selector_all('input[type="number"]')
            for i, input_elem in enumerate(number_inputs):
                try:
                    value = input_elem.get_attribute("value")
                    placeholder = input_elem.get_attribute("placeholder")
                    label = input_elem.get_attribute("aria-label")
                    print(f"Number input {i}: value={value}, placeholder={placeholder}, label={label}")
                    
                    # If it looks like a duration field (has a small value like 12 seconds)
                    if value and float(value) > 0 and float(value) < 100:
                        print(f"  -> This might be a duration field with {value} seconds")
                except:
                    pass
            
            # Look for the timeline specifically
            print("\nLooking for timeline editor...")
            timeline_selectors = [
                '.timeline-container',
                '#timeline',
                '[class*="timeline-editor"]',
                '[class*="sequence-editor"]',
                '.editor-timeline',
            ]
            
            for selector in timeline_selectors:
                timeline = page.query_selector(selector)
                if timeline:
                    print(f"Found timeline element: {selector}")
                    timeline.screenshot(path="creatomate_timeline.png")
                    print("Timeline screenshot saved as creatomate_timeline.png")
                    break
            
            # Try to find scene or clip elements
            print("\nLooking for scene/clip elements...")
            scene_selectors = [
                '[class*="scene-item"]',
                '[class*="clip-item"]',
                '[class*="timeline-item"]',
                '[class*="track-item"]',
                '.scene',
                '.clip',
            ]
            
            scenes = []
            for selector in scene_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} scene/clip elements with selector: {selector}")
                    scenes = elements
                    break
            
            # If we found scenes, try to click on them to see if duration options appear
            if scenes:
                print(f"\nFound {len(scenes)} scenes. Clicking on first scene...")
                scenes[0].click()
                time.sleep(2)
                
                # Look for duration controls that might have appeared
                page.screenshot(path="creatomate_scene_selected.png")
                print("Screenshot after selecting scene saved as creatomate_scene_selected.png")
                
                # Look for duration input that might have appeared
                duration_inputs = page.query_selector_all('input[type="number"]')
                for input_elem in duration_inputs:
                    try:
                        value = input_elem.get_attribute("value")
                        if value and float(value) > 0 and float(value) < 100:
                            print(f"\nFound duration input with value: {value} seconds")
                            print("Changing duration to 20 seconds (slower)...")
                            
                            # Clear and set new value
                            input_elem.click()
                            input_elem.fill("")
                            input_elem.type("20")
                            input_elem.press("Enter")
                            time.sleep(1)
                            
                            print("Duration updated!")
                            break
                    except:
                        pass
            
            # Wait for user to make manual adjustments if needed
            print("\n" + "="*50)
            print("MANUAL ADJUSTMENT INSTRUCTIONS:")
            print("1. Look for the timeline at the bottom of the editor")
            print("2. Click on each 'Photo' scene in the timeline")
            print("3. Look for a duration/time field (usually shows '12s' or similar)")
            print("4. Change each photo duration from 12s to 20-24s for slower playback")
            print("5. The total video will be longer but images will display more slowly")
            print("\nPress Enter when you've made the adjustments...")
            input()
            
            # Save the template
            print("\nLooking for save button...")
            save_selectors = [
                'button:has-text("Save")',
                'button:has-text("Update")',
                '[aria-label="Save"]',
                '.save-button',
                'button[type="submit"]',
            ]
            
            for selector in save_selectors:
                try:
                    save_btn = page.query_selector(selector)
                    if save_btn and save_btn.is_visible():
                        print(f"Found save button: {selector}")
                        save_btn.click()
                        print("Template saved!")
                        time.sleep(2)
                        break
                except:
                    pass
            
            print("\nProcess complete! Your template timing should now be adjusted.")
            print("Test the new timing by generating a video with your app.")
            
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="creatomate_error.png")
            print("Error screenshot saved as creatomate_error.png")
        
        finally:
            print("\nPress Enter to close the browser...")
            input()
            browser.close()

if __name__ == "__main__":
    print("Creatomate Template Timing Adjuster")
    print("===================================")
    print("This script will help you adjust the timing in your Creatomate template")
    print("to make images display more slowly.\n")
    
    adjust_template_timing()