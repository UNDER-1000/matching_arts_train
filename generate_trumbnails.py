# generate_thumbnails.py
from PIL import Image
import os

IMAGE_FOLDER = os.path.join("data", "data")
THUMBNAIL_FOLDER = os.path.join("data", "thumbnails")
THUMBNAIL_SIZE = (250, 250) # Max width/height for your thumbnails

if not os.path.exists(THUMBNAIL_FOLDER):
    os.makedirs(THUMBNAIL_FOLDER)

for filename in os.listdir(IMAGE_FOLDER):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        img_path = os.path.join(IMAGE_FOLDER, filename)
        thumb_path = os.path.join(THUMBNAIL_FOLDER, filename)

        if os.path.exists(thumb_path):
            print(f"Thumbnail for {filename} already exists. Skipping.")
            continue

        try:
            with Image.open(img_path) as img:
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS) # Use LANCZOS for quality
                # Save with optimized settings for JPEGs
                if img.mode == 'RGBA': # Convert RGBA to RGB for JPEG saving
                    img = img.convert('RGB')
                img.save(thumb_path, quality=85, optimize=True)
            print(f"Generated thumbnail for {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Thumbnail generation complete.")