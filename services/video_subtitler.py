# services/video_subtitler.py
import os
import subprocess
import whisper
from datetime import timedelta

def transcribe_video(video_path, srt_path="temp_subtitles.srt", model_size="tiny"):
    """
    Transcribe the audio from a video using OpenAI Whisper 
    and save subtitles in SRT format.
    """
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, verbose=False)

    # Convert segments to SRT
    srt_lines = []
    for i, seg in enumerate(result["segments"], start=1):
        start_ts = seconds_to_srt_timestamp(seg["start"])
        end_ts = seconds_to_srt_timestamp(seg["end"])
        text = seg["text"].strip()
        srt_lines.append(f"{i}\n{start_ts} --> {end_ts}\n{text}\n\n")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.writelines(srt_lines)
    
    return srt_path

def burn_subtitles(ffmpeg_path, input_video, srt_file, output_video):
    """
    Use FFmpeg to burn the SRT subtitles into the video.
    """
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_video,
        "-vf", f"subtitles={srt_file}:force_style='FontSize=18'",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_video
    ]
    print("[FFmpeg burn_subtitles] ", " ".join(cmd))
    subprocess.run(cmd, check=True)

def seconds_to_srt_timestamp(seconds_float):
    """Convert float seconds to SRT timestamp format: HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds_float)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = (total_seconds % 60)
    millis = int(td.microseconds / 1000.0)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
