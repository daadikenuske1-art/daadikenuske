"""
Fetches stock video clips (falling back to photos) from Pexels for a list of
English visual keywords. Free API, requires PEXELS_API_KEY.
"""

import os
import time

import requests

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/videos/search"
PEXELS_PHOTO_SEARCH = "https://api.pexels.com/v1/search"

VISUALS_DIR = os.path.join(os.path.dirname(__file__), "..", "state", "visuals")


def _headers():
    return {"Authorization": os.environ["PEXELS_API_KEY"]}


def _pick_best_video_file(video, min_width=1080):
    files = video.get("video_files", [])
    # prefer mp4, closest to min_width without going too huge
    candidates = [f for f in files if f.get("file_type") == "video/mp4"]
    if not candidates:
        return None
    candidates.sort(key=lambda f: abs((f.get("width") or 0) - min_width))
    return candidates[0]


def search_video_clip(keyword, orientation="landscape"):
    params = {"query": keyword, "per_page": 5, "orientation": orientation}
    r = requests.get(PEXELS_VIDEO_SEARCH, headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    videos = data.get("videos", [])
    if not videos:
        return None
    return _pick_best_video_file(videos[0])


def search_photo(keyword, orientation="landscape"):
    params = {"query": keyword, "per_page": 5, "orientation": orientation}
    r = requests.get(PEXELS_PHOTO_SEARCH, headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    photos = data.get("photos", [])
    if not photos:
        return None
    return photos[0]["src"]["large2x"]


def download_file(url, out_path):
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    return out_path


def fetch_visual_for_keyword(keyword, out_dir, index, orientation="landscape"):
    os.makedirs(out_dir, exist_ok=True)
    try:
        video_file = search_video_clip(keyword, orientation=orientation)
        if video_file:
            out_path = os.path.join(out_dir, f"clip_{index:03d}.mp4")
            download_file(video_file["link"], out_path)
            return {"type": "video", "path": out_path}
    except requests.RequestException:
        pass

    time.sleep(1)  # be polite to rate limits before falling back

    try:
        photo_url = search_photo(keyword, orientation=orientation)
        if photo_url:
            out_path = os.path.join(out_dir, f"clip_{index:03d}.jpg")
            download_file(photo_url, out_path)
            return {"type": "image", "path": out_path}
    except requests.RequestException:
        pass

    return None


def fetch_all_for_plan(plan):
    """Downloads visuals for every long-video section and the short video.
    Returns dict: {"long": [[assets...], ...], "short": [assets...]}
    """
    long_assets = []
    idx = 0
    for section in plan["long_video"]["script_sections"]:
        section_assets = []
        for kw in section["visual_keywords"]:
            asset = fetch_visual_for_keyword(
                kw, os.path.join(VISUALS_DIR, "long"), idx, orientation="landscape"
            )
            if asset:
                section_assets.append(asset)
            idx += 1
            time.sleep(0.5)
        long_assets.append(section_assets)

    short_assets = []
    for i, kw in enumerate(plan["short_video"]["visual_keywords"]):
        asset = fetch_visual_for_keyword(
            kw, os.path.join(VISUALS_DIR, "short"), i, orientation="portrait"
        )
        if asset:
            short_assets.append(asset)
        time.sleep(0.5)

    return {"long": long_assets, "short": short_assets}


if __name__ == "__main__":
    import json

    plan_path = os.path.join(os.path.dirname(__file__), "..", "state", "today_plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    assets = fetch_all_for_plan(plan)
    print(
        f"Fetched visuals: {sum(len(s) for s in assets['long'])} for long video, "
        f"{len(assets['short'])} for short video."
    )
