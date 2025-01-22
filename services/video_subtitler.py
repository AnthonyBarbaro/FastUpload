import math
import os
import subprocess
import whisper
from datetime import timedelta

def transcribe_video(
    video_path,
    srt_path="temp_subtitles.srt",
    model_size="tiny",
    words_per_sub=6  # <-- Control how many words per subtitle chunk
):
    """
    Transcribe the audio from a video using OpenAI Whisper and save smaller
    subtitle chunks in SRT format for a more "fast-paced" reading experience.
    """

    # 1) Load the Whisper model
    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, verbose=False)

    # 2) We'll hold the new smaller subtitle segments here
    new_segments = []

    for seg in result["segments"]:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"].strip()

        # Split the segment into sub-chunks
        sub_chunks = split_segment_into_chunks(start, end, text, words_per_sub)
        new_segments.extend(sub_chunks)

    # 3) Convert new_segments -> SRT lines
    srt_lines = []
    for i, seg in enumerate(new_segments, start=1):
        start_ts = seconds_to_srt_timestamp(seg["start"])
        end_ts = seconds_to_srt_timestamp(seg["end"])
        text = seg["text"]
        srt_lines.append(f"{i}\n{start_ts} --> {end_ts}\n{text}\n\n")

    # 4) Write SRT file
    with open(srt_path, "w", encoding="utf-8") as f:
        f.writelines(srt_lines)

    return srt_path


def split_segment_into_chunks(start, end, text, words_per_sub=6):
    """
    Split a single Whisper segment into multiple smaller chunks,
    each showing fewer words. We distribute the original segment's
    duration across these sub-chunks proportionally.
    """
    words = text.split()
    total_words = len(words)
    duration = end - start

    # If there's fewer words than words_per_sub, just return one chunk
    if total_words <= words_per_sub:
        return [{"start": start, "end": end, "text": text}]

    chunks = []
    num_chunks = math.ceil(total_words / words_per_sub)

    # For each chunk, compute time slice
    # e.g., if segment is 4 seconds, and we have 2 sub-chunks, each is 2 seconds.
    chunk_duration = duration / num_chunks

    for i in range(num_chunks):
        chunk_start_time = start + i * chunk_duration
        chunk_end_time = start + (i + 1) * chunk_duration

        # Grab the portion of words for this chunk
        chunk_words = words[i * words_per_sub:(i + 1) * words_per_sub]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "start": chunk_start_time,
            "end": chunk_end_time,
            "text": chunk_text
        })

    return chunks


def burn_subtitles(ffmpeg_path, input_video, srt_file, output_video):
    """
    Use FFmpeg to burn the SRT subtitles into the video.
    """
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", input_video,
        "-vf", f"subtitles={srt_file}:force_style='FontSize=24,Outline=2,Shadow=1,MarginV=50'",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_video
    ]
    print("[FFmpeg burn_subtitles] ", " ".join(cmd))
    subprocess.run(cmd, check=True)


def seconds_to_srt_timestamp(seconds_float):
    """Convert float seconds to SRT timestamp format: HH:MM:SS,mmm."""
    td = timedelta(seconds=seconds_float)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = (total_seconds % 60)
    millis = int(td.microseconds / 1000.0)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
