#!/usr/bin/env python3
"""
Remove Dark Mode Script for Tailwind CSS Templates
Systematically removes all dark mode classes from all templates
"""

import os
import re
import glob

# Define dark mode class removal patterns
DARK_MODE_REMOVALS = [
    # Remove dark: prefixed classes and their variants
    r'\s+dark:[a-zA-Z0-9-/]+',
    # Remove malformed dark classes like :bg-blue-900/50
    r':[a-zA-Z0-9-/]+',
    # Remove standalone dark mode related classes
    r'\s+dark(?=\s|"|\>)',
    # Clean up multiple spaces that might remain
    r'\s{2,}',
]

def clean_template_from_dark_mode(file_path):
    """Remove all dark mode classes from a template file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        original_content = content
        changes_made = []
        
        # Apply dark mode class removals
        for pattern in DARK_MODE_REMOVALS:
            old_content = content
            if pattern == r'\s{2,}':
                # Replace multiple spaces with single space
                content = re.sub(pattern, ' ', content)
            else:
                # Remove dark mode classes
                content = re.sub(pattern, '', content)
            
            if content != old_content:
                changes_made.append(f"Removed: {pattern}")
        
        # Clean up any remaining artifacts
        # Remove trailing spaces before quotes
        content = re.sub(r'\s+"', '"', content)
        # Clean up class attributes that might be empty or have only spaces
        content = re.sub(r'class="\s*"', '', content)
        content = re.sub(r'class="\s+([^"]*?)\s*"', r'class="\1"', content)
        
        # Write back only if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"✅ Cleaned: {file_path}")
            dark_classes_removed = len([c for c in changes_made if 'dark:' in c or 'dark' in c])
            if dark_classes_removed > 0:
                print(f"   - Removed {dark_classes_removed} dark mode class references")
            return True
        else:
            print(f"⏸️  No dark mode classes found: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error cleaning {file_path}: {e}")
        return False

def find_all_templates():
    """Find all HTML template files"""
    template_files = []
    for root, dirs, files in os.walk('app/templates'):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                template_files.append(file_path)
    return template_files

def main():
    """Main function to remove dark mode from all templates"""
    print("🌞 Removing Dark Mode from All Tailwind CSS Templates")
    print("=" * 60)
    
    # Find all templates
    templates = find_all_templates()
    
    if not templates:
        print("❌ No templates found")
        return
    
    print(f"📁 Found {len(templates)} templates to clean:")
    for template in templates:
        print(f"   - {template}")
    
    print("\n🧹 Starting cleanup...")
    print("-" * 40)
    
    cleaned_count = 0
    for template_path in templates:
        if clean_template_from_dark_mode(template_path):
            cleaned_count += 1
    
    print("-" * 40)
    print(f"✨ Cleanup complete!")
    print(f"📊 Cleaned {cleaned_count} out of {len(templates)} templates")
    
    if cleaned_count > 0:
        print("\n🌞 Dark mode has been completely removed!")
        print("   All templates are now light mode only.")
    else:
        print("\n✅ No dark mode classes were found!")

if __name__ == "__main__":
    main()
