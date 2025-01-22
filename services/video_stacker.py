# services/video_stacker.py
import os
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

def process_videos(ffmpeg_path, videos):
    """
    Process multiple video trimming tasks in parallel.
    Each task trims a video using FFmpeg based on the provided input, start, end, and output.
    """
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                trim_video, ffmpeg_path, video["input"], video["start"], video["end"], video["output"]
            )
            for video in videos
        ]
        for future in futures:
            future.result()  # Wait for all tasks to complete

def trim_video(ffmpeg_path, input_path, start_time, end_time, output_path):
    """
    Trim a video using FFmpeg from start_time to end_time (in seconds).
    """
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",
        output_path
    ]
    print("[FFmpeg trim_video]", " ".join(cmd))
    subprocess.run(cmd, check=True)

def stack_vertical(ffmpeg_path, top_video, bottom_video, output_video):
    """
    Stacks two videos vertically, scaling them both to 1920 width if desired.
    """
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", top_video,
        "-i", bottom_video,
        "-filter_complex",
        "[0:v]scale=1920:-1[v0];[1:v]scale=1920:-1[v1];[v0][v1]vstack=inputs=2",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_video
    ]
    print("[FFmpeg stack_vertical]", " ".join(cmd))
    subprocess.run(cmd, check=True)
def get_resolution(ffmpeg_path, input_video):
    """
    Get the resolution of a video using ffprobe.
    """
    cmd = [
        ffmpeg_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "v:0",
        input_video
    ]
    try:
        output = subprocess.check_output(cmd).decode("utf-8")
        streams = json.loads(output).get("streams", [])
        if streams:
            return streams[0].get("width", 0), streams[0].get("height", 0)
        return 0, 0  # No video stream
    except subprocess.CalledProcessError:
        print(f"[ERROR] Failed to get resolution for: {input_video}")
        return 0, 0  # Fallback if FFmpeg fails
    
def create_vertical_zoom(ffmpeg_path, input_video, output_video):
    """
    Create a vertical zoom effect or pad the video if the resolution is too small.
    """
    # Dynamically get video resolution
    width, height = get_resolution(ffmpeg_path, input_video)
    if width == 0 or height == 0:
        raise ValueError(f"No valid video stream found in {input_video}")

    # Adjust filter graph based on resolution
    if height < 1080:
        # Use padding for smaller videos
        filter_graph = (
            "scale=1920:-1:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
        )
    else:
        # Crop for larger videos
        filter_graph = (
            "[0:v]scale=1920:-1[v1];"
            "[v1]crop=1920:1080:0:(ih-1080)/2[vzoom];"
            "[vzoom][v1]vstack=inputs=2[outv]"
        )

    # Build FFmpeg command
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_video,
        "-filter_complex", filter_graph,
        "-c:v", "libx264",
        "-r", "30",
        "-c:a", "aac",
        output_video
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg failed: {e}")
        raise



def split_into_chunks(ffmpeg_path, input_video, chunk_length, chunk_folder="output_chunks"):
    """
    Split the video into multiple segments of chunk_length (in seconds).
    """
    os.makedirs(chunk_folder, exist_ok=True)
    chunk_pattern = os.path.join(chunk_folder, "chunk_%03d.mp4")

    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_video,
        "-c", "copy",
        "-map", "0",
        "-f", "segment",
        "-segment_time", str(chunk_length),
        "-reset_timestamps", "1",
        chunk_pattern
    ]
    print("[FFmpeg split_into_chunks]", " ".join(cmd))
    subprocess.run(cmd, check=True)
    
    return chunk_folder
