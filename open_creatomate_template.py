"""
Open Creatomate template in browser for timing adjustment
"""
import webbrowser
import time

def open_template():
    template_url = "https://creatomate.com/projects/561802cc-1851-4993-8742-55b2dc4fcd1d/templates/5c2eca01-84b8-4302-bad2-9189db4dae70"
    
    print("Opening Creatomate template in your browser...")
    print("="*60)
    
    # Open the template in default browser
    webbrowser.open(template_url)
    
    time.sleep(2)
    
    print("\nINSTRUCTIONS FOR ADJUSTING TIMING:")
    print("="*60)
    print("\n1. LOG IN (if needed)")
    print("   - Enter your Creatomate credentials")
    
    print("\n2. FIND THE TIMELINE")
    print("   - Look at the bottom of the editor")
    print("   - You should see a timeline with 5 'Photo' scenes")
    
    print("\n3. ADJUST EACH PHOTO DURATION")
    print("   - Click on 'Photo-1' in the timeline")
    print("   - Look for a duration field (shows '12.00s')")
    print("   - Change it to '20.00s' or '24.00s'")
    print("   - Repeat for all 5 photos")
    
    print("\n4. OPTIONAL: ADJUST TRANSITIONS")
    print("   - Look for transition markers between photos")
    print("   - You can make these longer too")
    
    print("\n5. SAVE YOUR CHANGES")
    print("   - Click 'Save' or 'Update' button")
    print("   - Usually in top-right corner")
    
    print("\n6. TEST")
    print("   - Generate a new video in your app")
    print("   - Images should now display more slowly")
    
    print("\n" + "="*60)
    print("CURRENT: 12 seconds per image = 60 second video")
    print("SUGGESTED: 20-24 seconds per image = 100-120 second video")
    print("="*60)

if __name__ == "__main__":
    open_template()