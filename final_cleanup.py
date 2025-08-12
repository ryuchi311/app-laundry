import os
import re
import sys

print("Starting final cleanup script...")

def clean_dark_mode_from_file(file_path):
    """Remove all dark mode related classes and attributes from HTML files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    original_content = content
    
    # Remove dark mode classes patterns
    patterns = [
        r'dark:[^"\s]+',  # dark: prefixed classes
        r'dark\s*=\s*"[^"]*"',  # dark attributes
        r'data-theme\s*=\s*"[^"]*"',  # theme attributes
        r'class="[^"]*dark:[^"]*"',  # classes containing dark:
        r'localStorage\.[^;]+theme[^;]*;',  # localStorage theme code
        r'isDark[^;]*;',  # isDark variables
        r'theme[^;]*toggle[^;]*',  # theme toggle references
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Clean up extra spaces and empty class attributes
    content = re.sub(r'class="[\s]*"', '', content)
    content = re.sub(r'\s+class=""', '', content)
    content = re.sub(r'\s{2,}', ' ', content)
    content = re.sub(r'>\s+<', '><', content)
    
    # Clean up JavaScript blocks that reference dark mode
    js_patterns = [
        r'<script[^>]*>.*?theme.*?</script>',
        r'<script[^>]*>.*?dark.*?</script>',
        r'function\s+toggleTheme[^}]*}',
        r'function\s+setTheme[^}]*}',
        r'document\.documentElement\.classList\.[^;]*theme[^;]*;',
    ]
    
    for pattern in js_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned: {file_path}")
        return True
    
    return False

# Find all HTML files
html_files = []
for root, dirs, files in os.walk('app/templates'):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

# Also include the test file if it exists
if os.path.exists('dark_mode_test.html'):
    html_files.append('dark_mode_test.html')

print(f"Found {len(html_files)} HTML files to check")

cleaned_files = 0
for file_path in html_files:
    if clean_dark_mode_from_file(file_path):
        cleaned_files += 1

print(f"Cleaned {cleaned_files} files")
print("Final cleanup complete!")
