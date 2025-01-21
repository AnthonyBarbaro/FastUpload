# config.py
import os

# If you installed ffmpeg system-wide, just use "ffmpeg" here:
FFMPEG_PATH = "ffmpeg"

# For storing intermediate or final videos:
TEMP_DIR = "temp"
OUTPUT_DIR = "output"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
