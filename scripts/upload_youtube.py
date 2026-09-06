"""
Uploads a finished video to YouTube using a pre-generated OAuth refresh token
(so it can run headlessly in GitHub Actions with no browser).

Required env vars:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""

import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def upload_video(file_path, title, description, tags, category_id="26", is_short=False):
    """category_id 26 = Howto & Style (fits home remedies well)."""
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://www.youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    import json
    import sys

    kind = sys.argv[1] if len(sys.argv) > 1 else "long"  # "long" or "short"

    state_dir = os.path.join(os.path.dirname(__file__), "..", "state")
    with open(os.path.join(state_dir, "today_plan.json"), "r", encoding="utf-8") as f:
        plan = json.load(f)

    if kind == "long":
        video_path = os.path.join(state_dir, "output", "long_video.mp4")
        meta = plan["long_video"]
        upload_video(video_path, meta["title"], meta["description"], meta["tags"], is_short=False)
    else:
        video_path = os.path.join(state_dir, "output", "short_video.mp4")
        meta = plan["short_video"]
        desc = meta["description"]
        if "#Shorts" not in desc:
            desc += "\n\n#Shorts"
        upload_video(video_path, meta["title"], desc, meta["tags"], is_short=True)
