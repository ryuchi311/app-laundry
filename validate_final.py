#!/usr/bin/env python3

import re

template_path = 'app/templates/dashboard.html'

def analyze_jinja_structure(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    stack = []
    
    # Pattern to match Jinja tags
    tag_pattern = r'{%\s*(\w+).*?%}'
    
    for i, line in enumerate(lines, 1):
        matches = re.findall(tag_pattern, line)
        for tag in matches:
            if tag in ['if', 'for', 'with', 'block', 'macro']:
                stack.append((tag, i, line.strip()))
            elif tag in ['endif', 'endfor', 'endwith', 'endblock', 'endmacro']:
                expected_tag = tag[3:]  # Remove 'end' prefix
                if not stack:
                    print(f'ERROR Line {i}: Found {tag} but no opening tag in stack')
                    print(f'  Line content: {line.strip()}')
                    continue
                
                last_tag, last_line, last_content = stack.pop()
                if last_tag != expected_tag:
                    print(f'ERROR Line {i}: Found {tag} but expected end{last_tag}')
                    print(f'  Opening: Line {last_line}: {last_content}')
                    print(f'  Closing: Line {i}: {line.strip()}')
                    return False
                    
    if stack:
        print('ERROR: Unclosed tags at end of file:')
        for tag, line_num, content in stack:
            print(f'  Line {line_num}: {content}')
        return False
    
    print('✅ SUCCESS: All Jinja tags properly matched!')
    return True

if __name__ == '__main__':
    print('🔍 Analyzing Jinja2 template structure...')
    result = analyze_jinja_structure(template_path)
    if result:
        print('🎉 Dashboard template is ready for production!')
    else:
        print('❌ Template still has structural issues.')
