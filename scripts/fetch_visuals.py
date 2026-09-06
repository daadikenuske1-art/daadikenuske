"""
Generates AI images (via Gemini's native image generation) that precisely match
each section's content, replacing generic stock footage/photos. Uses
GEMINI_API_KEY (already required by generate_script.py).
"""

import os
import time

import google.generativeai as genai

GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image"

VISUALS_DIR = os.path.join(os.path.dirname(__file__), "..", "state", "visuals")

STYLE_SUFFIX = (
    ", photorealistic, warm natural lighting, authentic Indian home/kitchen setting, "
    "no text or watermarks, no logos"
)


def _configure():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def generate_image(prompt, out_path, max_retries=3):
    """Generates a single image for `prompt` and saves it to `out_path`.
    Returns out_path on success, or None if generation failed after retries."""
    model = genai.GenerativeModel(GEMINI_IMAGE_MODEL)
    full_prompt = prompt.strip() + STYLE_SUFFIX

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_modalities=["TEXT", "IMAGE"]
                ),
            )
            for part in response.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.mime_type.startswith("image"):
                    with open(out_path, "wb") as f:
                        f.write(inline.data)
                    return out_path
        except Exception:
            pass
        time.sleep(3 * (attempt + 1))
    return None


def fetch_all_for_plan(plan):
    """Generates AI images for every long-video section and the short video.
    Returns dict: {"long": [[assets...], ...], "short": [assets...]}
    (assets are {"type": "image", "path": ...}, same shape the ffmpeg
    assembly step already expects.)
    """
    _configure()

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
