import re

# Read the file
with open('app/templates/customer_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix incomplete classes patterns
replacements = [
    # Fix hover classes
    ('class="([^"]*?)\\bhover\\b(?![:-])([^"]*?)"', r'class="\1hover:bg-gray-100\2"'),
    
    # Fix focus classes
    ('focus focus focus focus', 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50'),
    ('hover hover hover', 'hover:shadow-xl'),
    ('hover hover', 'hover:shadow-lg'),
    
    # Fix responsive classes
    ('hidden md items-center', 'hidden md:flex items-center'),
    ('grid-cols-1 md lg gap-6', 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'),
    ('flex-col lg gap-4', 'flex-col lg:flex-row gap-4'),
    ('flex flex-col sm gap-4', 'flex flex-col sm:flex-row gap-4'),
    ('hidden sm sm sm sm', 'hidden sm:block'),
    ('grid-cols-1 sm lg gap-4', 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4'),
    
    # Fix specific button hover states
    ('bg-blue-600 hover text-white', 'bg-blue-600 hover:bg-blue-700 text-white'),
    ('bg-gray-500 hover text-white', 'bg-gray-500 hover:bg-gray-600 text-white'),
    ('bg-green-600 hover text-white', 'bg-green-600 hover:bg-green-700 text-white'),
    ('bg-orange-600 hover text-white', 'bg-orange-600 hover:bg-orange-700 text-white'),
    ('bg-indigo-600 hover', 'bg-indigo-600 hover:bg-indigo-700'),
    
    # Fix link hover states  
    ('text-gray-700 hover truncate', 'text-gray-700 hover:text-blue-600 truncate'),
    ('text-gray-700 hover font-medium', 'text-gray-700 hover:text-blue-600 font-medium'),
    ('text-gray-600 hover', 'text-gray-600 hover:text-gray-800'),
    
    # Fix card hover states
    ('border border-gray-200 hover transition-all', 'border border-gray-200 hover:shadow-xl transition-all'),
    
    # Fix button hover states
    ('bg-blue-50 hover rounded-lg', 'bg-blue-50 hover:bg-blue-100 rounded-lg'),
    ('bg-orange-50 hover rounded-lg', 'bg-orange-50 hover:bg-orange-100 rounded-lg'),
    ('bg-green-50 hover rounded-lg', 'bg-green-50 hover:bg-green-100 rounded-lg'),
    ('bg-red-50 hover', 'bg-red-50 hover:bg-red-100'),
]

# Apply replacements
for old, new in replacements:
    content = re.sub(old, new, content)

# Write the file back
with open('app/templates/customer_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all incomplete CSS classes in customer_list.html")
