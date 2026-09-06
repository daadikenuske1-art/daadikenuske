"""
Assembles the Shorts video (1080x1920, portrait, <=30s) from the short audio + visuals.
"""

import json
import os

from ffmpeg_utils import (
    ffprobe_duration, build_visual_track, mux_audio_video,
    burn_subtitles, make_srt,
)

WIDTH, HEIGHT = 1080, 1920
STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")
WORK_DIR = os.path.join(STATE_DIR, "work_short")
OUTPUT_PATH = os.path.join(STATE_DIR, "output", "short_video.mp4")


def assemble_short_video(plan, audio_path, visual_assets):
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    duration = ffprobe_duration(audio_path)
    duration = min(duration, 30.0)

    raw_video = os.path.join(WORK_DIR, "short_raw.mp4")
    build_visual_track(visual_assets, duration, raw_video, WIDTH, HEIGHT)

    muxed = os.path.join(WORK_DIR, "short_muxed.mp4")
    mux_audio_video(raw_video, audio_path, muxed)

    srt_path = os.path.join(WORK_DIR, "short.srt")
    make_srt(
        plan["short_video"]["narration_hi"], duration, srt_path,
        chars_per_line=18, lines_per_cue=2,
    )

    burn_subtitles(muxed, srt_path, OUTPUT_PATH, font_size=22, vertical=True)
    return OUTPUT_PATH


if __name__ == "__main__":
    plan_path = os.path.join(STATE_DIR, "today_plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    audio_path = os.path.join(STATE_DIR, "audio", "short.mp3")

    assets_path = os.path.join(STATE_DIR, "visual_assets.json")
    with open(assets_path, "r", encoding="utf-8") as f:
        assets = json.load(f)

    out = assemble_short_video(plan, audio_path, assets["short"])
    print(f"Short video assembled: {out}")
