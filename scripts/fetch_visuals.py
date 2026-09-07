"""
Generates AI images (via Gemini's native image generation) that precisely match
each section's content, replacing generic stock footage/photos. Uses
GEMINI_API_KEY (already required by generate_script.py).

Uses the google-genai SDK (the current, supported client for Gemini image
generation) rather than the older google-generativeai package — the older
package's GenerativeModel.generate_content() does not reliably support
response_modalities=["IMAGE"], which silently produced zero images.
"""

import os
import time
import traceback

from google import genai
from google.genai import types

GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image"

VISUALS_DIR = os.path.join(os.path.dirname(__file__), "..", "state", "visuals")

STYLE_SUFFIX = (
    ", photorealistic, warm natural lighting, authentic Indian home/kitchen setting, "
    "no text or watermarks, no logos"
)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def generate_image(prompt, out_path, max_retries=3):
    """Generates a single image for `prompt` and saves it to `out_path`.
    Returns out_path on success, or None if generation failed after retries."""
    client = _get_client()
    full_prompt = prompt.strip() + STYLE_SUFFIX

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"]
                ),
            )
            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if not content:
                    continue
                for part in content.parts or []:
                    inline = getattr(part, "inline_data", None)
                    if inline and inline.data:
                        with open(out_path, "wb") as f:
                            f.write(inline.data)
                        return out_path
            print(f"  [visuals] No image data in response for prompt: {prompt[:80]!r}")
        except Exception as e:
            print(f"  [visuals] Attempt {attempt + 1}/{max_retries} failed for prompt "
                  f"{prompt[:80]!r}: {e}")
            traceback.print_exc()
        time.sleep(3 * (attempt + 1))
    return None


def fetch_all_for_plan(plan):
    """Generates AI images for every long-video section and the short video.
    Returns dict: {"long": [[assets...], ...], "short": [assets...]}
    (assets are {"type": "image", "path": ...}, same shape the ffmpeg
    assembly step already expects.)
    """
    long_assets = []
    idx = 0
    long_dir = os.path.join(VISUALS_DIR, "long")
    os.makedirs(long_dir, exist_ok=True)
    for section in plan["long_video"]["script_sections"]:
        section_assets = []
        for kw in section["visual_keywords"]:
            out_path = os.path.join(long_dir, f"img_{idx:03d}.png")
            result = generate_image(kw, out_path)
            if result:
                section_assets.append({"type": "image", "path": result})
            idx += 1
            time.sleep(2)
        long_assets.append(section_assets)

    short_assets = []
    short_dir = os.path.join(VISUALS_DIR, "short")
    os.makedirs(short_dir, exist_ok=True)
    for i, kw in enumerate(plan["short_video"]["visual_keywords"]):
        out_path = os.path.join(short_dir, f"img_{i:03d}.png")
        result = generate_image(kw, out_path)
        if result:
            short_assets.append({"type": "image", "path": result})
        time.sleep(2)

    total_long = sum(len(s) for s in long_assets)
    total_short = len(short_assets)
    print(f"[visuals] Generated {total_long} long-video images, {total_short} short-video images.")
    if total_long == 0 and total_short == 0:
        print("[visuals] WARNING: zero images generated — video will fall back to a solid background.")

    return {"long": long_assets, "short": short_assets}


if __name__ == "__main__":
    import json

    plan_path = os.path.join(os.path.dirname(__file__), "..", "state", "today_plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    assets = fetch_all_for_plan(plan)
    print(
        f"Generated visuals: {sum(len(s) for s in assets['long'])} for long video, "
        f"{len(assets['short'])} for short video."
    )
