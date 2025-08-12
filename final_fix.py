import re

# Read the file
with open('app/templates/customer_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix malformed classes
fixes = [
    # Fix malformed hover classes
    ('hover:text-gray-800:bg-gray-100', 'hover:text-gray-800 hover:bg-gray-100'),
    ('hover:bg-gray-100 text-white', 'hover:bg-blue-700 text-white'),
    ('shadow-md hover"', 'shadow-md hover:shadow-lg"'),
    
    # Fix button backgrounds that don't make sense
    ('bg-blue-600 hover:bg-gray-100 text-white', 'bg-blue-600 hover:bg-blue-700 text-white'),
    ('bg-gray-500 hover:bg-gray-100 text-white', 'bg-gray-500 hover:bg-gray-600 text-white'), 
    ('bg-green-600 hover:bg-gray-100 text-white', 'bg-green-600 hover:bg-green-700 text-white'),
    ('bg-orange-600 hover:bg-gray-100 text-white', 'bg-orange-600 hover:bg-orange-700 text-white'),
    
    # Fix group hover classes  
    ('group-hover:bg-gray-100 transition-transform', 'group-hover:scale-110 transition-transform'),
    
    # Fix text hover classes
    ('hover:bg-gray-100 truncate', 'hover:text-blue-600 truncate'),
    ('hover:bg-gray-100 font-medium', 'hover:text-blue-600 font-medium'),
    
    # Fix card hover classes
    ('hover:bg-gray-100 transition-all duration-300', 'hover:shadow-xl transition-all duration-300'),
]

# Apply fixes
for old, new in fixes:
    content = content.replace(old, new)

# Write the file back
with open('app/templates/customer_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied final fixes to customer_list.html")
