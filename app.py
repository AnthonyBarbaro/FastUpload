from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid

from config import FFMPEG_PATH, TEMP_DIR, OUTPUT_DIR
from services.youtube_downloader import download_youtube_video
from services.video_subtitler import transcribe_video, burn_subtitles
from services.video_stacker import (
    trim_video, stack_vertical, create_vertical_zoom, split_into_chunks
)

app = Flask(__name__)

# Ensure temp folders exist
app.config["UPLOAD_FOLDER"] = os.path.join(TEMP_DIR, "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Renders a form (GET) allowing user to:
      - Provide a YouTube link or upload a local file
      - Pick a bottom video from a dropdown (or none)
      - Specify optional trimming (start_time, end_time)
      - Choose vertical zoom or chunk splitting

    Processes the video (POST) accordingly.
    """
    if request.method == "GET":
        # List available bottom videos from /videos folder (besides main videos).
        bottom_videos = []
        video_folder = os.path.join(os.getcwd(), "videos")
        if os.path.isdir(video_folder):
            # Collect all .mp4 files
            bottom_videos = [
                f for f in os.listdir(video_folder)
                if f.endswith(".mp4") and "main" not in f
            ]
        
        return render_template("index.html", bottom_videos=bottom_videos)

    # POST: process form submission
    else:
        # 1) Extract form inputs
        youtube_url = request.form.get("youtube_url", "").strip()
        local_file = request.files.get("local_file")
        start_time = float(request.form.get("start_time", "0") or 0)
        end_time = float(request.form.get("end_time", "0") or 0)
        bottom_video_choice = request.form.get("bottom_video_choice", "")  # from dropdown
        do_zoom = request.form.get("do_zoom") == "on"
        chunk = request.form.get("chunk") == "on"

        # 2) Acquire main video: either from YouTube or local upload
        main_video_path = None
        if youtube_url:
            main_video_path = download_youtube_video(youtube_url, download_dir=app.config["UPLOAD_FOLDER"])
        elif local_file and local_file.filename:
            filename = secure_filename(local_file.filename)
            main_video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            local_file.save(main_video_path)

        # Validate main video path
        if not main_video_path or not os.path.exists(main_video_path):
            return "Error: No valid main video found or download failed."

        # 3) (Optional) Trim if end_time > start_time
        if end_time > start_time:
            trimmed_name = f"{uuid.uuid4().hex[:8]}_trimmed.mp4"
            trimmed_path = os.path.join(TEMP_DIR, trimmed_name)
            trim_video(FFMPEG_PATH, main_video_path, start_time, end_time, trimmed_path)
            main_video_path = trimmed_path

        # 4) Transcribe + burn subtitles
        srt_file = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:8]}.srt")
        transcribe_video(main_video_path, srt_path=srt_file, model_size="tiny")

        subtitled_name = f"{uuid.uuid4().hex[:8]}_subtitled.mp4"
        subtitled_path = os.path.join(TEMP_DIR, subtitled_name)
        burn_subtitles(FFMPEG_PATH, main_video_path, srt_file, subtitled_path)

        # 5) Stacking / Zoom
        final_name = f"{uuid.uuid4().hex[:8]}_final.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_name)

        # If user selected a bottom video from dropdown
        if bottom_video_choice:
            chosen_bottom_path = os.path.join("videos", bottom_video_choice)
            # stack with bottom video
            stack_vertical(FFMPEG_PATH, subtitled_path, chosen_bottom_path, final_path)
        elif do_zoom:
            # create vertical zoom
            create_vertical_zoom(FFMPEG_PATH, subtitled_path, final_path)
        else:
            # no stacking or zoom - just rename
            os.rename(subtitled_path, final_path)

        # 6) (Optional) split into chunks
        if chunk:
            chunk_folder = os.path.join(OUTPUT_DIR, f"chunks_{uuid.uuid4().hex[:8]}")
            os.makedirs(chunk_folder, exist_ok=True)
            split_into_chunks(FFMPEG_PATH, final_path, 60, chunk_folder=chunk_folder)

            chunks = sorted(os.listdir(chunk_folder))
            chunk_paths = [os.path.join(chunk_folder, c) for c in chunks if c.endswith(".mp4")]
            return render_template("result.html", final_video=None, chunk_files=chunk_paths)
        
        # 7) Return final
        return render_template("result.html", final_video=final_path, chunk_files=None)


@app.route("/download/<path:filename>")
def download_file(filename):
    """
    Lets the user download a file from the OUTPUT_DIR or chunk folder.
    """
    directory = os.path.dirname(filename)
    basename = os.path.basename(filename)
    return send_from_directory(directory or OUTPUT_DIR, basename, as_attachment=True)


if __name__ == "__main__":
    # Run on port 5000, accessible outside container if you're using Docker
    app.run(host="0.0.0.0", port=5000)
