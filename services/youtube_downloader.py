# services/youtube_downloader.py

import yt_dlp
import os
import uuid

def download_youtube_video(video_url, download_dir="videos"):
    """
    Downloads a YouTube video as MP4 using yt-dlp.
    Returns the final path of the downloaded MP4.
    """
    os.makedirs(download_dir, exist_ok=True)
    
    # We'll generate a random filename to avoid collisions
    random_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(download_dir, f"{random_id}__%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "verbose": True,
        "force_ipv4": True
    }


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            # The final name after merging is typically .mp4
            downloaded_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(downloaded_filename)
            final_path = base + ".mp4"
            
            # If yt-dlp didn't rename automatically:
            if not os.path.exists(final_path) and os.path.exists(downloaded_filename):
                os.rename(downloaded_filename, final_path)
                
            return final_path
    except Exception as e:
        print(f"[ERROR] YouTube download failed: {e}")
        return None
