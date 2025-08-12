#!/usr/bin/env python3
"""
Template Syntax Validation Script
Check dashboard.html for Jinja2 template syntax errors
"""

from jinja2 import Environment, FileSystemLoader, Template
import os
import sys

def validate_template_syntax():
    print("🧪 Template Syntax Validation")
    print("=" * 40)
    
    template_path = 'app/templates/dashboard.html'
    
    # Check if template file exists
    if not os.path.exists(template_path):
        print(f"❌ Template file not found: {template_path}")
        return False
    
    try:
        # Load template content
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        print(f"📄 Template file: {template_path}")
        print(f"📏 Template size: {len(template_content)} characters")
        
        # Create Jinja2 environment
        env = Environment()
        
        # Parse template
        template = env.from_string(template_content)
        print("✅ Template syntax is valid!")
        
        return True
        
    except Exception as e:
        print(f"❌ Template syntax error: {e}")
        
        # Try to identify the problematic area
        lines = template_content.split('\n')
        print(f"\n🔍 Template Analysis:")
        print(f"   Total lines: {len(lines)}")
        
        # Count template tags
        for_count = template_content.count('{%% for')
        endfor_count = template_content.count('{%% endfor')
        if_count = template_content.count('{%% if')
        endif_count = template_content.count('{%% endif')
        
        print(f"   for tags: {for_count}")
        print(f"   endfor tags: {endfor_count}")
        print(f"   if tags: {if_count}")
        print(f"   endif tags: {endif_count}")
        
        if for_count != endfor_count:
            print(f"⚠️  Mismatch: {for_count} for vs {endfor_count} endfor")
        
        if if_count != endif_count:
            print(f"⚠️  Mismatch: {if_count} if vs {endif_count} endif")
            
        return False

if __name__ == "__main__":
    validate_template_syntax()
