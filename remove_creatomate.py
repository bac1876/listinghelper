#!/usr/bin/env python3
"""
Script to remove Creatomate integration files
This helps clean up the codebase when switching to GitHub Actions/Remotion
"""

import os
import shutil

def remove_creatomate_files():
    """Remove Creatomate-related files from the project"""
    
    print("=== Removing Creatomate Integration Files ===\n")
    
    # List of Creatomate-related files to remove
    files_to_remove = [
        'creatomate_integration.py',
        'creatomate_integration_v2.py',
        'creatomate_timing_helper.py',
        'adjust_creatomate_timing.py',
        'browse_creatomate_templates.py',
        'check_new_template.py',
        'open_creatomate_template.py',
        'test_template_directly.py',
        'TEMPLATE_TIMING_SUMMARY.md',
        'SLOW_DOWN_OPTIONS.md'
    ]
    
    removed_files = []
    kept_files = []
    
    for filename in files_to_remove:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            try:
                # Create backup first
                backup_path = filepath + '.backup'
                shutil.copy2(filepath, backup_path)
                # Remove the file
                os.remove(filepath)
                removed_files.append(filename)
                print(f"✅ Removed: {filename} (backup created: {filename}.backup)")
            except Exception as e:
                print(f"❌ Error removing {filename}: {e}")
                kept_files.append(filename)
        else:
            print(f"⏭️  Skipped: {filename} (not found)")
    
    print(f"\n📊 Summary:")
    print(f"   - Files removed: {len(removed_files)}")
    print(f"   - Files kept due to errors: {len(kept_files)}")
    print(f"   - Backups created in same directory with .backup extension")
    
    if removed_files:
        print(f"\n📝 Next steps:")
        print(f"   1. Update your Railway environment variables:")
        print(f"      - Remove: CREATOMATE_API_KEY")
        print(f"      - Remove: CREATOMATE_TEMPLATE_ID")
        print(f"      - Remove: USE_CREATOMATE")
        print(f"      - Add: USE_GITHUB_ACTIONS=true")
        print(f"   2. Test the new GitHub Actions integration")
        print(f"   3. Delete backup files once confirmed working")
    
    return removed_files, kept_files

def check_creatomate_imports():
    """Check for any remaining Creatomate imports in the codebase"""
    
    print("\n=== Checking for Creatomate imports ===\n")
    
    files_with_imports = []
    
    # Files to check
    check_files = [
        'main.py',
        'working_ken_burns.py',
        'working_ken_burns_github.py'
    ]
    
    for filename in check_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'creatomate' in content.lower():
                        files_with_imports.append(filename)
                        print(f"⚠️  Found Creatomate reference in: {filename}")
            except Exception as e:
                print(f"❌ Error checking {filename}: {e}")
    
    if not files_with_imports:
        print("✅ No Creatomate imports found in main files")
    else:
        print(f"\n⚠️  Found Creatomate references in {len(files_with_imports)} files")
        print("   These may need manual review")
    
    return files_with_imports

if __name__ == "__main__":
    # Remove Creatomate files
    removed, kept = remove_creatomate_files()
    
    # Check for remaining imports
    files_with_imports = check_creatomate_imports()
    
    print("\n" + "="*50)
    
    if not kept and not files_with_imports:
        print("✅ Creatomate removal complete!")
        print("   Your project is ready to use GitHub Actions with Remotion")
    else:
        print("⚠️  Some manual cleanup may be needed")
        if kept:
            print(f"   - Could not remove {len(kept)} files")
        if files_with_imports:
            print(f"   - Found imports in {len(files_with_imports)} files")