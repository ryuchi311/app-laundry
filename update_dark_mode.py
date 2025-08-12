#!/usr/bin/env python3
"""
Dark Mode Update Script for Tailwind CSS Templates
Systematically updates all templates that extend base.html for full dark mode support
"""

import os
import re
import glob

# Define common dark mode class mappings
DARK_MODE_REPLACEMENTS = [
    # Background colors
    (r'bg-white(\s)', r'bg-white dark:bg-gray-800\1'),
    (r'bg-white/', r'bg-white dark:bg-gray-800/'),
    (r'bg-gray-50(\s)', r'bg-gray-50 dark:bg-gray-900\1'),
    (r'bg-gray-100(\s)', r'bg-gray-100 dark:bg-gray-700\1'),
    (r'bg-gray-200(\s)', r'bg-gray-200 dark:bg-gray-600\1'),
    (r'from-gray-50\s+to-blue-50', r'from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800'),
    (r'from-blue-50\s+to-indigo-50', r'from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800'),
    
    # Text colors
    (r'text-gray-900(\s)', r'text-gray-900 dark:text-gray-100\1'),
    (r'text-gray-800(\s)', r'text-gray-800 dark:text-gray-200\1'),
    (r'text-gray-700(\s)', r'text-gray-700 dark:text-gray-300\1'),
    (r'text-gray-600(\s)', r'text-gray-600 dark:text-gray-400\1'),
    (r'text-gray-500(\s)', r'text-gray-500 dark:text-gray-500\1'),
    
    # Border colors
    (r'border-gray-200(\s)', r'border-gray-200 dark:border-gray-700\1'),
    (r'border-gray-300(\s)', r'border-gray-300 dark:border-gray-600\1'),
    (r'border-gray-100(\s)', r'border-gray-100 dark:border-gray-700\1'),
    (r'border-white/20', r'border-white/20 dark:border-gray-700/50'),
    
    # Hover states
    (r'hover:bg-gray-50(\s)', r'hover:bg-gray-50 dark:hover:bg-gray-700\1'),
    (r'hover:bg-blue-50(\s)', r'hover:bg-blue-50 dark:hover:bg-blue-900/50\1'),
    (r'hover:text-blue-700(\s)', r'hover:text-blue-700 dark:hover:text-blue-300\1'),
    
    # Status badges
    (r'bg-green-100\s+text-green-800', r'bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300'),
    (r'bg-red-100\s+text-red-800', r'bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300'),
    (r'bg-yellow-100\s+text-yellow-800', r'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300'),
    (r'bg-blue-100\s+text-blue-800', r'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300'),
    
    # Gradients for headers
    (r'from-blue-600\s+via-indigo-600\s+to-purple-700', r'from-blue-600 via-indigo-600 to-purple-700 dark:from-blue-700 dark:via-indigo-700 dark:to-purple-800'),
    (r'from-red-600\s+via-pink-600\s+to-red-700', r'from-red-600 via-pink-600 to-red-700 dark:from-red-700 dark:via-pink-700 dark:to-red-800'),
    (r'from-green-600\s+via-emerald-600\s+to-green-700', r'from-green-600 via-emerald-600 to-green-700 dark:from-green-700 dark:via-emerald-700 dark:to-green-800'),
    (r'from-indigo-600\s+via-purple-600\s+to-blue-700', r'from-indigo-600 via-purple-600 to-blue-700 dark:from-indigo-700 dark:via-purple-700 dark:to-blue-800'),
]

# Input field specific updates
INPUT_FIELD_REPLACEMENTS = [
    (r'border-gray-300(\s+[^"]*?"[^"]*?rounded)', r'border-gray-300 dark:border-gray-600\1'),
    (r'text-gray-900(\s+[^"]*?placeholder)', r'text-gray-900 dark:text-gray-100\1'),
    (r'placeholder-gray-400', r'placeholder-gray-400 dark:placeholder-gray-500'),
    (r'bg-white/70(\s+backdrop-blur)', r'bg-white/70 dark:bg-gray-700/70\1'),
]

def update_template_for_dark_mode(file_path):
    """Update a single template file for dark mode support"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        original_content = content
        changes_made = []
        
        # Apply general dark mode replacements
        for pattern, replacement in DARK_MODE_REPLACEMENTS:
            old_content = content
            content = re.sub(pattern, replacement, content)
            if content != old_content:
                changes_made.append(f"Updated: {pattern}")
        
        # Apply input field specific replacements
        for pattern, replacement in INPUT_FIELD_REPLACEMENTS:
            old_content = content
            content = re.sub(pattern, replacement, content)
            if content != old_content:
                changes_made.append(f"Updated input: {pattern}")
        
        # Write back only if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"✅ Updated: {file_path}")
            for change in changes_made[:3]:  # Show first 3 changes
                print(f"   - {change}")
            if len(changes_made) > 3:
                print(f"   - ... and {len(changes_made) - 3} more changes")
            return True
        else:
            print(f"⏸️  No changes needed: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def find_templates_extending_base():
    """Find all template files that extend base.html"""
    template_files = []
    for root, dirs, files in os.walk('app/templates'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_few_lines = ''.join(f.readlines()[:5])
                        if 'extends "base.html"' in first_few_lines:
                            template_files.append(file_path)
                except:
                    pass
    return template_files

def main():
    """Main function to update all templates"""
    print("🌙 Starting Dark Mode Update for Tailwind CSS Templates")
    print("=" * 60)
    
    # Find all templates that extend base.html
    templates = find_templates_extending_base()
    
    if not templates:
        print("❌ No templates found that extend base.html")
        return
    
    print(f"📁 Found {len(templates)} templates to update:")
    for template in templates:
        print(f"   - {template}")
    
    print("\n🔄 Starting updates...")
    print("-" * 40)
    
    updated_count = 0
    for template_path in templates:
        if update_template_for_dark_mode(template_path):
            updated_count += 1
    
    print("-" * 40)
    print(f"✨ Update complete!")
    print(f"📊 Updated {updated_count} out of {len(templates)} templates")
    
    if updated_count > 0:
        print("\n🎉 Dark mode support has been added to your templates!")
        print("   Users can now toggle between light and dark themes")
        print("   using the toggle button in the navigation bar.")
    else:
        print("\n✅ All templates were already up to date!")

if __name__ == "__main__":
    main()
