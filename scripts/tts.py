"""
Text-to-speech using edge-tts (free, no API key) with a Hindi voice.
Generates one MP3 per long-video section, plus one MP3 for the short video.
"""

import asyncio
import json
import os

import edge_tts

VOICE = "hi-IN-SwaraNeural"  # warm female Hindi voice; alt: hi-IN-MadhurNeural (male)
RATE = "-2%"  # slightly slower, warm "daadi" pacing

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "state", "audio")


async def _synth(text, out_path):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(out_path)


def synth_text(text, out_path):
    asyncio.run(_synth(text, out_path))


def generate_all_audio(plan):
    os.makedirs(AUDIO_DIR, exist_ok=True)

    long_paths = []
    for i, section in enumerate(plan["long_video"]["script_sections"]):
        out_path = os.path.join(AUDIO_DIR, f"long_section_{i:02d}.mp3")
        synth_text(section["narration_hi"], out_path)
        long_paths.append(out_path)

    short_path = os.path.join(AUDIO_DIR, "short.mp3")
    synth_text(plan["short_video"]["narration_hi"], short_path)

    return long_paths, short_path


if __name__ == "__main__":
    plan_path = os.path.join(os.path.dirname(__file__), "..", "state", "today_plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    long_paths, short_path = generate_all_audio(plan)
    print(f"Generated {len(long_paths)} long-video section audios and 1 short audio.")
