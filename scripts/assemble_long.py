"""
Assembles the long-form video (1920x1080, landscape) from per-section audio + visuals.
"""

import json
import os

from ffmpeg_utils import (
    ffprobe_duration, build_visual_track, mux_audio_video,
    burn_subtitles, concat_videos,
)

WIDTH, HEIGHT = 1920, 1080
STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")
WORK_DIR = os.path.join(STATE_DIR, "work_long")
OUTPUT_PATH = os.path.join(STATE_DIR, "output", "long_video.mp4")


def assemble_long_video(plan, audio_paths, visual_assets_per_section):
    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    section_final_paths = []
    for i, section in enumerate(plan["long_video"]["script_sections"]):
        audio_path = audio_paths[i]
        duration = ffprobe_duration(audio_path)
        assets = visual_assets_per_section[i]

        raw_video = os.path.join(WORK_DIR, f"section_{i:02d}_raw.mp4")
        build_visual_track(assets, duration, raw_video, WIDTH, HEIGHT)

        muxed = os.path.join(WORK_DIR, f"section_{i:02d}_muxed.mp4")
        mux_audio_video(raw_video, audio_path, muxed)

        srt_path = os.path.join(WORK_DIR, f"section_{i:02d}.srt")
        from ffmpeg_utils import make_srt
        make_srt(section["narration_hi"], duration, srt_path)

        captioned = os.path.join(WORK_DIR, f"section_{i:02d}_captioned.mp4")
        burn_subtitles(muxed, srt_path, captioned, vertical=False)

        section_final_paths.append(captioned)

    concat_videos(section_final_paths, OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    plan_path = os.path.join(STATE_DIR, "today_plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    audio_dir = os.path.join(STATE_DIR, "audio")
    audio_paths = [
        os.path.join(audio_dir, f"long_section_{i:02d}.mp3")
        for i in range(len(plan["long_video"]["script_sections"]))
    ]

    assets_path = os.path.join(STATE_DIR, "visual_assets.json")
    with open(assets_path, "r", encoding="utf-8") as f:
        assets = json.load(f)

    out = assemble_long_video(plan, audio_paths, assets["long"])
    print(f"Long video assembled: {out}")
