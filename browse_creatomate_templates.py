"""
Browse Creatomate templates to find one with Ken Burns effects
"""
import webbrowser

print("Let's find a Creatomate template with Ken Burns effects!")
print("="*60)

# Creatomate template gallery
template_gallery = "https://creatomate.com/templates"

# Your project templates
your_templates = "https://creatomate.com/projects/561802cc-1851-4993-8742-55b2dc4fcd1d/templates"

print("\nOpening Creatomate template resources...")
print("\n1. TEMPLATE GALLERY - Look for real estate templates with movement:")
print("   - Search for 'real estate' or 'property'")
print("   - Look for templates that mention 'Ken Burns' or 'pan and zoom'")
print("   - Check preview videos for movement within images")

print("\n2. YOUR PROJECT TEMPLATES - See all templates in your project:")
print("   - You might have other templates available")
print("   - Can duplicate and modify existing ones")

print("\n3. What to look for:")
print("   - Zoom in/out effects on images")
print("   - Pan movements (left/right, up/down)")
print("   - NOT just transitions between images")
print("   - Movement WITHIN each image display")

print("\nOpening both pages...")
webbrowser.open(template_gallery)
import time
time.sleep(2)
webbrowser.open(your_templates)

print("\nOnce you find a good template:")
print("1. Note the template ID")
print("2. We'll update the code to use it")
print("3. Test with your images")