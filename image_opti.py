import os
import sys
from PIL import Image

def reduce_image_size(input_path, output_path, target_size_kb=800, max_size_kb=1000):
    target_size_bytes = target_size_kb * 1024
    max_size_bytes = max_size_kb * 1024
    try:
        with Image.open(input_path) as img:
            original_size = os.path.getsize(input_path)
            
            if original_size <= max_size_bytes:
                print(f"Image size is already below {max_size_kb} KB: {input_path}")
                img.save(output_path)
                return

            quality = 85
            step = 5
            width, height = img.size

            while original_size > max_size_bytes and quality > 0:
                # Resize the image if it's still too large
                img = img.resize((width, height), Image.ANTIALIAS)
                img.save(output_path, quality=quality)
                original_size = os.path.getsize(output_path)
                quality -= step
                width = int(width * 0.9)  # Reduce width by 10%
                height = int(height * 0.9)  # Reduce height by 10%

            print(f"Image size reduced to {original_size / 1024:.2f} KB with quality {quality + step}: {output_path}")

    except Exception as e:
        print(f"Error processing {input_path}: {e}")

def process_images_in_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        if os.path.isfile(input_path):
            try:
                with Image.open(input_path) as img:
                    img.verify()  # Check if the file is an image
                reduce_image_size(input_path, output_path)
            except (IOError, SyntaxError) as e:
                print(f"File is not an image or is corrupted: {input_path}, {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    process_images_in_folder(input_folder, output_folder)
