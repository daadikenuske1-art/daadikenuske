"""
Shared ffmpeg/ffprobe helpers.
"""

import json
import os
import subprocess
import textwrap


def ffprobe_duration(path):
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", path,
        ],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(out.stdout)
    return float(data["format"]["duration"])


def run_ffmpeg(args):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    subprocess.run(cmd, check=True)


def make_srt(text, duration, out_path, chars_per_line=22, lines_per_cue=2, seconds_per_cue=4.0):
    """Splits `text` into wrapped cues spread evenly across `duration` seconds."""
    wrapped_lines = textwrap.wrap(text, width=chars_per_line) or [text]
    cues = []
    for i in range(0, len(wrapped_lines), lines_per_cue):
        cues.append("\n".join(wrapped_lines[i:i + lines_per_cue]))
    if not cues:
        cues = [text]

    n = len(cues)
    per_cue = max(duration / n, 1.0)

    def fmt_ts(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(out_path, "w", encoding="utf-8") as f:
        for i, cue in enumerate(cues):
            start = i * per_cue
            end = min((i + 1) * per_cue, duration)
            f.write(f"{i + 1}\n")
            f.write(f"{fmt_ts(start)} --> {fmt_ts(end)}\n")
            f.write(f"{cue}\n\n")

    return out_path


def build_visual_track(assets, duration, out_path, width, height):
    """Builds a silent video track of exactly `duration` seconds from a list of
    {"type": "video"|"image", "path": ...} assets, evenly split and scaled/cropped
    to fill the given canvas."""
    if not assets:
        # solid warm background as ultimate fallback
        run_ffmpeg([
            "-f", "lavfi", "-i", f"color=c=0xFFF3E0:s={width}x{height}:d={duration}",
            "-t", str(duration), out_path,
        ])
        return out_path

    n = len(assets)
    per_asset = max(duration / n, 1.5)
    segment_paths = []
    tmp_dir = os.path.join(os.path.dirname(out_path), "tmp_segments")
    os.makedirs(tmp_dir, exist_ok=True)

    for i, asset in enumerate(assets):
        seg_out = os.path.join(tmp_dir, f"seg_{i:03d}.mp4")
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},fps=30,setsar=1"
        )
        if asset["type"] == "video":
            run_ffmpeg([
                "-stream_loop", "-1", "-i", asset["path"],
                "-t", str(per_asset), "-vf", vf, "-an", seg_out,
            ])
        else:
            vf_img = (
                f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
                f"crop={width * 2}:{height * 2},"
                f"zoompan=z='min(zoom+0.0008,1.15)':d={int(per_asset * 30)}:s={width}x{height}:fps=30,"
                f"setsar=1"
            )
            run_ffmpeg([
                "-loop", "1", "-i", asset["path"],
                "-t", str(per_asset), "-vf", vf_img, "-an", seg_out,
            ])
        segment_paths.append(seg_out)

    concat_list = os.path.join(tmp_dir, "concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in segment_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    run_ffmpeg([
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path,
    ])
    return out_path


def mux_audio_video(video_path, audio_path, out_path):
    run_ffmpeg([
        "-i", video_path, "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        "-shortest", out_path,
    ])
    return out_path


def burn_subtitles(video_path, srt_path, out_path, font_name="Noto Sans Devanagari", font_size=16, vertical=False):
    margin_v = 120 if vertical else 60
    style = (
        f"FontName={font_name},FontSize={font_size},PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=0,"
        f"Alignment=2,MarginV={margin_v}"
    )
    srt_escaped = srt_path.replace(":", "\\:")
    run_ffmpeg([
        "-i", video_path,
        "-vf", f"subtitles={srt_escaped}:force_style='{style}'",
        "-c:a", "copy", out_path,
    ])
    return out_path


def concat_videos(paths, out_path):
    tmp_dir = os.path.dirname(out_path)
    concat_list = os.path.join(tmp_dir, "final_concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    run_ffmpeg([
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", out_path,
    ])
    return out_path
