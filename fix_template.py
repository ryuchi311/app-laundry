#!/usr/bin/env python3
"""
Quick Template Syntax Fix
Find and fix the template syntax error in dashboard.html
"""

def fix_template():
    template_path = 'app/templates/dashboard.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    print(f"Total lines: {len(lines)}")
    
    # Find all for/endfor pairs
    for_stack = []
    if_stack = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        if '{% for' in line:
            for_stack.append((line_num, line.strip()))
            print(f"Line {line_num}: FOR - {line.strip()}")
            
        elif '{% endfor' in line:
            if for_stack:
                start_line, start_content = for_stack.pop()
                print(f"Line {line_num}: ENDFOR (matches line {start_line})")
            else:
                print(f"Line {line_num}: ENDFOR - NO MATCHING FOR!")
                
        elif '{% if' in line and 'endif' not in line:
            if_stack.append((line_num, line.strip()))
            
        elif '{% endif' in line:
            if if_stack:
                start_line, start_content = if_stack.pop()
                if line_num == 458:  # The problem line
                    print(f"Line {line_num}: ENDIF (matches line {start_line}) - PROBLEM LINE")
                    print(f"  Previous IF: {start_content}")
                    print(f"  Current line: {line.strip()}")
            else:
                print(f"Line {line_num}: ENDIF - NO MATCHING IF!")
    
    print(f"\nUnmatched FOR loops: {len(for_stack)}")
    for line_num, content in for_stack:
        print(f"  Line {line_num}: {content}")
        
    print(f"\nUnmatched IF statements: {len(if_stack)}")
    for line_num, content in if_stack:
        print(f"  Line {line_num}: {content}")

if __name__ == "__main__":
    fix_template()
