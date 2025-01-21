# services/video_stacker.py
import os
import subprocess

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

def create_vertical_zoom(ffmpeg_path, input_video, output_video, final_height=1080, final_width=1920):
    """
    Creates a vertical layout from a horizontal video:
     - The bottom layer is the original scaled video
     - The top layer is a cropped/zoomed portion
     - Then they are stacked vertically
    """
    # Example filter:
    filter_complex = (
        "[0:v]scale=1920:-1[v1];"  
        "[v1]crop=1920:1080:0:(ih-1080)/2[vzoom];"
        "[vzoom][v1]vstack=inputs=2[outv]"
    )

    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_video,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_video
    ]
    print("[FFmpeg create_vertical_zoom]", " ".join(cmd))
    subprocess.run(cmd, check=True)

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
