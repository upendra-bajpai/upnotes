import sys

# Check if filename is provided
if len(sys.argv) != 2:
    print("Usage: python script.py <filename>")
    sys.exit(1)

# Markdown content
content = '''---
layout: post
title:  "Powerful things you can do with the Markdown editor"
author: sal
date: 2020-07-24-02:25:54
categories: [ Jekyll, tutorial ]
image: assets/images/4.jpg
---
'''

# Write content to file
with open(sys.argv[1], 'w') as f:
    f.write(content)