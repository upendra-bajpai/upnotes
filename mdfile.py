import os
import re
import shutil
import sys
from datetime import datetime

def process_markdown_file(filepath, output_dir, assets_prefix):
    first_image_url = None
    modified_content = ""
    input_root_folder = os.path.basename(os.path.normpath(sys.argv[1]))
    with open(filepath, 'r') as file:
        content = file.read()

        # Extract the first image URL
        image_match = re.search(r'!\[.*?\]\((.*?)\)', content)
        if image_match:
            first_image_url = image_match.group(1)
        first_image_url=assets_prefix+ input_root_folder +'/'+ os.path.basename(first_image_url) if first_image_url else ""
        # Append asset prefix to asset paths and modify image/video paths 
        modified_content = re.sub(r'!\[(.*?)\]\((images/.*?)\)', lambda match: copy_media_and_replace_path(match, filepath, output_dir, assets_prefix), content)

    return first_image_url, modified_content

def copy_media_and_replace_path(match, original_filepath, output_dir, assets_prefix):
    media_name = match.group(1)
    media_file = match.group(2)

    original_dir = os.path.dirname(original_filepath)
    input_root_folder = os.path.basename(os.path.normpath(sys.argv[1]))
    new_dir = os.path.join(output_dir, assets_prefix, input_root_folder)
    os.makedirs(new_dir, exist_ok=True)
    original_media_path = os.path.join(original_dir, media_file)
    new_media_path = os.path.join(new_dir, os.path.basename(media_file))

    if os.path.exists(original_media_path):
        shutil.copy(original_media_path, new_media_path)

    return f'{{% include image.html src="{os.path.join(assets_prefix, input_root_folder, os.path.basename(media_file)).replace("//", "/")}" alt="{media_name}" caption="" %}}'

    #return f'![{media_name}](/{assets_prefix}{input_root_folder}/{os.path.basename(media_file).replace("//", "/")})'

def write_new_markdown_file(original_filepath, modified_content, first_image_url, output_dir, assets_prefix):
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_date_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    input_root_folder = os.path.basename(os.path.normpath(sys.argv[1]))

    # Extract title and folder from original filepath
    title = os.path.basename(original_filepath).replace('-', ' ').split('.')[0]
    folder = os.path.basename(os.path.dirname(original_filepath))
    first_image_name = os.path.splitext(os.path.basename(first_image_url))[0] if first_image_url else "no_image"
    #print(f'dir {ori} {os.path.basename(original_filepath)}')

    # New markdown content
    new_content = f'''---
layout: post
title:  "{folder.title()} - {first_image_name}"
author: sal
date: {current_date_time}
categories: [tutorial, {first_image_name},{input_root_folder}]
image: {first_image_url if first_image_url else 'assets/images/4.jpg'}
---
{modified_content}
###### credit goes to @preslavmihaylov
'''

    # Ensure date is not duplicated in filename
    #if not re.search(r'\d{4}-\d{2}-\d{2}', original_filepath):
    filename = os.path.join(output_dir, f"{current_date}-{folder}-{title}.md")

    with open(filename, 'w') as new_file:
        new_file.write(new_content)
    print(f'file written as {filename}')

def process_files_recursively(input_dir, output_dir):
    assets_prefix = f'assets/images/{os.path.basename(input_dir)}'
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                first_image_url, modified_content = process_markdown_file(filepath, output_dir, assets_prefix)
                write_new_markdown_file(filepath, modified_content, first_image_url, output_dir, assets_prefix)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_directory> <output_directory>")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    os.makedirs(output_directory, exist_ok=True)
    
    process_files_recursively(input_directory, output_directory)
