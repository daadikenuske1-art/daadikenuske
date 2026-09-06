"""
Orchestrates the full daily pipeline:
  1. Generate today's content plan (Gemini) — topic, long script, short script.
  2. Generate TTS audio (Hindi) for every section + the short.
  3. Fetch stock visuals (Pexels) for every section + the short.
  4. Assemble the long video and the short video (ffmpeg).
  5. Upload both to YouTube.

Run with: python main.py
"""

import json
import os
import sys

from generate_script import generate_content_plan
from tts import generate_all_audio
from fetch_visuals import fetch_all_for_plan
from assemble_long import assemble_long_video
from assemble_short import assemble_short_video
from upload_youtube import upload_video

STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")


def main():
    os.makedirs(STATE_DIR, exist_ok=True)

    print("=== Step 1: Generating content plan with Gemini ===")
    plan = generate_content_plan()
    with open(os.path.join(STATE_DIR, "today_plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"Topic: {plan['topic']}")

    print("=== Step 2: Generating TTS audio ===")
    long_audio_paths, short_audio_path = generate_all_audio(plan)

    print("=== Step 3: Fetching stock visuals ===")
    assets = fetch_all_for_plan(plan)
    with open(os.path.join(STATE_DIR, "visual_assets.json"), "w", encoding="utf-8") as f:
        json.dump(assets, f, ensure_ascii=False, indent=2)

    print("=== Step 4: Assembling long video ===")
    long_video_path = assemble_long_video(plan, long_audio_paths, assets["long"])
    print(f"Long video ready: {long_video_path}")

    print("=== Step 5: Assembling short video ===")
    short_video_path = assemble_short_video(plan, short_audio_path, assets["short"])
    print(f"Short video ready: {short_video_path}")

    if os.environ.get("SKIP_UPLOAD") == "1":
        print("SKIP_UPLOAD=1 set — skipping YouTube upload (dry run).")
        return

    print("=== Step 6: Uploading long video to YouTube ===")
    meta = plan["long_video"]
    upload_video(long_video_path, meta["title"], meta["description"], meta["tags"])

    print("=== Step 7: Uploading short video to YouTube ===")
    meta = plan["short_video"]
    desc = meta["description"]
    if "#Shorts" not in desc:
        desc += "\n\n#Shorts"
    upload_video(short_video_path, meta["title"], desc, meta["tags"], is_short=True)

    print("=== Done ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"PIPELINE FAILED: {e}", file=sys.stderr)
        raise
