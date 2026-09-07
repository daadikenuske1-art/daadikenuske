"""
Fetches royalty-free background photos from Pexels that match each section's
content, using the same detailed visual-keyword prompts Gemini writes for the
script. Requires PEXELS_API_KEY.

Switched away from Gemini's native image generation (gemini-3.1-flash-image)
because that model has a hard zero-quota limit on the free API tier
(429 RESOURCE_EXHAUSTED on every call) — it needs a paid/billing-enabled
Google Cloud project. Pexels needs no billing and is reliable.
"""

import os
import re
import time

import requests

PEXELS_PHOTO_SEARCH = "https://api.pexels.com/v1/search"
VISUALS_DIR = os.path.join(os.path.dirname(__file__), "..", "state", "visuals")


def _headers():
    return {"Authorization": os.environ["PEXELS_API_KEY"]}


def _simplify_query(prompt):
    """Turns a long, detailed AI-image-style prompt into a short search query
    Pexels can actually match against (its search works best on 2-5 words)."""
    text = prompt.split(",")[0].strip()
    text = re.sub(r"^(a|an|the)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[^A-Za-z0-9 ]", " ", text)
    words = [w for w in text.split() if w]
    return " ".join(words[:6]) or "indian home remedy ingredients"


def _download_photo(query, out_path, max_retries=3):
    """Searches Pexels for `query` and saves the top matching photo to
    `out_path`. Returns out_path on success, None if it failed after
    retries (or no results were found)."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                PEXELS_PHOTO_SEARCH,
                headers=_headers(),
                params={"query": query, "per_page": 5, "orientation": "portrait"},
                timeout=20,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
            if not photos:
                print(f"  [visuals] No Pexels results for query: {query!r}")
                return None
            src = photos[0].get("src", {})
            photo_url = src.get("large") or src.get("original") or src.get("large2x")
            if not photo_url:
                return None
            img_resp = requests.get(photo_url, timeout=30)
            img_resp.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(img_resp.content)
            return out_path
        except Exception as e:
            print(f"  [visuals] Attempt {attempt + 1}/{max_retries} failed for query "
                  f"{query!r}: {e}")
        time.sleep(2 * (attempt + 1))
    return None


def fetch_all_for_plan(plan):
    """Fetches a matching Pexels photo for every long-video section and the
    short video. Returns dict: {"long": [[assets...], ...], "short": [assets...]}
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
            query = _simplify_query(kw)
            out_path = os.path.join(long_dir, f"img_{idx:03d}.jpg")
            result = _download_photo(query, out_path)
            if result:
                section_assets.append({"type": "image", "path": result})
            idx += 1
            time.sleep(1)
        long_assets.append(section_assets)

    short_assets = []
    short_dir = os.path.join(VISUALS_DIR, "short")
    os.makedirs(short_dir, exist_ok=True)
    for i, kw in enumerate(plan["short_video"]["visual_keywords"]):
        query = _simplify_query(kw)
        out_path = os.path.join(short_dir, f"img_{i:03d}.jpg")
        result = _download_photo(query, out_path)
        if result:
            short_assets.append({"type": "image", "path": result})
        time.sleep(1)

    total_long = sum(len(s) for s in long_assets)
    total_short = len(short_assets)
    print(f"[visuals] Downloaded {total_long} long-video images, {total_short} short-video images from Pexels.")
    if total_long == 0 and total_short == 0:
        print("[visuals] WARNING: zero images downloaded — video will fall back to a solid background.")

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
