#!/usr/bin/env python3
"""
Advanced Template Structure Analysis
Find the exact template structure issue
"""

def analyze_template_structure():
    template_path = 'app/templates/dashboard.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Stack to track nested structures
    stack = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        
        # Track opening tags
        if '{% for' in stripped:
            stack.append(('for', line_num, stripped))
            print(f"Line {line_num}: OPEN FOR - {stripped}")
            
        elif '{% if' in stripped and 'endif' not in stripped:
            # Only count block-level if statements, not inline ones
            if stripped.startswith('{% if') or 'elif' in stripped:
                stack.append(('if', line_num, stripped))
                print(f"Line {line_num}: OPEN IF - {stripped}")
        
        # Track closing tags
        elif '{% endfor' in stripped:
            print(f"Line {line_num}: CLOSE ENDFOR - {stripped}")
            # Find matching for
            found = False
            for j in range(len(stack) - 1, -1, -1):
                if stack[j][0] == 'for':
                    match = stack.pop(j)
                    print(f"  -> Matches FOR at line {match[1]}")
                    found = True
                    break
            if not found:
                print(f"  -> ERROR: No matching FOR!")
                
        elif '{% endif' in stripped:
            print(f"Line {line_num}: CLOSE ENDIF - {stripped}")
            if line_num == 458:
                print(f"  -> THIS IS THE PROBLEM LINE!")
                print(f"  -> Current stack: {stack}")
            
            # Find matching if
            found = False
            for j in range(len(stack) - 1, -1, -1):
                if stack[j][0] == 'if':
                    match = stack.pop(j)
                    print(f"  -> Matches IF at line {match[1]}")
                    found = True
                    break
            if not found:
                print(f"  -> ERROR: No matching IF!")
    
    print(f"\nRemaining open structures:")
    for item in stack:
        print(f"  {item[0].upper()} at line {item[1]}: {item[2]}")

if __name__ == "__main__":
    analyze_template_structure()
