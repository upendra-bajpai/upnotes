import sys
from datetime import datetime

# Check if filename is provided
if len(sys.argv) != 2:
    print("Usage: python script.py <filename>")
    sys.exit(1)

# Get current date
current_date = datetime.now().strftime('%Y-%m-%d')
current_date_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

# Extract title from filename
title = sys.argv[1].split('/')[-1].replace('-', ' ').split('.')[0]
folder=sys.argv[1].split('/')[0]

# Markdown content
content = f'''---
layout: post
title:  "{title.title()}"
author: sal
date: {current_date_time}
categories: [  tutorial ]
image: assets/images/4.jpg
---
'''

# Append date to filename if not already present
filename = sys.argv[1]
if not filename.startswith(current_date):
    filename = f"{folder}/{current_date}-{title}.md"

# Write content to file
with open(filename, 'w') as f:
    f.write(content)

