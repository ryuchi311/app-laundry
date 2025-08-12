#!/usr/bin/env python3
"""
Fix CSS classes in user_management/list_users.html template
Fixes the same issues found in other templates after dark mode removal
"""

import re
import os

def fix_user_management_css():
    """Fix CSS syntax errors in the user management template"""
    
    file_path = r'd:\app-laundry\app\templates\user_management\list_users.html'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("Original file length:", len(content))
        
        # Fix malformed hover classes - these are missing the full selector
        fixes = [
            # Fix incomplete hover states
            ('class="bg-white hover backdrop-blur-sm', 'class="bg-white hover:bg-gray-50 backdrop-blur-sm'),
            ('class="border-b border-gray-100 hover transition-colors"', 'class="border-b border-gray-100 hover:bg-gray-50 transition-colors"'),
            ('class="bg-green-100 hover text-green-700', 'class="bg-green-100 hover:bg-green-200 text-green-700'),
            ('class="bg-red-100 hover text-red-700', 'class="bg-red-100 hover:bg-red-200 text-red-700'),
            ('class="bg-orange-100 hover text-orange-700', 'class="bg-orange-100 hover:bg-orange-200 text-orange-700'),
            ('class="bg-blue-100 hover text-blue-700', 'class="bg-blue-100 hover:bg-blue-200 text-blue-700'),
            ('class="bg-gradient-to-r from-blue-600 to-indigo-600 hover hover text-white', 'class="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white'),
            ('class="inline-flex items-center space-x-2 px-6 py-3 bg-white hover backdrop-blur-sm', 'class="inline-flex items-center space-x-2 px-6 py-3 bg-white hover:bg-gray-50 backdrop-blur-sm'),
            
            # Fix style attributes with missing values
            ('style="display;"', 'style="display:inline;"'),
            ('shadow-lg hover border', 'shadow-lg hover:shadow-xl border'),
        ]
        
        # Apply fixes
        changes_made = 0
        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
                changes_made += 1
                print(f"✓ Fixed: {old[:50]}...")
        
        # Fix any remaining standalone "hover" classes
        # Look for patterns like 'hover transition' or 'hover text-'
        hover_patterns = [
            (r'hover transition-', r'hover:bg-gray-50 transition-'),
            (r'hover text-', r'hover:bg-gray-50 text-'),
            (r'hover border', r'hover:shadow-lg border'),
            (r'hover backdrop', r'hover:bg-gray-50 backdrop'),
        ]
        
        for pattern, replacement in hover_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                changes_made += len(matches)
                print(f"✓ Fixed hover pattern: {pattern}")
        
        # Write the fixed content back
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"\n✅ Successfully fixed {changes_made} CSS issues in {file_path}")
            print("New file length:", len(content))
            return True
        else:
            print("❌ No CSS issues found or fixes needed")
            return False
            
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing CSS classes in user_management/list_users.html...")
    print("=" * 60)
    
    if fix_user_management_css():
        print("\n🎉 CSS fixes completed successfully!")
    else:
        print("\n❌ CSS fixes failed or were not needed")
    
    print("=" * 60)
