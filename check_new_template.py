"""
Check what's in the new Creatomate template
"""
import webbrowser

# New template URL
new_template_url = "https://creatomate.com/projects/561802cc-1851-4993-8742-55b2dc4fcd1d/templates/31b06afe-9073-4f68-a329-0e910a8be6a7"

# Original template URL for comparison
original_template_url = "https://creatomate.com/projects/561802cc-1851-4993-8742-55b2dc4fcd1d/templates/5c2eca01-84b8-4302-bad2-9189db4dae70"

print("Opening BOTH templates for comparison...")
print("="*60)
print("\nNEW TEMPLATE (current - slideshow issue):")
print(new_template_url)
print("\nORIGINAL TEMPLATE (had Ken Burns effects):")
print(original_template_url)
print("\n" + "="*60)

print("\nWhat to look for:")
print("1. Check if the NEW template has any animations on the Video elements")
print("2. Compare timeline - does NEW have movement keyframes?")
print("3. Look for animation properties or effects")
print("4. Check element properties for zoom/pan/position animations")

print("\nOpening both in your browser...")
webbrowser.open(new_template_url)
import time
time.sleep(2)
webbrowser.open(original_template_url)

print("\nCheck both templates and see what's different!")