#!/usr/bin/env python3
# Fix Hugging Face cache warning - set environment variables BEFORE imports
import os
import sys

# Create and set custom cache directories in the project folder
cache_dir = os.path.join(os.getcwd(), "hf_cache")
os.makedirs(cache_dir, exist_ok=True)

# Set ALL the relevant environment variables
os.environ["TRANSFORMERS_CACHE"] = cache_dir
os.environ["HF_HOME"] = cache_dir
os.environ["HF_DATASETS_CACHE"] = cache_dir
os.environ["HUGGINGFACE_HUB_CACHE"] = cache_dir
os.environ["HUGGINGFACE_ASSETS_CACHE"] = cache_dir
os.environ["XDG_CACHE_HOME"] = cache_dir

# Now import the rest
import urllib.request
import shutil

# Create directory for models
model_dir = "models"
os.makedirs(model_dir, exist_ok=True)

# Direct download URL for TitaNet model from NVIDIA NGC
# The location is from: https://api.ngc.nvidia.com/v2/models/nvidia/nemo/titanet_large/versions/v1/files/titanet-l.nemo
ngc_url = "https://api.ngc.nvidia.com/v2/models/nvidia/nemo/titanet_large/versions/v1/files/titanet-l.nemo"
target_path = os.path.join(model_dir, "titanet_large.nemo")

# Only download if the file doesn't exist
if os.path.exists(target_path):
    print(f"Model already exists at {target_path}")
else:
    print(f"Downloading TitaNet model from NVIDIA NGC...")
    try:
        # Create a simple progress bar
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(int(downloaded * 100 / total_size), 100)
            sys.stdout.write(f"\rDownloading: {percent}% [{downloaded} / {total_size}]")
            sys.stdout.flush()
        
        # Download the file
        urllib.request.urlretrieve(ngc_url, target_path, reporthook=report_progress)
        print(f"\nModel successfully downloaded to {target_path}")
    except Exception as e:
        print(f"Error downloading the model: {e}")
        print("You may need to download it manually.")
        sys.exit(1)

print("\nModel ready to use!")
print("You can now run speaker_id_testing.py with your audio file.") 